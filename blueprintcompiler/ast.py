# ast.py
#
# Copyright 2021 James Westman <james@jwestman.net>
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

from .ast_utils import *
from .errors import CompileError, CompilerBugError, MultipleErrors
from . import gir
from .lsp_utils import Completion, CompletionItemKind, SemanticToken, SemanticTokenType
from .tokenizer import Token
from .utils import lazy_prop
from .xml_emitter import XmlEmitter


class UI(AstNode):
    """ The AST node for the entire file """

    @property
    def gir(self):
        gir_ctx = gir.GirContext()
        self._gir_errors = []

        try:
            gir_ctx.add_namespace(self.children[GtkDirective][0].gir_namespace)
        except CompileError as e:
            e.start = self.children[GtkDirective][0].group.start
            e.end = self.children[GtkDirective][0].group.end
            self._gir_errors.append(e)

        for i in self.children[Import]:
            try:
                if i.gir_namespace is not None:
                    gir_ctx.add_namespace(i.gir_namespace)
            except CompileError as e:
                e.start = i.group.tokens["namespace"].start
                e.end = i.group.tokens["version"].end
                self._gir_errors.append(e)

        return gir_ctx


    @lazy_prop
    def objects_by_id(self):
        return { obj.tokens["id"]: obj for obj in self.iterate_children_recursive() if obj.tokens["id"] is not None }


    @validate()
    def gir_errors(self):
        # make sure gir is loaded
        self.gir
        if len(self._gir_errors):
            raise MultipleErrors(self._gir_errors)


    @validate()
    def at_most_one_template(self):
        if len(self.children[Template]) > 1:
            for template in self.children[Template][1:]:
                raise CompileError(
                    f"Only one template may be defined per file, but this file contains {len(self.children[Template])}",
                    template.group.tokens["name"].start, template.group.tokens["name"].end,
                )


    @validate()
    def unique_ids(self):
        passed = {}
        for obj in self.iterate_children_recursive():
            if obj.tokens["id"] is None:
                continue

            if obj.tokens["id"] in passed:
                token = obj.group.tokens["id"]
                raise CompileError(f"Duplicate object ID '{obj.tokens['id']}'", token.start, token.end)
            passed[obj.tokens["id"]] = obj


    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("interface")
        for x in self.children:
            x.emit_xml(xml)
        xml.end_tag()


class GtkDirective(AstNode):
    @validate("version")
    def gtk_version(self):
        if self.tokens["version"] not in ["4.0"]:
            err = CompileError("Only GTK 4 is supported")
            if self.tokens["version"].startswith("4"):
                err.hint("Expected the GIR version, not an exact version number. Use `using Gtk 4.0;`.")
            else:
                err.hint("Expected `using Gtk 4.0;`")
            raise err


    @property
    def gir_namespace(self):
        return gir.get_namespace("Gtk", self.tokens["version"])


    def emit_xml(self, xml: XmlEmitter):
        xml.put_self_closing("requires", lib="gtk", version=self.tokens["version"])


class Import(AstNode):
    @validate("namespace", "version")
    def namespace_exists(self):
        gir.get_namespace(self.tokens["namespace"], self.tokens["version"])

    @property
    def gir_namespace(self):
        try:
            return gir.get_namespace(self.tokens["namespace"], self.tokens["version"])
        except CompileError:
            return None

    def emit_xml(self, xml):
        pass


class Object(AstNode):
    @validate("namespace")
    def gir_ns_exists(self):
        if not self.tokens["ignore_gir"]:
            self.root.gir.validate_ns(self.tokens["namespace"])

    @validate("class_name")
    def gir_class_exists(self):
        if not self.tokens["ignore_gir"] and self.gir_ns is not None:
            self.root.gir.validate_class(self.tokens["class_name"], self.tokens["namespace"])

    @property
    def gir_ns(self):
        if not self.tokens["ignore_gir"]:
            return self.root.gir.namespaces.get(self.tokens["namespace"] or "Gtk")

    @property
    def gir_class(self):
        if not self.tokens["ignore_gir"]:
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
            "id": self.tokens["id"],
        })
        for child in self.children:
            child.emit_xml(xml)
        xml.end_tag()


class Template(Object):
    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("template", **{
            "class": self.tokens["name"],
            "parent": self.gir_class.glib_type_name if self.gir_class else self.tokens["class_name"],
        })
        for child in self.children:
            child.emit_xml(xml)
        xml.end_tag()


class Child(AstNode):
    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("child", type=self.tokens["child_type"])
        for child in self.children:
            child.emit_xml(xml)
        xml.end_tag()


class ObjectContent(AstNode):
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


class Property(AstNode):
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
        if self.tokens["sync_create"]:
            bind_flags.append("sync-create")
        if self.tokens["after"]:
            bind_flags.append("after")
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


class Signal(AstNode):
    @property
    def gir_signal(self):
        if self.gir_class is not None:
            return self.gir_class.signals.get(self.tokens["name"])


    @property
    def gir_class(self):
        return self.parent.parent.gir_class


    @validate("name")
    def signal_exists(self):
        if self.gir_class is None:
            # Objects that we have no gir data on should not be validated
            # This happens for classes defined by the app itself
            return

        if isinstance(self.parent.parent, Template):
            # If the signal is part of a template, it might be defined by
            # the application and thus not in gir
            return

        if self.gir_signal is None:
            raise CompileError(
                f"Class {self.gir_class.full_name} does not contain a signal called {self.tokens['name']}",
                did_you_mean=(self.tokens["name"], self.gir_class.signals.keys())
            )


    @docs("name")
    def signal_docs(self):
        if self.gir_signal is not None:
            return self.gir_signal.doc


    def emit_xml(self, xml: XmlEmitter):
        name = self.tokens["name"]
        if self.tokens["detail_name"]:
            name += "::" + self.tokens["detail_name"]
        xml.put_self_closing("signal", name=name, handler=self.tokens["handler"], swapped="true" if self.tokens["swapped"] else None)


class Value(ast.AstNode):
    pass


class TranslatedStringValue(Value):
    @property
    def attrs(self):
        attrs = { "translatable": "true" }
        if "context" in self.tokens:
            attrs["context"] = self.tokens["context"]
        return attrs

    def emit_xml(self, xml: XmlEmitter):
        xml.put_text(self.tokens["value"])


class LiteralValue(Value):
    def emit_xml(self, xml: XmlEmitter):
        xml.put_text(self.tokens["value"])

    @validate()
    def validate_for_type(self):
        type = self.parent.value_type
        if isinstance(type, gir.IntType):
            try:
                int(self.tokens["value"])
            except:
                raise CompileError(f"Cannot convert {self.group.tokens['value']} to integer")

        elif isinstance(type, gir.UIntType):
            try:
                int(self.tokens["value"])
                if int(self.tokens["value"]) < 0:
                    raise Exception()
            except:
                raise CompileError(f"Cannot convert {self.group.tokens['value']} to unsigned integer")

        elif isinstance(type, gir.FloatType):
            try:
                float(self.tokens["value"])
            except:
                raise CompileError(f"Cannot convert {self.group.tokens['value']} to float")

        elif isinstance(type, gir.StringType):
            pass

        elif isinstance(type, gir.Class) or isinstance(type, gir.Interface):
            parseable_types = [
                "Gdk.Paintable",
                "Gdk.Texture",
                "Gdk.Pixbuf",
                "GLib.File",
                "Gtk.ShortcutTrigger",
                "Gtk.ShortcutAction",
            ]
            if type.full_name not in parseable_types:
                raise CompileError(f"Cannot convert {self.group.tokens['value']} to {type.full_name}")

        elif type is not None:
            raise CompileError(f"Cannot convert {self.group.tokens['value']} to {type.full_name}")


class Flag(AstNode):
    pass

class FlagsValue(Value):
    def emit_xml(self, xml: XmlEmitter):
        xml.put_text("|".join([flag.tokens["value"] for flag in self.children[Flag]]))


class IdentValue(Value):
    def emit_xml(self, xml: XmlEmitter):
        if isinstance(self.parent.value_type, gir.Enumeration):
            xml.put_text(self.parent.value_type.members[self.tokens["value"]].nick)
        else:
            xml.put_text(self.tokens["value"])

    @validate()
    def validate_for_type(self):
        type = self.parent.value_type

        if isinstance(type, gir.Enumeration):
            if self.tokens["value"] not in type.members:
                raise CompileError(
                    f"{self.tokens['value']} is not a member of {type.full_name}",
                    did_you_mean=(self.tokens['value'], type.members.keys()),
                )

        elif isinstance(type, gir.BoolType):
            if self.tokens["value"] not in ["true", "false"]:
                raise CompileError(
                    f"Expected 'true' or 'false' for boolean value",
                    did_you_mean=(self.tokens['value'], ["true", "false"]),
                )

        elif type is not None:
            object = self.root.objects_by_id.get(self.tokens["value"])
            if object is None:
                raise CompileError(
                    f"Could not find object with ID {self.tokens['value']}",
                    did_you_mean=(self.tokens['value'], self.root.objects_by_id.keys()),
                )
            elif object.gir_class and not object.gir_class.assignable_to(type):
                raise CompileError(
                    f"Cannot assign {object.gir_class.full_name} to {type.full_name}"
                )


    @docs()
    def docs(self):
        type = self.parent.value_type
        if isinstance(type, gir.Enumeration):
            if member := type.members.get(self.tokens["value"]):
                return member.doc
            else:
                return type.doc
        elif isinstance(type, gir.GirNode):
            return type.doc


    def get_semantic_tokens(self) -> T.Iterator[SemanticToken]:
        if isinstance(self.parent.value_type, gir.Enumeration):
            token = self.group.tokens["value"]
            yield SemanticToken(token.start, token.end, SemanticTokenType.EnumMember)


class BaseAttribute(AstNode):
    """ A helper class for attribute syntax of the form `name: literal_value;`"""

    tag_name: str = ""
    attr_name: str = "name"

    def emit_xml(self, xml: XmlEmitter):
        value = self.children[Value][0]
        attrs = { self.attr_name: self.tokens["name"] }

        if isinstance(value, TranslatedStringValue):
            attrs = { **attrs, **value.attrs }

        xml.start_tag(self.tag_name, **attrs)
        value.emit_xml(xml)
        xml.end_tag()


class BaseTypedAttribute(BaseAttribute):
    """ A BaseAttribute whose parent has a value_type property that can assist
    in validation. """
