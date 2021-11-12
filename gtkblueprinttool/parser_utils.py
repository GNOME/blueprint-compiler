# parser_utils.py
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


from . import ast
from .parse_tree import *


class_name = AnyOf(
    Sequence(
        UseIdent("namespace"),
        Op("."),
        UseIdent("class_name"),
    ),
    Sequence(
        Op("."),
        UseIdent("class_name"),
        UseLiteral("ignore_gir", True),
    ),
    UseIdent("class_name"),
)

literal = Group(
    ast.LiteralValue,
    AnyOf(
        UseNumber("value"),
        UseQuoted("value"),
    )
)

ident_value = Group(
    ast.IdentValue,
    UseIdent("value"),
)

flags_value = Group(
    ast.FlagsValue,
    Sequence(
        Group(ast.Flag, UseIdent("value")),
        Op("|"),
        Delimited(Group(ast.Flag, UseIdent("value")), Op("|")),
    ),
)

translated_string = Group(
    ast.TranslatedStringValue,
    Sequence(
        Keyword("_"),
        OpenParen(),
        UseQuoted("value").expected("a quoted string"),
        CloseParen().expected("`)`"),
    ),
)

value = AnyOf(translated_string, literal, flags_value, ident_value)
