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


from dataclasses import dataclass, field

from .errors import CompileError, CompileWarning, MultipleErrors
from .language import UI
from .linter import lint
from .parse_tree import AnyOf, ParseContext
from .tokenizer import SourceCode, tokenize


@dataclass
class CompileOptions:
    lint_categories: list[str] = field(default_factory=list)
    lint_rule_ids: list[str] = field(default_factory=list)
    lint_platform: str | None = None
    lint_no_suggestions: bool = False


@dataclass
class CompileResult:
    success: bool
    source: SourceCode
    ast: UI
    errors: list[CompileError]
    warnings: list[CompileWarning]
    lint_warnings: list[CompileWarning]

    @property
    def diagnostics(self) -> list[CompileError]:
        return self.errors + self.warnings + self.lint_warnings


def parse(
    blueprint: str,
    opts: CompileOptions | None = None,
) -> CompileResult:
    """Parses Blueprint source code into an abstract syntax tree."""

    opts = opts or CompileOptions()

    source = tokenize(blueprint)

    errors: list[CompileError] = []
    warnings: list[CompileWarning] = []
    lint_warnings: list[CompileWarning] = []

    ctx = ParseContext(source)
    AnyOf(UI).parse(ctx)
    assert ctx.last_group is not None
    ast_node = ctx.last_group.to_ast()

    errors = [*ctx.errors, *ast_node.errors]
    warnings = [w for w in [*ctx.warnings, *ast_node.warnings] if not w.ignored]

    if len(opts.lint_categories) > 0:
        lint_warnings = lint(
            ast_node,
            categories=opts.lint_categories,
            rule_ids=opts.lint_rule_ids,
            platform=opts.lint_platform,
            no_suggestions=opts.lint_no_suggestions,
        )
    else:
        lint_warnings = []

    return CompileResult(
        success=len(errors) == 0,
        source=source,
        ast=ast_node,
        errors=errors,
        warnings=warnings,
        lint_warnings=lint_warnings,
    )
