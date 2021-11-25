# gtk_menus.py
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
from ..ast_utils import AstNode
from ..completions_utils import *
from ..lsp_utils import Completion, CompletionItemKind
from ..parse_tree import *
from ..parser_utils import *
from ..xml_emitter import XmlEmitter


class Menu(AstNode):
    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag(self.tokens["tag"], id=self.tokens["id"])
        for child in self.children:
            child.emit_xml(xml)
        xml.end_tag()

    @property
    def gir_class(self):
        return self.root.gir.namespaces["Gtk"].lookup_type("Gio.MenuModel")


class MenuAttribute(BaseAttribute):
    tag_name = "attribute"

    @property
    def value_type(self):
        return None


menu_contents = Sequence()

menu_section = Group(
    Menu,
    Sequence(
        Keyword("section"),
        UseLiteral("tag", "section"),
        Optional(UseIdent("id")),
        menu_contents
    )
)

menu_submenu = Group(
    Menu,
    Sequence(
        Keyword("submenu"),
        UseLiteral("tag", "submenu"),
        Optional(UseIdent("id")),
        menu_contents
    )
)

menu_attribute = Group(
    MenuAttribute,
    Sequence(
        UseIdent("name"),
        Op(":"),
        value.expected("a value"),
        StmtEnd().expected("`;`"),
    )
)

menu_item = Group(
    Menu,
    Sequence(
        Keyword("item"),
        UseLiteral("tag", "item"),
        Optional(UseIdent("id")),
        OpenBlock().expected("`{`"),
        Until(menu_attribute, CloseBlock()),
    )
)

menu_item_shorthand = Group(
    Menu,
    Sequence(
        Keyword("item"),
        UseLiteral("tag", "item"),
        Group(
            MenuAttribute,
            Sequence(UseLiteral("name", "label"), value),
        ),
        Optional(Group(
            MenuAttribute,
            Sequence(UseLiteral("name", "action"), value),
        )),
        Optional(Group(
            MenuAttribute,
            Sequence(UseLiteral("name", "icon"), value),
        )),
        StmtEnd().expected("`;`"),
    )
)

menu_contents.children = [
    OpenBlock().expected("`{`"),
    Until(AnyOf(
        menu_section,
        menu_submenu,
        menu_item_shorthand,
        menu_item,
        menu_attribute,
    ), CloseBlock()),
]

menu = Group(
    Menu,
    Sequence(
        Keyword("menu"),
        UseLiteral("tag", "menu"),
        Optional(UseIdent("id")),
        menu_contents
    ),
)


@completer(
    applies_in=[ast.UI],
    matches=new_statement_patterns,
)
def menu_completer(ast_node, match_variables):
    yield Completion(
        "menu", CompletionItemKind.Snippet,
        snippet="menu {\n  $0\n}"
    )


@completer(
    applies_in=[Menu],
    matches=new_statement_patterns,
)
def menu_content_completer(ast_node, match_variables):
    yield Completion(
        "submenu", CompletionItemKind.Snippet,
        snippet="submenu {\n  $0\n}"
    )
    yield Completion(
        "section", CompletionItemKind.Snippet,
        snippet="section {\n  $0\n}"
    )
    yield Completion(
        "item", CompletionItemKind.Snippet,
        snippet="item {\n  $0\n}"
    )
    yield Completion(
        "item (shorthand)", CompletionItemKind.Snippet,
        snippet='item _("${1:Label}") "${2:action-name}" "${3:icon-name}";'
    )

    yield Completion(
        "label", CompletionItemKind.Snippet,
        snippet='label: $0;'
    )
    yield Completion(
        "action", CompletionItemKind.Snippet,
        snippet='action: "$0";'
    )
    yield Completion(
        "icon", CompletionItemKind.Snippet,
        snippet='icon: "$0";'
    )

