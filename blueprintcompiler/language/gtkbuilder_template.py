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
from .types import ClassName


class Template(Object):
    grammar = [
        "template",
        UseIdent("id").expected("template class name"),
        Optional([
            Match(":"),
            to_parse_node(ClassName).expected("parent class"),
        ]),
        ObjectContent,
    ]

    @property
    def gir_class(self):
        # Templates might not have a parent class defined
        if len(self.children[ClassName]):
            return self.children[ClassName][0].gir_type

    @validate("id")
    def unique_in_parent(self):
        self.validate_unique_in_parent(f"Only one template may be defined per file, but this file contains {len(self.parent.children[Template])}",)

    def emit_start_tag(self, xml: XmlEmitter):
        if len(self.children[ClassName]):
            parent = self.children[ClassName][0].glib_type_name
        else:
            parent = None

        xml.start_tag(
            "template",
            **{"class": self.tokens["id"]},
            parent=parent
        )


@decompiler("template")
def decompile_template(ctx: DecompileCtx, gir, klass, parent="Widget"):
    gir_class = ctx.type_by_cname(parent)
    if gir_class is None:
        ctx.print(f"template {klass} : .{parent} {{")
    else:
        ctx.print(f"template {klass} : {decompile.full_name(gir_class)} {{")
    return gir_class
