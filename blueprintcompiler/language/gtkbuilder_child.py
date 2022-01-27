# gtkbuilder_child.py
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


from .gobject_object import Object
from .common import *


class Child(AstNode):
    grammar = [
        Optional([
            "[",
            Optional(["internal-child", UseLiteral("internal_child", True)]),
            UseIdent("child_type").expected("a child type"),
            "]",
        ]),
        Object,
    ]

    def emit_xml(self, xml: XmlEmitter):
        child_type = internal_child = None
        if self.tokens["internal_child"]:
            internal_child = self.tokens["child_type"]
        else:
            child_type = self.tokens["child_type"]
        xml.start_tag("child", type=child_type, internal_child=internal_child)
        for child in self.children:
            child.emit_xml(xml)
        xml.end_tag()
