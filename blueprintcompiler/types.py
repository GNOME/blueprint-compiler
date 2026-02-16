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


BASIC_TYPES = {
    "bool": BoolType,
    "string": StringType,
    "int": IntType,
    "uint": UIntType,
    "float": FloatType,
    "double": FloatType,
    "type": TypeType,
}
