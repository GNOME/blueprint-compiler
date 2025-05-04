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

from . import annotations, gir, language
from .ast_utils import AstNode
from .completions_utils import (
    CompletionContext,
    CompletionItemKind,
    CompletionPriority,
    completer,
    completers,
    get_available_namespace_completions,
    get_property_completion,
    get_sort_key,
    get_value_completions,
    new_statement_patterns,
)
from .language.contexts import ValueTypeCtx
from .language.types import ClassName
from .lsp_utils import Completion, CompletionItemKind, get_docs_section
from .parser import SKIP_TOKENS
from .tokenizer import Token, TokenType

Pattern = T.List[T.Tuple[TokenType, T.Optional[str]]]


def _complete(
    lsp,
    ast_node: AstNode,
    tokens: T.List[Token],
    idx: int,
    token_idx: int,
    next_token: Token,
) -> T.Iterator[Completion]:
    prev_tokens: T.List[Token] = []

    # collect the 5 previous non-skipped tokens
    while len(prev_tokens) < 5 and token_idx >= 0:
        token = tokens[token_idx]
        if token.type not in SKIP_TOKENS:
            prev_tokens.insert(0, token)
        token_idx -= 1

    for completer in completers:
        yield from completer(prev_tokens, next_token, ast_node, lsp, idx)


def complete(
    lsp, ast_node: AstNode, tokens: T.List[Token], idx: int
) -> T.Iterator[Completion]:
    token_idx = 0
    # find the current token
    for i, token in enumerate(tokens):
        if token.start < idx <= token.end:
            token_idx = i

    if tokens[token_idx].type == TokenType.EOF:
        next_token = tokens[token_idx]
    else:
        next_token_idx = token_idx + 1
        while tokens[next_token_idx].type == TokenType.WHITESPACE:
            next_token_idx += 1
        next_token = tokens[next_token_idx]

    # if the current token is an identifier or whitespace, move to the token before it
    if tokens[token_idx].type == TokenType.IDENT:
        idx = tokens[token_idx].start
        token_idx -= 1

    while tokens[token_idx].type == TokenType.WHITESPACE:
        idx = tokens[token_idx].start
        token_idx -= 1

    child_node = ast_node.get_child_at(idx)
    # If the cursor is at the end of a node, completions should be for the next child of the parent, unless the node
    # is incomplete.
    while (
        child_node.range.end == idx
        and not child_node.incomplete
        and child_node.parent is not None
    ):
        child_node = child_node.parent

    yield from _complete(lsp, child_node, tokens, idx, token_idx, next_token)


@completer([language.GtkDirective])
def using_gtk(_ctx: CompletionContext):
    yield Completion(
        "using Gtk 4.0", CompletionItemKind.Keyword, snippet="using Gtk 4.0;\n"
    )


@completer([language.UI])
def using(ctx: CompletionContext):
    imported_namespaces = set(
        [import_.namespace for import_ in ctx.ast_node.root.using]
    )

    # Import statements must be before any content
    for i in ctx.ast_node.root.children:
        if not isinstance(i, language.GtkDirective) and not isinstance(
            i, language.Import
        ):
            if ctx.index >= i.range.end:
                return

    for ns, version in gir.get_available_namespaces():
        if ns not in imported_namespaces and ns != "Gtk":
            yield Completion(
                f"using {ns} {version}",
                CompletionItemKind.Module,
                text=f"using {ns} {version};",
                sort_text=get_sort_key(CompletionPriority.NAMESPACE, ns),
            )


@completer([language.UI])
def translation_domain(ctx: CompletionContext):
    if ctx.ast_node.root.translation_domain is not None:
        return

    # Translation domain must be after the import statements but before any content
    for i in ctx.ast_node.root.children:
        if isinstance(i, language.Import):
            if ctx.index <= i.range.start:
                return
        elif not isinstance(i, language.GtkDirective):
            if ctx.index >= i.range.end:
                return

    yield Completion(
        "translation-domain",
        CompletionItemKind.Keyword,
        sort_text=get_sort_key(CompletionPriority.KEYWORD, "translation-domain"),
        snippet='translation-domain "$0";',
        docs=get_docs_section("Syntax TranslationDomain"),
    )


@completer(
    applies_in=[
        language.UI,
        language.ObjectContent,
        language.Template,
        language.TypeName,
        language.BracketedTypeName,
    ],
    matches=new_statement_patterns,
)
def namespace(ctx: CompletionContext):
    yield Completion("Gtk", CompletionItemKind.Module, text="Gtk.")

    for ns in ctx.ast_node.root.children[language.Import]:
        if ns.gir_namespace is not None:
            yield Completion(
                ns.gir_namespace.name,
                CompletionItemKind.Module,
                text=ns.gir_namespace.name + ".",
                sort_text=get_sort_key(
                    CompletionPriority.NAMESPACE, ns.gir_namespace.name
                ),
            )

    yield from get_available_namespace_completions(ctx)


@completer(
    applies_in=[
        language.UI,
        language.ObjectContent,
        language.Template,
        language.TypeName,
        language.BracketedTypeName,
    ],
    matches=[
        [TokenType.IDENT, "."],
    ],
)
def object_completer(ctx: CompletionContext):
    ns = ctx.ast_node.root.gir.namespaces.get(ctx.match_variables[0])
    if ns is not None:
        for c in ns.classes.values():
            snippet = c.name
            if (
                str(ctx.next_token) != "{"
                and not isinstance(ctx.ast_node, language.TypeName)
                and not isinstance(ctx.ast_node, language.BracketedTypeName)
            ):
                snippet += " {\n  $0\n}"

            yield Completion(
                c.name,
                CompletionItemKind.Class,
                sort_text=get_sort_key(CompletionPriority.CLASS, c.name),
                snippet=snippet,
                docs=c.doc,
                detail=c.detail,
            )


@completer(
    applies_in=[
        language.UI,
        language.ObjectContent,
        language.Template,
        language.TypeName,
        language.BracketedTypeName,
    ],
    matches=new_statement_patterns,
)
def gtk_object_completer(ctx: CompletionContext):
    ns = ctx.ast_node.root.gir.namespaces.get("Gtk")
    if ns is not None:
        for c in ns.classes.values():
            snippet = c.name
            if (
                str(ctx.next_token) != "{"
                and not isinstance(ctx.ast_node, language.TypeName)
                and not isinstance(ctx.ast_node, language.BracketedTypeName)
            ):
                snippet += " {\n  $0\n}"

            yield Completion(
                c.name,
                CompletionItemKind.Class,
                sort_text=get_sort_key(CompletionPriority.CLASS, c.name),
                snippet=snippet,
                docs=c.doc,
                detail=c.detail,
            )

    if isinstance(ctx.ast_node, language.BracketedTypeName) or (
        isinstance(ctx.ast_node, language.TypeName)
        and not isinstance(ctx.ast_node, language.ClassName)
    ):
        for basic_type in gir.BASIC_TYPES:
            yield Completion(
                basic_type,
                CompletionItemKind.Class,
                sort_text=get_sort_key(CompletionPriority.CLASS, basic_type),
            )


@completer(
    applies_in=[language.ObjectContent],
    matches=new_statement_patterns,
)
def property_completer(ctx: CompletionContext):
    assert isinstance(ctx.ast_node, language.ObjectContent)
    if ctx.ast_node.gir_class and hasattr(ctx.ast_node.gir_class, "properties"):
        for prop_name, prop in ctx.ast_node.gir_class.properties.items():
            yield get_property_completion(
                prop_name,
                prop.type,
                ctx,
                annotations.is_property_translated(prop),
                prop.doc,
            )


@completer(
    applies_in=[language.Property, language.A11yProperty],
    matches=[
        [TokenType.IDENT, ":"],
        [","],
        ["["],
    ],
)
def prop_value_completer(ctx: CompletionContext):
    if isinstance(ctx.ast_node, language.Property):
        yield Completion(
            "bind",
            CompletionItemKind.Keyword,
            snippet="bind $0",
            docs=get_docs_section("Syntax Binding"),
            sort_text=get_sort_key(CompletionPriority.KEYWORD, "bind"),
        )

    assert isinstance(ctx.ast_node, language.Property) or isinstance(
        ctx.ast_node, language.A11yProperty
    )

    if (vt := ctx.ast_node.value_type) is not None:
        assert isinstance(vt, ValueTypeCtx)
        yield from get_value_completions(ctx, vt.value_type, vt.allow_null)


@completer(
    applies_in=[language.ObjectContent],
    matches=new_statement_patterns,
)
def signal_completer(ctx: CompletionContext):
    assert isinstance(ctx.ast_node, language.ObjectContent)

    if ctx.ast_node.gir_class and hasattr(ctx.ast_node.gir_class, "signals"):
        for signal_name, signal in ctx.ast_node.gir_class.signals.items():
            if str(ctx.next_token) == "=>":
                snippet = signal_name
            else:
                if not isinstance(ctx.ast_node.parent, language.Object):
                    name = "on"
                else:
                    name = "on_" + (
                        ctx.ast_node.parent.children[ClassName][0].tokens["id"]
                        or ctx.ast_node.parent.children[ClassName][0]
                        .tokens["class_name"]
                        .lower()
                    )

                snippet = f"{signal_name} => \\$${{1:{name}_{signal_name.replace('-', '_')}}}()$0;"

            yield Completion(
                signal_name,
                CompletionItemKind.Event,
                sort_text=get_sort_key(CompletionPriority.OBJECT_MEMBER, signal_name),
                snippet=snippet,
                docs=signal.doc,
                detail=signal.detail,
            )


@completer(applies_in=[language.UI], matches=new_statement_patterns)
def template_completer(_ctx: CompletionContext):
    yield Completion(
        "template",
        CompletionItemKind.Snippet,
        snippet="template ${1:ClassName} : ${2:ParentClass} {\n  $0\n}",
    )


@completer(
    applies_in=[language.ObjectContent, language.ChildType],
    matches=[["["]],
    applies_in_subclass=[("Gtk", "Dialog"), ("Gtk", "InfoBar")],
)
def response_id_completer(ctx: CompletionContext):
    yield Completion(
        "action",
        CompletionItemKind.Snippet,
        sort_text=get_sort_key(CompletionPriority.KEYWORD, "action"),
        snippet="action response=$0",
    )


@completer(
    [language.ChildAnnotation, language.ExtResponse],
    [["action", "response", "="]],
)
def complete_response_id(ctx: CompletionContext):
    gir = ctx.ast_node.root.gir
    response_type = gir.get_type("ResponseType", "Gtk")
    yield from [
        Completion(
            name,
            kind=CompletionItemKind.EnumMember,
            docs=member.doc,
        )
        for name, member in response_type.members.items()
    ]


@completer(
    [language.ChildAnnotation, language.ExtResponse],
    [
        [
            "action",
            "response",
            "=",
            TokenType.IDENT,
        ],
        [
            "action",
            "response",
            "=",
            TokenType.NUMBER,
        ],
    ],
)
def complete_response_default(ctx: CompletionContext):
    yield Completion(
        "default",
        kind=CompletionItemKind.Keyword,
    )


@completer(
    [language.ObjectContent],
    matches=new_statement_patterns,
    applies_in_subclass=["Adw.Breakpoint"],
)
def complete_breakpoint_condition(ctx: CompletionContext):
    yield Completion("condition", CompletionItemKind.Keyword, snippet="condition ($0)")
