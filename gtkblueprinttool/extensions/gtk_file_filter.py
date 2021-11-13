# gtk_file_filter.py
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


class Filters(AstNode):
    @validate()
    def container_is_file_filter(self):
        self.validate_parent_type("Gtk", "FileFilter", "file filter properties")

    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag(self.tokens["tag_name"])
        for child in self.children:
            child.emit_xml(xml)
        xml.end_tag()


class FilterString(AstNode):
    def emit_xml(self, xml):
        xml.start_tag(self.tokens["tag_name"])
        xml.put_text(self.tokens["name"])
        xml.end_tag()


def create_node(tag_name: str, singular: str):
    return Group(
        Filters,
        Statement(
            Keyword(tag_name, True),
            UseLiteral("tag_name", tag_name),
            OpenBracket(),
            Delimited(
                Group(
                    FilterString,
                    Sequence(
                        UseQuoted("name"),
                        UseLiteral("tag_name", singular),
                    )
                ),
                Comma(),
            ),
            CloseBracket(),
        )
    )


mime_types = create_node("mime-types", "mime-type")
patterns = create_node("patterns", "pattern")
suffixes = create_node("suffixes", "suffix")


@completer(
    applies_in=[ast.ObjectContent],
    applies_in_subclass=("Gtk", "FileFilter"),
    matches=new_statement_patterns,
)
def file_filter_completer(ast_node, match_variables):
    yield Completion("mime-types", CompletionItemKind.Snippet, snippet="mime-types [\"$0\"];")
    yield Completion("patterns", CompletionItemKind.Snippet, snippet="patterns [\"$0\"];")
    yield Completion("suffixes", CompletionItemKind.Snippet, snippet="suffixes [\"$0\"];")

