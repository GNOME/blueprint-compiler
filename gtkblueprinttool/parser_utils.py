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

value = AnyOf(
    Sequence(
        Keyword("_"),
        OpenParen(),
        UseQuoted("value").expected("a quoted string"),
        CloseParen().expected("`)`"),
        UseLiteral("translatable", True),
    ),
    Sequence(Keyword("True"), UseLiteral("value", True)),
    Sequence(Keyword("true"), UseLiteral("value", True)),
    Sequence(Keyword("Yes"), UseLiteral("value", True)),
    Sequence(Keyword("yes"), UseLiteral("value", True)),
    Sequence(Keyword("False"), UseLiteral("value", False)),
    Sequence(Keyword("false"), UseLiteral("value", False)),
    Sequence(Keyword("No"), UseLiteral("value", False)),
    Sequence(Keyword("no"), UseLiteral("value", False)),
    UseIdent("value"),
    UseNumber("value"),
    UseQuoted("value"),
)
