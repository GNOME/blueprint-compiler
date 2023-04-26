# contexts.py
#
# Copyright 2023 James Westman <james@jwestman.net>
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
from functools import cached_property

from .common import *
from .gobject_object import Object


@dataclass
class ValueTypeCtx:
    value_type: T.Optional[GirType]
    allow_null: bool = False


@dataclass
class ScopeCtx:
    node: AstNode

    @cached_property
    def objects(self) -> T.Dict[str, Object]:
        return {
            obj.tokens["id"]: obj
            for obj in self._iter_recursive(self.node)
            if obj.tokens["id"] is not None
        }

    def validate_unique_ids(self) -> None:
        passed = {}
        for obj in self._iter_recursive(self.node):
            if obj.tokens["id"] is None:
                continue

            if obj.tokens["id"] in passed:
                token = obj.group.tokens["id"]
                raise CompileError(
                    f"Duplicate object ID '{obj.tokens['id']}'", token.start, token.end
                )
            passed[obj.tokens["id"]] = obj

    def _iter_recursive(self, node: AstNode):
        yield node
        for child in node.children:
            if child.context[ScopeCtx] is self:
                yield from self._iter_recursive(child)
