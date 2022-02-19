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


from functools import cached_property

from .gobject_object import Object
from .response_id import ResponseId
from .common import *


class Child(AstNode):
    grammar = [
        Optional([
            "[",
            Optional(["internal-child", UseLiteral("internal_child", True)]),
            UseIdent("child_type").expected("a child type"),
            Optional(ResponseId),
            "]",
        ]),
        Object,
    ]

    @cached_property
    def response_id(self) -> T.Optional[ResponseId]:
        """Get action widget's response ID.

        If child is not action widget, returns `None`.
        """
        response_ids = self.children[ResponseId]

        if response_ids:
            return response_ids[0]
        else:
            return None

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


@decompiler("child")
def decompile_child(ctx, gir, type=None, internal_child=None):
    if type is not None:
        ctx.print(f"[{type}]")
    elif internal_child is not None:
        ctx.print(f"[internal-child {internal_child}]")
    return gir
