# gir.py
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
import os, sys

from .errors import CompileError, CompilerBugError
from .utils import lazy_prop
from . import xml_reader


extra_search_paths: T.List[str] = []
_namespace_cache = {}

_search_paths = []
xdg_data_home = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
_search_paths.append(os.path.join(xdg_data_home, "gir-1.0"))
xdg_data_dirs = os.environ.get("XDG_DATA_DIRS", "/usr/share:/usr/local/share").split(":")
_search_paths += [os.path.join(dir, "gir-1.0") for dir in xdg_data_dirs]


def get_namespace(namespace, version):
    filename = f"{namespace}-{version}.gir"

    if filename not in _namespace_cache:
        for search_path in _search_paths:
            path = os.path.join(search_path, filename)

            if os.path.exists(path) and os.path.isfile(path):
                xml = xml_reader.parse(path, xml_reader.PARSE_GIR)
                repository = Repository(xml)

                _namespace_cache[filename] = repository.namespaces.get(namespace)
                break

        if filename not in _namespace_cache:
            raise CompileError(f"Namespace {namespace}-{version} could not be found")

    return _namespace_cache[filename]


class GirType:
    @property
    def doc(self):
        return None

    def assignable_to(self, other) -> bool:
        raise NotImplementedError()

    @property
    def full_name(self) -> str:
        raise NotImplementedError()


class BasicType(GirType):
    name: str = "unknown type"

    @property
    def full_name(self) -> str:
        return self.name

class BoolType(BasicType):
    name = "bool"
    def assignable_to(self, other) -> bool:
        return isinstance(other, BoolType)

class IntType(BasicType):
    name = "int"
    def assignable_to(self, other) -> bool:
        return isinstance(other, IntType) or isinstance(other, UIntType) or isinstance(other, FloatType)

class UIntType(BasicType):
    name = "uint"
    def assignable_to(self, other) -> bool:
        return isinstance(other, IntType) or isinstance(other, UIntType) or isinstance(other, FloatType)

class FloatType(BasicType):
    name = "float"
    def assignable_to(self, other) -> bool:
        return isinstance(other, FloatType)

class StringType(BasicType):
    name = "string"
    def assignable_to(self, other) -> bool:
        return isinstance(other, StringType)

_BASIC_TYPES = {
    "gboolean": BoolType,
    "int": IntType,
    "gint": IntType,
    "gint64": IntType,
    "guint": UIntType,
    "guint64": UIntType,
    "gfloat": FloatType,
    "gdouble": FloatType,
    "float": FloatType,
    "double": FloatType,
    "utf8": StringType,
}

class GirNode:
    def __init__(self, container, xml):
        self.container = container
        self.xml = xml

    def get_containing(self, container_type):
        if self.container is None:
            return None
        elif isinstance(self.container, container_type):
            return self.container
        else:
            return self.container.get_containing(container_type)

    @lazy_prop
    def glib_type_name(self):
        return self.xml["glib:type-name"]

    @lazy_prop
    def full_name(self):
        if self.container is None:
            return self.name
        else:
            return f"{self.container.name}.{self.name}"

    @lazy_prop
    def name(self) -> str:
        return self.xml["name"]

    @lazy_prop
    def available_in(self) -> str:
        return self.xml.get("version")

    @lazy_prop
    def doc(self) -> T.Optional[str]:
        sections = []

        if self.signature:
            sections.append("```\n" + self.signature + "\n```")

        el = self.xml.get_elements("doc")
        if len(el) == 1:
            sections.append(el[0].cdata.strip())

        return "\n\n---\n\n".join(sections)

    @property
    def signature(self) -> T.Optional[str]:
        return None

    @property
    def type_name(self):
        return self.xml.get_elements('type')[0]['name']

    @property
    def type(self):
        return self.get_containing(Namespace).lookup_type(self.type_name)


class Property(GirNode):
    def __init__(self, klass, xml: xml_reader.Element):
        super().__init__(klass, xml)

    @property
    def type_name(self):
        return self.xml.get_elements('type')[0]['name']

    @property
    def signature(self):
        return f"{self.type_name} {self.container.name}.{self.name}"


class Parameter(GirNode):
    def __init__(self, container: GirNode, xml: xml_reader.Element):
        super().__init__(container, xml)


class Signal(GirNode):
    def __init__(self, klass, xml: xml_reader.Element):
        super().__init__(klass, xml)
        if parameters := xml.get_elements('parameters'):
            self.params = [Parameter(self, child) for child in parameters[0].get_elements('parameter')]
        else:
            self.params = []

    @property
    def signature(self):
        args = ", ".join([f"{p.type_name} {p.name}" for p in self.params])
        return f"signal {self.container.name}.{self.name} ({args})"


class Interface(GirNode, GirType):
    def __init__(self, ns, xml: xml_reader.Element):
        super().__init__(ns, xml)
        self.properties = {child["name"]: Property(self, child) for child in xml.get_elements("property")}
        self.signals = {child["name"]: Signal(self, child) for child in xml.get_elements("glib:signal")}
        self.prerequisites = [child["name"] for child in xml.get_elements("prerequisite")]

    def assignable_to(self, other) -> bool:
        if self == other:
            return True
        for pre in self.prerequisites:
            if self.get_containing(Namespace).lookup_type(pre).assignable_to(other):
                return True
        return False


class Class(GirNode, GirType):
    def __init__(self, ns, xml: xml_reader.Element):
        super().__init__(ns, xml)
        self._parent = xml["parent"]
        self.implements = [impl["name"] for impl in xml.get_elements("implements")]
        self.own_properties = {child["name"]: Property(self, child) for child in xml.get_elements("property")}
        self.own_signals = {child["name"]: Signal(self, child) for child in xml.get_elements("glib:signal")}

    @property
    def signature(self):
        result = f"class {self.container.name}.{self.name}"
        if self.parent is not None:
            result += f" : {self.parent.container.name}.{self.parent.name}"
        if len(self.implements):
            result += " implements " + ", ".join(self.implements)
        return result

    @lazy_prop
    def properties(self):
        return { p.name: p for p in self._enum_properties() }

    @lazy_prop
    def signals(self):
        return { s.name: s for s in self._enum_signals() }

    @lazy_prop
    def parent(self):
        if self._parent is None:
            return None
        return self.get_containing(Namespace).lookup_type(self._parent)


    def assignable_to(self, other) -> bool:
        if self == other:
            return True
        elif self.parent and self.parent.assignable_to(other):
            return True
        elif other in self.implements:
            return True
        else:
            return False


    def _enum_properties(self):
        yield from self.own_properties.values()

        if self.parent is not None:
            yield from self.parent.properties.values()

        for impl in self.implements:
            yield from self.get_containing(Namespace).lookup_type(impl).properties.values()

    def _enum_signals(self):
        yield from self.own_signals.values()

        if self.parent is not None:
            yield from self.parent.signals.values()

        for impl in self.implements:
            yield from self.get_containing(Namespace).lookup_type(impl).signals.values()


class EnumMember(GirNode):
    def __init__(self, ns, xml: xml_reader.Element):
        super().__init__(ns, xml)
        self._value = xml["value"]

    @property
    def value(self):
        return self._value

    @property
    def nick(self):
        return self.xml["glib:nick"]

    @property
    def signature(self):
        return f"enum member {self.full_name} = {self.value}"


class Enumeration(GirNode):
    def __init__(self, ns, xml: xml_reader.Element):
        super().__init__(ns, xml)
        self.members = { child["name"]: EnumMember(self, child) for child in xml.get_elements("member") }

    @property
    def signature(self):
        return f"enum {self.full_name}"


class Namespace(GirNode):
    def __init__(self, repo, xml: xml_reader.Element):
        super().__init__(repo, xml)
        self.classes = { child["name"]: Class(self, child) for child in xml.get_elements("class") }
        self.interfaces = { child["name"]: Interface(self, child) for child in xml.get_elements("interface") }
        self.enumerations = { child["name"]: Enumeration(self, child) for child in xml.get_elements("enumeration") }
        self.version = xml["version"]

    @property
    def signature(self):
        return f"namespace {self.name} {self.version}"


    def get_type(self, name):
        """ Gets a type (class, interface, enum, etc.) from this namespace. """
        return self.classes.get(name) or self.interfaces.get(name) or self.enumerations.get(name)


    def lookup_type(self, type_name: str):
        """ Looks up a type in the scope of this namespace (including in the
        namespace's dependencies). """

        if type_name in _BASIC_TYPES:
            return _BASIC_TYPES[type_name]()
        elif "." in type_name:
            ns, name = type_name.split(".", 1)
            return self.get_containing(Repository).get_type(name, ns)
        else:
            return self.get_type(type_name)


class Repository(GirNode):
    def __init__(self, xml: xml_reader.Element):
        super().__init__(None, xml)
        self.namespaces = { child["name"]: Namespace(self, child) for child in xml.get_elements("namespace") }

        try:
            self.includes = { include["name"]: get_namespace(include["name"], include["version"]) for include in xml.get_elements("include") }
        except:
            raise CompilerBugError(f"Failed to load dependencies.")


    def get_type(self, name: str, ns: str) -> T.Optional[GirNode]:
        if namespace := self.namespaces.get(ns):
            return namespace.get_type(name)
        else:
            return self.lookup_namespace(ns).get_type(name)


    def lookup_namespace(self, ns: str):
        """ Finds a namespace among this namespace's dependencies. """
        if namespace := self.namespaces.get(ns):
            return namespace
        else:
            for include in self.includes.values():
                if namespace := include.get_containing(Repository).lookup_namespace(ns):
                    return namespace


class GirContext:
    def __init__(self):
        self.namespaces = {}


    def add_namespace(self, namespace: Namespace):
        other = self.namespaces.get(namespace.name)
        if other is not None and other.version != namespace.version:
            raise CompileError(f"Namespace {namespace.name}-{namespace.version} can't be imported because version {other.version} was imported earlier")

        self.namespaces[namespace.name] = namespace


    def get_type(self, name: str, ns: str) -> T.Optional[GirNode]:
        ns = ns or "Gtk"

        if ns not in self.namespaces:
            return None

        return self.namespaces[ns].get_type(name)


    def get_class(self, name: str, ns: str) -> T.Optional[Class]:
        type = self.get_type(name, ns)
        if isinstance(type, Class):
            return type
        else:
            return None


    def validate_ns(self, ns: str):
        """ Raises an exception if there is a problem looking up the given
        namespace. """

        ns = ns or "Gtk"

        if ns not in self.namespaces:
            raise CompileError(
                f"Namespace {ns} was not imported",
                did_you_mean=(ns, self.namespaces.keys()),
            )


    def validate_class(self, name: str, ns: str):
        """ Raises an exception if there is a problem looking up the given
        class (it doesn't exist, it isn't a class, etc.) """

        ns = ns or "Gtk"
        self.validate_ns(ns)

        type = self.get_type(name, ns)

        if type is None:
            raise CompileError(
                f"Namespace {ns} does not contain a class called {name}",
                did_you_mean=(name, self.namespaces[ns].classes.keys()),
            )
        elif not isinstance(type, Class):
            raise CompileError(
                f"{ns}.{name} is not a class",
                did_you_mean=(name, self.namespaces[ns].classes.keys()),
            )

