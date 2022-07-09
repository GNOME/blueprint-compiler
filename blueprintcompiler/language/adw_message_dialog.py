# adw_message_dialog.py
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


from .gobject_object import ObjectContent, validate_parent_type
from .attributes import BaseAttribute
from .common import *


class AppearanceClass(AstNode):
    grammar = AnyOf(Keyword("destructive"), Keyword("suggested"))

    @property
    def name(self):
        if self.tokens["destructive"]:
            return "destructive"
        else:
            return "suggested"

    @validate()
    def unique_in_parent(self):
        self.validate_unique_in_parent("Only one of 'destructive' or 'suggested' is allowed")


class Response(BaseAttribute):
    tag_name = "response"
    attr_name = "id"

    value_type = gir.StringType()

    grammar = [
        UseIdent("name"),
        ":",
        VALUE_HOOKS,
        ZeroOrMore(AnyOf(
            Keyword("disabled"),
            AppearanceClass,
        )),
    ]

    @validate("name")
    def unique_in_parent(self):
        self.validate_unique_in_parent(
            f"Duplicate response ID '{self.tokens['name']}'",
            lambda other: other.tokens["name"] == self.tokens["name"],
        )

    def extra_attributes(self):
        attrs = {}

        if len(self.children[AppearanceClass]) == 1:
            attrs["appearance"] = self.children[AppearanceClass][0].name

        if self.tokens["disabled"]:
            attrs["enabled"] = "false"

        return attrs

    def emit_xml(self, xml):
        xml.put_self_closing("response", name=self.tokens["name"])


class Responses(AstNode):
    grammar = [
        Keyword("responses"),
        "{",
        Delimited(Response, ","),
        "}",
    ]

    @validate("responses")
    def container_is_adw_message_dialog(self):
        validate_parent_type(self, "Adw", "MessageDialog", "responses")

    @validate("responses")
    def unique_in_parent(self):
        self.validate_unique_in_parent("Duplicate responses block")

    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("responses")
        for child in self.children:
            child.emit_xml(xml)
        xml.end_tag()

@completer(
    applies_in=[ObjectContent],
    applies_in_subclass=("Gtk", "Widget"),
    matches=new_statement_patterns,
)
def style_completer(ast_node, match_variables):
    yield Completion("styles", CompletionItemKind.Keyword, snippet="styles [\"$0\"]")

