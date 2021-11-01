# completions.py
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

from . import ast
from .completions_utils import *
from .lsp_utils import Completion, CompletionItemKind
from .parser import SKIP_TOKENS
from .tokenizer import TokenType, Token

Pattern = T.List[T.Tuple[TokenType, T.Optional[str]]]


def complete(ast_node: ast.AstNode, tokens: T.List[Token], idx: int) -> T.Iterator[Completion]:
    for child in ast_node.children:
        if child.group.start <= idx <= child.group.end:
            yield from complete(child, tokens, idx)
            return

    prev_tokens: T.List[Token] = []
    token_idx = 0

    # find the current token
    for i, token in enumerate(tokens):
        if token.start < idx <= token.end:
            token_idx = i

    # if the current token is an identifier, move to the token before it
    if tokens[token_idx].type == TokenType.IDENT:
        token_idx -= 1

    # collect the 5 previous non-skipped tokens
    while len(prev_tokens) < 5 and token_idx >= 0:
        token = tokens[token_idx]
        if token.type not in SKIP_TOKENS:
            prev_tokens.insert(0, token)
        token_idx -= 1

    for completer in ast_node.completers:
        yield from completer(prev_tokens, ast_node)


@completer([ast.GtkDirective])
def using_gtk(ast_node, match_variables):
    yield Completion("using Gtk 4.0;", CompletionItemKind.Keyword)


@completer(
    applies_in=[ast.UI, ast.ObjectContent, ast.Template],
    matches=new_statement_patterns
)
def namespace(ast_node, match_variables):
    yield Completion("Gtk", CompletionItemKind.Module, text="Gtk.")
    for ns in ast_node.root.children[ast.Import]:
        yield Completion(ns.namespace, CompletionItemKind.Module, text=ns.namespace + ".")


@completer(
    applies_in=[ast.UI, ast.ObjectContent, ast.Template],
    matches=[
        [(TokenType.IDENT, None), (TokenType.OP, "."), (TokenType.IDENT, None)],
        [(TokenType.IDENT, None), (TokenType.OP, ".")],
    ]
)
def object_completer(ast_node, match_variables):
    ns = ast_node.root.gir.namespaces.get(match_variables[0])
    if ns is not None:
        for c in ns.classes.values():
            yield Completion(c.name, CompletionItemKind.Class, docs=c.doc)


@completer(
    applies_in=[ast.ObjectContent],
    matches=new_statement_patterns,
)
def property_completer(ast_node, match_variables):
    if ast_node.gir_class:
        for prop in ast_node.gir_class.properties:
            yield Completion(prop, CompletionItemKind.Property, snippet=f"{prop}: $0;")


@completer(
    applies_in=[ast.ObjectContent],
    matches=new_statement_patterns,
)
def signal_completer(ast_node, match_variables):
    if ast_node.gir_class:
        for signal in ast_node.gir_class.signals:
            name = ("on" if not isinstance(ast_node.parent, ast.Object)
                else "on_" + (ast_node.parent.id or ast_node.parent.class_name.lower()))
            yield Completion(signal, CompletionItemKind.Property, snippet=f"{signal} => ${{1:{name}_{signal.replace('-', '_')}}}()$0;")


@completer(
    applies_in=[ast.UI],
    matches=new_statement_patterns
)
def template_completer(ast_node, match_variables):
    yield Completion(
        "template", CompletionItemKind.Snippet,
        snippet="template ${1:ClassName} : ${2:ParentClass} {\n  $0\n}"
    )
