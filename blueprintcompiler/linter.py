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
from blueprintcompiler.language.values import Translated, Literal
from .errors import CompileError, CompileWarning

def lint(ast, problems = []): 
    for child in ast.children:
        if isinstance(child, Object):
            children = child.content.children[Child]
            properties = child.content.children[Property]
            type = child.class_name.gir_type.full_name

            if (type in gir_types_no_children and len(children) > 0):
                range = children[0].range
                problem = CompileError(f'{type} cannot have children', range)
                problems.append(problem)
            elif (type in gir_types_single_child and len(children) > 1):
                range = children[1].range
                problem = CompileError(f'{type} cannot have more than one child', range)
                problems.append(problem)
            
            if (type == 'Gtk.Box' and len(children) == 1):
                range = children[0].range
                problem = CompileWarning(f'Use Adw.Bin instead of a Gtk.Box for a single child', range)
                problems.append(problem)

            for translatable_property in translatable_properties:
                if type == translatable_property[0] or translatable_property[0] == None:
                    for property in properties:
                        if (property.name == translatable_property[1]):
                            value = property.children[0].child
                            if (not isinstance(value, Translated)):
                                range = value.range
                                problem = CompileWarning(f'Mark {type} {property.name} as translatable using _("...")', range)
                                problems.append(problem)

            # FIXME GTK4 only
            for property in properties:
                if (property.name == 'visible'):
                    value = property.children[0].child
                    ident = value.value.ident
                    if ident == 'true':
                        range = value.range
                        problem = CompileWarning(f'Property {property.name} default value is already true', range)
                        problems.append(problem)


            if (type == 'Gtk.Switch'):
                for property in properties:
                    if (property.name == 'state'):
                        range = property.range
                        problem = CompileError(f'Use the Gtk.Switch active property instead of the state property', range)
                        problems.append(problem)

        lint(child, problems)

    return problems

gir_types_no_children = ['Gtk.Label']
gir_types_single_child = ['Adw.Bin', 'Adw.StatusPage']

translatable_properties = [
    (None, 'tooltip-text'),
    ('Gtk.Label', 'label'),
    ('Gtk.Window', 'title'),
]
