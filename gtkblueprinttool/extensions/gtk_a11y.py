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

from ..ast import BaseTypedAttribute, Value
from ..ast_utils import AstNode, validate, docs
from ..completions_utils import *
from ..gir import StringType, BoolType, IntType, FloatType, GirType
from ..lsp_utils import Completion, CompletionItemKind
from ..parse_tree import *
from ..parser_utils import *
from ..xml_emitter import XmlEmitter


def _get_property_types(gir):
    # from <https://docs.gtk.org/gtk4/enum.AccessibleProperty.html>
    return {
        "autocomplete": gir.get_type("AccessibleAutocomplete", "Gtk"),
        "description": StringType(),
        "has_popup": BoolType(),
        "key_shortcuts": StringType(),
        "label": StringType(),
        "level": IntType(),
        "modal": BoolType(),
        "multi_line": BoolType(),
        "multi_selectable": BoolType(),
        "orientation": gir.get_type("Orientation", "Gtk"),
        "placeholder": StringType(),
        "read_only": BoolType(),
        "required": BoolType(),
        "role_description": StringType(),
        "sort": gir.get_type("AccessibleSort", "Gtk"),
        "value_max": FloatType(),
        "value_min": FloatType(),
        "value_now": FloatType(),
        "value_text": StringType(),
    }


def _get_relation_types(gir):
    # from <https://docs.gtk.org/gtk4/enum.AccessibleRelation.html>
    widget = gir.get_type("Widget", "Gtk")
    return {
        "active_descendant": widget,
        "col_count": IntType(),
        "col_index": IntType(),
        "col_index_text": StringType(),
        "col_span": IntType(),
        "controls": widget,
        "described_by": widget,
        "details": widget,
        "error_message": widget,
        "flow_to": widget,
        "labelled_by": widget,
        "owns": widget,
        "pos_in_set": IntType(),
        "row_count": IntType(),
        "row_index": IntType(),
        "row_index_text": StringType(),
        "row_span": IntType(),
        "set_size": IntType(),
    }


def _get_state_types(gir):
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
    }

def _get_types(gir):
    return {
        **_get_property_types(gir),
        **_get_relation_types(gir),
        **_get_state_types(gir),
    }

def _get_docs(gir, name):
    return (
        gir.get_type("AccessibleProperty", "Gtk").members.get(name)
        or gir.get_type("AccessibleRelation", "Gtk").members.get(name)
        or gir.get_type("AccessibleState", "Gtk").members.get(name)
    ).doc


class A11y(AstNode):
    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("accessibility")
        for child in self.children:
            child.emit_xml(xml)
        xml.end_tag()


class A11yProperty(BaseTypedAttribute):
    @property
    def tag_name(self):
        name = self.tokens["name"]
        gir = self.root.gir
        if name in _get_property_types(gir):
            return "property"
        elif name in _get_relation_types(gir):
            return "relation"
        elif name in _get_state_types(gir):
            return "state"
        else:
            raise CompilerBugError()

    @property
    def value_type(self) -> GirType:
        return _get_types(self.root.gir).get(self.tokens["name"])

    @validate("name")
    def is_valid_property(self):
        types = _get_types(self.root.gir)
        if self.tokens["name"] not in types:
            raise CompileError(
                f"'{self.tokens['name']}' is not an accessibility property, relation, or state",
                did_you_mean=(self.tokens["name"], types.keys()),
            )

    @docs("name")
    def prop_docs(self):
        if self.tokens["name"] in _get_types(self.root.gir):
            return _get_docs(self.root.gir, self.tokens["name"])


a11y_prop = Group(
    A11yProperty,
    Statement(
        UseIdent("name"),
        Op(":"),
        value.expected("a value"),
    )
)

a11y = Group(
    A11y,
    Sequence(
        Keyword("accessibility"),
        OpenBlock().expected("`{`"),
        Until(a11y_prop, CloseBlock()),
    )
)


@completer(
    applies_in=[ast.ObjectContent],
    matches=new_statement_patterns,
)
def a11y_completer(ast_node, match_variables):
    yield Completion(
        "accessibility", CompletionItemKind.Snippet,
        snippet="accessibility {\n  $0\n}"
    )


@completer(
    applies_in=[A11y],
    matches=new_statement_patterns,
)
def a11y_name_completer(ast_node, match_variables):
    for name, type in _get_types(ast_node.root.gir).items():
        yield Completion(name, CompletionItemKind.Property, docs=_get_docs(ast_node.root.gir, type))
