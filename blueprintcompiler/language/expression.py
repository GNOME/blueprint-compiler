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
from .gtkbuilder_template import Template


expr = Sequence()


class Expr(AstNode):
    @property
    def type(self) -> T.Optional[GirType]:
        raise NotImplementedError()

    @property
    def type_complete(self) -> bool:
        return True

    @property
    def rhs(self) -> T.Optional["Expr"]:
        if isinstance(self.parent, ExprChain):
            children = list(self.parent.children)
            if children.index(self) + 1 < len(children):
                return children[children.index(self) + 1]
            else:
                return self.parent.rhs
        else:
            return None


class ExprChain(Expr):
    grammar = expr

    @property
    def last(self) -> Expr:
        return self.children[-1]

    @property
    def type(self) -> T.Optional[GirType]:
        return self.last.type

    @property
    def type_complete(self) -> bool:
        return self.last.type_complete


class InfixExpr(Expr):
    @property
    def lhs(self):
        children = list(self.parent_by_type(ExprChain).children)
        return children[children.index(self) - 1]


class IdentExpr(Expr):
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

    @property
    def type_complete(self) -> bool:
        if object := self.root.objects_by_id.get(self.ident):
            return not isinstance(object, Template)
        else:
            return True


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
        if (
            self.lhs.type is None
            or not self.lhs.type_complete
            or isinstance(self.lhs.type, UncheckedType)
        ):
            return

        elif not isinstance(self.lhs.type, gir.Class) and not isinstance(
            self.lhs.type, gir.Interface
        ):
            raise CompileError(
                f"Type {self.lhs.type.full_name} does not have properties"
            )

        elif self.lhs.type.properties.get(self.property_name) is None:
            raise CompileError(
                f"{self.lhs.type.full_name} does not have a property called {self.property_name}",
                did_you_mean=(self.property_name, self.lhs.type.properties.keys()),
            )


class CastExpr(InfixExpr):
    grammar = ["as", "(", TypeName, ")"]

    @property
    def type(self) -> T.Optional[GirType]:
        return self.children[TypeName][0].gir_type

    @property
    def type_complete(self) -> bool:
        return True

    @validate()
    def cast_makes_sense(self):
        if self.type is None or self.lhs.type is None:
            return

        if not self.type.assignable_to(self.lhs.type):
            raise CompileError(
                f"Invalid cast. No instance of {self.lhs.type.full_name} can be an instance of {self.type.full_name}."
            )


class ClosureExpr(Expr):
    grammar = [
        Optional(["$", UseLiteral("extern", True)]),
        UseIdent("name"),
        "(",
        Delimited(ExprChain, ","),
        ")",
    ]

    @property
    def type(self) -> T.Optional[GirType]:
        if isinstance(self.rhs, CastExpr):
            return self.rhs.type
        else:
            return None

    @property
    def closure_name(self) -> str:
        return self.tokens["name"]

    @property
    def args(self) -> T.List[ExprChain]:
        return self.children[ExprChain]

    @validate()
    def cast_to_return_type(self):
        if not isinstance(self.rhs, CastExpr):
            raise CompileError(
                "Closure expression must be cast to the closure's return type"
            )

    @validate()
    def builtin_exists(self):
        if not self.tokens["extern"]:
            raise CompileError(f"{self.closure_name} is not a builtin function")


expr.children = [
    AnyOf(ClosureExpr, IdentExpr, ["(", ExprChain, ")"]),
    ZeroOrMore(AnyOf(LookupOp, CastExpr)),
]
