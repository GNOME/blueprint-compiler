# gtk_a11y.py
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

from .common import *
from .contexts import ValueTypeCtx
from .gobject_object import ObjectContent, validate_parent_type
from .values import Value


def get_property_types(gir):
    # from <https://docs.gtk.org/gtk4/enum.AccessibleProperty.html>
    return {
        "autocomplete": gir.get_type("AccessibleAutocomplete", "Gtk"),
        "description": StringType(),
        "has-popup": BoolType(),
        "help-text": StringType(),
        "key-shortcuts": StringType(),
        "label": StringType(),
        "level": IntType(),
        "modal": BoolType(),
        "multi-line": BoolType(),
        "multi-selectable": BoolType(),
        "orientation": gir.get_type("Orientation", "Gtk"),
        "placeholder": StringType(),
        "read-only": BoolType(),
        "required": BoolType(),
        "role-description": StringType(),
        "sort": gir.get_type("AccessibleSort", "Gtk"),
        "value-max": FloatType(),
        "value-min": FloatType(),
        "value-now": FloatType(),
        "value-text": StringType(),
    }


def get_relation_types(gir):
    # from <https://docs.gtk.org/gtk4/enum.AccessibleRelation.html>
    widget = gir.get_type("Widget", "Gtk")
    return {
        "active-descendant": widget,
        "col-count": IntType(),
        "col-index": IntType(),
        "col-index-text": StringType(),
        "col-span": IntType(),
        "controls": widget,
        "described-by": widget,
        "details": widget,
        "error-message": widget,
        "flow-to": widget,
        "labelled-by": widget,
        "owns": widget,
        "pos-in-set": IntType(),
        "row-count": IntType(),
        "row-index": IntType(),
        "row-index-text": StringType(),
        "row-span": IntType(),
        "set-size": IntType(),
    }


def get_state_types(gir):
    # from <https://docs.gtk.org/gtk4/enum.AccessibleState.html>
    return {
        "busy": BoolType(),
        "checked": gir.get_type("AccessibleTristate", "Gtk"),
        "disabled": BoolType(),
        "expanded": BoolType(),
        "hidden": BoolType(),
        "invalid": gir.get_type("AccessibleInvalidState", "Gtk"),
        "pressed": gir.get_type("AccessibleTristate", "Gtk"),
        "selected": BoolType(),
        "visited": BoolType(),
    }


def get_types(gir):
    return {
        **get_property_types(gir),
        **get_relation_types(gir),
        **get_state_types(gir),
    }


allow_duplicates = [
    "controls",
    "described-by",
    "details",
    "flow-to",
    "labelled-by",
    "owns",
]


def _get_docs(gir, name):
    name = name.replace("-", "_")
    if gir_type := (
        gir.get_type("AccessibleProperty", "Gtk").members.get(name)
        or gir.get_type("AccessibleRelation", "Gtk").members.get(name)
        or gir.get_type("AccessibleState", "Gtk").members.get(name)
    ):
        return gir_type.doc


class A11yProperty(AstNode):
    grammar = Statement(
        UseIdent("name"),
        ":",
        AnyOf(Value, ["[", UseLiteral("list_form", True), Delimited(Value, ","), "]"]),
    )

    @property
    def tag_name(self):
        name = self.tokens["name"]
        gir = self.root.gir
        if name in get_property_types(gir):
            return "property"
        elif name in get_relation_types(gir):
            return "relation"
        elif name in get_state_types(gir):
            return "state"
        else:
            raise CompilerBugError()

    @property
    def name(self):
        return self.tokens["name"].replace("_", "-")

    @property
    def values(self) -> T.List[Value]:
        return list(self.children)

    @context(ValueTypeCtx)
    def value_type(self) -> ValueTypeCtx:
        return ValueTypeCtx(get_types(self.root.gir).get(self.tokens["name"]))

    @property
    def document_symbol(self) -> DocumentSymbol:
        return DocumentSymbol(
            self.name,
            SymbolKind.Field,
            self.range,
            self.group.tokens["name"].range,
            ", ".join(v.range.text for v in self.values),
        )

    @validate("name")
    def is_valid_property(self):
        types = get_types(self.root.gir)
        if self.tokens["name"] not in types:
            raise CompileError(
                f"'{self.tokens['name']}' is not an accessibility property, relation, or state",
                did_you_mean=(self.tokens["name"], types.keys()),
            )

    @validate("name")
    def unique_in_parent(self):
        self.validate_unique_in_parent(
            f"Duplicate accessibility attribute '{self.tokens['name']}'",
            check=lambda child: child.tokens["name"] == self.tokens["name"],
        )

    @validate("name")
    def list_only_allowed_for_subset(self):
        if self.tokens["list_form"] and self.tokens["name"] not in allow_duplicates:
            raise CompileError(
                f"'{self.tokens['name']}' does not allow a list of values",
            )

    @validate("name")
    def list_non_empty(self):
        if len(self.values) == 0:
            raise CompileError(
                f"'{self.tokens['name']}' may not be empty",
            )

    @docs("name")
    def prop_docs(self):
        if self.tokens["name"] in get_types(self.root.gir):
            return _get_docs(self.root.gir, self.tokens["name"])


class ExtAccessibility(AstNode):
    grammar = [
        Keyword("accessibility"),
        "{",
        Until(A11yProperty, "}"),
    ]

    @property
    def properties(self) -> T.List[A11yProperty]:
        return self.children[A11yProperty]

    @property
    def document_symbol(self) -> DocumentSymbol:
        return DocumentSymbol(
            "accessibility",
            SymbolKind.Struct,
            self.range,
            self.group.tokens["accessibility"].range,
        )

    @validate("accessibility")
    def container_is_widget(self):
        validate_parent_type(self, "Gtk", "Widget", "accessibility properties")

    @validate("accessibility")
    def unique_in_parent(self):
        self.validate_unique_in_parent("Duplicate accessibility block")

    @docs("accessibility")
    def ref_docs(self):
        return get_docs_section("Syntax ExtAccessibility")


@completer(
    applies_in=[ObjectContent],
    matches=new_statement_patterns,
)
def a11y_completer(lsp, ast_node, match_variables):
    yield Completion(
        "accessibility", CompletionItemKind.Snippet, snippet="accessibility {\n  $0\n}"
    )


@completer(
    applies_in=[ExtAccessibility],
    matches=new_statement_patterns,
)
def a11y_name_completer(lsp, ast_node, match_variables):
    for name, type in get_types(ast_node.root.gir).items():
        yield Completion(
            name,
            CompletionItemKind.Property,
            docs=_get_docs(ast_node.root.gir, type.name),
        )


@decompiler("accessibility", skip_children=True, element=True)
def decompile_accessibility(ctx: DecompileCtx, _gir, element):
    ctx.print("accessibility {")
    already_printed = set()
    types = get_types(ctx.gir)

    for child in element.children:
        name = child["name"]

        if name in allow_duplicates:
            if name in already_printed:
                continue

            ctx.print(f"{name}: [")
            for value in element.children:
                if value["name"] == name:
                    comments, string = ctx.decompile_value(
                        value.cdata,
                        types.get(value["name"]),
                        (value["translatable"], value["context"], value["comments"]),
                    )
                    ctx.print(f"{comments} {string},")
            ctx.print("];")
        else:
            comments, string = ctx.decompile_value(
                child.cdata,
                types.get(child["name"]),
                (child["translatable"], child["context"], child["comments"]),
            )
            ctx.print(f"{comments} {name}: {string};")

        already_printed.add(name)
    ctx.print("}")
    ctx.end_block_with("")
