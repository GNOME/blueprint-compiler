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

user_facing_text_checks = [
    (6, "Gtk.Label", "label"),
    (9, "Gtk.Button", "label"),
    (12, "Gtk.Window", "title"),
    (15, "Gtk.CheckButton", "label"),
    (18, "Gtk.Expander", "label"),
    (21, "Gtk.Frame", "label"),
    (24, "Gtk.MenuButton", "label"),
    (27, "Gtk.Entry", "placeholder-text"),
    (30, "Gtk.PasswordEntry", "placeholder-text"),
    (33, "Gtk.SearchEntry", "placeholder-text"),
    (36, "Gtk.Entry", "primary-icon-tooltip-markup"),
    (39, "Gtk.Entry", "primary-icon-tooltip-text"),
    (42, "Gtk.Entry", "secondary-icon-tooltip-markup"),
    (45, "Gtk.Entry", "secondary-icon-tooltip-text"),
    (48, "Gtk.EntryBuffer", "text"),
    (51, "Gtk.ListItem", "accessible-description"),
    (54, "Gtk.ListItem", "accessible-label"),
    (57, "Gtk.AlertDialog", "message"),
    (60, "Gtk.AppChooserButton", "heading"),
    (63, "Gtk.AppChooserDialog", "heading"),
    (66, "Gtk.AppChooserWidget", "default-text"),
    (69, "Gtk.AssistantPage", "title"),
    (72, "Gtk.CellRendererText", "markup"),
    (75, "Gtk.CellRendererText", "text"),
    (78, "Gtk.ColorButton", "title"),
    (81, "Gtk.ColorDialog", "title"),
    (84, "Gtk.ColumnViewColumn", "title"),
    (87, "Gtk.ColumnViewRow", "accessible-description"),
    (90, "Gtk.ColumnViewRow", "accessible-label"),
    (93, "Gtk.FileChooserNative", "accept-label"),
    (96, "Gtk.FileChooserNative", "cancel-label"),
    (99, "Gtk.FileDialog", "accept-label"),
    (102, "Gtk.FileDialog", "title"),
    (105, "Gtk.FileDialog", "initial-name"),
    (108, "Gtk.FileFilter", "name"),
    (111, "Gtk.FontButton", "title"),
    (114, "Gtk.FontDialog", "title"),
    (117, "Gtk.Inscription", "markup"),
    (120, "Gtk.Inscription", "text"),
    (123, "Gtk.LockButton", "text-lock"),
    (126, "Gtk.LockButton", "text-unlock"),
    (129, "Gtk.LockButton", "tooltip-lock"),
    (132, "Gtk.LockButton", "tooltip-not-authorized"),
    (135, "Gtk.LockButton", "tooltip-unlock"),
    (138, "Gtk.MessageDialog", "text"),
    (141, "Gtk.NotebookPage", "menu-label"),
    (144, "Gtk.NotebookPage", "tab-label"),
    (147, "Gtk.PrintDialog", "accept-label"),
    (150, "Gtk.PrintDialog", "title"),
    (153, "Gtk.Printer", "name"),
    (156, "Gtk.PrintJob", "title"),
    (159, "Gtk.PrintOperation", "custom-tab-label"),
    (162, "Gtk.PrintOperation", "export-filename"),
    (165, "Gtk.PrintOperation", "job-name"),
    (168, "Gtk.ProgressBar", "text"),
    (171, "Gtk.ShortcutLabel", "disabled-text"),
    (174, "Gtk.ShortcutsGroup", "title"),
    (177, "Gtk.ShortcutsSection", "title"),
    (180, "Gtk.ShortcutsShortcut", "title"),
    (183, "Gtk.ShortcutsShortcut", "subtitle"),
    (186, "Gtk.StackPage", "title"),
    (189, "Gtk.Text", "placeholder-text"),
    (192, "Gtk.TextBuffer", "text"),
    (195, "Gtk.TreeViewColumn", "title"),
    (198, "Adw.Dialog", "title"),
    (201, "Adw.PreferencesGroup", "description"),
    (204, "Adw.PreferencesGroup", "title"),
    (207, "Adw.PreferencesPage", "description"),
    (210, "Adw.PreferencesPage", "title"),
    (213, "Adw.PreferencesRow", "title"),
    (216, "Adw.SplitButton", "dropdown-tooltip"),
    (219, "Adw.SplitButton", "label"),
    (222, "Adw.StatusPage", "description"),
    (225, "Adw.StatusPage", "title"),
    (228, "Adw.TabPage", "indicator-tooltip"),
    (231, "Adw.TabPage", "keyword"),
    (234, "Adw.TabPage", "title"),
    (237, "Adw.Toast", "button-label"),
    (240, "Adw.Toast", "title"),
    (243, "Adw.ViewStackPage", "title"),
    (246, "Adw.ViewSwitcherTitle", "subtitle"),
    (249, "Adw.ViewSwitcherTitle", "title"),
    (252, "Adw.WindowTitle", "subtitle"),
    (255, "Adw.WindowTitle", "title"),
]


class TestLinter(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    def test_linter_samples(self):
        self.check_file(
            "label_with_child",
            [{"line": 7, "message": "Gtk.Label cannot have children"}],
        )
        self.check_file(
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
            [
                {
                    "line": 6,
                    "message": "Use Adw.Bin instead of a Gtk.Box for a single child",
                }
            ],
        )
        self.check_file(
            "translatable_display_string",
            [
                {
                    "line": line,
                    "message": f'Mark {toolkit} {properties} as translatable using _("...")',
                }
                for line, toolkit, properties in user_facing_text_checks
            ]
            + [
                {
                    "line": 258,
                    "message": 'Mark Gtk.Picture alternative-text as translatable using _("...")',
                },
                {
                    "line": 257,
                    "message": "Gtk.Picture is missing an accessibility label",
                },
            ],
        )
        self.check_file(
            "avoid_all_caps",
            [
                {
                    "line": line,
                    "message": f"Avoid using all upper case for {toolkit} {properties}",
                }
                for line, toolkit, properties in user_facing_text_checks
            ]
            + [
                {
                    "line": 257,
                    "message": "Gtk.Picture is missing an accessibility label",
                },
                {
                    "line": 258,
                    "message": "Avoid using all upper case for Gtk.Picture alternative-text",
                },
                {
                    "line": 261,
                    "message": 'Mark Gtk.Button label as translatable using _("...")',
                },
                {
                    "line": 261,
                    "message": "Avoid using all upper case for Gtk.Button label",
                },
            ],
        )
        self.check_file(
            "no_visible_true",
            [{"line": 6, "message": "In GTK4 widgets are visible by default"}],
        )
        self.check_file(
            "no_gtk_switch_state",
            [
                {
                    "line": 6,
                    "message": "Use the active property instead of the state property",
                }
            ],
        )
        self.check_file(
            "require_a11y_label",
            [
                {"line": 5, "message": "Gtk.Image is missing an accessibility label"},
                {"line": 8, "message": "Gtk.Button is missing an accessibility label"},
            ],
        )
        self.check_file(
            "prefer_unicode",
            [
                {
                    "line": 7,
                    "message": "Prefer using an ellipsis (<…>, U+2026) instead of <...> in <hello...>",
                },
                {
                    "line": 11,
                    "message": "Prefer using an ellipsis (<…>, U+2026) instead of <...> in <hello...>",
                },
                {
                    "line": 15,
                    "message": 'Mark Gtk.Button label as translatable using _("...")',
                },
                {
                    "line": 15,
                    "message": "Prefer using an ellipsis (<…>, U+2026) instead of <...> in <times...>",
                },
                {
                    "line": 19,
                    "message": "Prefer using a bullet (<•>, U+2022) instead of <*> at the start of a line in <* one>",
                },
                {
                    "line": 19,
                    "message": "Prefer using a bullet (<•>, U+2022) instead of <*> at the start of a line in <* two>",
                },
                {
                    "line": 19,
                    "message": "Prefer using a bullet (<•>, U+2022) instead of <*> at the start of a line in <* three>",
                },
                {
                    "line": 23,
                    "message": "Prefer using a bullet (<•>, U+2022) instead of <-> at the start of a line in <  - one>",
                },
                {
                    "line": 23,
                    "message": "Prefer using a bullet (<•>, U+2022) instead of <-> at the start of a line in <  - two>",
                },
                {
                    "line": 23,
                    "message": "Prefer using a bullet (<•>, U+2022) instead of <-> at the start of a line in <  - three>",
                },
                {
                    "line": 27,
                    "message": 'Prefer using genuine quote marks (<“>, U+201C, and <”>, U+201D) instead of <"> in <"what?">',
                },
                {
                    "line": 31,
                    "message": "Prefer using a right single quote (<’>, U+2019) instead of <'> to denote an apostrophe in <printer's>",
                },
                {
                    "line": 35,
                    "message": "Prefer using a right single quote (<’>, U+2019) instead of <'> to denote an apostrophe in <kings'>",
                },
                {
                    "line": 39,
                    "message": "Prefer using a multiplication sign (<×>, U+00D7), instead of <x> in <1920x1080>",
                },
                {
                    "line": 43,
                    "message": "Prefer using a multiplication sign (<×>, U+00D7), instead of <x> in <1920 x 1080>",
                },
                {
                    "line": 47,
                    "message": "Prefer using a multiplication sign (<×>, U+00D7), instead of <x> in <6in x 4in>",
                },
                {
                    "line": 47,
                    "message": "When a number is displayed with units, e.g. <6in>, the two should be separated by a narrow no-break space (< >, U+202F)",
                },
                {
                    "line": 47,
                    "message": "When a number is displayed with units, e.g. <4in>, the two should be separated by a narrow no-break space (< >, U+202F)",
                },
                {
                    "line": 51,
                    "message": 'Prefer using a multiplication sign (<×>, U+00D7), instead of <x> in <6" x 4">',
                },
                {
                    "line": 55,
                    "message": "Prefer using a multiplication sign (<×>, U+00D7), instead of <x> in <10x>",
                },
                {
                    "line": 55,
                    "message": "When a number is displayed with units, e.g. <10x>, the two should be separated by a narrow no-break space (< >, U+202F)",
                },
            ],
        )
        # This creates error messages for the unique elements
        unique_elements = set()
        line = 5
        results = []
        for _, toolkit, _ in user_facing_text_checks:
            if toolkit not in unique_elements:
                results.append(
                    {
                        "line": line,
                        "message": f"{toolkit} is missing required user-facing text property",
                    }
                )
                unique_elements.add(toolkit)
                line += 3
        results.insert(
            1, {"line": 8, "message": "Gtk.Button is missing an accessibility label"}
        )
        self.check_file(
            "missing_user_facing_properties",
            results
            + [
                {
                    "line": 170,
                    "message": "Gtk.Picture is missing an accessibility label",
                },
                {
                    "line": 170,
                    "message": "Gtk.Picture is missing required user-facing text property",
                },
            ],
        )

    def check_file(self, name, expected_problems):
        filepath = Path(__file__).parent.joinpath("linter_samples", f"{name}.blp")

        with open(filepath, "r+") as file:
            code = file.read()
            tokens = tokenize(code)
            ast, errors, warnings = parse(tokens)

            if errors:
                raise errors

            problems = lint(ast)
            self.assertEqual(len(problems), len(expected_problems))

            for actual, expected in zip(problems, expected_problems):
                line_num, col_num = utils.idx_to_pos(actual.range.start + 1, code)
                self.assertEqual(line_num + 1, expected["line"])
                self.assertEqual(actual.message, expected["message"])
