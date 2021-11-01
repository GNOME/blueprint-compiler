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
            raise CompileError(f"Namespace `{namespace}-{version}` could not be found.")

    return _namespace_cache[filename]


class GirNode:
    def __init__(self, xml):
        self.xml = xml

    @lazy_prop
    def glib_type_name(self):
        return self.xml["glib:type-name"]

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


class Property(GirNode):
    def __init__(self, klass, xml: xml_reader.Element):
        super().__init__(xml)
        self.klass = klass

    @property
    def type_name(self):
        return self.xml.get_elements('type')[0]['name']

    @property
    def signature(self):
        return f"{self.type_name} {self.klass.name}.{self.name}"


class Parameter(GirNode):
    def __init__(self, xml: xml_reader.Element):
        super().__init__(xml)

    @property
    def type_name(self):
        return self.xml.get_elements('type')[0]['name']


class Signal(GirNode):
    def __init__(self, klass, xml: xml_reader.Element):
        super().__init__(xml)
        self.klass = klass
        if parameters := xml.get_elements('parameters'):
            self.params = [Parameter(child) for child in parameters[0].get_elements('parameter')]
        else:
            self.params = []

    @property
    def signature(self):
        args = ", ".join([f"{p.type_name} {p.name}" for p in self.params])
        return f"signal {self.klass.name}.{self.name} ({args})"


class Interface(GirNode):
    def __init__(self, ns, xml: xml_reader.Element):
        super().__init__(xml)
        self.ns = ns
        self.properties = {child["name"]: Property(self, child) for child in xml.get_elements("property")}
        self.signals = {child["name"]: Signal(self, child) for child in xml.get_elements("glib:signal")}


class Class(GirNode):
    def __init__(self, ns, xml: xml_reader.Element):
        super().__init__(xml)
        self.ns = ns
        self._parent = xml["parent"]
        self.implements = [impl["name"] for impl in xml.get_elements("implements")]
        self.own_properties = {child["name"]: Property(self, child) for child in xml.get_elements("property")}
        self.own_signals = {child["name"]: Signal(self, child) for child in xml.get_elements("glib:signal")}

    @property
    def signature(self):
        result = f"class {self.ns.name}.{self.name}"
        if self.parent is not None:
            result += f" : {self.parent.ns.name}.{self.parent.name}"
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
    def full_name(self):
        return f"{self.ns.name}.{self.name}"

    @lazy_prop
    def parent(self):
        if self._parent is None:
            return None
        return self.ns.lookup_class(self._parent)


    def _enum_properties(self):
        yield from self.own_properties.values()

        if self.parent is not None:
            yield from self.parent.properties.values()

        for impl in self.implements:
            yield from self.ns.lookup_interface(impl).properties.values()

    def _enum_signals(self):
        yield from self.own_signals.values()

        if self.parent is not None:
            yield from self.parent.signals.values()

        for impl in self.implements:
            yield from self.ns.lookup_interface(impl).signals.values()


class Namespace(GirNode):
    def __init__(self, repo, xml: xml_reader.Element):
        super().__init__(xml)
        self.repo = repo
        self.classes = { child["name"]: Class(self, child) for child in xml.get_elements("class") }
        self.interfaces = { child["name"]: Interface(self, child) for child in xml.get_elements("interface") }
        self.version = xml["version"]

    @property
    def signature(self):
        return f"namespace {self.name} {self.version}"


    def get_type(self, name):
        """ Gets a type (class, interface, enum, etc.) from this namespace. """
        return self.classes.get(name) or self.interfaces.get(name)


    def lookup_class(self, name: str):
        if "." in name:
            ns, cls = name.split(".")
            return self.repo.lookup_namespace(ns).lookup_class(cls)
        else:
            return self.classes.get(name)

    def lookup_interface(self, name: str):
        if "." in name:
            ns, iface = name.split(".")
            return self.repo.lookup_namespace(ns).lookup_interface(iface)
        else:
            return self.interfaces.get(name)

    def lookup_namespace(self, ns: str):
        return self.repo.lookup_namespace(ns)


class Repository(GirNode):
    def __init__(self, xml: xml_reader.Element):
        super().__init__(xml)
        self.namespaces = { child["name"]: Namespace(self, child) for child in xml.get_elements("namespace") }

        try:
            self.includes = { include["name"]: get_namespace(include["name"], include["version"]) for include in xml.get_elements("include") }
        except:
            raise CompilerBugError(f"Failed to load dependencies.")

    def lookup_namespace(self, name: str):
        ns = self.namespaces.get(name)
        if ns is not None:
            return ns
        for include in self.includes.values():
            ns = include.lookup_namespace(name)
            if ns is not None:
                return ns


class GirContext:
    def __init__(self):
        self.namespaces = {}


    def add_namespace(self, namespace: Namespace):
        other = self.namespaces.get(namespace.name)
        if other is not None and other.version != namespace.version:
            raise CompileError(f"Namespace {namespace.name}-{namespace.version} can't be imported because version {other.version} was imported earlier")

        self.namespaces[namespace.name] = namespace


    def get_type(self, name: str, ns: str) -> GirNode:
        ns = ns or "Gtk"

        if ns not in self.namespaces:
            return None

        return self.namespaces[ns].get_type(name)


    def get_class(self, name: str, ns: str) -> T.Optional[Class]:
        type = self.get_type(name, ns)
        if isinstance(type, Class):
            return type


    def validate_class(self, name: str, ns: str) -> Class:
        """ Raises an exception if there is a problem looking up the given
        class (it doesn't exist, it isn't a class, etc.) """

        ns = ns or "Gtk"

        if ns not in self.namespaces:
            raise CompileError(
                f"Namespace `{ns}` was not imported.",
                did_you_mean=(ns, self.namespaces.keys()),
            )

        type = self.get_type(name, ns)

        if type is None:
            raise CompileError(
                f"Namespace {ns} does not contain a class called {name}.",
                did_you_mean=(name, self.namespaces[ns].classes.keys()),
            )
        elif not isinstance(type, Class):
            raise CompileError(
                f"{ns}.{name} is not a class.",
                did_you_mean=(name, self.namespaces[ns].classes.keys()),
            )

