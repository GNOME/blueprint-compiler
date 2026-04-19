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


import os
import unittest
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from blueprintcompiler import decompiler, parser, tokenizer, utils
from blueprintcompiler.ast_utils import AstNode
from blueprintcompiler.completions import complete
from blueprintcompiler.errors import (
    CompileError,
    DeprecatedWarning,
    MultipleErrors,
    PrintableError,
)
from blueprintcompiler.linter import lint
from blueprintcompiler.lsp import LanguageServer
from blueprintcompiler.outputs.xml import XmlOutput


class TestSamples(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

        self.have_adw_1_4 = False
        self.have_adw_1_5 = False
        self.have_gtk_22 = False

        try:
            import gi

            gi.require_version("Adw", "1")
            gi.require_version("Gtk", "4.0")
            from gi.repository import Adw

            Adw.init()
            if Adw.MINOR_VERSION >= 4:
                self.have_adw_1_4 = True
            if Adw.MINOR_VERSION >= 5:
                self.have_adw_1_5 = True
            if Gtk.MINOR_VERSION >= 22:
                self.have_gtk_22 = True
        except:
            pass

    def assert_ast_doesnt_crash(self, text, tokens, ast: AstNode):
        lsp = LanguageServer()
        for i in range(len(text) + 1):
            ast.get_docs(i)
        for i in range(len(text) + 1):
            list(complete(lsp, ast, tokens, i))
        for i in range(len(text) + 1):
            ast.get_reference(i)
        ast.get_document_symbols()
        lint(ast)

    def assert_sample(self, name: str, skip_run=False):
        print(f'assert_sample("{name}", skip_run={skip_run})')
        try:
            with open((Path(__file__).parent / f"samples/{name}.blp").resolve()) as f:
                blueprint = f.read()
            with open((Path(__file__).parent / f"samples/{name}.ui").resolve()) as f:
                expected = f.read()

            tokens = tokenizer.tokenize(blueprint)
            ast, errors, warnings = parser.parse(tokens, blpx=name.startswith("blpx_"))

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
            builder = Gtk.Builder()
            builder.set_scope(builder_scope)
            builder.add_from_string(expected)

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
            # Ignore deprecation warnings because new versions of libraries can introduce
            # new deprecations, which would cause the tests to fail
            errors = [
                error
                for error in (e.errors if isinstance(e, MultipleErrors) else [e])
                if (name == "deprecations" or not isinstance(error, DeprecatedWarning))
            ]

            def error_str(error: CompileError):
                line, col = utils.idx_to_pos(error.range.start + 1, blueprint)
                len = error.range.length
                return ",".join([str(line + 1), str(col), str(len), error.message])

            actual = "\n".join([error_str(error) for error in errors])

            self.assertEqual(actual.strip(), expected.strip())
        else:  # pragma: no cover
            raise AssertionError("Expected a compiler error, but none was emitted")

    def assert_decompile(self, name):
        print(f'assert_decompile("{name}")')
        try:
            if os.path.exists(
                (Path(__file__).parent / f"samples/{name}_dec.blp").resolve()
            ):
                with open(
                    (Path(__file__).parent / f"samples/{name}_dec.blp").resolve()
                ) as f:
                    expected = f.read().strip()
            else:
                with open(
                    (Path(__file__).parent / f"samples/{name}.blp").resolve()
                ) as f:
                    expected = f.read().strip()

            name = name.removesuffix("_dec")
            ui_path = (Path(__file__).parent / f"samples/{name}.ui").resolve()

            ast, errors, warnings, actual = decompiler.decompile(ui_path)

            self.assertEqual(actual.strip(), expected)
        except PrintableError as e:  # pragma: no cover
            e.pretty_print(name + ".blp", expected)
            raise AssertionError()

    def test_samples(self):
        # list the samples directory
        samples = [f.stem for f in Path(__file__).parent.glob("samples/*.blp")]
        samples.sort()
        for sample in samples:
            REQUIRE_ADW_1_4 = ["adw_breakpoint"]
            REQUIRE_ADW_1_5 = [
                "adw_alertdialog_responses",
                "adw_alert_dialog_duplicate_flags",
            ]
            REQUIRE_GTK_22 = ["expr_try", "expr_null", "expr_null_infer_type"]

            SKIP_RUN = [
                "adw_breakpoint_template",
                "expr_closure",
                "expr_closure_inferred_type",
                "expr_closure_args",
                "expr_null",
                "expr_null_infer_type",
                "expr_translated",
                "expr_try",
                "expr_value_closure",
                "extern_class_with_namespace",
                "extern_enum",
                "issue_221",
                "parseable",
                "signal",
                "signal_not_swapped",
                "signal_template_object",
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

            # Decompiler-only tests
            SKIP_COMPILE = ["issue_177", "issue_187", "translator_comments"]

            SKIP_DECOMPILE = [
                # Comments are not preserved in either direction
                "comments",
            ]

            if sample in REQUIRE_ADW_1_4 and not self.have_adw_1_4:  # pragma: no cover
                continue
            if sample in REQUIRE_ADW_1_5 and not self.have_adw_1_5:  # pragma: no cover
                continue
            if sample in REQUIRE_GTK_22 and not self.have_gtk_22:
                continue

            with self.subTest(sample):
                if sample not in SKIP_COMPILE and not sample.endswith("_dec"):
                    self.assert_sample(sample, skip_run=sample in SKIP_RUN)

            with self.subTest("decompile/" + sample):
                if sample not in SKIP_DECOMPILE:
                    self.assert_decompile(sample)

        # list the sample_errors directory
        sample_errors = [
            f.stem for f in Path(__file__).parent.glob("sample_errors/*.blp")
        ]
        sample_errors.sort()
        for sample_error in sample_errors:
            if (
                sample_error in REQUIRE_ADW_1_4 and not self.have_adw_1_4
            ):  # pragma: no cover
                continue
            if (
                sample_error in REQUIRE_ADW_1_5 and not self.have_adw_1_5
            ):  # pragma: no cover
                continue

            with self.subTest(sample_error):
                self.assert_sample_error(sample_error)


class BuilderScope(Gtk.BuilderCScope):
    __gtype_name__ = "BlpBuilderScope"

    def __init__(self):
        super().__init__()

        for type in ("string", "float", "double", "int64", "uint64", "int", "uint"):
            setattr(self, f"blpx_eq_{type}", lambda this, a, b: a == b)
            setattr(self, f"blpx_ne_{type}", lambda this, a, b: a != b)
            setattr(self, f"blpx_lt_{type}", lambda this, a, b: a < b)
            setattr(self, f"blpx_le_{type}", lambda this, a, b: a <= b)
            setattr(self, f"blpx_gt_{type}", lambda this, a, b: a > b)
            setattr(self, f"blpx_ge_{type}", lambda this, a, b: a >= b)
            setattr(self, f"blpx_add_{type}", lambda this, a, b: a + b)
            if type != "string":
                setattr(self, f"blpx_sub_{type}", lambda this, a, b: a - b)
                setattr(self, f"blpx_mul_{type}", lambda this, a, b: a * b)
                setattr(self, f"blpx_div_{type}", lambda this, a, b: a / b)
                setattr(self, f"blpx_mod_{type}", lambda this, a, b: a % b)

    def blpx_or(self, this, a, b):
        return a or b

    def blpx_and(self, this, a, b):
        return a and b

    def blpx_if(self, this, condition, then_branch, else_branch):
        return then_branch if condition else else_branch

    def blpx_not(self, this, value):
        return not value

    def do_create_closure(
        self,
        builder: Gtk.Builder,
        function_name: str,
        flags: Gtk.BuilderClosureFlags,
        object,
    ):
        return getattr(self, function_name, None)


builder_scope = BuilderScope()
