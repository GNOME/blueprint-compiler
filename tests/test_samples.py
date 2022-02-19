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
import traceback
import unittest

from blueprintcompiler import tokenizer, parser, decompiler
from blueprintcompiler.errors import PrintableError, MultipleErrors, CompileError
from blueprintcompiler.tokenizer import Token, TokenType, tokenize
from blueprintcompiler import utils


class TestSamples(unittest.TestCase):
    def assert_sample(self, name):
        try:
            with open((Path(__file__).parent / f"samples/{name}.blp").resolve()) as f:
                blueprint = f.read()
            with open((Path(__file__).parent / f"samples/{name}.ui").resolve()) as f:
                expected = f.read()

            tokens = tokenizer.tokenize(blueprint)
            ast, errors, warnings = parser.parse(tokens)

            if errors:
                raise errors
            if len(ast.errors):
                raise MultipleErrors(ast.errors)
            if len(warnings):
                raise MultipleErrors(warnings)

            actual = ast.generate()
            if actual.strip() != expected.strip(): # pragma: no cover
                diff = difflib.unified_diff(expected.splitlines(), actual.splitlines())
                print("\n".join(diff))
                raise AssertionError()
        except PrintableError as e: # pragma: no cover
            e.pretty_print(name + ".blp", blueprint)
            raise AssertionError()


    def assert_sample_error(self, name):
        try:
            with open((Path(__file__).parent / f"sample_errors/{name}.blp").resolve()) as f:
                blueprint = f.read()
            with open((Path(__file__).parent / f"sample_errors/{name}.err").resolve()) as f:
                expected = f.read()

            tokens = tokenizer.tokenize(blueprint)
            ast, errors, warnings = parser.parse(tokens)

            if errors:
                raise errors
            if len(ast.errors):
                raise MultipleErrors(ast.errors)
            if len(warnings):
                raise MultipleErrors(warnings)
        except PrintableError as e:
            def error_str(error):
                line, col = utils.idx_to_pos(error.start + 1, blueprint)
                len = error.end - error.start
                return ",".join([str(line + 1), str(col), str(len), error.message])

            if isinstance(e, CompileError):
                actual = error_str(e)
            elif isinstance(e, MultipleErrors):
                actual = "\n".join([error_str(error) for error in e.errors])
            else: # pragma: no cover
                raise AssertionError()

            if actual.strip() != expected.strip(): # pragma: no cover
                diff = difflib.unified_diff(expected.splitlines(), actual.splitlines())
                print("\n".join(diff))
                raise AssertionError()
        else: # pragma: no cover
            raise AssertionError("Expected a compiler error, but none was emitted")


    def assert_decompile(self, name):
        try:
            with open((Path(__file__).parent / f"samples/{name}.blp").resolve()) as f:
                expected = f.read()

            name = name.removesuffix("_dec")
            ui_path = (Path(__file__).parent / f"samples/{name}.ui").resolve()

            actual = decompiler.decompile(ui_path)

            if actual.strip() != expected.strip(): # pragma: no cover
                diff = difflib.unified_diff(expected.splitlines(), actual.splitlines())
                print("\n".join(diff))
                raise AssertionError()
        except PrintableError as e: # pragma: no cover
            e.pretty_print(name + ".blp", blueprint)
            raise AssertionError()


    def test_samples(self):
        self.assert_sample("accessibility")
        self.assert_sample("action_widgets")
        self.assert_sample("binding")
        self.assert_sample("child_type")
        self.assert_sample("combo_box_text")
        self.assert_sample("comments")
        self.assert_sample("enum")
        self.assert_sample("file_filter")
        self.assert_sample("flags")
        self.assert_sample("id_prop")
        self.assert_sample("layout")
        self.assert_sample("menu")
        self.assert_sample("object_prop")
        self.assert_sample("parseable")
        self.assert_sample("property")
        self.assert_sample("signal")
        self.assert_sample("size_group")
        self.assert_sample("string_list")
        self.assert_sample("strings")
        self.assert_sample("style")
        self.assert_sample("template")
        self.assert_sample("template_no_parent")
        self.assert_sample("translated")
        self.assert_sample("uint")
        self.assert_sample("using")


    def test_sample_errors(self):
        self.assert_sample_error("a11y_in_non_widget")
        self.assert_sample_error("a11y_prop_dne")
        self.assert_sample_error("a11y_prop_obj_dne")
        self.assert_sample_error("a11y_prop_type")
        self.assert_sample_error("action_widget_float_response")
        self.assert_sample_error("action_widget_have_no_id")
        self.assert_sample_error("action_widget_multiple_default")
        self.assert_sample_error("action_widget_not_action")
        self.assert_sample_error("action_widget_in_invalid_container")
        self.assert_sample_error("action_widget_response_dne")
        self.assert_sample_error("action_widget_negative_response")
        self.assert_sample_error("class_assign")
        self.assert_sample_error("class_dne")
        self.assert_sample_error("consecutive_unexpected_tokens")
        self.assert_sample_error("does_not_implement")
        self.assert_sample_error("duplicate_obj_id")
        self.assert_sample_error("enum_member_dne")
        self.assert_sample_error("filters_in_non_file_filter")
        self.assert_sample_error("invalid_bool")
        self.assert_sample_error("layout_in_non_widget")
        self.assert_sample_error("ns_not_imported")
        self.assert_sample_error("not_a_class")
        self.assert_sample_error("object_dne")
        self.assert_sample_error("obj_in_string_list")
        self.assert_sample_error("obj_prop_type")
        self.assert_sample_error("property_dne")
        self.assert_sample_error("signal_dne")
        self.assert_sample_error("signal_object_dne")
        self.assert_sample_error("size_group_non_widget")
        self.assert_sample_error("size_group_obj_dne")
        self.assert_sample_error("styles_in_non_widget")
        self.assert_sample_error("two_templates")
        self.assert_sample_error("uint")
        self.assert_sample_error("using_invalid_namespace")
        self.assert_sample_error("widgets_in_non_size_group")


    def test_decompiler(self):
        self.assert_decompile("accessibility_dec")
        self.assert_decompile("binding")
        self.assert_decompile("child_type")
        self.assert_decompile("file_filter")
        self.assert_decompile("flags")
        self.assert_decompile("id_prop")
        self.assert_decompile("layout_dec")
        self.assert_decompile("menu_dec")
        self.assert_decompile("property")
        self.assert_decompile("signal")
        self.assert_decompile("strings")
        self.assert_decompile("style_dec")
        self.assert_decompile("template")
        self.assert_decompile("translated")
        self.assert_decompile("using")
