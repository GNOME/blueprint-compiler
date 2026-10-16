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
from gi.repository import GObject, Gtk

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
from blueprintcompiler.utils import CompilerOptions, ExpressionFormat


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
            if Adw.MINOR_VERSION >= 4:  # pragma: no cover
                self.have_adw_1_4 = True
            if Adw.MINOR_VERSION >= 5:  # pragma: no cover
                self.have_adw_1_5 = True
            if Gtk.MINOR_VERSION >= 22:  # pragma: no cover
                self.have_gtk_22 = True
        except:  # pragma: no cover
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

    def compile(self, blueprint: str, expressions: ExpressionFormat | None):
        tokens = tokenizer.tokenize(blueprint)
        ast, errors, warnings = parser.parse(
            tokens, opts=CompilerOptions(expressions=expressions)
        )

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

        return tokens, ast, actual

    def assert_sample(self, name: str, skip_run=False):
        try:
            with open((Path(__file__).parent / f"samples/{name}.blp").resolve()) as f:
                blueprint = f.read()
            with open((Path(__file__).parent / f"samples/{name}.ui").resolve()) as f:
                expected = f.read()

            tokens, ast, actual = self.compile(
                blueprint,
                expressions=ExpressionFormat.BLPX if name.startswith("blpx_") else None,
            )
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
        try:
            with open(
                (Path(__file__).parent / f"sample_errors/{name}.blp").resolve()
            ) as f:
                blueprint = f.read()
            with open(
                (Path(__file__).parent / f"sample_errors/{name}.err").resolve()
            ) as f:
                expected = f.read()

            blpx = name.startswith("blpx_")

            tokens = tokenizer.tokenize(blueprint)
            ast, errors, warnings = parser.parse(
                tokens,
                opts=CompilerOptions(
                    expressions=ExpressionFormat.BLPX if blpx else None
                ),
            )

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
                line, col = error.range.source.idx_to_pos(error.range.start + 1)
                len = error.range.length
                return ",".join([str(line + 1), str(col), str(len), error.message])

            actual = "\n".join([error_str(error) for error in errors])

            self.assertEqual(actual.strip(), expected.strip())
        else:  # pragma: no cover
            raise AssertionError("Expected a compiler error, but none was emitted")

    def assert_decompile(self, name):
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

            self.assertEqual(actual.text.strip(), expected)
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

    def test_expressions(self):
        dynamic_scope = BuilderScope(dynamic=True)

        def assert_expr(self, expr: str, expressions: ExpressionFormat | None):
            blueprint = f"""
                using Gtk 4.0;

                $Assertion assertion {{
                    value: bind {expr};
                }}
            """

            try:
                tokens, ast, actual = self.compile(blueprint, expressions=expressions)
            except PrintableError as e:  # pragma: no cover
                e.pretty_print(expr, blueprint)
                raise AssertionError()

            builder = Gtk.Builder()
            builder.set_scope(
                dynamic_scope
                if expressions == ExpressionFormat.BLPX_DYNAMIC
                else builder_scope
            )
            builder.add_from_string(actual)
            assertion = builder.get_object("assertion")
            self.assertTrue(assertion.props.value)

        for expr in [
            "1 + 2 == 3",
            "1 + 2 * 3 == 7",
            "(1 + 2) * 3 == 9",
            "1.5 + 2.5 == 4.0",
            '"foo" + "bar" == "foobar"',
            "true && true",
            "true || false",
            "!false",
            "if false { false } elif 3 > 1 { true } else { false }",
            "1_000_000_000_000 > 999_999_999_999",
            "-1_000_000_000_000 < -999_999_999_999",
            "1.5 + 1.5 == 3",
            "true != false",
            "assertion == assertion",
            "!(assertion != assertion)",
        ]:
            with self.subTest("static " + expr):
                assert_expr(self, expr, expressions=ExpressionFormat.BLPX)
            with self.subTest("dynamic " + expr):
                assert_expr(self, expr, expressions=ExpressionFormat.BLPX_DYNAMIC)


class BuilderScope(Gtk.BuilderCScope):
    __gtype_name__ = "BlpBuilderScope"

    def __init__(self, dynamic: bool = False):
        super().__init__()

        numeric_types = [
            "float",
            "double",
            "int64",
            "uint64",
            "int",
            "uint",
        ]

        def add_func(name, func, types):
            f = lambda this, *args: func(*args)
            if dynamic:
                setattr(self, f"blpx_{name}", f)
            else:
                for t in types:
                    setattr(self, f"blpx_{name}_{t}", f)

        add_func(
            "if",
            lambda condition, a, b: a if condition else b,
            ["string", "ptr", "bool", *numeric_types],
        )
        add_func("eq", lambda a, b: a == b, ["string", "bool", "ptr", *numeric_types])
        add_func("ne", lambda a, b: a != b, ["string", "bool", "ptr", *numeric_types])
        add_func("lt", lambda a, b: a < b, numeric_types)
        add_func("le", lambda a, b: a <= b, numeric_types)
        add_func("gt", lambda a, b: a > b, numeric_types)
        add_func("ge", lambda a, b: a >= b, numeric_types)
        add_func("add", lambda a, b: a + b, ["string", *numeric_types])
        add_func("sub", lambda a, b: a - b, numeric_types)
        add_func("neg", lambda a: -a, numeric_types)
        add_func("mul", lambda a, b: a * b, numeric_types)
        add_func("div", lambda a, b: a / b, numeric_types)
        add_func("mod", lambda a, b: a % b, numeric_types)

        def add_cast(type_a, type_bs):
            if not dynamic:
                for type_b in type_bs:
                    setattr(
                        self, f"blpx_cast_{type_a}_{type_b}", lambda this, value: value
                    )

        add_cast("int64", ["uint64", "double"])
        add_cast("uint64", ["int64", "double"])
        add_cast("int", ["int64", "double"])
        add_cast("uint", ["uint64", "double"])
        add_cast("float", ["double"])
        for numeric_type in numeric_types:
            add_cast(numeric_type, numeric_types)

    def blpx_or(self, this, a, b):
        return a or b

    def blpx_and(self, this, a, b):
        return a and b

    def blpx_not(self, this, value):
        return not value

    def do_create_closure(
        self,
        builder: Gtk.Builder,
        function_name: str,
        flags: Gtk.BuilderClosureFlags,
        object,
    ):
        f = getattr(self, function_name, None)
        if function_name.startswith("blpx_") and f is None:  # pragma: no cover
            raise AttributeError(f"Closure function '{function_name}' not found")

        return f


builder_scope = BuilderScope()


class Assertion(GObject.Object):
    __gtype_name__ = "Assertion"

    @GObject.Property(type=bool, default=False)
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = val
