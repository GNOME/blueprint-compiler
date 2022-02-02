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
from .common import *


class ObjectContent(AstNode):
    grammar = ["{", Until(OBJECT_CONTENT_HOOKS, "}")]

    @property
    def gir_class(self):
        return self.parent.gir_class

    # @validate()
    # def only_one_style_class(self):
    #     if len(self.children[Style]) > 1:
    #         raise CompileError(
    #             f"Only one style directive allowed per object, but this object contains {len(self.children[Style])}",
    #             start=self.children[Style][1].group.start,
    #         )

    def emit_xml(self, xml: XmlEmitter):
        for x in self.children:
            x.emit_xml(xml)

        if self.parent.gir_class and self.parent.gir_class.assignable_to(self.root.gir.get_type("Dialog", "Gtk")):
            action_widgets = [widget for widget in self.children if hasattr(widget, "is_action_widget") and widget.is_action_widget]
            if len(action_widgets):
                xml.start_tag("action-widgets")
                for widget in action_widgets:
                    widget.emit_action_widget(xml)
                xml.end_tag()


class Object(AstNode):
    grammar: T.Any = [
        class_name,
        Optional(UseIdent("id")),
        ObjectContent,
    ]

    @property
    def id(self):
        if self.tokens["id"] is None:
            if hasattr(self.parent, "child_needs_id") and self.parent.child_needs_id:
                return self.unique_id
        return self.tokens["id"]

    @validate("namespace")
    def gir_ns_exists(self):
        if not self.tokens["ignore_gir"]:
            self.root.gir.validate_ns(self.tokens["namespace"])

    @validate("class_name")
    def gir_class_exists(self):
        if self.tokens["class_name"] and not self.tokens["ignore_gir"] and self.gir_ns is not None:
            self.root.gir.validate_class(self.tokens["class_name"], self.tokens["namespace"])

    @property
    def gir_ns(self):
        if not self.tokens["ignore_gir"]:
            return self.root.gir.namespaces.get(self.tokens["namespace"] or "Gtk")

    @property
    def gir_class(self):
        if self.tokens["class_name"] and not self.tokens["ignore_gir"]:
            return self.root.gir.get_class(self.tokens["class_name"], self.tokens["namespace"])


    @docs("namespace")
    def namespace_docs(self):
        if ns := self.root.gir.namespaces.get(self.tokens["namespace"]):
            return ns.doc


    @docs("class_name")
    def class_docs(self):
        if self.gir_class:
            return self.gir_class.doc


    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("object", **{
            "class": self.gir_class.glib_type_name if self.gir_class else self.tokens["class_name"],
            "id": self.id,
        })
        for child in self.children:
            child.emit_xml(xml)
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
