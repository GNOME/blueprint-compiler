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
        self.check_file('label_with_child', [
            { 'line': 6, 'message': 'Gtk.Label cannot have children' }
        ])
        self.check_file('number_of_children', [
            { 'line': 8, 'message': 'Adw.StatusPage cannot have more than one child' }
        ])
        self.check_file('prefer_adw_bin', [
            { 'line': 6, 'message': 'Use Adw.Bin instead of a Gtk.Box for a single child' }
        ])
        self.check_file('translatable_display_string', [
            { 'line': 6, 'message': 'Mark Gtk.Label label as translatable using _("...")' },
            { 'line': 9, 'message': 'Mark Gtk.Button tooltip-text as translatable using _("...")' },
            { 'line': 12, 'message': 'Mark Gtk.Window title as translatable using _("...")' }
        ])
        self.check_file('avoid_all_caps', [
            { 'line': 6, 'message': 'Avoid using all upper case for Gtk.Label label' },
            { 'line': 9, 'message': 'Avoid using all upper case for Gtk.Button label' }
            # { 'line': 13, 'message': 'Avoid using all upper case for Gtk.Button label' }
        ])
        self.check_file('no_visible_true', [
            { 'line': 6, 'message': 'In GTK4 widgets are visible by default' }
        ])
        self.check_file('no_gtk_switch_state', [
            { 'line': 6, 'message': 'Use the active property instead of the state property' }
        ])
        self.check_file('require_a11y_label', [
            { 'line': 5, 'message': 'Gtk.Image is missing an accessibility label' },
            { 'line': 8, 'message': 'Gtk.Button is missing an accessibility label' }
        ])

    def check_file(self, name, expected_problems):
        filepath = Path(__file__).parent.joinpath('linter_samples', f'{name}.blp')

        with open(filepath, "r+") as file:
            code = file.read()
            tokens = tokenize(code)
            ast, errors, warnings = parse(tokens)

            if errors:
                raise errors

            problems = lint(ast)
            self.assertEqual(len(problems), len(expected_problems))

            for (actual, expected) in zip(problems, expected_problems):
                line_num, col_num = utils.idx_to_pos(actual.range.start + 1, code)
                self.assertEqual(line_num + 1, expected['line'])
                self.assertEqual(actual.message, expected['message'])
