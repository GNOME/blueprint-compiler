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

import os
import sys
import typing as T
from functools import cached_property

import gi  # type: ignore
from gi.repository import GLib, GObject  # type: ignore

from . import xml_reader
from .errors import CompileError, CompilerBugError

try:
    gi.require_version("GIRepository", "3.0")
    from gi.repository import GIRepository  # type: ignore

    gir3 = True

    arg_info_get_type_info = GIRepository.ArgInfo.get_type_info

    callable_info_get_n_args = GIRepository.CallableInfo.get_n_args
    callable_info_get_arg = GIRepository.CallableInfo.get_arg
    callable_info_get_return_type = GIRepository.CallableInfo.get_return_type

    interface_info_get_n_signals = GIRepository.InterfaceInfo.get_n_signals
    interface_info_get_signal = GIRepository.InterfaceInfo.get_signal
    interface_info_get_n_prerequisites = GIRepository.InterfaceInfo.get_n_prerequisites
    interface_info_get_prerequisite = GIRepository.InterfaceInfo.get_prerequisite
    interface_info_get_n_properties = GIRepository.InterfaceInfo.get_n_properties
    interface_info_get_property = GIRepository.InterfaceInfo.get_property

    object_info_get_parent = GIRepository.ObjectInfo.get_parent
    object_info_get_n_signals = GIRepository.ObjectInfo.get_n_signals
    object_info_get_signal = GIRepository.ObjectInfo.get_signal
    object_info_get_n_properties = GIRepository.ObjectInfo.get_n_properties
    object_info_get_property = GIRepository.ObjectInfo.get_property
    object_info_get_n_interfaces = GIRepository.ObjectInfo.get_n_interfaces
    object_info_get_interface = GIRepository.ObjectInfo.get_interface
    object_info_get_type_name = GIRepository.ObjectInfo.get_type_name

    property_info_get_type_info = GIRepository.PropertyInfo.get_type_info
    property_info_get_flags = GIRepository.PropertyInfo.get_flags

    registered_type_info_get_type_name = GIRepository.RegisteredTypeInfo.get_type_name

    type_info_get_tag = GIRepository.TypeInfo.get_tag
    type_info_get_interface = GIRepository.TypeInfo.get_interface
    type_info_get_param_type = GIRepository.TypeInfo.get_param_type

    value_info_get_value = GIRepository.ValueInfo.get_value

except ValueError:
    # We can remove this once we can bump the minimum dependencies
    # to glib 2.80 and pygobject 3.52
    # dependency('glib-2.0', version: '>= 2.80.0')
    # dependency('girepository-2.0', version: '>= 2.80.0')
    gi.require_version("GIRepository", "2.0")
    from gi.repository import GIRepository  # type: ignore

    gir3 = False

    arg_info_get_type_info = GIRepository.arg_info_get_type

    callable_info_get_n_args = GIRepository.callable_info_get_n_args
    callable_info_get_arg = GIRepository.callable_info_get_arg
    callable_info_get_return_type = GIRepository.callable_info_get_return_type

    interface_info_get_n_signals = GIRepository.interface_info_get_n_signals
    interface_info_get_signal = GIRepository.interface_info_get_signal
    interface_info_get_n_prerequisites = GIRepository.interface_info_get_n_prerequisites
    interface_info_get_prerequisite = GIRepository.interface_info_get_prerequisite
    interface_info_get_n_properties = GIRepository.interface_info_get_n_properties
    interface_info_get_property = GIRepository.interface_info_get_property

    object_info_get_parent = GIRepository.object_info_get_parent
    object_info_get_n_signals = GIRepository.object_info_get_n_signals
    object_info_get_signal = GIRepository.object_info_get_signal
    object_info_get_n_properties = GIRepository.object_info_get_n_properties
    object_info_get_property = GIRepository.object_info_get_property
    object_info_get_n_interfaces = GIRepository.object_info_get_n_interfaces
    object_info_get_interface = GIRepository.object_info_get_interface
    object_info_get_type_name = GIRepository.object_info_get_type_name

    property_info_get_type_info = GIRepository.property_info_get_type
    property_info_get_flags = GIRepository.property_info_get_flags

    registered_type_info_get_type_name = GIRepository.registered_type_info_get_type_name

    type_info_get_tag = GIRepository.type_info_get_tag
    type_info_get_interface = GIRepository.type_info_get_interface
    type_info_get_param_type = GIRepository.type_info_get_param_type

    value_info_get_value = GIRepository.value_info_get_value

_namespace_cache: T.Dict[str, "Namespace"] = {}
_xml_cache: T.Dict[str, xml_reader.Element] = {}

_user_typelib_search_paths = []
_user_gir_search_paths = []


def add_typelib_search_path(path: str):
    _user_typelib_search_paths.append(path)


def add_gir_search_path(path: str):
    _user_gir_search_paths.append(path)


def get_namespace(namespace: str, version: str) -> "Namespace":
    filename = f"{namespace}-{version}.typelib"

    if filename not in _namespace_cache:
        try:
            gir_repo = GIRepository.Repository()

            for path in reversed(_user_typelib_search_paths):
                gir_repo.prepend_search_path(path)

            gir_repo.require(namespace, version, 0)
            repo = Repository(gir_repo, namespace)
            _namespace_cache[filename] = repo.lookup_namespace(namespace)
        except GLib.GError as e:
            if e.matches(
                GIRepository.Repository.error_quark(),
                GIRepository.RepositoryError.TYPELIB_NOT_FOUND,
            ):
                raise CompileError(
                    f"Namespace {namespace}-{version} could not be found",
                    hints=[
                        "search path: " + os.pathsep.join(gir_repo.get_search_path())
                    ],
                )
            else:
                raise e

    return _namespace_cache[filename]


_available_namespaces: list[tuple[str, str]] = []


def get_available_namespaces() -> T.List[T.Tuple[str, str]]:
    if len(_available_namespaces):
        return _available_namespaces

    gir_repo = GIRepository.Repository()
    search_paths: list[str] = [
        *_user_typelib_search_paths,
        *gir_repo.get_search_path(),
    ]

    for search_path in search_paths:
        try:
            filenames = os.listdir(search_path)
        except FileNotFoundError:
            continue

        for filename in filenames:
            if filename.endswith(".typelib"):
                namespace, version = filename.removesuffix(".typelib").rsplit("-", 1)
                _available_namespaces.append((namespace, version))

    return _available_namespaces


def get_xml(namespace: str, version: str):
    from .main import DATADIR

    search_paths = []

    search_paths += _user_gir_search_paths

    if gi_gir_path := os.environ.get("GI_GIR_PATH"):
        search_paths += gi_gir_path.split(os.pathsep)

    try:
        from gi.repository import GLib  # type: ignore

        search_paths += [
            os.path.join(path, "gir-1.0") for path in GLib.get_user_data_dir()
        ]
        search_paths += [
            os.path.join(path, "gir-1.0") for path in GLib.get_system_data_dirs()
        ]
    except ImportError:
        pass

    if DATADIR is not None:
        search_paths += [os.path.join(DATADIR, "gir-1.0")]

    if sys.platform != "win32":
        search_paths += ["/usr/share/gir-1.0", "/usr/local/share/gir-1.0"]

    filename = f"{namespace}-{version}.gir"

    if filename not in _xml_cache:
        for search_path in search_paths:
            path = os.path.join(search_path, filename)

            if os.path.exists(path) and os.path.isfile(path):
                _xml_cache[filename] = xml_reader.parse(path)
                break

        if filename not in _xml_cache:
            raise CompileError(
                f"GObject introspection file '{namespace}-{version}.gir' could not be found",
                hints=["search path: " + os.pathsep.join(search_paths)],
            )

    return _xml_cache[filename]


ONLINE_DOCS = {
    "Adw-1": "https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1-latest/",
    "Gdk-4.0": "https://docs.gtk.org/gdk4/",
    "GdkPixbuf-2.0": "https://docs.gtk.org/gdk-pixbuf/",
    "Gio-2.0": "https://docs.gtk.org/gio/",
    "GLib-2.0": "https://docs.gtk.org/glib/",
    "GModule-2.0": "https://docs.gtk.org/gmodule/",
    "GObject-2.0": "https://docs.gtk.org/gobject/",
    "Gsk-4.0": "https://docs.gtk.org/gsk4/",
    "Gtk-4.0": "https://docs.gtk.org/gtk4/",
    "GtkSource-5": "https://gnome.pages.gitlab.gnome.org/gtksourceview/gtksourceview5",
    "Pango-1.0": "https://docs.gtk.org/Pango/",
    "Shumate-1.0": "https://gnome.pages.gitlab.gnome.org/libshumate/",
    "WebKit2-4.1": "https://webkitgtk.org/reference/webkit2gtk/stable/",
}


class GirType:
    @property
    def doc(self) -> T.Optional[str]:
        return None

    def assignable_to(self, other: "GirType") -> bool:
        raise NotImplementedError()

    @property
    def name(self) -> str:
        """The GIR name of the type, not including the namespace"""
        raise NotImplementedError()

    @property
    def full_name(self) -> str:
        """The GIR name of the type to use in diagnostics"""
        raise NotImplementedError()

    @property
    def glib_type_name(self) -> str:
        """The name of the type in the GObject type system, suitable to pass to `g_type_from_name()`."""
        raise NotImplementedError()

    @property
    def incomplete(self) -> bool:
        return False

    @property
    def deprecated(self) -> bool:
        return False

    @property
    def deprecated_doc(self) -> T.Optional[str]:
        return None


class ExternType(GirType):
    def __init__(self, ns: T.Optional[str], name: str) -> None:
        super().__init__()
        self._name = name
        self._ns = ns

    def assignable_to(self, other: GirType) -> bool:
        return True

    @property
    def full_name(self) -> str:
        if self._ns:
            return f"${self._ns}.{self._name}"
        else:
            return self._name

    @property
    def glib_type_name(self) -> str:
        if self._ns:
            return self._ns + self._name
        else:
            return self._name

    @property
    def incomplete(self) -> bool:
        return True


class ArrayType(GirType):
    def __init__(self, inner: GirType) -> None:
        self._inner = inner

    def assignable_to(self, other: GirType) -> bool:
        return isinstance(other, ArrayType) and self._inner.assignable_to(other._inner)

    @property
    def inner(self) -> GirType:
        return self._inner

    @property
    def name(self) -> str:
        return self._inner.name + "[]"

    @property
    def full_name(self) -> str:
        return self._inner.full_name + "[]"


class BasicType(GirType):
    name: str = "unknown type"

    @property
    def full_name(self) -> str:
        return self.name


class VoidType(GirType):
    name: str = "void"
    glib_type_name: str = "void"

    def assignable_to(self, other: GirType):
        return False


class BoolType(BasicType):
    name = "bool"
    glib_type_name: str = "gboolean"

    def assignable_to(self, other: GirType) -> bool:
        return isinstance(other, BoolType)


class IntType(BasicType):
    name = "int"
    glib_type_name: str = "gint"

    def assignable_to(self, other: GirType) -> bool:
        return (
            isinstance(other, IntType)
            or isinstance(other, UIntType)
            or isinstance(other, FloatType)
        )


class UIntType(BasicType):
    name = "uint"
    glib_type_name: str = "guint"

    def assignable_to(self, other: GirType) -> bool:
        return (
            isinstance(other, IntType)
            or isinstance(other, UIntType)
            or isinstance(other, FloatType)
        )


class FloatType(BasicType):
    name = "float"
    glib_type_name: str = "gfloat"

    def assignable_to(self, other: GirType) -> bool:
        return isinstance(other, FloatType)


class StringType(BasicType):
    name = "string"
    glib_type_name: str = "gchararray"

    def assignable_to(self, other: GirType) -> bool:
        return isinstance(other, StringType)


class TypeType(BasicType):
    name = "GType"
    glib_type_name: str = "GType"

    def assignable_to(self, other: GirType) -> bool:
        return isinstance(other, TypeType)


_BASIC_TYPES = {
    "bool": BoolType,
    "string": StringType,
    "int": IntType,
    "uint": UIntType,
    "float": FloatType,
    "double": FloatType,
    "type": TypeType,
}


TNode = T.TypeVar("TNode", bound="GirNode")


class GirNode:
    xml_tag: str

    def __init__(
        self, container: T.Optional["GirNode"], info: T.Optional[GIRepository.BaseInfo]
    ) -> None:
        self.container = container
        self.info = info

    def get_containing(self, container_type: T.Type[TNode]) -> TNode:
        if self.container is None:
            raise CompilerBugError()
        elif isinstance(self.container, container_type):
            return self.container
        else:
            return self.container.get_containing(container_type)

    @cached_property
    def xml(self):
        for el in self.container.xml.children:
            if el.attrs.get("name") == self.name:
                if el.tag == self.xml_tag:
                    return el

    @cached_property
    def full_name(self) -> str:
        if self.container is None:
            return self.name
        else:
            return f"{self.container.name}.{self.name}"

    @cached_property
    def name(self) -> str:
        assert self.info is not None
        return self.info.get_name()

    @cached_property
    def available_in(self) -> str:
        return self.xml.get("version")

    @cached_property
    def detail(self) -> T.Optional[str]:
        try:
            el = self.xml.get_elements("doc")
            if len(el) == 1:
                return el[0].cdata.strip().partition("\n")[0]
            else:
                return None
        except:
            return None

    @cached_property
    def doc(self) -> T.Optional[str]:
        sections = []

        if self.signature:
            sections.append("```\n" + self.signature + "\n```")

        try:
            el = self.xml.get_elements("doc")
            if len(el) == 1:
                sections.append(el[0].cdata.strip())
        except:
            # Not a huge deal, but if you want docs in the language server you
            # should ensure .gir files are installed
            sections.append("Documentation is not installed")

        if self.online_docs:
            sections.append(f"[Online documentation]({self.online_docs})")

        return "\n\n---\n\n".join(sections)

    @property
    def online_docs(self) -> T.Optional[str]:
        return None

    @property
    def signature(self) -> T.Optional[str]:
        return None

    @property
    def type(self) -> GirType:
        raise NotImplementedError()

    @property
    def deprecated(self) -> bool:
        if self.info is None:
            return False
        else:
            return self.info.is_deprecated()

    @property
    def deprecated_doc(self) -> T.Optional[str]:
        try:
            return self.xml.get_elements("doc-deprecated")[0].cdata.strip()
        except:
            return None


class Property(GirNode):
    xml_tag = "property"

    def __init__(
        self, klass: T.Union["Class", "Interface"], info: GIRepository.BaseInfo
    ):
        super().__init__(klass, info)

    @cached_property
    def type(self):
        return self.get_containing(Repository)._resolve_type_info(
            property_info_get_type_info(self.info)
        )

    @cached_property
    def signature(self):
        return f"{self.type.full_name} {self.container.name}:{self.name}"

    @property
    def writable(self) -> bool:
        flags = property_info_get_flags(self.info)
        return bool(flags & GObject.ParamFlags.WRITABLE)

    @property
    def construct_only(self) -> bool:
        flags = property_info_get_flags(self.info)
        return bool(flags & GObject.ParamFlags.CONSTRUCT_ONLY)

    @property
    def online_docs(self) -> T.Optional[str]:
        if ns := self.get_containing(Namespace).online_docs:
            assert self.container is not None
            return f"{ns}property.{self.container.name}.{self.name}.html"
        else:
            return None


class Argument(GirNode):
    def __init__(self, container: GirNode, info: GIRepository.BaseInfo) -> None:
        super().__init__(container, info)

    @cached_property
    def type(self) -> GirType:
        typeinfo = arg_info_get_type_info(self.info)
        return self.get_containing(Repository)._resolve_type_info(typeinfo)


class Signature(GirNode):
    def __init__(self, container: GirNode, info: GIRepository.BaseInfo) -> None:
        super().__init__(container, info)

    @cached_property
    def args(self) -> T.List[Argument]:
        result = []
        for i in range(callable_info_get_n_args(self.info)):
            arg_info = callable_info_get_arg(self.info, i)
            result.append(Argument(self, arg_info))
        return result

    @cached_property
    def return_type(self) -> GirType:
        return self.get_containing(Repository)._resolve_type_info(
            callable_info_get_return_type(self.info)
        )


class Signal(GirNode):
    xml_tag = "glib:signal"

    def __init__(
        self, klass: T.Union["Class", "Interface"], info: GIRepository.BaseInfo
    ) -> None:
        super().__init__(klass, info)

    @cached_property
    def gir_signature(self) -> Signature:
        return Signature(self, self.info)

    @property
    def signature(self):
        args = ", ".join(
            [f"{a.type.full_name} {a.name}" for a in self.gir_signature.args]
        )
        result = f"signal {self.container.full_name}::{self.name} ({args})"
        if not isinstance(self.gir_signature.return_type, VoidType):
            result += f" -> {self.gir_signature.return_type.full_name}"
        return result

    @property
    def online_docs(self) -> T.Optional[str]:
        if ns := self.get_containing(Namespace).online_docs:
            assert self.container is not None
            return f"{ns}signal.{self.container.name}.{self.name}.html"
        else:
            return None


class Interface(GirNode, GirType):
    xml_tag = "interface"

    def __init__(self, ns: "Namespace", info: GIRepository.BaseInfo):
        super().__init__(ns, info)

    @cached_property
    def properties(self) -> T.Mapping[str, Property]:
        n_properties = interface_info_get_n_properties(self.info)
        result = {}
        for i in range(n_properties):
            property = Property(self, interface_info_get_property(self.info, i))
            result[property.name] = property
        return result

    @cached_property
    def signals(self) -> T.Mapping[str, Signal]:
        n_signals = interface_info_get_n_signals(self.info)
        result = {}
        for i in range(n_signals):
            signal = Signal(self, interface_info_get_signal(self.info, i))
            result[signal.name] = signal
        return result

    @cached_property
    def prerequisites(self) -> T.List["Interface"]:
        n_prerequisites = interface_info_get_n_prerequisites(self.info)
        result = []
        for i in range(n_prerequisites):
            entry = interface_info_get_prerequisite(self.info, i)
            result.append(self.get_containing(Repository)._resolve_entry(entry))
        return result

    def assignable_to(self, other: GirType) -> bool:
        if self == other:
            return True
        for pre in self.prerequisites:
            if pre.assignable_to(other):
                return True
        return False

    @cached_property
    def glib_type_name(self) -> str:
        return registered_type_info_get_type_name(self.info)

    @property
    def online_docs(self) -> T.Optional[str]:
        if ns := self.get_containing(Namespace).online_docs:
            return f"{ns}iface.{self.name}.html"
        else:
            return None


class Class(GirNode, GirType):
    xml_tag = "class"

    def __init__(self, ns: "Namespace", info: GIRepository.BaseInfo) -> None:
        super().__init__(ns, info)

    @property
    def abstract(self) -> bool:
        if gir3:
            assert self.info is not None
            return self.info.get_abstract()
        else:
            return GIRepository.object_info_get_abstract(self.info)

    @cached_property
    def implements(self) -> T.List[Interface]:
        n_interfaces = object_info_get_n_interfaces(self.info)
        result = []
        for i in range(n_interfaces):
            entry = object_info_get_interface(self.info, i)
            result.append(self.get_containing(Repository)._resolve_entry(entry))
        return result

    @cached_property
    def own_properties(self) -> T.Mapping[str, Property]:
        n_properties = object_info_get_n_properties(self.info)
        result = {}
        for i in range(n_properties):
            property = Property(self, object_info_get_property(self.info, i))
            result[property.name] = property
        return result

    @cached_property
    def own_signals(self) -> T.Mapping[str, Signal]:
        n_signals = object_info_get_n_signals(self.info)
        result = {}
        for i in range(n_signals):
            signal = Signal(self, object_info_get_signal(self.info, i))
            result[signal.name] = signal
        return result

    @cached_property
    def parent(self) -> T.Optional["Class"]:
        if entry := object_info_get_parent(self.info):
            return self.get_containing(Repository)._resolve_entry(entry)
        else:
            return None

    @cached_property
    def signature(self) -> str:
        assert self.container is not None
        result = f"class {self.container.name}.{self.name}"
        if self.parent is not None:
            assert self.parent.container is not None
            result += f" : {self.parent.container.name}.{self.parent.name}"
        if len(self.implements):
            result += " implements " + ", ".join(
                [impl.full_name for impl in self.implements]
            )
        return result

    @cached_property
    def properties(self) -> T.Mapping[str, Property]:
        return {p.name: p for p in self._enum_properties()}

    @cached_property
    def signals(self) -> T.Mapping[str, Signal]:
        return {s.name: s for s in self._enum_signals()}

    @cached_property
    def glib_type_name(self) -> str:
        return object_info_get_type_name(self.info)

    @cached_property
    def cname(self) -> str:
        return self.glib_type_name

    def assignable_to(self, other: GirType) -> bool:
        if self == other:
            return True
        elif self.parent and self.parent.assignable_to(other):
            return True
        else:
            for iface in self.implements:
                if iface.assignable_to(other):
                    return True

            return False

    def _enum_properties(self) -> T.Iterable[Property]:
        yield from self.own_properties.values()

        if self.parent is not None:
            yield from self.parent.properties.values()

        for impl in self.implements:
            yield from impl.properties.values()

    def _enum_signals(self) -> T.Iterable[Signal]:
        yield from self.own_signals.values()

        if self.parent is not None:
            yield from self.parent.signals.values()

        for impl in self.implements:
            yield from impl.signals.values()

    @property
    def online_docs(self) -> T.Optional[str]:
        if ns := self.get_containing(Namespace).online_docs:
            return f"{ns}class.{self.name}.html"
        else:
            return None


class TemplateType(GirType):
    def __init__(self, name: str, parent: T.Optional[GirType]):
        self._name = name
        self.parent = parent

    @property
    def name(self) -> str:
        return self._name

    @property
    def full_name(self) -> str:
        return self._name

    @property
    def glib_type_name(self) -> str:
        return self._name

    @cached_property
    def properties(self) -> T.Mapping[str, Property]:
        if not (isinstance(self.parent, Class) or isinstance(self.parent, Interface)):
            return {}
        else:
            return self.parent.properties

    @cached_property
    def signals(self) -> T.Mapping[str, Signal]:
        if not (isinstance(self.parent, Class) or isinstance(self.parent, Interface)):
            return {}
        else:
            return self.parent.signals

    def assignable_to(self, other: "GirType") -> bool:
        if self == other:
            return True
        elif isinstance(other, Interface):
            # we don't know the template type's interfaces, assume yes
            return True
        elif self.parent is None or isinstance(self.parent, ExternType):
            return isinstance(other, Class) or isinstance(other, ExternType)
        else:
            return self.parent.assignable_to(other)

    @cached_property
    def signature(self) -> str:
        if self.parent is None:
            return f"template {self.name}"
        else:
            return f"template {self.name} : {self.parent.full_name}"

    @property
    def incomplete(self) -> bool:
        return True


class EnumMember(GirNode):
    xml_tag = "member"

    def __init__(self, enum: "Enumeration", info: GIRepository.BaseInfo) -> None:
        super().__init__(enum, info)

    @property
    def value(self) -> int:
        return value_info_get_value(self.info)

    @cached_property
    def nick(self) -> str:
        return self.name.replace("_", "-")

    @property
    def c_ident(self) -> T.Optional[str]:
        if self.info is None:
            return None
        else:
            return self.info.get_attribute("c:identifier")

    @property
    def signature(self) -> str:
        return f"enum member {self.full_name} = {self.value}"


class Enumeration(GirNode, GirType):
    xml_tag = "enumeration"

    def __init__(self, ns: "Namespace", info: GIRepository.BaseInfo) -> None:
        super().__init__(ns, info)

    @cached_property
    def members(self) -> T.Dict[str, EnumMember]:
        members = {}
        get_n_values, get_value = (
            (GIRepository.EnumInfo.get_n_values, GIRepository.EnumInfo.get_value)
            if gir3
            else (GIRepository.enum_info_get_n_values, GIRepository.enum_info_get_value)
        )
        n_values = get_n_values(self.info)
        for i in range(n_values):
            member = EnumMember(self, get_value(self.info, i))
            members[member.name] = member
        return members

    @property
    def signature(self) -> str:
        return f"enum {self.full_name}"

    def assignable_to(self, type: GirType) -> bool:
        return type == self

    @property
    def online_docs(self) -> T.Optional[str]:
        if ns := self.get_containing(Namespace).online_docs:
            return f"{ns}enum.{self.name}.html"
        else:
            return None


class Boxed(GirNode, GirType):
    xml_tag = "glib:boxed"

    def __init__(self, ns: "Namespace", info: GIRepository.BaseInfo) -> None:
        super().__init__(ns, info)

    @property
    def signature(self) -> str:
        return f"boxed {self.full_name}"

    def assignable_to(self, type) -> bool:
        return type == self

    @property
    def online_docs(self) -> T.Optional[str]:
        if ns := self.get_containing(Namespace).online_docs:
            return f"{ns}boxed.{self.name}.html"
        else:
            return None


class Bitfield(Enumeration):
    xml_tag = "bitfield"

    def __init__(self, ns: "Namespace", info: GIRepository.BaseInfo) -> None:
        super().__init__(ns, info)


class Namespace(GirNode):
    def __init__(
        self, repo: "Repository", gir_repo: GIRepository.Repository, name: str
    ) -> None:
        super().__init__(repo, None)
        self.gir_repo = gir_repo
        self.name = name

    def _create_entry(self, entry: GIRepository.BaseInfo):
        if gir3:
            if isinstance(entry, GIRepository.FlagsInfo):
                return Bitfield(self, entry)
            elif isinstance(entry, GIRepository.EnumInfo):
                return Enumeration(self, entry)
            elif isinstance(entry, GIRepository.ObjectInfo):
                return Class(self, entry)
            elif isinstance(entry, GIRepository.InterfaceInfo):
                return Interface(self, entry)
            elif isinstance(entry, GIRepository.StructInfo):
                return Boxed(self, entry)
        else:
            entry_type = entry.get_type()

            if entry_type == GIRepository.InfoType.ENUM:
                return Enumeration(self, entry)
            elif entry_type == GIRepository.InfoType.FLAGS:
                return Bitfield(self, entry)
            elif entry_type == GIRepository.InfoType.OBJECT:
                return Class(self, entry)
            elif entry_type == GIRepository.InfoType.INTERFACE:
                return Interface(self, entry)
            elif (
                entry_type == GIRepository.InfoType.BOXED
                or entry_type == GIRepository.InfoType.STRUCT
            ):
                return Boxed(self, entry)

    @cached_property
    def entries(self) -> T.Mapping[str, GirType]:
        entries: dict[str, GirType] = {}

        n_entries = self.gir_repo.get_n_infos(self.name)
        for i in range(n_entries):
            entry = self.gir_repo.get_info(self.name, i)
            entry_name = entry.get_name()
            entries[entry_name] = self._create_entry(entry)

        return entries

    @cached_property
    def xml(self):
        return get_xml(self.name, self.version).get_elements("namespace")[0]

    @cached_property
    def name(self) -> str:
        return self.name

    @cached_property
    def version(self) -> str:
        return self.gir_repo.get_version(self.name)

    @property
    def signature(self) -> str:
        return f"namespace {self.name} {self.version}"

    @cached_property
    def classes(self) -> T.Mapping[str, Class]:
        return {
            name: entry
            for name, entry in self.entries.items()
            if isinstance(entry, Class)
        }

    def get_type(self, name) -> T.Optional[GirType]:
        """Gets a type (class, interface, enum, etc.) from this namespace."""
        return self.entries.get(name)

    def get_type_by_cname(self, cname: str) -> T.Optional[GirType]:
        """Gets a type from this namespace by its C name."""
        for basic in _BASIC_TYPES.values():
            if basic.glib_type_name == cname:
                return basic()

        for item in self.entries.values():
            if (
                hasattr(item, "cname")
                and item.cname is not None
                and item.cname == cname
            ):
                return item
        return None

    def lookup_type(self, type_name: str) -> T.Optional[GirType]:
        """Looks up a type in the scope of this namespace (including in the
        namespace's dependencies)."""

        ns, name = type_name.split(".", 1)
        return self.get_containing(Repository).get_type(name, ns)

    @property
    def online_docs(self) -> T.Optional[str]:
        return ONLINE_DOCS.get(f"{self.name}-{self.version}")


class Repository(GirNode):
    def __init__(self, gir_repo: GIRepository.Repository, ns: str) -> None:
        super().__init__(None, None)
        self.gir_repo = gir_repo

        self._namespace = Namespace(self, gir_repo, ns)

    def get_type(self, name: str, ns: str) -> T.Optional[GirType]:
        return self.lookup_namespace(ns).get_type(name)

    def lookup_namespace(self, ns: str):
        """Finds a namespace among this namespace's dependencies."""
        if ns == self._namespace.name:
            return self._namespace

        version = self.gir_repo.get_version(ns)
        return get_namespace(ns, version)

    def _resolve_entry(self, baseinfo: GIRepository.BaseInfo):
        return self.get_type(baseinfo.get_name(), baseinfo.get_namespace())

    def _resolve_type_info(self, typeinfo: GIRepository.BaseInfo) -> GirType:
        type_tag = type_info_get_tag(typeinfo)
        if type_tag == GIRepository.TypeTag.VOID:
            return VoidType()
        elif type_tag == GIRepository.TypeTag.BOOLEAN:
            return BoolType()
        elif type_tag in [GIRepository.TypeTag.FLOAT, GIRepository.TypeTag.DOUBLE]:
            return FloatType()
        elif type_tag in [
            GIRepository.TypeTag.INT8,
            GIRepository.TypeTag.INT16,
            GIRepository.TypeTag.INT32,
            GIRepository.TypeTag.INT64,
        ]:
            return IntType()
        elif type_tag in [
            GIRepository.TypeTag.UINT8,
            GIRepository.TypeTag.UINT16,
            GIRepository.TypeTag.UINT32,
            GIRepository.TypeTag.UINT64,
        ]:
            return UIntType()
        elif type_tag == GIRepository.TypeTag.UTF8:
            return StringType()
        elif type_tag == GIRepository.TypeTag.GTYPE:
            return TypeType()
        elif type_tag == GIRepository.TypeTag.INTERFACE:
            return self._resolve_entry(type_info_get_interface(typeinfo))
        elif type_tag == GIRepository.TypeTag.ARRAY:
            item_type = type_info_get_param_type(typeinfo, 0)
            return ArrayType(self._resolve_type_info(item_type))
        else:
            raise CompilerBugError("Unknown type tag", type_tag)


class GirContext:
    def __init__(self):
        self.namespaces = {}
        self.not_found_namespaces: T.Set[str] = set()

    def add_namespace(self, namespace: Namespace):
        other = self.namespaces.get(namespace.name)
        if other is not None and other.version != namespace.version:
            raise CompileError(
                f"Namespace {namespace.name}-{namespace.version} can't be imported because version {other.version} was imported earlier"
            )

        self.namespaces[namespace.name] = namespace

    def get_type_by_cname(self, name: str) -> T.Optional[GirType]:
        for ns in self.namespaces.values():
            if type := ns.get_type_by_cname(name):
                return type
        return None

    def get_type(self, name: str, ns: str) -> T.Optional[GirType]:
        if ns is None and name in _BASIC_TYPES:
            return _BASIC_TYPES[name]()

        ns = ns or "Gtk"

        if ns not in self.namespaces:
            return None

        return self.namespaces[ns].get_type(name)

    def get_class(self, ns: str, name: str) -> T.Optional[Class]:
        type = self.get_type(ns, name)
        if isinstance(type, Class):
            return type
        else:
            return None

    def validate_ns(self, ns: str) -> None:
        """Raises an exception if there is a problem looking up the given
        namespace."""

        ns = ns or "Gtk"

        if ns not in self.namespaces and ns not in self.not_found_namespaces:
            all_available = list(set(ns for ns, _version in get_available_namespaces()))

            raise CompileError(
                f"Namespace {ns} was not imported",
                did_you_mean=(ns, all_available),
            )

    def validate_type(self, name: str, ns: str) -> None:
        """Raises an exception if there is a problem looking up the given type."""

        self.validate_ns(ns)

        type = self.get_type(name, ns)

        ns = ns or "Gtk"

        if type is None:
            raise CompileError(
                f"Namespace {ns} does not contain a type called {name}",
                did_you_mean=(name, self.namespaces[ns].classes.keys()),
            )
