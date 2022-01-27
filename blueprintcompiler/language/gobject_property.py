# gobject_property.py
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
from .gtkbuilder_template import Template
from .values import Value, TranslatedStringValue
from .common import *


class Property(AstNode):
    grammar = AnyOf(
        Statement(
            UseIdent("name"),
            ":",
            "bind",
            UseIdent("bind_source").expected("the ID of a source object to bind from"),
            ".",
            UseIdent("bind_property").expected("a property name to bind from"),
            ZeroOrMore(AnyOf(
                "sync-create",
                ["no-sync-create", UseLiteral("no_sync_create", True)],
                ["inverted", UseLiteral("inverted", True)],
                ["bidirectional", UseLiteral("bidirectional", True)],
            )),
        ),
        Statement(
            UseIdent("name"),
            ":",
            AnyOf(
                OBJECT_HOOKS,
                VALUE_HOOKS,
            ).expected("a value"),
        ),
    )

    @property
    def gir_class(self):
        return self.parent.parent.gir_class


    @property
    def gir_property(self):
        if self.gir_class is not None:
            return self.gir_class.properties.get(self.tokens["name"])


    @property
    def value_type(self):
        if self.gir_property is not None:
            return self.gir_property.type


    @validate("name")
    def property_exists(self):
        if self.gir_class is None:
            # Objects that we have no gir data on should not be validated
            # This happens for classes defined by the app itself
            return

        if isinstance(self.parent.parent, Template):
            # If the property is part of a template, it might be defined by
            # the application and thus not in gir
            return

        if self.gir_property is None:
            raise CompileError(
                f"Class {self.gir_class.full_name} does not contain a property called {self.tokens['name']}",
                did_you_mean=(self.tokens["name"], self.gir_class.properties.keys())
            )


    @validate()
    def obj_property_type(self):
        if len(self.children[Object]) == 0:
            return

        object = self.children[Object][0]
        type = self.value_type
        if object and type and object.gir_class and not object.gir_class.assignable_to(type):
            raise CompileError(
                f"Cannot assign {object.gir_class.full_name} to {type.full_name}"
            )


    @docs("name")
    def property_docs(self):
        if self.gir_property is not None:
            return self.gir_property.doc


    def emit_xml(self, xml: XmlEmitter):
        values = self.children[Value]
        value = values[0] if len(values) == 1 else None

        bind_flags = []
        if self.tokens["bind_source"] and not self.tokens["no_sync_create"]:
            bind_flags.append("sync-create")
        if self.tokens["inverted"]:
            bind_flags.append("invert-boolean")
        if self.tokens["bidirectional"]:
            bind_flags.append("bidirectional")
        bind_flags_str = "|".join(bind_flags) or None

        props = {
            "name": self.tokens["name"],
            "bind-source": self.tokens["bind_source"],
            "bind-property": self.tokens["bind_property"],
            "bind-flags": bind_flags_str,
        }

        if isinstance(value, TranslatedStringValue):
            props = { **props, **value.attrs }

        if len(self.children[Object]) == 1:
            xml.start_tag("property", **props)
            self.children[Object][0].emit_xml(xml)
            xml.end_tag()
        elif value is None:
            xml.put_self_closing("property", **props)
        else:
            xml.start_tag("property", **props)
            value.emit_xml(xml)
            xml.end_tag()
