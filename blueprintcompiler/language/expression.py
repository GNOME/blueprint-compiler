# expressions.py
#
# Copyright 2022 James Westman <james@jwestman.net>
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


from .common import *
from .types import TypeName


expr = Pratt()


class Expr:
    @property
    def type(self) -> T.Optional[GirType]:
        raise NotImplementedError()


class ExprChain(Expr, AstNode):
    grammar = expr

    @property
    def last(self) -> Expr:
        return self.children[-1]

    @property
    def type(self) -> T.Optional[GirType]:
        return self.last.type


class InfixExpr(Expr, AstNode):
    @property
    def lhs(self):
        children = list(self.parent_by_type(ExprChain).children)
        return children[children.index(self) - 1]


class IdentExpr(Expr, AstNode):
    grammar = UseIdent("ident")

    @property
    def ident(self) -> str:
        return self.tokens["ident"]

    @validate()
    def exists(self):
        if self.root.objects_by_id.get(self.ident) is None:
            raise CompileError(
                f"Could not find object with ID {self.ident}",
                did_you_mean=(self.ident, self.root.objects_by_id.keys()),
            )

    @property
    def type(self) -> T.Optional[GirType]:
        if object := self.root.objects_by_id.get(self.ident):
            return object.gir_class
        else:
            return None


class LookupOp(InfixExpr):
    grammar = [".", UseIdent("property")]

    @property
    def property_name(self) -> str:
        return self.tokens["property"]

    @property
    def type(self) -> T.Optional[GirType]:
        if isinstance(self.lhs.type, gir.Class) or isinstance(
            self.lhs.type, gir.Interface
        ):
            if property := self.lhs.type.properties.get(self.property_name):
                return property.type

        return None

    @validate("property")
    def property_exists(self):
        if self.lhs.type is None or isinstance(self.lhs.type, UncheckedType):
            return
        elif not isinstance(self.lhs.type, gir.Class) and not isinstance(
            self.lhs.type, gir.Interface
        ):
            raise CompileError(
                f"Type {self.lhs.type.full_name} does not have properties"
            )
        elif self.lhs.type.properties.get(self.property_name) is None:
            raise CompileError(
                f"{self.lhs.type.full_name} does not have a property called {self.property_name}"
            )


class CastExpr(InfixExpr):
    grammar = ["as", "(", TypeName, ")"]

    @property
    def type(self) -> T.Optional[GirType]:
        return self.children[TypeName][0].gir_type

    @validate()
    def cast_makes_sense(self):
        if self.lhs.type is None:
            return

        if not self.type.assignable_to(self.lhs.type):
            raise CompileError(
                f"Invalid cast. No instance of {self.lhs.type.full_name} can be an instance of {self.type.full_name}."
            )


expr.children = [
    Prefix(IdentExpr),
    Prefix(["(", ExprChain, ")"]),
    Infix(10, LookupOp),
    Infix(10, CastExpr),
]
