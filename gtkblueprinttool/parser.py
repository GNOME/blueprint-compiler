# parser.py
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


from . import ast
from .errors import MultipleErrors
from .parse_tree import *
from .tokenizer import TokenType


def parse(tokens) -> ast.UI:
    """ Parses a list of tokens into an abstract syntax tree. """

    gtk_directive = Group(
        ast.GtkDirective,
        Sequence(
            Keyword("using"),
            Keyword("Gtk"),
            UseNumberText("version").expected("a version number for GTK"),
            StmtEnd().expected("`;`"),
        )
    )

    import_statement = Group(
        ast.Import,
        Sequence(
            Keyword("using"),
            UseIdent("namespace").expected("a GIR namespace"),
            UseNumberText("version").expected("a version number"),
            StmtEnd().expected("`;`"),
        )
    ).recover()

    class_name = AnyOf(
        Sequence(
            UseIdent("namespace"),
            Op("."),
            UseIdent("class_name"),
        ),
        UseIdent("class_name"),
    )

    value = AnyOf(
        Sequence(
            Keyword("_"),
            OpenParen(),
            UseQuoted("value").expected("a quoted string"),
            CloseParen().expected("`)`"),
            UseLiteral("translatable", True),
        ),
        Sequence(Keyword("True"), UseLiteral("value", True)),
        Sequence(Keyword("true"), UseLiteral("value", True)),
        Sequence(Keyword("Yes"), UseLiteral("value", True)),
        Sequence(Keyword("yes"), UseLiteral("value", True)),
        Sequence(Keyword("False"), UseLiteral("value", False)),
        Sequence(Keyword("false"), UseLiteral("value", False)),
        Sequence(Keyword("No"), UseLiteral("value", False)),
        Sequence(Keyword("no"), UseLiteral("value", False)),
        UseIdent("value"),
        UseNumber("value"),
        UseQuoted("value"),
    )

    object = Group(
        ast.Object,
        None
    )

    property = Group(
        ast.Property,
        Sequence(
            UseIdent("name"),
            Op(":"),
            AnyOf(
                object,
                value,
            ).expected("a value"),
            StmtEnd().expected("`;`"),
        )
    ).recover()

    binding = Group(
        ast.Property,
        Sequence(
            UseIdent("name"),
            Op(":"),
            Keyword("bind"),
            UseIdent("bind_source").expected("the ID of a source object to bind from"),
            Op("."),
            UseIdent("bind_property").expected("a property name to bind from"),
            AnyOf(
                Sequence(Keyword("sync-create"), UseLiteral("sync_create", True)),
                Sequence(Keyword("after"), UseLiteral("after", True)),
            ),
            StmtEnd().expected("`;`"),
        )
    ).recover()

    signal = Group(
        ast.Signal,
        Sequence(
            UseIdent("name"),
            Optional(Sequence(
                Op("::"),
                UseIdent("detail_name").expected("a signal detail name"),
            )),
            Op("=>"),
            UseIdent("handler").expected("the name of a function to handle the signal"),
            OpenParen().expected("argument list"),
            CloseParen().expected("`)`"),
            ZeroOrMore(AnyOf(
                Sequence(Keyword("swapped"), UseLiteral("swapped", True)),
                Sequence(Keyword("after"), UseLiteral("after", True)),
                Sequence(Keyword("object"), UseLiteral("object", True)),
            )),
            StmtEnd().expected("`;`"),
        )
    ).recover()

    child = Group(
        ast.Child,
        Sequence(
            Optional(Sequence(
                OpenBracket(),
                UseIdent("child_type").expected("a child type"),
                CloseBracket(),
            )),
            object,
        )
    )

    style = Group(
        ast.Style,
        Sequence(
            Keyword("style"),
            Delimited(
                Group(
                    ast.StyleClass,
                    UseQuoted("name")
                ),
                Comma(),
            ),
            StmtEnd(),
        )
    )

    menu_contents = Sequence()

    menu_section = Group(
        ast.Menu,
        Sequence(
            Keyword("section"),
            UseLiteral("tag", "section"),
            Optional(UseIdent("id")),
            menu_contents
        )
    )

    menu_submenu = Group(
        ast.Menu,
        Sequence(
            Keyword("submenu"),
            UseLiteral("tag", "submenu"),
            Optional(UseIdent("id")),
            menu_contents
        )
    )

    menu_attribute = Group(
        ast.MenuAttribute,
        Sequence(
            UseIdent("name"),
            Op(":"),
            value.expected("a value"),
            StmtEnd().expected("`;`"),
        )
    )

    menu_item = Group(
        ast.Menu,
        Sequence(
            Keyword("item"),
            UseLiteral("tag", "item"),
            Optional(UseIdent("id")),
            OpenBlock().expected("`{`"),
            ZeroOrMore(menu_attribute),
            CloseBlock().err("Could not understand statement"),
        )
    )

    menu_item_shorthand = Group(
        ast.Menu,
        Sequence(
            Keyword("item"),
            UseLiteral("tag", "item"),
            Group(
                ast.MenuAttribute,
                Sequence(UseLiteral("name", "label"), value),
            ),
            Optional(Group(
                ast.MenuAttribute,
                Sequence(UseLiteral("name", "action"), value),
            )),
            Optional(Group(
                ast.MenuAttribute,
                Sequence(UseLiteral("name", "verb-icon-name"), value),
            )),
            StmtEnd().expected("`;`"),
        )
    )

    menu_contents.children = [
        OpenBlock().expected("`{`"),
        ZeroOrMore(AnyOf(
            menu_section,
            menu_submenu,
            menu_item_shorthand,
            menu_item,
            menu_attribute,
        )),
        CloseBlock().err("Could not understand statement"),
    ]

    menu = Group(
        ast.Menu,
        Sequence(
            Keyword("menu"),
            UseLiteral("tag", "menu"),
            Optional(UseIdent("id")),
            menu_contents
        ),
    )

    object_content = Group(
        ast.ObjectContent,
        Sequence(
            OpenBlock(),
            ZeroOrMore(AnyOf(
                style,
                binding,
                property,
                signal,
                child,
            )),
            CloseBlock().err("Could not understand statement"),
        )
    )

    # work around the recursive reference
    object.child = Sequence(
        class_name,
        Optional(UseIdent("id")),
        object_content,
    )

    template = Group(
        ast.Template,
        Sequence(
            Keyword("template"),
            UseIdent("name").expected("template class name"),
            Op(":").expected("`:`"),
            class_name.expected("parent class"),
            object_content.expected("block"),
        )
    )

    ui = Group(
        ast.UI,
        Sequence(
            gtk_directive.err("File must start with a \"using gtk\" directive (e.g. `using Gtk 4.0;`)"),
            ZeroOrMore(import_statement),
            ZeroOrMore(AnyOf(
                template,
                menu,
                object,
            )),
            Eof().err("Failed to parse the rest of the file"),
        )
    ).recover()

    ctx = ParseContext(tokens)
    ui.parse(ctx)
    if len(ctx.errors):
        raise MultipleErrors(ctx.errors)
    return ctx.last_group.to_ast()
