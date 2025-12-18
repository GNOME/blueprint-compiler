# gtk_level_bar.py
#
# Copyright 2025 Matthijs Velsink <mvelsink@gnome.org>
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

from .common import *
from .gobject_object import ObjectContent, validate_parent_type
from .values import StringValue


class ExtLevelBarOffset(AstNode):
    grammar = [
        Keyword("offset"),
        Match("(").expected(),
        [
            Optional(AnyOf(UseExact("sign", "-"), UseExact("sign", "+"))),
            UseNumber("value"),
            ",",
            UseQuoted("name"),
        ],
        Match(")").expected(),
    ]

    @property
    def value(self) -> float:
        return self.tokens["value"]

    @property
    def name(self) -> str:
        return self.tokens["name"]

    @property
    def document_symbol(self) -> DocumentSymbol:
        return DocumentSymbol(
            str(self.value),
            SymbolKind.Field,
            self.range,
            self.group.tokens["offset"].range,
            self.name,
        )

    @validate("value")
    def validate_value(self):
        if self.tokens["sign"] == "-":
            raise CompileError(
                "Offset value can't be negative",
                Range.join(self.ranges["sign"], self.ranges["value"]),
            )

    @docs("offset")
    def ref_docs(self):
        return get_docs_section("Syntax ExtLevelBarOffsets")


class ExtLevelBarOffsets(AstNode):
    grammar = [
        Keyword("offsets"),
        Match("[").expected(),
        Until(ExtLevelBarOffset, "]", ","),
    ]

    @property
    def offsets(self) -> T.List[ExtLevelBarOffset]:
        return self.children

    @property
    def document_symbol(self) -> DocumentSymbol:
        return DocumentSymbol(
            "offsets",
            SymbolKind.Array,
            self.range,
            self.group.tokens["offsets"].range,
        )

    @validate("offsets")
    def container_is_level_bar(self):
        validate_parent_type(self, "Gtk", "LevelBar", "level bar offsets")

    @validate("offsets")
    def unique_in_parent(self):
        self.validate_unique_in_parent("Duplicate 'offsets' block")

    @docs("offsets")
    def ref_docs(self):
        return get_docs_section("Syntax ExtLevelBarOffsets")


@completer(
    applies_in=[ObjectContent],
    applies_in_subclass=("Gtk", "LevelBar"),
    matches=new_statement_patterns,
)
def complete_offsets(_ctx: CompletionContext):
    yield Completion(
        "offsets",
        CompletionItemKind.Keyword,
        snippet="offsets [\n\t$0\n]",
        sort_text=get_sort_key(CompletionPriority.OBJECT_MEMBER, "offsets"),
    )


@completer(
    applies_in=[ExtLevelBarOffsets],
)
def complete_offset(_ctx: CompletionContext):
    yield Completion(
        "offset",
        CompletionItemKind.Snippet,
        snippet='offset (${1:value}, "${2:name}"),',
    )


@decompiler("offsets")
def decompile_offsets(ctx, gir):
    ctx.print("offsets [")


@decompiler("offset")
def decompile_offset(ctx: DecompileCtx, gir, value, name):
    ctx.print(f'offset ({value}, "{name}"),')
