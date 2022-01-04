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


from ..ast import BaseTypedAttribute
from ..ast_utils import AstNode, validate
from ..completions_utils import *
from ..gir import StringType
from ..lsp_utils import Completion, CompletionItemKind
from ..parse_tree import *
from ..parser_utils import *
from ..xml_emitter import XmlEmitter


class Items(AstNode):
    @validate("items")
    def container_is_combo_box_text(self):
        self.validate_parent_type("Gtk", "ComboBoxText", "combo box items")


    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("items")
        for child in self.children:
            child.emit_xml(xml)
        xml.end_tag()


class Item(BaseTypedAttribute):
    tag_name = "item"
    attr_name = "id"

    @property
    def value_type(self):
        return StringType()


item = Group(
    Item,
    [
        Optional([
            UseIdent("name"),
            ":",
        ]),
        value,
    ]
)

items = Group(
    Items,
    [
        Keyword("items"),
        "[",
        Delimited(item, ","),
        "]",
    ]
)


@completer(
    applies_in=[ast.ObjectContent],
    applies_in_subclass=("Gtk", "ComboBoxText"),
    matches=new_statement_patterns,
)
def items_completer(ast_node, match_variables):
    yield Completion(
        "items", CompletionItemKind.Snippet,
        snippet="items [$0]"
    )
