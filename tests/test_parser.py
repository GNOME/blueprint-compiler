# test_parser.py
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

from gtkblueprinttool.ast import *
from gtkblueprinttool.errors import PrintableError
from gtkblueprinttool.tokenizer import tokenize
from gtkblueprinttool.parser import parse


class TestParser(unittest.TestCase):
    def test_parser(self):
        f = """
        using Gtk 4.0;

        template MyAppWindow : Gtk.ApplicationWindow {
            title: _("Hello, world!");
            app-defined-prop: 10.5;

            [titlebar]
            Gtk.HeaderBar header_bar {
            }

            Gtk.Button {
                clicked => on_clicked() swapped;
            }
        }

        Label {
            style "dim-label", "my-class";
            label: "Text";
            notify::visible => on_notify_visible();
        }

        Box {}
        """

        tokens = tokenize(f)
        ui = parse(tokens)
        self.assertIsInstance(ui, UI)
        self.assertEqual(len(ui.errors), 0)

        self.assertIsInstance(ui.gtk_directive, GtkDirective)
        self.assertEqual(ui.gtk_directive.version, "4.0")

        self.assertEqual(len(ui.templates), 1)
        template = ui.templates[0]
        self.assertEqual(template.name, "MyAppWindow")
        self.assertEqual(template.parent_namespace, "Gtk")
        self.assertEqual(template.parent_class, "ApplicationWindow")

        self.assertEqual(len(template.object_content.properties), 2)
        prop = template.object_content.properties[0]
        self.assertEqual(prop.name, "title")
        self.assertEqual(prop.value, "Hello, world!")
        self.assertTrue(prop.translatable)
        prop = template.object_content.properties[1]
        self.assertEqual(prop.name, "app-defined-prop")
        self.assertEqual(prop.value, 10.5)
        self.assertFalse(prop.translatable)

        self.assertEqual(len(template.object_content.children), 2)
        child = template.object_content.children[0]
        self.assertEqual(child.child_type, "titlebar")
        self.assertEqual(child.object.id, "header_bar")
        self.assertEqual(child.object.namespace, "Gtk")
        self.assertEqual(child.object.class_name, "HeaderBar")
        child = template.object_content.children[1]
        self.assertIsNone(child.child_type)
        self.assertIsNone(child.object.id)
        self.assertEqual(child.object.namespace, "Gtk")
        self.assertEqual(child.object.class_name, "Button")
        self.assertEqual(len(child.object.object_content.signals), 1)
        signal = child.object.object_content.signals[0]
        self.assertEqual(signal.name, "clicked")
        self.assertEqual(signal.handler, "on_clicked")
        self.assertTrue(signal.swapped)
        self.assertIsNone(signal.detail_name)

        self.assertEqual(len(ui.objects), 2)
        obj = ui.objects[0]
        self.assertIsNone(obj.namespace)
        self.assertEqual(obj.class_name, "Label")
        self.assertEqual(len(obj.object_content.properties), 1)
        prop = obj.object_content.properties[0]
        self.assertEqual(prop.name, "label")
        self.assertEqual(prop.value, "Text")
        self.assertFalse(prop.translatable)
        self.assertEqual(len(obj.object_content.signals), 1)
        signal = obj.object_content.signals[0]
        self.assertEqual(signal.name, "notify")
        self.assertEqual(signal.handler, "on_notify_visible")
        self.assertEqual(signal.detail_name, "visible")
        self.assertFalse(signal.swapped)
        self.assertEqual(len(obj.object_content.style), 1)
        style = obj.object_content.style[0]
        self.assertEqual(len(style.style_classes), 2)
        self.assertEqual([s.name for s in style.style_classes], ["dim-label", "my-class"])
