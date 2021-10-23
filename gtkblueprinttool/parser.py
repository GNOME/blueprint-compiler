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
            Directive("gtk"),
            Fail(UseNumber(None), "Version number must be in quotation marks"),
            UseQuoted("version").expected("a version number for GTK"),
            StmtEnd().expected("`;`"),
        )
    )

    import_statement = Group(
        ast.Import,
        Sequence(
            Directive("import"),
            UseIdent("namespace").expected("a GIR namespace"),
            Fail(UseNumber(None), "Version number must be in quotation marks"),
            UseQuoted("version").expected("a version number"),
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

    property = Group(
        ast.Property,
        Sequence(
            UseIdent("name"),
            Op(":"),
            value.expected("a value"),
            StmtEnd().expected("`;`"),
        )
    ).recover()

    binding = Group(
        ast.Property,
        Sequence(
            UseIdent("name"),
            Op(":="),
            UseIdent("bind_source").expected("the ID of a source object to bind from"),
            Op("."),
            UseIdent("bind_property").expected("a property name to bind from"),
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

    object = Group(
        ast.Object,
        None
    )

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

    object_content = Group(
        ast.ObjectContent,
        Sequence(
            OpenBlock(),
            ZeroOrMore(AnyOf(
                property,
                binding,
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
        object_content.expected("block"),
    )

    template = Group(
        ast.Template,
        Sequence(
            Directive("template"),
            UseIdent("name").expected("template class name"),
            Op(":").expected("`:`"),
            class_name.expected("parent class"),
            object_content.expected("block"),
        )
    )

    ui = Group(
        ast.UI,
        Sequence(
            gtk_directive.err("File must start with a @gtk directive (e.g. `@gtk 4.0;`)"),
            ZeroOrMore(import_statement),
            ZeroOrMore(AnyOf(
                template,
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
