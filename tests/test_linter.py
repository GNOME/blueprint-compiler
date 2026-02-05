# test_samples.py
#
# Copyright 2025 James Westman <james@jwestman.net>
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

from blueprintcompiler import utils
from blueprintcompiler.linter import lint
from blueprintcompiler.parser import parse
from blueprintcompiler.tokenizer import tokenize


class TestLinter(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    def test_linter_samples(self):
        self.check_file(
            "label_with_child",
            "number_of_children",
            [
                {"line": 7, "message": "Gtk.Label cannot have children"},
            ],
        )
        self.check_file(
            "number_of_children",
            "number_of_children",
            [
                {
                    "line": 10,
                    "message": "Adw.StatusPage cannot have more than one child",
                },
                {"line": 15, "message": "Adw.Clamp cannot have more than one child"},
                {
                    "line": 20,
                    "message": "Gtk.ScrolledWindow cannot have more than one child",
                },
            ],
        )
        self.check_file(
            "prefer_adw_bin",
            "use_adw_bin",
            [
                {
                    "line": 5,
                    "message": "Use Adw.Bin instead of a Gtk.Box for a single child",
                },
            ],
        )
        self.check_file(
            "translatable_display_string",
            "translate_display_string",
            [
                {
                    "line": 6,
                    "message": 'Mark Gtk.Label label as translatable using _("...")',
                }
            ],
        )
        self.check_file(
            "avoid_all_caps",
            "avoid_all_caps",
            [
                {
                    "line": 6,
                    "message": "Avoid using all upper case for Gtk.Label label",
                },
            ],
        )
        self.check_file(
            "no_visible_true",
            "visible_true",
            [
                {
                    "line": 6,
                    "message": "In GTK 4, widgets are visible by default, so this property is unnecessary",
                }
            ],
        )
        self.check_file(
            "no_gtk_switch_state",
            "gtk_switch_state",
            [
                {
                    "line": 6,
                    "message": "Use the active property instead of the state property",
                }
            ],
        )
        self.check_file(
            "require_a11y_label",
            "missing_descriptive_text",
            [
                {"line": 4, "message": "Gtk.Image is missing an accessibility label"},
                {"line": 8, "message": "Gtk.Button is missing an accessibility label"},
            ],
        )
        self.check_file(
            "prefer_unicode",
            "use_unicode",
            [
                {
                    "line": 7,
                    "message": "Prefer using an ellipsis (<…>, U+2026) instead of <...>",
                },
                {
                    "line": 11,
                    "message": "Prefer using an ellipsis (<…>, U+2026) instead of <...>",
                },
                {
                    "line": 15,
                    "message": "Prefer using an ellipsis (<…>, U+2026) instead of <....>",
                },
                {
                    "line": 19,
                    "message": "Prefer using a bullet (<•>, U+2022) instead of <*> at the start of a line",
                },
                {
                    "line": 19,
                    "message": "Prefer using a bullet (<•>, U+2022) instead of <*> at the start of a line",
                },
                {
                    "line": 19,
                    "message": "Prefer using a bullet (<•>, U+2022) instead of <*> at the start of a line",
                },
                {
                    "line": 23,
                    "message": "Prefer using a bullet (<•>, U+2022) instead of <-> at the start of a line",
                },
                {
                    "line": 23,
                    "message": "Prefer using a bullet (<•>, U+2022) instead of <-> at the start of a line",
                },
                {
                    "line": 23,
                    "message": "Prefer using a bullet (<•>, U+2022) instead of <-> at the start of a line",
                },
                {
                    "line": 27,
                    "message": 'Prefer using genuine quote marks (<“>, U+201C, and <”>, U+201D) instead of <">',
                },
                {
                    "line": 31,
                    "message": "Prefer using a right single quote (<’>, U+2019) instead of <'> to denote an apostrophe",
                },
                {
                    "line": 35,
                    "message": "Prefer using a right single quote (<’>, U+2019) instead of <'> to denote an apostrophe",
                },
                {
                    "line": 39,
                    "message": "Prefer using a multiplication sign (<×>, U+00D7), instead of <x>",
                },
                {
                    "line": 43,
                    "message": "Prefer using a multiplication sign (<×>, U+00D7), instead of <x>",
                },
                {
                    "line": 47,
                    "message": "Prefer using a multiplication sign (<×>, U+00D7), instead of <x>",
                },
                {
                    "line": 47,
                    "message": "When a number is displayed with units, the two should be separated by a narrow no-break space (< >, U+202F)",
                },
                {
                    "line": 47,
                    "message": "When a number is displayed with units, the two should be separated by a narrow no-break space (< >, U+202F)",
                },
                {
                    "line": 51,
                    "message": "Prefer using a multiplication sign (<×>, U+00D7), instead of <x>",
                },
                {
                    "line": 55,
                    "message": "Prefer using a multiplication sign (<×>, U+00D7), instead of <x>",
                },
            ],
        )
        self.check_file(
            "use_styles_over_css_classes",
            "use_styles",
            [{"line": 9, "message": "Avoid using css-classes. Use styles[] instead."}],
        )
        self.check_file(
            "scrollable_parent",
            "scrollable_parent",
            [
                {
                    "line": 6,
                    "message": "Scrollable widget should be placed in a scroll container",
                },
            ],
        )
        self.check_file(
            "missing_user_facing_properties",
            "missing_user_facing_text",
            [
                {
                    "line": 5,
                    "message": "Gtk.Label is missing required user-facing text property",
                },
            ],
        )
        self.check_file(
            "incorrect_widget_placement",
            "wrong_parent",
            [
                {"line": 6, "message": "Gtk.StackPage must be a child of a Gtk.Stack"},
                {
                    "line": 9,
                    "message": "Gtk.StackPage must be a child of a Gtk.Stack",
                },
            ],
        )
        self.check_file(
            "order_properties_gtk_adjustment",
            "adjustment_prop_order",
            [
                {
                    "line": 7,
                    "message": "Gtk.Adjustment properties should be ordered as lower, upper, and then value.",
                },
                {
                    "line": 16,
                    "message": "Gtk.Adjustment properties should be ordered as lower, upper, and then value.",
                },
                {
                    "line": 25,
                    "message": "Gtk.Adjustment properties should be ordered as lower, upper, and then value.",
                },
            ],
        )
        self.check_file(
            "unused_object",
            "unused_object",
            [
                {
                    "line": 4,
                    "message": "Gtk.Label is unused because it has no ID and no parent",
                }
            ],
        )

    def check_file(self, name, rule_id, expected_problems):
        with self.subTest("linter/" + name):
            print(f"assert_linter({name})")

            filepath = Path(__file__).parent.joinpath("linter_samples", f"{name}.blp")

            with open(filepath, "r+") as file:
                code = file.read()
                tokens = tokenize(code)
                ast, errors, warnings = parse(tokens)

                if errors:
                    raise errors

                problems = lint(ast, rule_ids=[rule_id])
                self.assertEqual(len(problems), len(expected_problems))

                for actual, expected in zip(problems, expected_problems):
                    line_num, col_num = utils.idx_to_pos(actual.range.start + 1, code)
                    self.assertEqual(line_num + 1, expected["line"])
                    self.assertEqual(actual.message, expected["message"])
