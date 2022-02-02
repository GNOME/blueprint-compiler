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
            AnyOf(
                [
                    Keyword("action"),
                    "response", "=", AnyOf(UseNumber("response_id"), UseIdent("response_enum")),
                ],
                [
                    Optional(["internal-child", UseLiteral("internal_child", True)]),
                    UseIdent("child_type"),
                ]
            ),
            "]",
        ]),
        Object,
    ]

    @property
    def child_needs_id(self):
        return self.is_action_widget

    @property
    def is_action_widget(self):
        return self.tokens["action"] is not None

    @validate("action")
    def action_widget(self):
        if self.is_action_widget:
            parent = self.parent_by_type(Object).gir_class
            dialog = self.root.gir.get_type("Dialog", "Gtk")
            info_bar = self.root.gir.get_type("InfoBar", "Gtk")
            if not (parent is None or parent.assignable_to(dialog) or parent.assignable_to(info_bar)):
                raise CompileError(f"Parent type {parent.full_name} does not have action widgets")

    def emit_xml(self, xml: XmlEmitter):
        child_type = internal_child = None
        if self.tokens["internal_child"]:
            internal_child = self.tokens["child_type"]
        elif self.tokens["action"]:
            child_type = "action"
        else:
            child_type = self.tokens["child_type"]
        xml.start_tag("child", type=child_type, internal_child=internal_child)
        for child in self.children:
            child.emit_xml(xml)
        xml.end_tag()

    @validate("response_enum")
    def valid_response_enum(self):
        if response := self.tokens["response_enum"]:
            if response not in self.root.gir.get_type("ResponseType", "Gtk").members:
                raise CompileError(f"{response} is not a member of Gtk.ResponseType")

    @docs("response_enum")
    def response_enum_docs(self):
        member = self.root.gir.get_type("ResponseType", "Gtk").members.get(self.tokens["response_enum"])
        if member:
            return member.doc

    def emit_action_widget(self, xml: XmlEmitter):
        if self.is_action_widget:
            xml.start_tag("action-widget", response=self.tokens["response_id"] or self.tokens["response_enum"])
            xml.put_text(self.children[Object][0].id)
            xml.end_tag()


@decompiler("child")
def decompile_child(ctx, gir, type=None, internal_child=None):
    if type is not None:
        ctx.print(f"[{type}]")
    elif internal_child is not None:
        ctx.print(f"[internal-child {internal_child}]")
    return gir
