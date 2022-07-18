# gtk_list_item_factory.py
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

from .types import ClassName
from .gobject_object import ObjectContent
from .common import *

class ListItemFactoryContent(AstNode):
    grammar = ObjectContent

    @property
    def gir_class(self):
        return self.root.gir.namespaces["Gtk"].lookup_type("Gtk.ListItem")

    def emit_xml(self, xml: XmlEmitter):
        self.children[ObjectContent][0].emit_xml(xml)


class ListItemFactory(AstNode, Scope):
    grammar = [
        "list_item_factory",
        "(",
        ClassName,
        ")",
        Optional(UseIdent("id")),
        ListItemFactoryContent,
    ]

    @property
    def variables(self) -> T.Dict[str, ScopeVariable]:
        def emit_xml(xml: XmlEmitter, id: str):
            xml.start_tag("constant")
            xml.put_text(id)
            xml.end_tag()

        def emit_item_xml(xml: XmlEmitter):
            xml.start_tag("lookup", name="item")
            xml.put_text("GtkListItem")
            xml.end_tag()

        return {
            **{
                obj.tokens["id"]: ScopeVariable(obj.tokens["id"], obj.gir_class, lambda xml: emit_xml(xml, obj.tokens["id"]))
                for obj in self.iterate_children_recursive()
                if obj.tokens["id"] is not None
            },
            "item": ScopeVariable("item", self.item_type, emit_item_xml),
        }

    @property
    def gir_class(self):
        return self.root.gir.namespaces["Gtk"].lookup_type("Gtk.ListItemFactory")

    @property
    def item_type(self):
        return self.children[ClassName][0].gir_type

    def emit_xml(self, xml: XmlEmitter):
        sub = XmlEmitter()
        sub.start_tag("interface")
        sub.put_self_closing("requires", lib="gtk", version="4.0")
        sub.start_tag("template", **{"class": "GtkListItem"})
        self.children[ListItemFactoryContent][0].emit_xml(sub)
        sub.end_tag()
        sub.end_tag()

        xml.start_tag("object", **{"class": "GtkBuilderListItemFactory"}, id=self.tokens["id"])
        xml.start_tag("property", name="bytes")
        xml.put_cdata("\n" + sub.result)
        xml.end_tag()
        xml.end_tag()
