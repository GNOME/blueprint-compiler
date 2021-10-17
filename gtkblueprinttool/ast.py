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


from .errors import assert_true
from .xml_emitter import XmlEmitter


class AstNode:
    """ Base class for nodes in the abstract syntax tree. """

    def generate(self) -> str:
        """ Generates an XML string from the node. """
        xml = XmlEmitter()
        self.emit_xml(xml)
        return xml.result

    def emit_xml(self, xml: XmlEmitter):
        """ Emits the XML representation of this AST node to the XmlEmitter. """
        raise NotImplementedError()


class UI(AstNode):
    """ The AST node for the entire file """

    def __init__(self, gtk_directives=[], imports=[], objects=[], templates=[]):
        assert_true(len(gtk_directives) == 1)

        self.gtk_directive = gtk_directives[0]
        self.imports = imports
        self.objects = objects
        self.templates = templates

    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("interface")
        self.gtk_directive.emit_xml(xml)
        for object in self.objects:
            object.emit_xml(xml)
        for template in self.templates:
            template.emit_xml(xml)
        xml.end_tag()


class GtkDirective(AstNode):
    child_type = "gtk_directives"
    def __init__(self, version):
        self.version = version

    def emit_xml(self, xml: XmlEmitter):
        xml.put_self_closing("requires", lib="gtk", version=self.version)


class Import(AstNode):
    child_type = "imports"
    def __init__(self, namespace, version):
        self.namespace = namespace
        self.version = version

    def emit_xml(self, xml: XmlEmitter):
        pass


class Template(AstNode):
    child_type = "templates"
    def __init__(self, name, class_name, object_content, namespace=None):
        assert_true(len(object_content) == 1)

        self.name = name
        self.parent_namespace = namespace
        self.parent_class = class_name
        self.object_content = object_content[0]

    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("template", **{
            "class": self.name,
            "parent": self.parent_namespace + self.parent_class,
        })
        self.object_content.emit_xml(xml)
        xml.end_tag()


class Object(AstNode):
    child_type = "objects"
    def __init__(self, class_name, object_content, namespace=None, id=None):
        assert_true(len(object_content) == 1)

        self.namespace = namespace
        self.class_name = class_name
        self.id = id
        self.object_content = object_content[0]

    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("object", **{
            "class": self.namespace + self.class_name,
            "id": self.id,
        })
        self.object_content.emit_xml(xml)
        xml.end_tag()


class Child(AstNode):
    child_type = "children"
    def __init__(self, objects, child_type=None):
        assert_true(len(objects) == 1)
        self.object = objects[0]
        self.child_type = child_type

    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("child", type=self.child_type)
        self.object.emit_xml(xml)
        xml.end_tag()


class ObjectContent(AstNode):
    child_type = "object_content"
    def __init__(self, properties=[], signals=[], children=[]):
        self.properties = properties
        self.signals = signals
        self.children = children

    def emit_xml(self, xml: XmlEmitter):
        for prop in self.properties:
            prop.emit_xml(xml)
        for signal in self.signals:
            signal.emit_xml(xml)
        for child in self.children:
            child.emit_xml(xml)


class Property(AstNode):
    child_type = "properties"
    def __init__(self, name, value=None, translatable=False, bind_source=None, bind_property=None):
        self.name = name
        self.value = value
        self.translatable = translatable
        self.bind_source = bind_source
        self.bind_property = bind_property

    def emit_xml(self, xml: XmlEmitter):
        props = {
            "name": self.name,
            "translatable": "yes" if self.translatable else None,
            "bind-source": self.bind_source,
            "bind-property": self.bind_property,
        }
        if self.value is None:
            xml.put_self_closing("property", **props)
        else:
            xml.start_tag("property", **props)
            xml.put_text(str(self.value))
            xml.end_tag()


class Signal(AstNode):
    child_type = "signals"
    def __init__(self, name, handler, swapped=False, after=False, object=False, detail_name=None):
        self.name = name
        self.handler = handler
        self.swapped = swapped
        self.after = after
        self.object = object
        self.detail_name = detail_name

    def emit_xml(self, xml: XmlEmitter):
        name = self.name
        if self.detail_name:
            name += "::" + self.detail_name
        xml.put_self_closing("signal", name=name, handler=self.handler, swapped="true" if self.swapped else None)
