# gtkbuilder_template.py
#
# Copyright 2022 James Westman <james@jwestman.net>
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


from .gobject_object import Object, ObjectContent
from .common import *


class Template(Object):
    grammar = [
        "template",
        UseIdent("name").expected("template class name"),
        Optional([
            Match(":"),
            class_name.expected("parent class"),
        ]),
        ObjectContent,
    ]

    @validate()
    def not_abstract(self):
        pass # does not apply to templates

    def emit_xml(self, xml: XmlEmitter):
        xml.start_tag(
            "template",
            **{"class": self.tokens["name"]},
            parent=self.gir_class or self.tokens["class_name"]
        )
        for child in self.children:
            child.emit_xml(xml)
        xml.end_tag()


@decompiler("template")
def decompile_template(ctx: DecompileCtx, gir, klass, parent="Widget"):
    gir_class = ctx.type_by_cname(parent)
    if gir_class is None:
        ctx.print(f"template {klass} : .{parent} {{")
    else:
        ctx.print(f"template {klass} : {decompile.full_name(gir_class)} {{")
    return gir_class
