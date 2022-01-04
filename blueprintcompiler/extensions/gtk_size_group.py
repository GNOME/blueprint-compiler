# gtk_size_group.py
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


from .. import ast
from ..ast_utils import AstNode, validate
from ..completions_utils import *
from ..lsp_utils import Completion, CompletionItemKind
from ..parse_tree import *
from ..parser_utils import *
from ..xml_emitter import XmlEmitter


class Widgets(AstNode):
    @validate("widgets")
    def container_is_size_group(self):
        self.validate_parent_type("Gtk", "SizeGroup", "size group properties")

    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("widgets")
        for child in self.children:
            child.emit_xml(xml)
        xml.end_tag()


class Widget(AstNode):
    @validate("name")
    def obj_widget(self):
        object = self.root.objects_by_id.get(self.tokens["name"])
        type = self.root.gir.get_type("Widget", "Gtk")
        if object is None:
            raise CompileError(
                f"Could not find object with ID {self.tokens['name']}",
                did_you_mean=(self.tokens['name'], self.root.objects_by_id.keys()),
            )
        elif object.gir_class and not object.gir_class.assignable_to(type):
            raise CompileError(
                f"Cannot assign {object.gir_class.full_name} to {type.full_name}"
            )

    def emit_xml(self, xml: XmlEmitter):
        xml.put_self_closing("widget", name=self.tokens["name"])


widgets = Group(
    Widgets,
    [
        Keyword("widgets"),
        "[",
        Delimited(
            Group(
                Widget,
                UseIdent("name"),
            ),
            ",",
        ),
        "]",
    ]
)


@completer(
    applies_in=[ast.ObjectContent],
    applies_in_subclass=("Gtk", "SizeGroup"),
    matches=new_statement_patterns,
)
def size_group_completer(ast_node, match_variables):
    yield Completion("widgets", CompletionItemKind.Snippet, snippet="widgets [$0]")
