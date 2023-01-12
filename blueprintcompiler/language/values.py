# values.py
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

import typing as T

from .common import *
from .types import TypeName
from .property_binding import PropertyBinding
from .binding import Binding
from .gobject_object import Object
from .contexts import ValueTypeCtx


class TranslatedWithoutContext(AstNode):
    grammar = ["_", "(", UseQuoted("string"), Optional(","), ")"]

    @property
    def string(self) -> str:
        return self.tokens["string"]


class TranslatedWithContext(AstNode):
    grammar = [
        "C_",
        "(",
        UseQuoted("context"),
        ",",
        UseQuoted("string"),
        Optional(","),
        ")",
    ]

    @property
    def string(self) -> str:
        return self.tokens["string"]

    @property
    def context(self) -> str:
        return self.tokens["context"]


class Translated(AstNode):
    grammar = AnyOf(TranslatedWithoutContext, TranslatedWithContext)

    @property
    def child(self) -> T.Union[TranslatedWithContext, TranslatedWithoutContext]:
        return self.children[0]

    @validate()
    def validate_for_type(self) -> None:
        expected_type = self.context[ValueTypeCtx].value_type
        if expected_type is not None and not expected_type.assignable_to(StringType()):
            raise CompileError(
                f"Cannot convert translated string to {expected_type.full_name}"
            )


class TypeLiteral(AstNode):
    grammar = [
        "typeof",
        "(",
        to_parse_node(TypeName).expected("type name"),
        Match(")").expected(),
    ]

    @property
    def type_name(self) -> TypeName:
        return self.children[TypeName][0]

    @validate()
    def validate_for_type(self) -> None:
        expected_type = self.context[ValueTypeCtx].value_type
        if expected_type is not None and not isinstance(expected_type, gir.TypeType):
            raise CompileError(f"Cannot convert GType to {expected_type.full_name}")


class QuotedLiteral(AstNode):
    grammar = UseQuoted("value")

    @property
    def value(self) -> str:
        return self.tokens["value"]

    @validate()
    def validate_for_type(self) -> None:
        expected_type = self.context[ValueTypeCtx].value_type
        if (
            isinstance(expected_type, gir.IntType)
            or isinstance(expected_type, gir.UIntType)
            or isinstance(expected_type, gir.FloatType)
        ):
            raise CompileError(f"Cannot convert string to number")

        elif isinstance(expected_type, gir.StringType):
            pass

        elif (
            isinstance(expected_type, gir.Class)
            or isinstance(expected_type, gir.Interface)
            or isinstance(expected_type, gir.Boxed)
        ):
            parseable_types = [
                "Gdk.Paintable",
                "Gdk.Texture",
                "Gdk.Pixbuf",
                "GLib.File",
                "Gtk.ShortcutTrigger",
                "Gtk.ShortcutAction",
                "Gdk.RGBA",
                "Gdk.ContentFormats",
                "Gsk.Transform",
                "GLib.Variant",
            ]
            if expected_type.full_name not in parseable_types:
                hints = []
                if isinstance(expected_type, gir.TypeType):
                    hints.append(f"use the typeof operator: 'typeof({self.value})'")
                raise CompileError(
                    f"Cannot convert string to {expected_type.full_name}", hints=hints
                )

        elif expected_type is not None:
            raise CompileError(f"Cannot convert string to {expected_type.full_name}")


class NumberLiteral(AstNode):
    grammar = [
        Optional(AnyOf(UseExact("sign", "-"), UseExact("sign", "+"))),
        UseNumber("value"),
    ]

    @property
    def value(self) -> T.Union[int, float]:
        return self.tokens["value"]

    @validate()
    def validate_for_type(self) -> None:
        expected_type = self.context[ValueTypeCtx].value_type
        if isinstance(expected_type, gir.IntType):
            try:
                int(self.tokens["value"])
            except:
                raise CompileError(
                    f"Cannot convert {self.group.tokens['value']} to integer"
                )

        elif isinstance(expected_type, gir.UIntType):
            try:
                int(self.tokens["value"])
                if int(self.tokens["value"]) < 0:
                    raise Exception()
            except:
                raise CompileError(
                    f"Cannot convert {self.group.tokens['value']} to unsigned integer"
                )

        elif isinstance(expected_type, gir.FloatType):
            try:
                float(self.tokens["value"])
            except:
                raise CompileError(
                    f"Cannot convert {self.group.tokens['value']} to float"
                )

        elif expected_type is not None:
            raise CompileError(f"Cannot convert number to {expected_type.full_name}")


class Flag(AstNode):
    grammar = UseIdent("value")

    @property
    def name(self) -> str:
        return self.tokens["value"]

    @property
    def value(self) -> T.Optional[int]:
        type = self.context[ValueTypeCtx].value_type
        if not isinstance(type, Enumeration):
            return None
        elif member := type.members.get(self.name):
            return member.value
        else:
            return None

    @docs()
    def docs(self):
        type = self.context[ValueTypeCtx].value_type
        if not isinstance(type, Enumeration):
            return
        if member := type.members.get(self.tokens["value"]):
            return member.doc

    @validate()
    def validate_for_type(self):
        expected_type = self.context[ValueTypeCtx].value_type
        if (
            isinstance(expected_type, gir.Bitfield)
            and self.tokens["value"] not in expected_type.members
        ):
            raise CompileError(
                f"{self.tokens['value']} is not a member of {expected_type.full_name}",
                did_you_mean=(self.tokens["value"], expected_type.members.keys()),
            )


class Flags(AstNode):
    grammar = [Flag, "|", Delimited(Flag, "|")]

    @property
    def flags(self) -> T.List[Flag]:
        return self.children

    @validate()
    def validate_for_type(self) -> None:
        expected_type = self.context[ValueTypeCtx].value_type
        if expected_type is not None and not isinstance(expected_type, gir.Bitfield):
            raise CompileError(f"{expected_type.full_name} is not a bitfield type")


class IdentLiteral(AstNode):
    grammar = UseIdent("value")

    @property
    def ident(self) -> str:
        return self.tokens["value"]

    @validate()
    def validate_for_type(self) -> None:
        expected_type = self.context[ValueTypeCtx].value_type
        if isinstance(expected_type, gir.BoolType):
            if self.ident not in ["true", "false"]:
                raise CompileError(f"Expected 'true' or 'false' for boolean value")

        elif isinstance(expected_type, gir.Enumeration):
            if self.ident not in expected_type.members:
                raise CompileError(
                    f"{self.ident} is not a member of {expected_type.full_name}",
                    did_you_mean=(self.ident, list(expected_type.members.keys())),
                )

        elif expected_type is not None:
            object = self.root.objects_by_id.get(self.ident)
            if object is None:
                raise CompileError(
                    f"Could not find object with ID {self.ident}",
                    did_you_mean=(self.ident, self.root.objects_by_id.keys()),
                )
            elif object.gir_class and not object.gir_class.assignable_to(expected_type):
                raise CompileError(
                    f"Cannot assign {object.gir_class.full_name} to {expected_type.full_name}"
                )

    @docs()
    def docs(self) -> T.Optional[str]:
        type = self.context[ValueTypeCtx].value_type
        if isinstance(type, gir.Enumeration):
            if member := type.members.get(self.ident):
                return member.doc
            else:
                return type.doc
        elif isinstance(type, gir.GirNode):
            return type.doc
        else:
            return None

    def get_semantic_tokens(self) -> T.Iterator[SemanticToken]:
        if isinstance(self.parent.value_type, gir.Enumeration):
            token = self.group.tokens["value"]
            yield SemanticToken(token.start, token.end, SemanticTokenType.EnumMember)


class Literal(AstNode):
    grammar = AnyOf(
        TypeLiteral,
        QuotedLiteral,
        NumberLiteral,
        IdentLiteral,
    )

    @property
    def value(
        self,
    ) -> T.Union[TypeLiteral, QuotedLiteral, NumberLiteral, IdentLiteral]:
        return self.children[0]


class ObjectValue(AstNode):
    grammar = Object

    @property
    def object(self) -> Object:
        return self.children[Object][0]

    @validate()
    def validate_for_type(self) -> None:
        expected_type = self.context[ValueTypeCtx].value_type
        if (
            expected_type is not None
            and self.object.gir_class is not None
            and not self.object.gir_class.assignable_to(expected_type)
        ):
            raise CompileError(
                f"Cannot assign {self.object.gir_class.full_name} to {expected_type.full_name}"
            )


class Value(AstNode):
    grammar = AnyOf(PropertyBinding, Binding, Translated, ObjectValue, Flags, Literal)

    @property
    def child(
        self,
    ) -> T.Union[PropertyBinding, Binding, Translated, ObjectValue, Flags, Literal,]:
        return self.children[0]
