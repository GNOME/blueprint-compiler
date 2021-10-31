# parse_tree.py
#
# Copyright 2021 James Westman <james@jwestman.net>
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This file is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

""" Utilities for parsing an AST from a token stream. """

import typing as T

from collections import defaultdict
from enum import Enum

from .ast import AstNode
from .errors import assert_true, CompilerBugError, CompileError
from .tokenizer import Token, TokenType


SKIP_TOKENS = [TokenType.COMMENT, TokenType.WHITESPACE]


class ParseResult(Enum):
    """ Represents the result of parsing. The extra EMPTY result is necessary
    to avoid freezing the parser: imagine a ZeroOrMore node containing a node
    that can match empty. It will repeatedly match empty and never advance
    the parser. So, ZeroOrMore stops when a failed *or empty* match is
    made. """

    SUCCESS = 0
    FAILURE = 1
    EMPTY   = 2

    def matched(self):
        return self == ParseResult.SUCCESS

    def succeeded(self):
        return self != ParseResult.FAILURE

    def failed(self):
        return self == ParseResult.FAILURE


class ParseGroup:
    """ A matching group. Match groups have an AST type, children grouped by
    type, and key=value pairs. At the end of parsing, the match groups will
    be converted to AST nodes by passing the children and key=value pairs to
    the AST node constructor. """

    def __init__(self, ast_type, start: int):
        self.ast_type = ast_type
        self.children: T.List[ParseGroup] = []
        self.keys: T.Dict[str, T.Any] = {}
        self.tokens: T.Dict[str, Token] = {}
        self.start = start
        self.end = None
        self.incomplete = False

    def add_child(self, child):
        self.children.append(child)

    def set_val(self, key, val, token):
        assert_true(key not in self.keys)

        self.keys[key] = val
        self.tokens[key] = token

    def to_ast(self) -> AstNode:
        """ Creates an AST node from the match group. """
        children = [child.to_ast() for child in self.children]

        try:
            return self.ast_type(self, children, self.keys, incomplete=self.incomplete)
        except TypeError as e:
            raise CompilerBugError(f"Failed to construct ast.{self.ast_type.__name__} from ParseGroup. See the previous stacktrace.")

    def __str__(self):
        result = str(self.ast_type.__name__)
        result += "".join([f"\n{key}: {val}" for key, val in self.keys.items()]) + "\n"
        result += "\n".join([str(child) for children in self.children.values() for child in children])
        return result.replace("\n", "\n  ")


class ParseContext:
    """ Contains the state of the parser. """

    def __init__(self, tokens, index=0):
        self.tokens = list(tokens)

        self.index = index
        self.start = index
        self.group = None
        self.group_keys = {}
        self.group_children = []
        self.last_group = None
        self.group_incomplete = False

        self.errors = []
        self.warnings = []


    def create_child(self):
        """ Creates a new ParseContext at this context's position. The new
        context will be used to parse one node. If parsing is successful, the
        new context will be applied to "self". If parsing fails, the new
        context will be discarded. """
        ctx = ParseContext(self.tokens, self.index)
        ctx.errors = self.errors
        ctx.warnings = self.warnings
        return ctx

    def apply_child(self, other):
        """ Applies a child context to this context. """

        if other.group is not None:
            # If the other context had a match group, collect all the matched
            # values into it and then add it to our own match group.
            for key, (val, token) in other.group_keys.items():
                other.group.set_val(key, val, token)
            for child in other.group_children:
                other.group.add_child(child)
            other.group.end = other.tokens[other.index - 1].end
            other.group.incomplete = other.group_incomplete
            self.group_children.append(other.group)
        else:
            # If the other context had no match group of its own, collect all
            # its matched values
            self.group_keys = {**self.group_keys, **other.group_keys}
            self.group_children += other.group_children
            self.group_incomplete |= other.group_incomplete

        self.index = other.index
        # Propagate the last parsed group down the stack so it can be easily
        # retrieved at the end of the process
        if other.group:
            self.last_group = other.group
        elif other.last_group:
            self.last_group = other.last_group


    def start_group(self, ast_type):
        """ Sets this context to have its own match group. """
        assert_true(self.group is None)
        self.group = ParseGroup(ast_type, self.tokens[self.index].start)

    def set_group_val(self, key, value, token):
        """ Sets a matched key=value pair on the current match group. """
        assert_true(key not in self.group_keys)
        self.group_keys[key] = (value, token)

    def set_group_incomplete(self):
        """ Marks the current match group as incomplete (it could not be fully
        parsed, but the parser recovered). """
        self.group_incomplete = True


    def skip(self):
        """ Skips whitespace and comments. """
        while self.index < len(self.tokens) and self.tokens[self.index].type in SKIP_TOKENS:
            self.index += 1

    def next_token(self) -> Token:
        """ Advances the token iterator and returns the next token. """
        self.skip()
        token = self.tokens[self.index]
        self.index += 1
        return token

    def peek_token(self) -> Token:
        """ Returns the next token without advancing the iterator. """
        self.skip()
        token = self.tokens[self.index]
        return token

    def is_eof(self) -> Token:
        return self.index >= len(self.tokens) or self.peek_token().type == TokenType.EOF


class ParseNode:
    """ Base class for the nodes in the parser tree. """

    def parse(self, ctx: ParseContext) -> ParseResult:
        """ Attempts to match the ParseNode at the context's current location. """
        start_idx = ctx.index
        inner_ctx = ctx.create_child()

        if self._parse(inner_ctx):
            ctx.apply_child(inner_ctx)
            if ctx.index == start_idx:
                return ParseResult.EMPTY
            else:
                return ParseResult.SUCCESS
        else:
            return ParseResult.FAILURE

    def _parse(self, ctx: ParseContext) -> bool:
        raise NotImplementedError()

    def err(self, message):
        """ Causes this ParseNode to raise an exception if it fails to parse.
        This prevents the parser from backtracking, so you should understand
        what it does and how the parser works before using it. """
        return Err(self, message)

    def expected(self, expect):
        """ Convenience method for err(). """
        return self.err("Expected " + expect)


class Err(ParseNode):
    """ ParseNode that emits a compile error if it fails to parse. """

    def __init__(self, child, message):
        self.child = child
        self.message = message

    def _parse(self, ctx):
        if self.child.parse(ctx).failed():
            start_idx = ctx.start
            while ctx.tokens[start_idx].type in SKIP_TOKENS:
                start_idx += 1

            start_token = ctx.tokens[start_idx]
            end_token = ctx.tokens[ctx.index]
            raise CompileError(self.message, start_token.start, end_token.end)
        return True


class Fail(ParseNode):
    """ ParseNode that emits a compile error if it parses successfully. """

    def __init__(self, child, message):
        self.child = child
        self.message = message

    def _parse(self, ctx):
        if self.child.parse(ctx).succeeded():
            start_idx = ctx.start
            while ctx.tokens[start_idx].type in SKIP_TOKENS:
                start_idx += 1

            start_token = ctx.tokens[start_idx]
            end_token = ctx.tokens[ctx.index]
            raise CompileError(self.message, start_token.start, end_token.end)
        return True


class Group(ParseNode):
    """ ParseNode that creates a match group. """
    def __init__(self, ast_type, child):
        self.ast_type = ast_type
        self.child = child

    def _parse(self, ctx: ParseContext) -> bool:
        ctx.skip()
        ctx.start_group(self.ast_type)
        return self.child.parse(ctx).succeeded()


class Sequence(ParseNode):
    """ ParseNode that attempts to match all of its children in sequence. """
    def __init__(self, *children):
        self.children = children

    def _parse(self, ctx) -> bool:
        for child in self.children:
            if child.parse(ctx).failed():
                return False
        return True


class Statement(ParseNode):
    """ ParseNode that attempts to match all of its children in sequence. If any
    child raises an error, the error will be logged but parsing will continue. """
    def __init__(self, *children):
        self.children = children

    def _parse(self, ctx) -> bool:
        for child in self.children:
            try:
                if child.parse(ctx).failed():
                    return False
            except CompileError as e:
                ctx.errors.append(e)
                ctx.set_group_incomplete(True)
                return True

        token = ctx.peek_token()
        if token.type != TokenType.STMT_END:
            ctx.errors.append(CompileError("Expected `;`", token.start, token.end))
        else:
            ctx.next_token()
        return True


class AnyOf(ParseNode):
    """ ParseNode that attempts to match exactly one of its children. Child
    nodes are attempted in order. """
    def __init__(self, *children):
        self.children = children

    def _parse(self, ctx):
        for child in self.children:
            if child.parse(ctx).succeeded():
                return True
        return False


class Until(ParseNode):
    """ ParseNode that repeats its child until a delimiting token is found. If
    the child does not match, one token is skipped and the match is attempted
    again. """
    def __init__(self, child, delimiter):
        self.child = child
        self.delimiter = delimiter

    def _parse(self, ctx):
        while not self.delimiter.parse(ctx).succeeded():
            try:
                if not self.child.parse(ctx).matched():
                    token = ctx.next_token()
                    ctx.errors.append(CompileError("Unexpected token", token.start, token.end))
            except CompileError as e:
                ctx.errors.append(e)
                ctx.next_token()

            if ctx.is_eof():
                return True

        return True


class ZeroOrMore(ParseNode):
    """ ParseNode that matches its child any number of times (including zero
    times). It cannot fail to parse. If its child raises an exception, one token
    will be skipped and parsing will continue. """
    def __init__(self, child):
        self.child = child


    def _parse(self, ctx):
        while True:
            try:
                if not self.child.parse(ctx).matched():
                    return True
            except CompileError as e:
                ctx.errors.append(e)
                ctx.next_token()


class Delimited(ParseNode):
    """ ParseNode that matches its first child any number of times (including zero
    times) with its second child in between and optionally at the end. """
    def __init__(self, child, delimiter):
        self.child = child
        self.delimiter = delimiter

    def _parse(self, ctx):
        while self.child.parse(ctx).matched() and self.delimiter.parse(ctx).matched():
            pass
        return True


class Optional(ParseNode):
    """ ParseNode that matches its child zero or one times. It cannot fail to
    parse. """
    def __init__(self, child):
        self.child = child

    def _parse(self, ctx):
        self.child.parse(ctx)
        return True


class StaticToken(ParseNode):
    """ Base class for ParseNodes that match a token type without inspecting
    the token's contents. """
    token_type: T.Optional[TokenType] = None

    def _parse(self, ctx: ParseContext) -> bool:
        return ctx.next_token().type == self.token_type

class StmtEnd(StaticToken):
    token_type = TokenType.STMT_END

class Eof(StaticToken):
    token_type = TokenType.EOF

class OpenBracket(StaticToken):
    token_type = TokenType.OPEN_BRACKET

class CloseBracket(StaticToken):
    token_type = TokenType.CLOSE_BRACKET

class OpenBlock(StaticToken):
    token_type = TokenType.OPEN_BLOCK

class CloseBlock(StaticToken):
    token_type = TokenType.CLOSE_BLOCK

class OpenParen(StaticToken):
    token_type = TokenType.OPEN_PAREN

class CloseParen(StaticToken):
    token_type = TokenType.CLOSE_PAREN

class Comma(StaticToken):
    token_type = TokenType.COMMA


class Op(ParseNode):
    """ ParseNode that matches the given operator. """
    def __init__(self, op):
        self.op = op

    def _parse(self, ctx: ParseContext) -> bool:
        token = ctx.next_token()
        if token.type != TokenType.OP:
            return False
        return str(token) == self.op


class UseIdent(ParseNode):
    """ ParseNode that matches any identifier and sets it in a key=value pair on
    the containing match group. """
    def __init__(self, key):
        self.key = key

    def _parse(self, ctx: ParseContext):
        token = ctx.next_token()
        if token.type != TokenType.IDENT:
            return False

        ctx.set_group_val(self.key, str(token), token)
        return True


class UseNumber(ParseNode):
    """ ParseNode that matches a number and sets it in a key=value pair on
    the containing match group. """
    def __init__(self, key):
        self.key = key

    def _parse(self, ctx: ParseContext):
        token = ctx.next_token()
        if token.type != TokenType.NUMBER:
            return False

        number = token.get_number()
        if number % 1.0 == 0:
            number = int(number)
        ctx.set_group_val(self.key, number, token)
        return True


class UseNumberText(ParseNode):
    """ ParseNode that matches a number, but sets its *original text* it in a
    key=value pair on the containing match group. """
    def __init__(self, key):
        self.key = key

    def _parse(self, ctx: ParseContext):
        token = ctx.next_token()
        if token.type != TokenType.NUMBER:
            return False

        ctx.set_group_val(self.key, str(token), token)
        return True


class UseQuoted(ParseNode):
    """ ParseNode that matches a quoted string and sets it in a key=value pair
    on the containing match group. """
    def __init__(self, key):
        self.key = key

    def _parse(self, ctx: ParseContext):
        token = ctx.next_token()
        if token.type != TokenType.QUOTED:
            return False

        string = (str(token)[1:-1]
            .replace("\\n", "\n")
            .replace("\\\"", "\"")
            .replace("\\\\", "\\"))
        ctx.set_group_val(self.key, string, token)
        return True


class UseLiteral(ParseNode):
    """ ParseNode that doesn't match anything, but rather sets a static key=value
    pair on the containing group. Useful for, e.g., property and signal flags:
    `Sequence(Keyword("swapped"), UseLiteral("swapped", True))` """
    def __init__(self, key, literal):
        self.key = key
        self.literal = literal

    def _parse(self, ctx: ParseContext):
        ctx.set_group_val(self.key, self.literal, None)
        return True


class Keyword(ParseNode):
    """ Matches the given identifier. """
    def __init__(self, kw):
        self.kw = kw

    def _parse(self, ctx: ParseContext):
        token = ctx.next_token()
        if token.type != TokenType.IDENT:
            return False

        return str(token) == self.kw
