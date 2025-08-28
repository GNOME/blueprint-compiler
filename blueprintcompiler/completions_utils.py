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

from .ast_utils import AstNode
from .lsp_utils import Completion
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
    def decorator(
        func: T.Callable[[CompletionContext], T.Generator[Completion, None, None]],
    ):
        def inner(
            prev_tokens: T.List[Token], next_token: Token, ast_node, lsp, idx: int
        ):
            # For completers that apply in ObjectContent nodes, we can further
            # check that the object is the right class
            if applies_in_subclass is not None:
                type = ast_node.root.gir.get_type(
                    applies_in_subclass[1], applies_in_subclass[0]
                )
                if not ast_node.gir_class or not ast_node.gir_class.assignable_to(type):
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
