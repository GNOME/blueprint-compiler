# gtk_combo_box_text.py
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


from ..ast import BaseTypedAttribute, Value, TranslatedStringValue
from ..ast_utils import AstNode, validate
from ..completions_utils import *
from ..gir import StringType
from ..lsp_utils import Completion, CompletionItemKind
from ..parse_tree import *
from ..parser_utils import *
from ..xml_emitter import XmlEmitter


class Item(AstNode):
    grammar = value

    @property
    def value_type(self):
        return StringType()

    def emit_xml(self, xml: XmlEmitter):
        value = self.children[Value][0]
        attrs = value.attrs if isinstance(value, TranslatedStringValue) else {}
        xml.start_tag("item", **attrs)
        value.emit_xml(xml)
        xml.end_tag()


class Strings(AstNode):
    grammar = [
        Keyword("strings"),
        "[",
        Delimited(Item, ","),
        "]",
    ]

    @validate("items")
    def container_is_string_list(self):
        self.validate_parent_type("Gtk", "StringList", "StringList items")


    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("items")
        for child in self.children:
            child.emit_xml(xml)
        xml.end_tag()


@completer(
    applies_in=[ast.ObjectContent],
    applies_in_subclass=("Gtk", "StringList"),
    matches=new_statement_patterns,
)
def strings_completer(ast_node, match_variables):
    yield Completion(
        "strings", CompletionItemKind.Snippet,
        snippet="strings [$0]"
    )
