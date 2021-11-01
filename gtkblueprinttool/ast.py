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
from .errors import assert_true, AlreadyCaughtError, CompileError, CompilerBugError, MultipleErrors
from . import gir
from .lsp_utils import Completion, CompletionItemKind
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
            self._gir_errors.append(e)

        for i in self.children[Import]:
            try:
                gir_ctx.add_namespace(i.gir_namespace)
            except CompileError as e:
                self._gir_errors.append(e)

        return gir_ctx


    @validate()
    def gir_errors(self):
        # make sure gir is loaded
        self.gir
        if len(self._gir_errors):
            raise MultipleErrors(self._gir_errors)


    @validate()
    def at_most_one_template(self):
        if len(self.children[Template]) > 1:
            raise CompileError(f"Only one template may be defined per file, but this file contains {len(self.templates)}",
                               self.children[Template][1].group.start)


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
            if self.version.startswith("4"):
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


class Template(AstNode):
    @validate("namespace", "class_name")
    def gir_parent_exists(self):
        if not self.tokens["ignore_gir"]:
            self.root.gir.validate_class(self.tokens["class_name"], self.tokens["namespace"])

    @property
    def gir_parent(self):
        return self.root.gir.get_class(self.tokens["class_name"], self.tokens["namespace"])


    @docs("namespace")
    def namespace_docs(self):
        return self.root.gir.namespaces[self.tokens["namespace"]].doc

    @docs("class_name")
    def class_docs(self):
        if self.gir_parent:
            return self.gir_parent.doc


    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("template", **{
            "class": self.tokens["name"],
            "parent": self.gir_parent.glib_type_name if self.gir_parent else self.tokens["class_name"],
        })
        for child in self.children:
            child.emit_xml(xml)
        xml.end_tag()


class Object(AstNode):
    @validate("namespace", "class_name")
    def gir_class_exists(self):
        if not self.tokens["ignore_gir"]:
            self.root.gir.validate_class(self.tokens["class_name"], self.tokens["namespace"])

    @property
    def gir_class(self):
        if not self.tokens["ignore_gir"]:
            return self.root.gir.get_class(self.tokens["class_name"], self.tokens["namespace"])


    @docs("namespace")
    def namespace_docs(self):
        return self.root.gir.namespaces[self.tokens["namespace"]].doc


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


class Child(AstNode):
    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("child", type=self.tokens["child_type"])
        for child in self.children:
            child.emit_xml(xml)
        xml.end_tag()


class ObjectContent(AstNode):
    @property
    def gir_class(self):
        if isinstance(self.parent, Template):
            return self.parent.gir_parent
        elif isinstance(self.parent, Object):
            return self.parent.gir_class
        else:
            raise CompilerBugError()

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
    def gir_property(self):
        if self.gir_class is not None:
            return self.gir_class.properties.get(self.tokens["name"])


    @property
    def gir_class(self):
        parent = self.parent.parent
        if isinstance(parent, Template):
            return parent.gir_parent
        elif isinstance(parent, Object):
            return parent.gir_class
        else:
            raise CompilerBugError()


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


    @docs("name")
    def property_docs(self):
        if self.gir_property is not None:
            return self.gir_property.doc


    def emit_xml(self, xml: XmlEmitter):
        bind_flags = []
        if self.tokens["sync_create"]:
            bind_flags.append("sync-create")
        if self.tokens["after"]:
            bind_flags.append("after")
        bind_flags_str = "|".join(bind_flags) or None

        props = {
            "name": self.tokens["name"],
            "translatable": "yes" if self.tokens["translatable"] else None,
            "bind-source": self.tokens["bind_source"],
            "bind-property": self.tokens["bind_property"],
            "bind-flags": bind_flags_str,
        }

        if len(self.children[Object]) == 1:
            xml.start_tag("property", **props)
            self.children[Object][0].emit_xml(xml)
            xml.end_tag()
        elif self.tokens["value"] is None:
            xml.put_self_closing("property", **props)
        else:
            xml.start_tag("property", **props)
            xml.put_text(str(self.tokens["value"]))
            xml.end_tag()


class Signal(AstNode):
    @property
    def gir_signal(self):
        if self.gir_class is not None:
            return self.gir_class.signals.get(self.tokens["name"])


    @property
    def gir_class(self):
        parent = self.parent.parent
        if isinstance(parent, Template):
            return parent.gir_parent
        elif isinstance(parent, Object):
            return parent.gir_class
        else:
            raise CompilerBugError()


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
