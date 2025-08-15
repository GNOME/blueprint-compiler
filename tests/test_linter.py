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
            { 'line': 12, 'message': 'Mark Gtk.Window title as translatable using _("...")' },
            { 'line': 15, 'message': 'Mark Gtk.Button label as translatable using _("...")' },
            { 'line': 18, 'message': 'Mark Gtk.CheckButton label as translatable using _("...")' },
            { 'line': 21, 'message': 'Mark Gtk.Expander label as translatable using _("...")' },
            { 'line': 24, 'message': 'Mark Gtk.Frame label as translatable using _("...")' },
            { 'line': 27, 'message': 'Mark Gtk.MenuButton label as translatable using _("...")' },
            { 'line': 30, 'message': 'Mark Gtk.Entry placeholder-text as translatable using _("...")' },
            { 'line': 33, 'message': 'Mark Gtk.PasswordEntry placeholder-text as translatable using _("...")' },
            { 'line': 36, 'message': 'Mark Gtk.SearchEntry placeholder-text as translatable using _("...")' },
            { 'line': 39, 'message': 'Mark Gtk.Entry primary-icon-tooltip-markup as translatable using _("...")' },
            { 'line': 42, 'message': 'Mark Gtk.Entry primary-icon-tooltip-text as translatable using _("...")' },
            { 'line': 45, 'message': 'Mark Gtk.Entry secondary-icon-tooltip-markup as translatable using _("...")' },
            { 'line': 48, 'message': 'Mark Gtk.Entry secondary-icon-tooltip-text as translatable using _("...")' },
            { 'line': 51, 'message': 'Mark Gtk.EntryBuffer text as translatable using _("...")' },
            { 'line': 54, 'message': 'Mark Gtk.ListItem accessible-description as translatable using _("...")' },
            { 'line': 57, 'message': 'Mark Gtk.ListItem accessible-label as translatable using _("...")' },
            { 'line': 60, 'message': 'Mark Gtk.AlertDialog message as translatable using _("...")' },
            { 'line': 63, 'message': 'Mark Gtk.AppChooserButton heading as translatable using _("...")' },
            { 'line': 66, 'message': 'Mark Gtk.AppChooserDialog heading as translatable using _("...")' },
            { 'line': 69, 'message': 'Mark Gtk.AppChooserWidget default-text as translatable using _("...")' },
            { 'line': 72, 'message': 'Mark Gtk.AssistantPage title as translatable using _("...")' },
            { 'line': 75, 'message': 'Mark Gtk.CellRendererText markup as translatable using _("...")' },
            { 'line': 78, 'message': 'Mark Gtk.CellRendererText text as translatable using _("...")' },
            { 'line': 81, 'message': 'Mark Gtk.ColorButton title as translatable using _("...")' },
            { 'line': 84, 'message': 'Mark Gtk.ColorDialog title as translatable using _("...")' },
            { 'line': 87, 'message': 'Mark Gtk.ColumnViewColumn title as translatable using _("...")' },
            { 'line': 90, 'message': 'Mark Gtk.ColumnViewRow accessible-description as translatable using _("...")' },
            { 'line': 93, 'message': 'Mark Gtk.ColumnViewRow accessible-label as translatable using _("...")' },
            { 'line': 96, 'message': 'Mark Gtk.FileChooserNative accept-label as translatable using _("...")' },
            { 'line': 99, 'message': 'Mark Gtk.FileChooserNative cancel-label as translatable using _("...")' },
            { 'line': 102, 'message': 'Mark Gtk.FileDialog accept-label as translatable using _("...")' },
            { 'line': 105, 'message': 'Mark Gtk.FileDialog title as translatable using _("...")' },
            { 'line': 108, 'message': 'Mark Gtk.FileDialog initial-name as translatable using _("...")' },
            { 'line': 111, 'message': 'Mark Gtk.FileFilter name as translatable using _("...")' },
            { 'line': 114, 'message': 'Mark Gtk.FontButton title as translatable using _("...")' },
            { 'line': 117, 'message': 'Mark Gtk.FontDialog title as translatable using _("...")' },
            { 'line': 120, 'message': 'Mark Gtk.Inscription markup as translatable using _("...")' },
            { 'line': 123, 'message': 'Mark Gtk.Inscription text as translatable using _("...")' },
            { 'line': 126, 'message': 'Mark Gtk.LockButton text-lock as translatable using _("...")' },
            { 'line': 129, 'message': 'Mark Gtk.LockButton text-unlock as translatable using _("...")' },
            { 'line': 132, 'message': 'Mark Gtk.LockButton tooltip-lock as translatable using _("...")' },
            { 'line': 135, 'message': 'Mark Gtk.LockButton tooltip-not-authorized as translatable using _("...")' },
            { 'line': 138, 'message': 'Mark Gtk.LockButton tooltip-unlock as translatable using _("...")' },
            { 'line': 141, 'message': 'Mark Gtk.MessageDialog text as translatable using _("...")' },
            { 'line': 144, 'message': 'Mark Gtk.NotebookPage menu-label as translatable using _("...")' },
            { 'line': 147, 'message': 'Mark Gtk.NotebookPage tab-label as translatable using _("...")' },
            { 'line': 150, 'message': 'Mark Gtk.PrintDialog accept-label as translatable using _("...")' },
            { 'line': 153, 'message': 'Mark Gtk.PrintDialog title as translatable using _("...")' },
            { 'line': 156, 'message': 'Mark Gtk.Printer name as translatable using _("...")' },
            { 'line': 159, 'message': 'Mark Gtk.PrintJob title as translatable using _("...")' },
            { 'line': 162, 'message': 'Mark Gtk.PrintOperation custom-tab-label as translatable using _("...")' },
            { 'line': 165, 'message': 'Mark Gtk.PrintOperation export-filename as translatable using _("...")' },
            { 'line': 168, 'message': 'Mark Gtk.PrintOperation job-name as translatable using _("...")' },
            { 'line': 171, 'message': 'Mark Gtk.ProgressBar text as translatable using _("...")' },
            { 'line': 174, 'message': 'Mark Gtk.ShortcutLabel disabled-text as translatable using _("...")' },
            { 'line': 177, 'message': 'Mark Gtk.ShortcutsGroup title as translatable using _("...")' },
            { 'line': 180, 'message': 'Mark Gtk.ShortcutsSection title as translatable using _("...")' },
            { 'line': 183, 'message': 'Mark Gtk.ShortcutsShortcut title as translatable using _("...")' },
            { 'line': 186, 'message': 'Mark Gtk.ShortcutsShortcut subtitle as translatable using _("...")' },
            { 'line': 189, 'message': 'Mark Gtk.StackPage title as translatable using _("...")' },
            { 'line': 192, 'message': 'Mark Gtk.Text placeholder-text as translatable using _("...")' },
            { 'line': 195, 'message': 'Mark Gtk.TextBuffer text as translatable using _("...")' },
            { 'line': 198, 'message': 'Mark Gtk.TreeViewColumn title as translatable using _("...")' }
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
