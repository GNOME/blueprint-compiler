# lambdas.py
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


from .types import TypeName
from .expression import Expr
from .values import Value
from .common import *


class Lambda(Value, Scope):
    grammar = [
        "(",
        TypeName,
        UseIdent("argument"),
        ")",
        "=>",
        Expr,
    ]

    def emit_xml(self, xml: XmlEmitter):
        for child in self.children:
            child.emit_xml(xml)

    def get_objects(self):
        return {
            **self.parent.parent_by_type(Scope).get_objects(),
            self.tokens["argument"]: None,
        }

    @property
    def this_name(self) -> str:
        return self.tokens["argument"]

    @property
    def this_type(self) -> str:
        return self.children[TypeName][0].gir_type

