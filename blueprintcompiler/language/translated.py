# translated.py
#
# Copyright 2022 James Westman <james@jwestman.net>
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

from .common import *
from .contexts import ValueTypeCtx


class Translated(AstNode):
    grammar = AnyOf(
        ["_", "(", UseQuoted("string"), ")"],
        [
            "C_",
            "(",
            UseQuoted("context"),
            ",",
            UseQuoted("string"),
            ")",
        ],
    )

    @property
    def string(self) -> str:
        return self.tokens["string"]

    @property
    def translate_context(self) -> T.Optional[str]:
        return self.tokens["context"]

    @property
    def string_token(self) -> Token:
        return self.group.tokens["string"]

    @validate()
    def validate_for_type(self) -> None:
        expected_type = self.context[ValueTypeCtx].value_type
        if expected_type is not None and not expected_type.assignable_to(StringType()):
            raise CompileError(
                f"Cannot convert translated string to {expected_type.full_name}"
            )

    @validate("context")
    def context_double_quoted(self):
        if self.translate_context is None:
            return

        if not str(self.group.tokens["context"]).startswith('"'):
            raise CompileWarning("gettext may not recognize single-quoted strings")

    @validate("string")
    def string_double_quoted(self):
        if not str(self.group.tokens["string"]).startswith('"'):
            raise CompileWarning("gettext may not recognize single-quoted strings")

    @docs()
    def ref_docs(self):
        return get_docs_section("Syntax Translated")
