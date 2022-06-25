# gobject_object.py
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


import typing as T
from functools import cached_property

from .common import *
from .response_id import ResponseId
from .types import ClassName, ConcreteClassName


class ObjectContent(AstNode):
    grammar = ["{", Until(OBJECT_CONTENT_HOOKS, "}")]

    @property
    def gir_class(self):
        return self.parent.gir_class

    def emit_xml(self, xml: XmlEmitter):
        for x in self.children:
            x.emit_xml(xml)

class Object(AstNode):
    grammar: T.Any = [
        ConcreteClassName,
        Optional(UseIdent("id")),
        ObjectContent,
    ]

    @property
    def gir_class(self):
        return self.children[ClassName][0].gir_type

    @cached_property
    def action_widgets(self) -> T.List[ResponseId]:
        """Get list of widget's action widgets.

        Empty if object doesn't have action widgets.
        """
        from .gtkbuilder_child import Child

        return [
            child.response_id
            for child in self.children[ObjectContent][0].children[Child]
            if child.response_id
        ]

    def emit_start_tag(self, xml: XmlEmitter):
        xml.start_tag("object", **{
            "class": self.children[ClassName][0].glib_type_name,
            "id": self.tokens["id"],
        })

    def emit_xml(self, xml: XmlEmitter):
        self.emit_start_tag(xml)

        for child in self.children:
            child.emit_xml(xml)

        # List action widgets
        action_widgets = self.action_widgets
        if action_widgets:
            xml.start_tag("action-widgets")
            for action_widget in action_widgets:
                action_widget.emit_action_widget(xml)
            xml.end_tag()

        xml.end_tag()


def validate_parent_type(node, ns: str, name: str, err_msg: str):
    parent = node.root.gir.get_type(name, ns)
    container_type = node.parent_by_type(Object).gir_class
    if container_type and not container_type.assignable_to(parent):
        raise CompileError(f"{container_type.full_name} is not a {parent.full_name}, so it doesn't have {err_msg}")


@decompiler("object")
def decompile_object(ctx, gir, klass, id=None):
    gir_class = ctx.type_by_cname(klass)
    klass_name = decompile.full_name(gir_class) if gir_class is not None else "." + klass
    if id is None:
        ctx.print(f"{klass_name} {{")
    else:
        ctx.print(f"{klass_name} {id} {{")
    return gir_class
