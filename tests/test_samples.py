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


import unittest
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from blueprintcompiler import decompiler, parser, tokenizer, utils
from blueprintcompiler.completions import complete
from blueprintcompiler.errors import (
    CompileError,
    DeprecatedWarning,
    MultipleErrors,
    PrintableError,
)
from blueprintcompiler.lsp import LanguageServer
from blueprintcompiler.outputs.xml import XmlOutput
from blueprintcompiler.tokenizer import Token, TokenType, tokenize


class TestSamples(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

        self.have_adw_1_4 = False
        self.have_adw_1_5 = False

        try:
            import gi

            gi.require_version("Adw", "1")
            from gi.repository import Adw

            Adw.init()
            if Adw.MINOR_VERSION >= 4:
                self.have_adw_1_4 = True
            if Adw.MINOR_VERSION >= 5:
                self.have_adw_1_5 = True
        except:
            pass

    def assert_ast_doesnt_crash(self, text, tokens, ast):
        for i in range(len(text)):
            ast.get_docs(i)
        for i in range(len(text)):
            list(complete(LanguageServer(), ast, tokens, i))
        ast.get_document_symbols()

    def assert_sample(self, name, skip_run=False):
        print(f'assert_sample("{name}", skip_run={skip_run})')
        try:
            with open((Path(__file__).parent / f"samples/{name}.blp").resolve()) as f:
                blueprint = f.read()
            with open((Path(__file__).parent / f"samples/{name}.ui").resolve()) as f:
                expected = f.read()

            tokens = tokenizer.tokenize(blueprint)
            ast, errors, warnings = parser.parse(tokens)

            # Ignore deprecation warnings because some of the things we're testing
            # are deprecated
            warnings = [
                warning
                for warning in warnings
                if not isinstance(warning, DeprecatedWarning)
            ]

            if errors:
                raise errors
            if len(warnings):
                raise MultipleErrors(warnings)

            xml = XmlOutput()
            actual = xml.emit(ast)
            self.assertEqual(actual.strip(), expected.strip())

            self.assert_ast_doesnt_crash(blueprint, tokens, ast)
        except PrintableError as e:  # pragma: no cover
            e.pretty_print(name + ".blp", blueprint)
            raise AssertionError()

        # Make sure the sample runs
        if not skip_run:
            Gtk.Builder.new_from_string(actual, -1)

    def assert_sample_error(self, name):
        print(f'assert_sample_error("{name}")')
        try:
            with open(
                (Path(__file__).parent / f"sample_errors/{name}.blp").resolve()
            ) as f:
                blueprint = f.read()
            with open(
                (Path(__file__).parent / f"sample_errors/{name}.err").resolve()
            ) as f:
                expected = f.read()

            tokens = tokenizer.tokenize(blueprint)
            ast, errors, warnings = parser.parse(tokens)

            if ast is not None:
                self.assert_ast_doesnt_crash(blueprint, tokens, ast)

            if errors:
                raise errors
            if len(ast.errors):
                raise MultipleErrors(ast.errors)
            if len(warnings):
                raise MultipleErrors(warnings)
        except PrintableError as e:

            def error_str(error: CompileError):
                line, col = utils.idx_to_pos(error.range.start + 1, blueprint)
                len = error.range.length
                return ",".join([str(line + 1), str(col), str(len), error.message])

            if isinstance(e, CompileError):
                actual = error_str(e)
            elif isinstance(e, MultipleErrors):
                actual = "\n".join([error_str(error) for error in e.errors])
            else:  # pragma: no cover
                raise AssertionError()

            self.assertEqual(actual.strip(), expected.strip())
        else:  # pragma: no cover
            raise AssertionError("Expected a compiler error, but none was emitted")

    def assert_decompile(self, name):
        print(f'assert_decompile("{name}")')
        try:
            with open((Path(__file__).parent / f"samples/{name}.blp").resolve()) as f:
                expected = f.read()

            name = name.removesuffix("_dec")
            ui_path = (Path(__file__).parent / f"samples/{name}.ui").resolve()

            actual = decompiler.decompile(ui_path)

            self.assertEqual(actual.strip(), expected.strip())
        except PrintableError as e:  # pragma: no cover
            e.pretty_print(name + ".blp", blueprint)
            raise AssertionError()

    def test_samples(self):
        # list the samples directory
        samples = [
            f.stem
            for f in Path(__file__).parent.glob("samples/*.blp")
            if not f.stem.endswith("_dec")
        ]
        samples.sort()
        for sample in samples:
            REQUIRE_ADW_1_4 = ["adw_breakpoint"]
            REQUIRE_ADW_1_5 = ["adw_alertdialog_responses"]

            SKIP_RUN = [
                "adw_breakpoint_template",
                "expr_closure",
                "expr_closure_args",
                "parseable",
                "signal",
                "template",
                "template_binding",
                "template_binding_extern",
                "template_bind_property",
                "template_id",
                "template_no_parent",
                "template_orphan",
                "template_simple_binding",
                "typeof",
                "unchecked_class",
            ]

            if sample in REQUIRE_ADW_1_4 and not self.have_adw_1_4:
                continue
            if sample in REQUIRE_ADW_1_5 and not self.have_adw_1_5:
                continue

            with self.subTest(sample):
                self.assert_sample(sample, skip_run=sample in SKIP_RUN)

        # list the sample_errors directory
        sample_errors = [
            f.stem for f in Path(__file__).parent.glob("sample_errors/*.blp")
        ]
        sample_errors.sort()
        for sample_error in sample_errors:
            REQUIRE_ADW_1_4 = ["adw_breakpoint"]
            REQUIRE_ADW_1_5 = ["adw_alert_dialog_duplicate_flags"]

            if sample_error in REQUIRE_ADW_1_4 and not self.have_adw_1_4:
                continue
            if sample_error in REQUIRE_ADW_1_5 and not self.have_adw_1_5:
                continue

            with self.subTest(sample_error):
                self.assert_sample_error(sample_error)

    def test_decompiler(self):
        self.assert_decompile("accessibility_dec")
        if self.have_adw_1_5:
            self.assert_decompile("adw_alertdialog_responses")
        self.assert_decompile("adw_messagedialog_responses")
        self.assert_decompile("child_type")
        self.assert_decompile("file_filter")
        self.assert_decompile("flags")
        self.assert_decompile("id_prop")
        self.assert_decompile("layout_dec")
        self.assert_decompile("menu_dec")
        self.assert_decompile("property")
        self.assert_decompile("property_binding_dec")
        self.assert_decompile("placeholder_dec")
        self.assert_decompile("scale_marks")
        self.assert_decompile("signal")
        self.assert_decompile("strings_dec")
        self.assert_decompile("style_dec")
        self.assert_decompile("template")
        self.assert_decompile("template_orphan")
        self.assert_decompile("translated")
        self.assert_decompile("using")
        self.assert_decompile("unchecked_class_dec")
