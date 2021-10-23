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


from .errors import assert_true, AlreadyCaughtError, CompileError, CompilerBugError, MultipleErrors
from .gir import GirContext, get_namespace
from .utils import lazy_prop
from .xml_emitter import XmlEmitter


class Validator():
    def __init__(self, func, token_name=None, end_token_name=None):
        self.func = func
        self.token_name = token_name
        self.end_token_name = end_token_name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        key = "_validation_result_" + self.func.__name__

        if key + "_err" in instance.__dict__:
            # If the validator has failed before, raise a generic Exception.
            # We want anything that depends on this validation result to
            # fail, but not report the exception twice.
            raise AlreadyCaughtError()

        if key not in instance.__dict__:
            try:
                instance.__dict__[key] = self.func(instance)
            except CompileError as e:
                # Mark the validator as already failed so we don't print the
                # same message again
                instance.__dict__[key + "_err"] = True

                # This mess of code sets the error's start and end positions
                # from the tokens passed to the decorator, if they have not
                # already been set
                if self.token_name is not None and e.start is None:
                    group = instance.group.tokens.get(self.token_name)
                    if self.end_token_name is not None and group is None:
                        group = instance.group.tokens[self.end_token_name]
                    e.start = group.start
                if (self.token_name is not None or self.end_token_name is not None) and e.end is None:
                    e.end = instance.group.tokens[self.end_token_name or self.token_name].end

                # Re-raise the exception
                raise e

        # Return the validation result (which other validators, or the code
        # generation phase, might depend on)
        return instance.__dict__[key]


def validate(*args, **kwargs):
    """ Decorator for functions that validate an AST node. Exceptions raised
    during validation are marked with range information from the tokens. Also
    creates a cached property out of the function. """

    def decorator(func):
        return Validator(func, *args, **kwargs)

    return decorator


class AstNode:
    """ Base class for nodes in the abstract syntax tree. """

    def __init__(self):
        self.group = None
        self.parent = None
        self.child_nodes = None

    @lazy_prop
    def root(self):
        if self.parent is None:
            return self
        else:
            return self.parent.root

    @lazy_prop
    def errors(self):
        return list(self._get_errors())

    def _get_errors(self):
        for name in dir(type(self)):
            item = getattr(type(self), name)
            if isinstance(item, Validator):
                try:
                    getattr(self, name)
                except AlreadyCaughtError:
                    pass
                except CompileError as e:
                    yield e

        for child in self.child_nodes:
            yield from child._get_errors()


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
        super().__init__()
        assert_true(len(gtk_directives) == 1)

        self.gtk_directive = gtk_directives[0]
        self.imports = imports
        self.objects = objects
        self.templates = templates

    @validate()
    def gir(self):
        gir = GirContext()

        gir.add_namespace(self.gtk_directive.gir_namespace)
        for i in self.imports:
            gir.add_namespace(i.gir_namespace)

        return gir

    @validate()
    def at_most_one_template(self):
        if len(self.templates) > 1:
            raise CompileError(f"Only one template may be defined per file, but this file contains {len(self.templates)}",
                               self.templates[1].group.start)

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
        super().__init__()
        self.version = version

    @validate("version")
    def gir_namespace(self):
        if self.version in ["4.0"]:
            return get_namespace("Gtk", self.version)
        else:
            err = CompileError("Only GTK 4 is supported")
            if self.version.startswith("4"):
                err.hint("Expected the GIR version, not an exact version number. Use `@gtk \"4.0\";`.")
            else:
                err.hint("Expected `@gtk \"4.0\";`")
            raise err

    def emit_xml(self, xml: XmlEmitter):
        xml.put_self_closing("requires", lib="gtk", version=self.version)


class Import(AstNode):
    child_type = "imports"
    def __init__(self, namespace, version):
        super().__init__()
        self.namespace = namespace
        self.version = version

    @validate("namespace", "version")
    def gir_namespace(self):
        return get_namespace(self.namespace, self.version)

    def emit_xml(self, xml: XmlEmitter):
        pass


class Template(AstNode):
    child_type = "templates"
    def __init__(self, name, class_name, object_content, namespace=None):
        super().__init__()
        assert_true(len(object_content) == 1)

        self.name = name
        self.parent_namespace = namespace
        self.parent_class = class_name
        self.object_content = object_content[0]


    @validate("namespace", "class_name")
    def gir_parent(self):
        return self.root.gir.get_class(self.parent_class, self.parent_namespace)


    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("template", **{
            "class": self.name,
            "parent": self.gir_parent.glib_type_name,
        })
        self.object_content.emit_xml(xml)
        xml.end_tag()


class Object(AstNode):
    child_type = "objects"
    def __init__(self, class_name, object_content, namespace=None, id=None):
        super().__init__()
        assert_true(len(object_content) == 1)

        self.namespace = namespace
        self.class_name = class_name
        self.id = id
        self.object_content = object_content[0]

    @validate("namespace", "class_name")
    def gir_class(self):
        return self.root.gir.get_class(self.class_name, self.namespace)

    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("object", **{
            "class": self.gir_class.glib_type_name,
            "id": self.id,
        })
        self.object_content.emit_xml(xml)
        xml.end_tag()


class Child(AstNode):
    child_type = "children"
    def __init__(self, objects, child_type=None):
        super().__init__()
        assert_true(len(objects) == 1)
        self.object = objects[0]
        self.child_type = child_type

    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("child", type=self.child_type)
        self.object.emit_xml(xml)
        xml.end_tag()


class ObjectContent(AstNode):
    child_type = "object_content"
    def __init__(self, properties=[], signals=[], children=[], style=[]):
        super().__init__()
        self.properties = properties
        self.signals = signals
        self.children = children
        self.style = style

    @validate()
    def only_one_style_class(self):
        if len(self.style) > 1:
            raise CompileError(
                f"Only one style directive allowed per object, but this object contains {len(self.style)}",
                start=self.style[1].group.start,
            )

    def emit_xml(self, xml: XmlEmitter):
        for x in [*self.properties, *self.signals, *self.children, *self.style]:
            x.emit_xml(xml)


class Property(AstNode):
    child_type = "properties"
    def __init__(self, name, value=None, translatable=False, bind_source=None, bind_property=None):
        super().__init__()
        self.name = name
        self.value = value
        self.translatable = translatable
        self.bind_source = bind_source
        self.bind_property = bind_property


    @validate()
    def gir_property(self):
        if self.gir_class is not None:
            return self.gir_class.properties.get(self.name)

    @validate()
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
                f"Class {self.gir_class.full_name} does not contain a property called {self.name}",
                did_you_mean=(self.name, self.gir_class.properties.keys())
            )


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
        super().__init__()
        self.name = name
        self.handler = handler
        self.swapped = swapped
        self.after = after
        self.object = object
        self.detail_name = detail_name


    @validate()
    def gir_signal(self):
        if self.gir_class is not None:
            return self.gir_class.signals.get(self.name)

    @validate()
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
            print(self.gir_class.signals.keys())
            raise CompileError(
                f"Class {self.gir_class.full_name} does not contain a signal called {self.name}",
                did_you_mean=(self.name, self.gir_class.signals.keys())
            )

    def emit_xml(self, xml: XmlEmitter):
        name = self.name
        if self.detail_name:
            name += "::" + self.detail_name
        xml.put_self_closing("signal", name=name, handler=self.handler, swapped="true" if self.swapped else None)


class Style(AstNode):
    child_type = "style"

    def __init__(self, style_classes=None):
        super().__init__()
        self.style_classes = style_classes or []

    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("style")
        for style in self.style_classes:
            style.emit_xml(xml)
        xml.end_tag()


class StyleClass(AstNode):
    child_type = "style_classes"

    def __init__(self, name):
        super().__init__()
        self.name = name

    def emit_xml(self, xml):
        xml.put_self_closing("class", name=self.name)
