# completions_utils.py
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


import typing as T
from dataclasses import dataclass
from enum import Enum

from . import gir
from .ast_utils import AstNode
from .lsp_utils import Completion, CompletionItemKind
from .tokenizer import Token, TokenType


class CompletionPriority(Enum):
    ENUM_MEMBER = "00"
    NAMED_OBJECT = "01"
    OBJECT_MEMBER = "02"
    CLASS = "03"
    NAMESPACE = "04"
    KEYWORD = "05"
    # An available namespace that hasn't been imported yet
    IMPORT_NAMESPACE = "99"


def get_sort_key(priority: CompletionPriority, name: str):
    return f"{priority.value} {name}"


@dataclass
class CompletionContext:
    client_supports_completion_choice: bool
    ast_node: AstNode
    match_variables: T.List[str]
    next_token: Token
    index: int


new_statement_patterns = [
    [(TokenType.PUNCTUATION, "{")],
    [(TokenType.PUNCTUATION, "}")],
    [(TokenType.PUNCTUATION, "]")],
    [(TokenType.PUNCTUATION, ";")],
]


def completer(applies_in: T.List, matches: T.List = [], applies_in_subclass=None):
    def decorator(func: T.Callable[[CompletionContext], T.Generator[Completion]]):
        def inner(
            prev_tokens: T.List[Token], next_token: Token, ast_node, lsp, idx: int
        ):
            # For completers that apply in ObjectContent nodes, we can further
            # check that the object is the right class
            if applies_in_subclass is not None:
                parent_obj = ast_node
                while parent_obj is not None and not hasattr(parent_obj, "gir_class"):
                    parent_obj = parent_obj.parent

                if (
                    parent_obj is None
                    or not parent_obj.gir_class
                    or not any(
                        [
                            parent_obj.gir_class.assignable_to(
                                parent_obj.root.gir.get_type(c[1], c[0])
                            )
                            for c in applies_in_subclass
                        ]
                    )
                ):
                    return

            any_match = len(matches) == 0
            match_variables: T.List[str] = []

            for pattern in matches:
                match_variables = []

                if len(pattern) <= len(prev_tokens):
                    for i in range(0, len(pattern)):
                        type, value = pattern[i]
                        token = prev_tokens[i - len(pattern)]
                        if token.type != type or (
                            value is not None and str(token) != value
                        ):
                            break
                        if value is None:
                            match_variables.append(str(token))
                    else:
                        any_match = True
                        break

            if not any_match:
                return

            context = CompletionContext(
                client_supports_completion_choice=lsp.client_supports_completion_choice,
                ast_node=ast_node,
                match_variables=match_variables,
                next_token=next_token,
                index=idx,
            )
            yield from func(context)

        for c in applies_in:
            c.completers.append(inner)
        return inner

    return decorator


def get_property_completion(
    name: str,
    type: gir.GirType,
    ctx: CompletionContext,
    translated: bool,
    doc: str,
) -> Completion:
    if str(ctx.next_token) == ":":
        snippet = name
    elif isinstance(type, gir.BoolType) and ctx.client_supports_completion_choice:
        snippet = f"{name}: ${{1|true,false|}};"
    elif isinstance(type, gir.StringType):
        snippet = f'{name}: _("$0");' if translated else f'{name}: "$0";'
    elif (
        isinstance(type, gir.Enumeration)
        and len(type.members) <= 10
        and ctx.client_supports_completion_choice
    ):
        choices = ",".join(type.members.keys())
        snippet = f"{name}: ${{1|{choices}|}};"
    elif type.full_name == "Gtk.Expression":
        snippet = f"{name}: expr $0;"
    else:
        snippet = f"{name}: $0;"

    return Completion(
        name,
        CompletionItemKind.Property,
        sort_text=get_sort_key(CompletionPriority.OBJECT_MEMBER, name),
        snippet=snippet,
        docs=doc,
    )
