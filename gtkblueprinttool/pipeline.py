# pipeline.py
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


from . import ast, parser, tokenizer, xml_emitter


class Pipeline:
    """ Represents the pipeline from blueprint code to XML, through the
        tokenizer and abstract syntax tree steps. Setting any step
        automatically updates the later steps. """

    def __init__(self, string=None):
        self._string = string
        self._tokens = None
        self._ast = None
        self._xml = None

    @property
    def string(self) -> str:
        """ Blueprint code """
        return self._string
    @string.setter
    def string(self, new_val):
        self._reset()
        self._string = new_val

    @property
    def tokens(self) -> [tokenizer.Token]:
        """ List of tokens """
        if self._tokens is None:
            if self.string is not None:
                self._tokens = tokenizer.tokenize(self._string)
        return self._tokens
    @tokens.setter
    def tokens(self, new_val):
        self._reset()
        self._tokens = new_val

    @property
    def ast(self) -> ast.UI:
        """ Abstract syntax tree """
        if self._ast is None:
            if self.tokens is not None:
                self._ast = parser.parse_ast(self.tokens)
        return self._ast
    @ast.setter
    def ast(self, new_val):
        self._reset()
        self._ast = new_val

    @property
    def xml(self) -> str:
        """ GtkBuilder XML string """
        if self._xml is None:
            if self.ast is not None:
                emitter = xml_emitter.XmlEmitter()
                self.ast.generate(emitter)
                self._xml = emitter.result
        return self._xml
    @xml.setter
    def xml(self, new_val):
        self._reset()
        self._xml = new_val


    def _reset(self):
        self._string = None
        self._tokens = None

