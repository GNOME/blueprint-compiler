# lsp_enums.py
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


from enum import Enum

from . import tokenizer, parser
from .errors import *
from .utils import *


class OpenFile:
    def __init__(self, uri, text, version):
        self.uri = uri
        self.text = text
        self.version = version

        self._update()

    def apply_changes(self, changes):
        for change in changes:
            start = utils.pos_to_idx(change.range.start.line, change.range.start.character, self.text)
            end = utils.pos_to_idx(change.range.end.line, change.range.end.character, self.text)
            self.text = self.text[:start] + change.text + self.text[end:]
        self._update()

    def _update(self):
        self.diagnostics = []
        try:
            self.tokens = tokenizer.tokenize(self.text)
            self.ast = parser.parse(self.tokens)
            self.diagnostics += self.ast.errors
        except MultipleErrors as e:
            self.diagnostics += e.errors
        except CompileError as e:
            self.diagnostics += e
