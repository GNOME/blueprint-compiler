# test_samples.py
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


import difflib # I love Python
from pathlib import Path
import unittest

from gtkblueprinttool import tokenizer, parser
from gtkblueprinttool.errors import PrintableError
from gtkblueprinttool.tokenizer import Token, TokenType, tokenize


class TestSamples(unittest.TestCase):
    def assert_sample(self, name):
        with open((Path(__file__).parent / f"samples/{name}.blp").resolve()) as f:
            blueprint = f.read()
        with open((Path(__file__).parent / f"samples/{name}.ui").resolve()) as f:
            expected = f.read()

        tokens = tokenizer.tokenize(blueprint)
        ast, errors = parser.parse(tokens)

        if errors:
            raise errors
        if len(ast.errors):
            raise MultipleErrors(ast.errors)

        actual = ast.generate()
        if actual.strip() != expected.strip():
            diff = difflib.unified_diff(expected.splitlines(), actual.splitlines())
            print("\n".join(diff))
            raise AssertionError()


    def test_samples(self):
        self.assert_sample("binding")
        self.assert_sample("child_type")
        self.assert_sample("layout")
        self.assert_sample("menu")
        self.assert_sample("property")
        self.assert_sample("signal")
        self.assert_sample("style")
        self.assert_sample("template")
        self.assert_sample("using")
