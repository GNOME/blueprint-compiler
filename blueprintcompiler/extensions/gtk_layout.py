# gtk_layout.py
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


from ..ast import BaseAttribute
from ..ast_utils import AstNode, validate
from ..completions_utils import *
from ..lsp_utils import Completion, CompletionItemKind
from ..parse_tree import *
from ..parser_utils import *
from ..xml_emitter import XmlEmitter


class Layout(AstNode):
    @validate("layout")
    def container_is_widget(self):
        self.validate_parent_type("Gtk", "Widget", "layout properties")


    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag("layout")
        for child in self.children:
            child.emit_xml(xml)
        xml.end_tag()


class LayoutProperty(BaseAttribute):
    tag_name = "property"

    @property
    def value_type(self):
        # there isn't really a way to validate these
        return None


layout_prop = Group(
    LayoutProperty,
    Statement(
        UseIdent("name"),
        ":",
        value.expected("a value"),
    )
)

layout = Group(
    Layout,
    Sequence(
        Keyword("layout"),
        "{",
        Until(layout_prop, "}"),
    )
)


@completer(
    applies_in=[ast.ObjectContent],
    applies_in_subclass=("Gtk", "Widget"),
    matches=new_statement_patterns,
)
def layout_completer(ast_node, match_variables):
    yield Completion(
        "layout", CompletionItemKind.Snippet,
        snippet="layout {\n  $0\n}"
    )
