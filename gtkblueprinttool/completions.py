# completions.py
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

import typing as T

from . import ast
from .lsp_utils import Completion, CompletionItemKind
from .parser import SKIP_TOKENS
from .tokenizer import TokenType, Token

Pattern = T.List[T.Tuple[TokenType, T.Optional[str]]]


def complete(ast_node: ast.AstNode, tokens: T.List[Token], idx: int) -> T.Iterator[Completion]:
    for child in ast_node.child_nodes:
        if child.group.start <= idx <= child.group.end:
            yield from complete(child, tokens, idx)
            return

    prev_tokens: T.List[Token] = []
    token_idx = 0

    # find the current token
    for i, token in enumerate(tokens):
        if token.start < idx <= token.end:
            token_idx = i

    # if the current token is an identifier, move to the token before it
    if tokens[token_idx].type == TokenType.IDENT:
        token_idx -= 1

    # collect the 5 previous non-skipped tokens
    while len(prev_tokens) < 5 and token_idx >= 0:
        token = tokens[token_idx]
        if token.type not in SKIP_TOKENS:
            prev_tokens.insert(0, token)
        token_idx -= 1

    for completer in ast_node.completers:
        yield from completer.completions(prev_tokens, ast_node)


class Completer:
    def __init__(self, func):
        self.func = func
        self.patterns: T.List = []
        self.ast_type: T.Type[ast.AstNode] = None

    def completions(self, prev_tokens: list[Token], ast_node: ast.AstNode) -> T.Iterator[Completion]:
        any_match = len(self.patterns) == 0
        match_variables: T.List[str] = []

        for pattern in self.patterns:
            match_variables = []

            if len(pattern) <= len(prev_tokens):
                for i in range(0, len(pattern)):
                    type, value = pattern[i]
                    token = prev_tokens[i - len(pattern)]
                    if token.type != type or (value is not None and str(token) != value):
                        break
                    if value is None:
                        match_variables.append(str(token))
                else:
                    any_match = True
                    break

        if not any_match:
            return

        if self.ast_type is not None:
            while ast_node is not None and not isinstance(ast_node, self.ast_type):
                ast_node = ast_node.parent

        yield from self.func(ast_node, match_variables)


def applies_to(*ast_types):
    """ Decorator describing which AST nodes the completer should apply in. """
    def _decorator(func):
        completer = Completer(func)
        for c in ast_types:
            c.completers.append(completer)
        return completer
    return _decorator

def matches(patterns: T.List):
    def _decorator(cls):
        cls.patterns = patterns
        return cls
    return _decorator

def ast_type(ast_type: T.Type[ast.AstNode]):
    def _decorator(cls):
        cls.ast_type = ast_type
        return cls
    return _decorator


new_statement_patterns = [
    [(TokenType.OPEN_BLOCK, None)],
    [(TokenType.CLOSE_BLOCK, None)],
    [(TokenType.STMT_END, None)],
]


@applies_to(ast.GtkDirective)
def using_gtk(ast_node, match_variables):
    yield Completion("using Gtk 4.0;", CompletionItemKind.Keyword)


@matches(new_statement_patterns)
@ast_type(ast.UI)
@applies_to(ast.UI, ast.ObjectContent, ast.Template)
def namespace(ast_node, match_variables):
    yield Completion("Gtk", CompletionItemKind.Module, text="Gtk.")
    for ns in ast_node.imports:
        yield Completion(ns.namespace, CompletionItemKind.Module, text=ns.namespace + ".")


@matches([
    [(TokenType.IDENT, None), (TokenType.OP, "."), (TokenType.IDENT, None)],
    [(TokenType.IDENT, None), (TokenType.OP, ".")],
])
@applies_to(ast.UI, ast.ObjectContent, ast.Template)
def object_completer(ast_node, match_variables):
    ns = ast_node.root.gir.namespaces.get(match_variables[0])
    if ns is not None:
        for c in ns.classes.values():
            yield Completion(c.name, CompletionItemKind.Class, docs=c.doc)


@matches(new_statement_patterns)
@applies_to(ast.ObjectContent)
def property_completer(ast_node, match_variables):
    if ast_node.gir_class:
        for prop in ast_node.gir_class.properties:
            yield Completion(prop, CompletionItemKind.Property, snippet=f"{prop}: $0;")


@matches(new_statement_patterns)
@applies_to(ast.ObjectContent)
def style_completer(ast_node, match_variables):
    yield Completion("style", CompletionItemKind.Keyword, snippet="style \"$0\";")


@matches(new_statement_patterns)
@applies_to(ast.ObjectContent)
def signal_completer(ast_node, match_variables):
    if ast_node.gir_class:
        for signal in ast_node.gir_class.signals:
            name = ("on" if not isinstance(ast_node.parent, ast.Object)
                else "on_" + (ast_node.parent.id or ast_node.parent.class_name.lower()))
            yield Completion(signal, CompletionItemKind.Property, snippet=f"{signal} => ${{1:{name}_{signal.replace('-', '_')}}}()$0;")


@matches(new_statement_patterns)
@applies_to(ast.UI)
def template_completer(ast_node, match_variables):
    yield Completion(
        "template", CompletionItemKind.Snippet,
        snippet="template ${1:ClassName} : ${2:ParentClass} {\n  $0\n}"
    )


@matches(new_statement_patterns)
@applies_to(ast.UI)
def menu_completer(ast_node, match_variables):
    yield Completion(
        "menu", CompletionItemKind.Snippet,
        snippet="menu {\n  $0\n}"
    )


@matches(new_statement_patterns)
@applies_to(ast.Menu)
def menu_content_completer(ast_node, match_variables):
    yield Completion(
        "submenu", CompletionItemKind.Snippet,
        snippet="submenu {\n  $0\n}"
    )
    yield Completion(
        "section", CompletionItemKind.Snippet,
        snippet="section {\n  $0\n}"
    )
    yield Completion(
        "item", CompletionItemKind.Snippet,
        snippet="item {\n  $0\n}"
    )
    yield Completion(
        "item (shorthand)", CompletionItemKind.Snippet,
        snippet='item _("${1:Label}") "${2:action-name}" "${3:icon-name}";'
    )

    yield Completion(
        "label", CompletionItemKind.Snippet,
        snippet='label: $0;'
    )
    yield Completion(
        "action", CompletionItemKind.Snippet,
        snippet='action: "$0";'
    )
    yield Completion(
        "icon", CompletionItemKind.Snippet,
        snippet='icon: "$0";'
    )

