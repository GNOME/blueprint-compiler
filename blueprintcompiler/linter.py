# parser.py
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
from blueprintcompiler.language.gtkbuilder_child import Child
from blueprintcompiler.language.gobject_property import Property
from blueprintcompiler.language.values import Translated
from .errors import CompileError, CompileWarning
from blueprintcompiler.language.gtk_a11y import ExtAccessibility

def lint(ast, problems = []): 
    for child in ast.children:
        if isinstance(child, Object):
            children = child.content.children[Child]
            properties = child.content.children[Property]
            type = child.class_name.gir_type.full_name

            # problems are for logical errors
            # suggestions are for alternative/recommended way of doing things

            # rule problem/number-of-children
            if (type in gir_types_no_children and len(children) > 0):
                range = children[0].range
                problem = CompileError(f'{type} cannot have children', range)
                problems.append(problem)
            elif (type in gir_types_single_child and len(children) > 1):
                range = children[1].range
                problem = CompileError(f'{type} cannot have more than one child', range)
                problems.append(problem)
            
            # rule suggestion/prefer-adwbin
            # FIXME: Only if use Adw is in scope and no Gtk.Box properties are used
            if (type == 'Gtk.Box' and len(children) == 1):
                range = children[0].range
                problem = CompileWarning(f'Use Adw.Bin instead of a Gtk.Box for a single child', range)
                problems.append(problem)

            # rule suggestion/translatable-display-string
            for translatable_property in translatable_properties:
                if type == translatable_property[0] or translatable_property[0] == None:
                    for property in properties:
                        if (property.name == translatable_property[1]):
                            value = property.children[0].child
                            if (not isinstance(value, Translated)):
                                range = value.range
                                problem = CompileWarning(f'Mark {type} {property.name} as translatable using _("...")', range)
                                problems.append(problem)

            # rule suggestion/no-visible-true
            # FIXME GTK4 only
            for property in properties:
                if (property.name == 'visible'):
                    value = property.children[0].child
                    ident = value.value.ident
                    if ident == 'true':
                        range = value.range
                        problem = CompileWarning(f'In GTK4 widgets are visible by default', range)
                        problems.append(problem)

            # rule problem/no-gtkswitch-state
            if (type == 'Gtk.Switch'):
                for property in properties:
                    if (property.name == 'state'):
                        range = property.range
                        problem = CompileError(f'Use the active property instead of the state property', range)
                        problems.append(problem)

            # rule suggestion/require-a11y-label
            if (type == 'Gtk.Button'):
                label = None
                tooltip_text = None
                accessibility_label = False

                # FIXME: Check what ATs actually do

                for property in properties:
                    if (property.name == 'label'):
                        label = property.value
                    elif (property.name == 'tooltip-text'):
                        tooltip_text = property.value

                accessibility__child = child.content.children[ExtAccessibility]
                if len(accessibility__child) > 0:
                    accessibility_properties = child.content.children[ExtAccessibility][0].properties
                    for accessibility_property in accessibility_properties:
                        if (accessibility_property.name == 'label'):
                            accessibility_label = True

                if (label is None and tooltip_text is None and accessibility_label is False):
                    problem = CompileWarning(f'{type} is missing an accessibility label', child.range)
                    problems.append(problem)

            # rule suggestion/require-a11y-label
            elif (type == 'Gtk.Image' or type == 'Gtk.Picture'):
                accessibility_label = False

                accessibility__child = child.content.children[ExtAccessibility]
                if len(accessibility__child) > 0:
                    accessibility_properties = child.content.children[ExtAccessibility][0].properties
                    for accessibility_property in accessibility_properties:
                        if (accessibility_property.name == 'label'):
                            accessibility_label = True

                if (accessibility_label is False):
                    problem = CompileWarning(f'{type} is missing an accessibility label', child.range)
                    problems.append(problem)

        lint(child, problems)

    return problems

gir_types_no_children = ['Gtk.Label']
gir_types_single_child = ['Adw.Bin', 'Adw.StatusPage']

translatable_properties = [
    (None, 'tooltip-text'),
    ('Gtk.Label', 'label'),
    ('Gtk.Window', 'title'),
    ('Gtk.Button', 'label')
]
