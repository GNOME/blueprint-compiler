# binding.py
#
# Copyright 2023 James Westman <james@jwestman.net>
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

from dataclasses import dataclass

from .common import *
from .expression import Expression, LookupOp, LiteralExpr


class Binding(AstNode):
    grammar = [
        Keyword("bind"),
        Expression,
    ]

    @property
    def expression(self) -> Expression:
        return self.children[Expression][0]

    @property
    def simple_binding(self) -> T.Optional["SimpleBinding"]:
        if isinstance(self.expression.last, LookupOp):
            if isinstance(self.expression.last.lhs, LiteralExpr):
                from .values import IdentLiteral

                if isinstance(self.expression.last.lhs.literal.value, IdentLiteral):
                    return SimpleBinding(
                        self.expression.last.lhs.literal.value.ident,
                        self.expression.last.property_name,
                    )
        return None


@dataclass
class SimpleBinding:
    source: str
    property_name: str
