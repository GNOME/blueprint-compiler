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
from .language import OBJECT_HOOKS, OBJECT_CONTENT_HOOKS


def parse(tokens) -> T.Tuple[ast.UI, T.Optional[MultipleErrors]]:
    """ Parses a list of tokens into an abstract syntax tree. """

    object = Group(
        ast.Object,
        None
    )

    property = Group(
        ast.Property,
        Statement(
            UseIdent("name"),
            ":",
            AnyOf(
                OBJECT_HOOKS,
                object,
                value,
            ).expected("a value"),
        )
    )

    binding = Group(
        ast.Property,
        Statement(
            UseIdent("name"),
            ":",
            "bind",
            UseIdent("bind_source").expected("the ID of a source object to bind from"),
            ".",
            UseIdent("bind_property").expected("a property name to bind from"),
            ZeroOrMore(AnyOf(
                ["sync-create", UseLiteral("sync_create", True)],
                ["inverted", UseLiteral("inverted", True)],
                ["bidirectional", UseLiteral("bidirectional", True)],
            )),
        )
    )

    child = Group(
        ast.Child,
        [
            Optional([
                "[",
                Optional(["internal-child", UseLiteral("internal_child", True)]),
                UseIdent("child_type").expected("a child type"),
                "]",
            ]),
            object,
        ]
    )

    object_content = Group(
        ast.ObjectContent,
        [
            "{",
            Until(AnyOf(
                OBJECT_CONTENT_HOOKS,
                binding,
                property,
                child,
            ), "}"),
        ]
    )

    # work around the recursive reference
    object.child = Sequence(
        class_name,
        Optional(UseIdent("id")),
        object_content,
    )

    template = Group(
        ast.Template,
        [
            "template",
            UseIdent("name").expected("template class name"),
            Optional([
                Match(":"),
                class_name.expected("parent class"),
            ]),
            object_content.expected("block"),
        ]
    )

    ui = Group(
        ast.UI,
        [
            ast.GtkDirective,
            ZeroOrMore(ast.Import),
            Until(AnyOf(
                OBJECT_HOOKS,
                template,
                object,
            ), Eof()),
        ]
    )

    ctx = ParseContext(tokens)
    ui.parse(ctx)

    ast_node = ctx.last_group.to_ast() if ctx.last_group else None
    errors = MultipleErrors(ctx.errors) if len(ctx.errors) else None

    return (ast_node, errors)
