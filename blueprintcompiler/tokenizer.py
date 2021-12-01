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


import typing as T
import re
from enum import Enum

from .errors import CompileError


class TokenType(Enum):
    EOF             = 0
    DIRECTIVE       = 1
    IDENT           = 2
    QUOTED          = 3
    NUMBER          = 4
    OPEN_PAREN      = 5
    CLOSE_PAREN     = 6
    OPEN_BLOCK      = 7
    CLOSE_BLOCK     = 8
    STMT_END        = 9
    OP              = 10
    WHITESPACE      = 11
    COMMENT         = 12
    OPEN_BRACKET    = 13
    CLOSE_BRACKET   = 14
    COMMA           = 15


_tokens = [
    (TokenType.DIRECTIVE,       r"@[\d\w\-_]+"),
    (TokenType.IDENT,           r"[A-Za-z_][\d\w\-_]*"),
    (TokenType.QUOTED,          r'"(\\"|[^"\n])*"'),
    (TokenType.QUOTED,          r"'(\\'|[^'\n])*'"),
    (TokenType.NUMBER,          r"[-+]?[\d_]+(\.[\d_]+)?"),
    (TokenType.NUMBER,          r"0x[A-Fa-f0-9]+"),
    (TokenType.OPEN_PAREN,      r"\("),
    (TokenType.CLOSE_PAREN,     r"\)"),
    (TokenType.OPEN_BLOCK,      r"\{"),
    (TokenType.CLOSE_BLOCK,     r"\}"),
    (TokenType.STMT_END,        r";"),
    (TokenType.WHITESPACE,      r"\s+"),
    (TokenType.COMMENT,         r"\/\*[\s\S]*?\*\/"),
    (TokenType.COMMENT,         r"\/\/[^\n]*"),
    (TokenType.OPEN_BRACKET,    r"\["),
    (TokenType.CLOSE_BRACKET,   r"\]"),
    (TokenType.OP,              r"[:=\.=\|<>\+\-/\*]+"),
    (TokenType.COMMA,           r"\,"),
]
_TOKENS = [(type, re.compile(regex)) for (type, regex) in _tokens]


class Token:
    def __init__(self, type, start, end, string):
        self.type = type
        self.start = start
        self.end = end
        self.string = string

    def __str__(self):
        return self.string[self.start:self.end]

    def is_directive(self, directive) -> bool:
        if self.type != TokenType.DIRECTIVE:
            return False
        return str(self) == "@" + directive

    def get_number(self):
        if self.type != TokenType.NUMBER:
            return None

        string = str(self)
        if string.startswith("0x"):
            return int(string, 16)
        else:
            return float(string)


def _tokenize(ui_ml: str):
    i = 0
    while i < len(ui_ml):
        matched = False
        for (type, regex) in _TOKENS:
            match = regex.match(ui_ml, i)

            if match is not None:
                yield Token(type, match.start(), match.end(), ui_ml)
                i = match.end()
                matched = True
                break

        if not matched:
            raise CompileError("Could not determine what kind of syntax is meant here", i, i)

    yield Token(TokenType.EOF, i, i, ui_ml)


def tokenize(data: str) -> T.List[Token]:
    return list(_tokenize(data))
