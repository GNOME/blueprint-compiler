# tokenizer.py
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

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    EOF = 0
    IDENT = 1
    QUOTED = 2
    NUMBER = 3
    OP = 4
    WHITESPACE = 5
    COMMENT = 6
    PUNCTUATION = 7


_tokens = [
    (TokenType.IDENT, r"[A-Za-z_][\d\w\-_]*"),
    (TokenType.QUOTED, r'"(\\(.|\n)|[^\\"\n])*"'),
    (TokenType.QUOTED, r"'(\\(.|\n)|[^\\'\n])*'"),
    (TokenType.NUMBER, r"0x[A-Za-z0-9_]+"),
    (TokenType.NUMBER, r"[\d_]+(\.[\d_]+)?"),
    (TokenType.NUMBER, r"\.[\d_]+"),
    (TokenType.WHITESPACE, r"\s+"),
    (TokenType.COMMENT, r"\/\*[\s\S]*?\*\/"),
    (TokenType.COMMENT, r"\/\/[^\n]*"),
    (TokenType.OP, r"\$|<<|>>|=>|==|!=|::|<|>|:=|\.|\|\||&&|\||\+|\-|\*|=|:|/|!|%"),
    (TokenType.PUNCTUATION, r"\(|\)|\{|\}|;|\[|\]|\,"),
]
_TOKENS = [(type, re.compile(regex)) for (type, regex) in _tokens]


class Token:
    def __init__(
        self, type: TokenType, start: int, end: int, source: SourceCode, index: int
    ):
        self.type = type
        self.start = start
        self.end = end
        self.source = source
        self.index = index

    def __str__(self) -> str:
        return self.source.text[self.start : self.end]

    @property
    def range(self) -> Range:
        return Range(self.start, self.end, self.source)

    @property
    def range_without_quotes(self) -> Range:
        if self.type == TokenType.QUOTED:
            return Range(self.start + 1, self.end - 1, self.source)
        else:
            return self.range

    @property
    def next(self) -> Token | None:
        if self.index + 1 < len(self.source.tokens):
            return self.source.tokens[self.index + 1]
        return None

    @property
    def prev(self) -> Token | None:
        if self.index > 0:
            return self.source.tokens[self.index - 1]
        return None

    def get_number(self) -> int | float:
        from .errors import CompileError, CompilerBugError

        if self.type != TokenType.NUMBER:
            raise CompilerBugError()

        string = str(self).replace("_", "")
        try:
            if string.startswith("0x"):
                return int(string, 16)
            elif "." in string:
                return float(string)
            else:
                return int(string)
        except:
            raise CompileError(f"{str(self)} is not a valid number literal", self.range)


@dataclass
class SourceCode:
    text: str
    tokens: list[Token]

    def token_at(self, idx: int) -> Token | None:
        """Gets the token at the specified character index, or None if the index is invalid."""

        first = 0
        last = len(self.tokens)
        while first < last:
            mid = (first + last) // 2
            token = self.tokens[mid]
            if token.start <= idx < token.end:
                return token
            elif idx < token.start:
                last = mid
            else:
                first = mid + 1

        if idx == len(self.text):
            return self.tokens[-1]

        return None

    def pos_to_idx(self, line: int, col: int) -> int:
        lines = self.text.splitlines(keepends=True)
        return sum([len(line) for line in lines[:line]]) + col

    def idx_to_pos(self, idx: int) -> tuple[int, int]:
        if idx == 0 or len(self.text) == 0:
            return (0, 0)
        line_num = self.text.count("\n", 0, idx) + 1
        col_num = idx - self.text.rfind("\n", 0, idx) - 1
        return (line_num - 1, col_num)

    def idxs_to_range(self, start: int, end: int):
        start_l, start_c = self.idx_to_pos(start)
        end_l, end_c = self.idx_to_pos(end)
        return {
            "start": {
                "line": start_l,
                "character": start_c,
            },
            "end": {
                "line": end_l,
                "character": end_c,
            },
        }


def _tokenize(blueprint: str, source: SourceCode):
    from .errors import CompileError

    i = 0
    t = 0
    while i < len(blueprint):
        for type, regex in _TOKENS:
            if match := regex.match(blueprint, i):
                yield Token(type, match.start(), match.end(), source, t)
                i = match.end()
                t += 1
                break
        else:
            raise CompileError(
                "Could not determine what kind of syntax is meant here",
                Range(i, i, source),
            )

    yield Token(TokenType.EOF, i, i, source, t)


def tokenize(data: str) -> SourceCode:
    source = SourceCode(text=data, tokens=[])
    source.tokens.extend(_tokenize(data, source))
    return source


@dataclass
class Range:
    start: int
    end: int
    source: SourceCode

    @property
    def length(self) -> int:
        return self.end - self.start

    @property
    def text(self) -> str:
        return self.source.text[self.start : self.end]

    @property
    def with_trailing_newline(self) -> "Range":
        if len(self.source.text) > self.end and self.source.text[self.end] == "\n":
            return Range(self.start, self.end + 1, self.source)
        else:
            return self

    @property
    def with_preceding_whitespace(self) -> "Range":
        start = self.start
        while start > 0 and self.source.text[start - 1].isspace():
            start -= 1
        return Range(start, self.end, self.source)

    @property
    def applicable_comments(self) -> list[Token]:
        """Returns comments that apply to this range.

        A comment is considered applicable if it is:
        - Intersecting this range, or
        - The first comment before this range, and on the same line, or
        - The first comment before this range, on the previous line, and not preceded by any text on its line, or
        - The first comment after this range and on the same line."""

        result = []

        first_token = self.source.token_at(self.start)
        assert first_token is not None
        last_token = self.source.token_at(
            self.end - 1 if self.end > self.start else self.end
        )
        assert last_token is not None

        token = first_token.prev
        line_breaks = 0
        while token is not None:
            if token.type == TokenType.COMMENT:
                # If the comment is on the previous line, it must not be preceded by any text on its line.
                if (
                    line_breaks == 0
                    or token.prev is None
                    or (
                        token.prev.type == TokenType.WHITESPACE
                        and ("\n" in str(token.prev) or token.prev.prev is None)
                    )
                ):
                    result.append(token)
                break
            elif token.type == TokenType.WHITESPACE and "\n" in str(token):
                line_breaks += str(token).count("\n")
                if line_breaks > 1:
                    break
            token = token.prev

        for i in range(first_token.index, last_token.index + 1):
            token = self.source.tokens[i]
            if token.type == TokenType.COMMENT:
                result.append(token)

        token = last_token.next
        while token is not None:
            if token.type == TokenType.COMMENT:
                result.append(token)
                break
            elif token.type == TokenType.WHITESPACE and "\n" in str(token):
                break
            token = token.next

        return result

    @staticmethod
    def join(a: "Range" | None, b: "Range" | None) -> "Range" | None:
        if a is None:
            return b
        if b is None:
            return a
        return Range(min(a.start, b.start), max(a.end, b.end), a.source)

    def __contains__(self, other: int | "Range") -> bool:
        if isinstance(other, int):
            return self.start <= other <= self.end
        else:
            return self.start <= other.start and self.end >= other.end

    def to_json(self):
        return self.source.idxs_to_range(self.start, self.end)

    def overlaps(self, other: "Range") -> bool:
        return not (self.end < other.start or self.start > other.end)


@dataclass
class TextEdit:
    range: Range
    newText: str

    def to_json(self):
        return {"range": self.range.to_json(), "newText": self.newText}

    @staticmethod
    def apply_edits(string: str, edits: list["TextEdit"]):
        offset = 0
        edits = sorted(edits, key=lambda e: e.range.start)
        for edit in edits:
            string = (
                string[: edit.range.start + offset]
                + edit.newText
                + string[edit.range.end + offset :]
            )
            offset += len(edit.newText) - edit.range.length

        return string
