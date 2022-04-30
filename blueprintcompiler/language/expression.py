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
from .types import ClassName, TypeName


expr = Pratt()


class Expr(AstNode):
    grammar = expr

    @property
    def gir_type(self):
        return self.children[-1].gir_type

    def emit_xml(self, xml: XmlEmitter):
        self.children[-1].emit_xml(xml)


class InfixExpr(AstNode):
    @property
    def lhs(self):
        children = list(self.parent_by_type(Expr).children)
        return children[children.index(self) - 1]


class IdentExpr(AstNode):
    grammar = UseIdent("ident")

    @property
    def is_this(self):
        return self.parent_by_type(Scope).this_name == self.tokens["ident"]

    @validate()
    def exists(self):
        if self.is_this:
            return

        scope = self.parent_by_type(Scope)
        if self.tokens["ident"] not in scope.get_objects():
            raise CompileError(
                f"Could not find object with ID '{self.tokens['ident']}'",
                did_you_mean=(self.tokens['ident'], scope.get_objects().keys()),
            )

    @property
    def gir_type(self):
        scope = self.parent_by_type(Scope)

        if self.is_this:
            return scope.this_type
        elif self.tokens["ident"] in scope.get_objects():
            return scope.get_objects()[self.tokens["ident"]].gir_class

    def emit_xml(self, xml: XmlEmitter):
        if self.is_this:
            raise CompilerBugError()

        xml.start_tag("constant")
        xml.put_text(self.tokens["ident"])
        xml.end_tag()


class ClosureExpr(AstNode):
    grammar = [
        UseIdent("function"),
        "(",
        Delimited(Expr, ",").expected("closure arguments"),
        Match(")").expected(),
    ]

    @validate()
    def is_cast_to_return_val(self):
        if not isinstance(self.parent.parent, CastExpr):
            raise CompileError(f"Closure expression needs to be cast to {self.tokens['function']}'s return type")

    @property
    def gir_type(self):
        return self.parent.parent.gir_type

    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("closure", function=self.tokens["function"], type=self.gir_type)
        for child in self.children[Expr]:
            child.emit_xml(xml)
        xml.end_tag()


class LookupOp(InfixExpr):
    grammar = [".", UseIdent("property")]

    @property
    def gir_type(self):
        if parent_type := self.lhs.gir_type:
            if prop := parent_type.properties.get(self.tokens["property"]):
                return prop.type

    @validate("property")
    def property_exists(self):
        if parent_type := self.lhs.gir_type:
            if not (isinstance(parent_type, gir.Class) or isinstance(parent_type, gir.Interface)):
                raise CompileError(f"Type {parent_type.full_name} does not have properties")
            elif self.tokens["property"] not in parent_type.properties:
                raise CompileError(
                    f"{parent_type.full_name} does not have a property called {self.tokens['property']}",
                    hints=["Do you need to cast the previous expression?"],
                    did_you_mean=(self.tokens['property'], parent_type.properties.keys()),
                )

    def emit_xml(self, xml: XmlEmitter):
        if isinstance(self.lhs, IdentExpr) and self.lhs.is_this:
            xml.put_self_closing("lookup", name=self.tokens["property"], type=self.parent_by_type(Scope).this_type)
        else:
            xml.start_tag("lookup", name=self.tokens["property"], type=self.lhs.gir_type)
            self.lhs.emit_xml(xml)
            xml.end_tag()


class CastExpr(AstNode):
    grammar = ["(", TypeName, ")", Expr]

    @property
    def gir_type(self):
        return self.children[TypeName][0].gir_type

    def emit_xml(self, xml: XmlEmitter):
        self.children[Expr][0].emit_xml(xml)


expr.children = [
    Prefix(ClosureExpr),
    Prefix(IdentExpr),
    Prefix(CastExpr),
    Prefix(["(", Expr, ")"]),
    Infix(10, LookupOp),
]
