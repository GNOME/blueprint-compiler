# types.py
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

    def castable_to(self, other: "GirType") -> bool:
        return self.assignable_to(other)

    def parent_types(self) -> T.Iterable["GirType"]:
        return []

    @staticmethod
    def common_ancestor(types: T.List["GirType"]) -> T.Optional["GirType"]:
        """Returns the most specific type that both this and the other type can be assigned to, or None if there is no such type."""

        if len(types) == 0:
            return None

        def pairwise(a: GirType, b: GirType) -> T.Optional[GirType]:
            for ancestor_a in [a] + list(a.parent_types()):
                for ancestor_b in [b] + list(b.parent_types()):
                    if ancestor_a.assignable_to(ancestor_b):
                        return ancestor_b
                    elif ancestor_b.assignable_to(ancestor_a):
                        return ancestor_a
            return None

        common = types[0]
        for t in types[1:]:
            if c := pairwise(common, t):
                common = c
            else:
                return None

        return common

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


class ObjectType(GirType):
    def castable_to(self, other: GirType) -> bool:
        return self.assignable_to(other) or other.assignable_to(self)


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

    def transformable_to(self, other: GirType):
        raise NotImplementedError()

    def castable_to(self, other: GirType):
        return self.transformable_to(other)


class VoidType(GirType):
    name: str = "void"
    glib_type_name: str = "void"

    def transformable_to(self, other: GirType):
        return False

    def assignable_to(self, other: GirType):
        return False


class CharacterType(BasicType):
    def transformable_to(self, other: GirType) -> bool:
        from .gir import Enumeration

        return (
            isinstance(other, CharType)
            or isinstance(other, UCharType)
            or isinstance(other, BoolType)
            or isinstance(other, NumericType)
            or isinstance(other, Enumeration)
            or isinstance(other, StringType)
        )


class CharType(CharacterType):
    name = "char"
    glib_type_name: str = "gchar"

    def assignable_to(self, other: GirType) -> bool:
        return isinstance(other, CharType)


class UCharType(CharacterType):
    name = "uchar"
    glib_type_name: str = "guchar"

    def assignable_to(self, other: GirType) -> bool:
        return isinstance(other, UCharType) or isinstance(other, CharType)


class BoolType(BasicType):
    name = "bool"
    glib_type_name: str = "gboolean"

    def assignable_to(self, other: GirType) -> bool:
        return isinstance(other, BoolType)

    def transformable_to(self, other: GirType) -> bool:
        from .gir import Enumeration

        return (
            isinstance(other, CharType)
            or isinstance(other, UCharType)
            or isinstance(other, BoolType)
            or isinstance(other, IntegerType)
            or isinstance(other, Enumeration)
            or isinstance(other, StringType)
        )


class NumericType(BasicType):
    signed: bool
    size: int
    floating: bool

    def assignable_to(self, other: GirType) -> bool:
        if not isinstance(other, NumericType):
            return False

        return not (
            (self.signed and not other.signed)
            or (self.size > other.size)
            or (self.floating and not other.floating)
        )


class IntegerType(NumericType):
    floating = False

    @property
    def min_value(self):
        return 0 if not self.signed else -(2 ** (self.size - 1))

    @property
    def max_value(self):
        return (2**self.size - 1) if not self.signed else (2 ** (self.size - 1) - 1)

    def transformable_to(self, other: GirType) -> bool:
        from .gir import Enumeration

        return (
            isinstance(other, CharType)
            or isinstance(other, UCharType)
            or isinstance(other, BoolType)
            or isinstance(other, NumericType)
            or isinstance(other, Enumeration)
            or isinstance(other, StringType)
        )


class Int8Type(IntegerType):
    name = "int8"
    glib_type_name: str = "gint8"
    signed = True
    size = 8


class UInt8Type(IntegerType):
    name = "uint8"
    glib_type_name: str = "guint8"
    signed = False
    size = 8


class Int16Type(IntegerType):
    name = "int16"
    glib_type_name: str = "gint16"
    signed = True
    size = 16


class UInt16Type(IntegerType):
    name = "uint16"
    glib_type_name: str = "guint16"
    signed = False
    size = 16


class Int32Type(IntegerType):
    name = "int32"
    glib_type_name: str = "gint32"
    signed = True
    size = 32


class UInt32Type(IntegerType):
    name = "uint32"
    glib_type_name: str = "guint32"
    signed = False
    size = 32


class Int64Type(IntegerType):
    name = "int64"
    glib_type_name: str = "gint64"
    signed = True
    size = 64


class UInt64Type(IntegerType):
    name = "uint64"
    glib_type_name: str = "guint64"
    signed = False
    size = 64


class IntType(IntegerType):
    name = "int"
    glib_type_name: str = "gint"
    signed = True
    size = 32


class UIntType(IntegerType):
    name = "uint"
    glib_type_name: str = "guint"
    signed = False
    size = 32


class LongType(IntegerType):
    name = "long"
    glib_type_name: str = "glong"
    signed = True
    size = 64  # on most platforms


class ULongType(IntegerType):
    name = "ulong"
    glib_type_name: str = "gulong"
    signed = False
    size = 64


class FloatingPointType(NumericType):
    floating = True
    signed = True

    def transformable_to(self, other: GirType) -> bool:
        return (
            isinstance(other, CharType)
            or isinstance(other, UCharType)
            or isinstance(other, NumericType)
            or isinstance(other, StringType)
        )


class FloatType(FloatingPointType):
    name = "float"
    glib_type_name: str = "gfloat"
    size = 32


class DoubleType(FloatingPointType):
    name = "double"
    glib_type_name: str = "gdouble"
    size = 64


class StringType(BasicType):
    name = "string"
    glib_type_name: str = "gchararray"

    def assignable_to(self, other: GirType) -> bool:
        return isinstance(other, StringType)

    def transformable_to(self, other: GirType) -> bool:
        return isinstance(other, StringType)


class TypeType(BasicType):
    name = "GType"
    glib_type_name: str = "GType"

    def assignable_to(self, other: GirType) -> bool:
        return isinstance(other, TypeType)


BASIC_TYPES = {
    "bool": BoolType,
    "char": CharType,
    "double": FloatType,
    "float": FloatType,
    "int": IntType,
    "int16": Int16Type,
    "int32": Int32Type,
    "int64": Int64Type,
    "int8": Int8Type,
    "long": LongType,
    "string": StringType,
    "type": TypeType,
    "uchar": UCharType,
    "uint": UIntType,
    "uint16": UInt16Type,
    "uint32": UInt32Type,
    "uint64": UInt64Type,
    "uint8": UInt8Type,
    "ulong": ULongType,
}
