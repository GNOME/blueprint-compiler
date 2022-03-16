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

    @property
    def gir_type(self):
        if self.is_this:
            return self.parent_by_type(Scope).this_type
        else:
            return None

    def emit_xml(self, xml: XmlEmitter):
        if self.is_this:
            raise CompilerBugError()

        xml.start_tag("constant")
        xml.put_text(self.tokens["ident"])
        xml.end_tag()


class LookupOp(InfixExpr):
    grammar = [".", UseIdent("property")]

    @property
    def gir_type(self):
        return None

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
    Prefix(IdentExpr),
    Prefix(CastExpr),
    Prefix(["(", Expr, ")"]),
    Infix(10, LookupOp),
]
