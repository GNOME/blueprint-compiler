# linter.py
#
# Copyright © 2024 GNOME Foundation Inc.
# Original Author: Sonny Piers <sonnyp@gnome.org>
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

from blueprintcompiler.language.gobject_object import Object
from blueprintcompiler.linter_rules.avoid_all_caps import AvoidAllCaps
from blueprintcompiler.linter_rules.missing_user_facing_properties import (
    MissingUserFacingProperties,
)
from blueprintcompiler.linter_rules.no_gtk_switch_state import NoGtkSwitchState
from blueprintcompiler.linter_rules.no_visible_true import NoVisibleTrue
from blueprintcompiler.linter_rules.number_of_children import NumberOfChildren
from blueprintcompiler.linter_rules.prefer_adw_bin import PreferAdwBin
from blueprintcompiler.linter_rules.prefer_unicode_chars import PreferUnicodeChars
from blueprintcompiler.linter_rules.require_a11y_label import RequireA11yLabel
from blueprintcompiler.linter_rules.translatable_display_string import (
    TranslatableDisplayString,
)


def walk_ast(ast, func, stack=None):
    stack = stack or []
    for child in ast.children:
        if isinstance(child, Object):
            type = child.class_name.gir_type.full_name
            func(type, child, stack)
            walk_ast(child, func, stack + [ast])


RULES = [
    NumberOfChildren,
    PreferAdwBin,
    TranslatableDisplayString,
    NoGtkSwitchState,
    NoVisibleTrue,
    RequireA11yLabel,
    AvoidAllCaps,
    PreferUnicodeChars,
    MissingUserFacingProperties,
]


def lint(ast):
    problems = []
    rules = [Rule(problems) for Rule in RULES]

    def visit_node(type, child, stack):
        for rule in rules:
            rule.check(type, child, stack)

    walk_ast(ast, visit_node)
    return problems
