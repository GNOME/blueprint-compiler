# common.py
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

import typing as T

from .. import gir
from ..ast_utils import AstNode, validate, docs
from ..errors import CompileError, MultipleErrors
from ..completions_utils import *
from .. import decompiler as decompile
from ..decompiler import DecompileCtx, decompiler
from ..gir import StringType, BoolType, IntType, FloatType, GirType, Enumeration
from ..lsp_utils import Completion, CompletionItemKind, SemanticToken, SemanticTokenType
from ..parse_tree import *
from ..xml_emitter import XmlEmitter


OBJECT_HOOKS = AnyOf()
OBJECT_CONTENT_HOOKS = AnyOf()
VALUE_HOOKS = AnyOf()


class ScopeVariable:
    def __init__(self, name: str, gir_class: gir.GirType, xml_func, glib_type_name=None):
        self._name = name
        self._gir_class = gir_class
        self._xml_func = xml_func
        self._glib_type_name = glib_type_name

    @property
    def name(self) -> str:
        return self._name

    @property
    def gir_class(self) -> gir.GirType:
        return self._gir_class

    @property
    def glib_type_name(self) -> T.Optional[str]:
        if self._glib_type_name is not None:
            return self._glib_type_name
        elif self.gir_class:
            return self.gir_class.glib_type_name
        else:
            return None

    def emit_xml(self, xml: XmlEmitter):
        if f := self._xml_func:
            f(xml)
        else:
            raise NotImplementedError()

class Scope:
    @property
    def variables(self) -> T.Dict[str, ScopeVariable]:
        raise NotImplementedError()

    @property
    def this_name(self) -> T.Optional[str]:
        return None

    @property
    def this_type(self) -> T.Optional[str]:
        return None

    @property
    def this_type_glib_name(self) -> T.Optional[str]:
        return None
