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
from .parser_utils import *
from .tokenizer import TokenType
from .extensions import OBJECT_HOOKS, OBJECT_CONTENT_HOOKS


def parse(tokens) -> T.Tuple[ast.UI, T.Optional[MultipleErrors]]:
    """ Parses a list of tokens into an abstract syntax tree. """

    gtk_directive = Group(
        ast.GtkDirective,
        Statement(
            Keyword("using").err("File must start with a \"using Gtk\" directive (e.g. `using Gtk 4.0;`)"),
            Keyword("Gtk").err("File must start with a \"using Gtk\" directive (e.g. `using Gtk 4.0;`)"),
            UseNumberText("version").expected("a version number for GTK"),
        )
    )

    import_statement = Group(
        ast.Import,
        Statement(
            Keyword("using"),
            UseIdent("namespace").expected("a GIR namespace"),
            UseNumberText("version").expected("a version number"),
        )
    )

    object = Group(
        ast.Object,
        None
    )

    property = Group(
        ast.Property,
        Statement(
            UseIdent("name"),
            Op(":"),
            AnyOf(
                *OBJECT_HOOKS,
                object,
                value,
            ).expected("a value"),
        )
    )

    binding = Group(
        ast.Property,
        Statement(
            UseIdent("name"),
            Op(":"),
            Keyword("bind"),
            UseIdent("bind_source").expected("the ID of a source object to bind from"),
            Op("."),
            UseIdent("bind_property").expected("a property name to bind from"),
            ZeroOrMore(AnyOf(
                Sequence(Keyword("sync-create"), UseLiteral("sync_create", True)),
                Sequence(Keyword("after"), UseLiteral("after", True)),
                Sequence(Keyword("bidirectional"), UseLiteral("bidirectional", True)),
            )),
        )
    )

    signal = Group(
        ast.Signal,
        Statement(
            UseIdent("name"),
            Optional(Sequence(
                Op("::"),
                UseIdent("detail_name").expected("a signal detail name"),
            )),
            Op("=>"),
            UseIdent("handler").expected("the name of a function to handle the signal"),
            OpenParen().expected("argument list"),
            Optional(UseIdent("object")).expected("object identifier"),
            CloseParen().expected("`)`"),
            ZeroOrMore(AnyOf(
                Sequence(Keyword("swapped"), UseLiteral("swapped", True)),
                Sequence(Keyword("after"), UseLiteral("after", True)),
            )),
        )
    )

    child = Group(
        ast.Child,
        Sequence(
            Optional(Sequence(
                OpenBracket(),
                Optional(Sequence(Keyword("internal-child"), UseLiteral("internal_child", True))),
                UseIdent("child_type").expected("a child type"),
                CloseBracket(),
            )),
            object,
        )
    )

    object_content = Group(
        ast.ObjectContent,
        Sequence(
            OpenBlock(),
            Until(AnyOf(
                *OBJECT_CONTENT_HOOKS,
                binding,
                property,
                signal,
                child,
            ), CloseBlock()),
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
            Optional(
                Sequence(
                    Op(":"),
                    class_name.expected("parent class"),
                )
            ),
            object_content.expected("block"),
        )
    )

    ui = Group(
        ast.UI,
        Sequence(
            gtk_directive,
            ZeroOrMore(import_statement),
            Until(AnyOf(
                *OBJECT_HOOKS,
                template,
                object,
            ), Eof()),
        )
    )

    ctx = ParseContext(tokens)
    ui.parse(ctx)

    ast_node = ctx.last_group.to_ast() if ctx.last_group else None
    errors = MultipleErrors(ctx.errors) if len(ctx.errors) else None

    return (ast_node, errors)
