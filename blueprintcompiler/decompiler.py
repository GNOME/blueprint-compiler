# decompiler.py
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

import re
from enum import Enum
import typing as T
from dataclasses import dataclass

from .extensions import gtk_a11y
from .xml_reader import Element, parse
from .gir import *
from .utils import Colors


__all__ = ["decompile"]


_DECOMPILERS: T.Dict = {}
_CLOSING = {
    "{": "}",
    "[": "]",
}
_NAMESPACES = [
    ("GLib", "2.0"),
    ("GObject", "2.0"),
    ("Gio", "2.0"),
    ("Adw", "1.0"),
]


class LineType(Enum):
    NONE = 1
    STMT = 2
    BLOCK_START = 3
    BLOCK_END = 4


class DecompileCtx:
    def __init__(self):
        self._result = ""
        self.gir = GirContext()
        self._indent = 0
        self._blocks_need_end = []
        self._last_line_type = LineType.NONE

        self.gir.add_namespace(get_namespace("Gtk", "4.0"))


    @property
    def result(self):
        imports = "\n".join([
            f"using {ns} {namespace.version};"
            for ns, namespace in self.gir.namespaces.items()
        ])
        return imports + "\n" + self._result


    def type_by_cname(self, cname):
        if type := self.gir.get_type_by_cname(cname):
            return type

        for ns, version in _NAMESPACES:
            try:
                namespace = get_namespace(ns, version)
                if type := namespace.get_type_by_cname(cname):
                    self.gir.add_namespace(namespace)
                    return type
            except:
                pass


    def start_block(self):
        self._blocks_need_end.append(None)

    def end_block(self):
        if close := self._blocks_need_end.pop():
            self.print(close)

    def end_block_with(self, text):
        self._blocks_need_end[-1] = text


    def print(self, line, newline=True):
        if line == "}" or line == "]":
            self._indent -= 1

        # Add blank lines between different types of lines, for neatness
        if newline:
            if line == "}" or line == "]":
                line_type = LineType.BLOCK_END
            elif line.endswith("{") or line.endswith("]"):
                line_type = LineType.BLOCK_START
            elif line.endswith(";"):
                line_type = LineType.STMT
            else:
                line_type = LineType.NONE
            if line_type != self._last_line_type and self._last_line_type != LineType.BLOCK_START and line_type != LineType.BLOCK_END:
                self._result += "\n"
            self._last_line_type = line_type

        self._result += ("  " * self._indent) + line
        if newline:
            self._result += "\n"

        if line.endswith("{") or line.endswith("["):
            if len(self._blocks_need_end):
                self._blocks_need_end[-1] = _CLOSING[line[-1]]
            self._indent += 1


    def print_attribute(self, name, value, type):
        if type is None:
            self.print(f"{name}: \"{_escape_quote(value)}\";")
        elif type.assignable_to(FloatType()):
            self.print(f"{name}: {value};")
        elif type.assignable_to(BoolType()):
            val = _truthy(value)
            self.print(f"{name}: {'true' if val else 'false'};")
        elif (
            type.assignable_to(self.gir.namespaces["Gtk"].lookup_type("Gdk.Pixbuf"))
            or type.assignable_to(self.gir.namespaces["Gtk"].lookup_type("Gdk.Texture"))
            or type.assignable_to(self.gir.namespaces["Gtk"].lookup_type("Gdk.Paintable"))
            or type.assignable_to(self.gir.namespaces["Gtk"].lookup_type("Gtk.ShortcutAction"))
            or type.assignable_to(self.gir.namespaces["Gtk"].lookup_type("Gtk.ShortcutTrigger"))
        ):
            self.print(f"{name}: \"{_escape_quote(value)}\";")
        elif type.assignable_to(self.gir.namespaces["Gtk"].lookup_type("GObject.Object")):
            self.print(f"{name}: {value};")
        elif isinstance(type, Enumeration):
            for member in type.members.values():
                if member.nick == value or member.c_ident == value:
                    self.print(f"{name}: {member.name};")
                    break
            else:
                self.print(f"{name}: {value.replace('-', '_')};")
        elif isinstance(type, Bitfield):
            flags = re.sub(r"\s*\|\s*", " | ", value).replace("-", "_")
            self.print(f"{name}: {flags};")
        else:
            self.print(f"{name}: \"{_escape_quote(value)}\";")


def _decompile_element(ctx: DecompileCtx, gir, xml):
    try:
        decompiler = _DECOMPILERS.get(xml.tag)
        if decompiler is None:
            raise UnsupportedError(f"unsupported XML tag: <{xml.tag}>")

        args = {_canon(name): value for name, value in xml.attrs.items()}
        if decompiler._cdata:
            if len(xml.children):
                args["cdata"] = None
            else:
                args["cdata"] = xml.cdata

        ctx.start_block()
        gir = decompiler(ctx, gir, **args)

        for child_type in xml.children.values():
            for child in child_type:
                _decompile_element(ctx, gir, child)

        ctx.end_block()

    except UnsupportedError as e:
        raise e
    except TypeError as e:
        raise UnsupportedError(tag=xml.tag)


def decompile(data):
    ctx = DecompileCtx()

    xml = parse(data)
    _decompile_element(ctx, None, xml)

    return ctx.result



def _canon(string: str) -> str:
    if string == "class":
        return "klass"
    else:
        return string.replace("-", "_").lower()

def _truthy(string: str) -> bool:
    return string.lower() in ["yes", "true", "t", "y", "1"]

def _full_name(gir):
    return gir.name if gir.full_name.startswith("Gtk.") else gir.full_name

def _lookup_by_cname(gir, cname: str):
    if isinstance(gir, GirContext):
        return gir.get_type_by_cname(cname)
    else:
        return gir.get_containing(Repository).get_type_by_cname(cname)


def decompiler(tag, cdata=False):
    def decorator(func):
        func._cdata = cdata
        _DECOMPILERS[tag] = func
        return func
    return decorator


def _escape_quote(string: str) -> str:
    return (string
            .replace("\\", "\\\\")
            .replace("\'", "\\'")
            .replace("\"", "\\\"")
            .replace("\n", "\\n"))


@decompiler("interface")
def decompile_interface(ctx, gir):
    return gir


@decompiler("requires")
def decompile_requires(ctx, gir, lib=None, version=None):
    return gir


@decompiler("template")
def decompile_template(ctx, gir, klass, parent="Widget"):
    gir_class = ctx.type_by_cname(parent)
    if gir_class is None:
        ctx.print(f"template {klass} : .{parent} {{")
    else:
        ctx.print(f"template {klass} : {_full_name(gir_class)} {{")
    return gir_class


@decompiler("object")
def decompile_object(ctx, gir, klass, id=None):
    gir_class = ctx.type_by_cname(klass)
    klass_name = _full_name(gir_class) if gir_class is not None else "." + klass
    if id is None:
        ctx.print(f"{klass_name} {{")
    else:
        ctx.print(f"{klass_name} {id} {{")
    return gir_class


@decompiler("child")
def decompile_child(ctx, gir, type=None):
    if type is not None:
        ctx.print(f"[{type}]")
    return gir


@decompiler("property", cdata=True)
def decompile_property(ctx, gir, name, cdata, bind_source=None, bind_property=None, bind_flags=None, translatable="false", comments=None, context=None):
    name = name.replace("_", "-")
    if comments is not None:
        ctx.print(f"/* Translators: {comments} */")

    if cdata is None:
        ctx.print(f"{name}: ", False)
        ctx.end_block_with(";")
    elif bind_source:
        flags = ""
        if bind_flags:
            if "sync-create" in bind_flags:
                flags += " sync-create"
            if "after" in bind_flags:
                flags += " after"
            if "bidirectional" in bind_flags:
                flags += " bidirectional"
        ctx.print(f"{name}: bind {bind_source}.{bind_property}{flags};")
    elif _truthy(translatable):
        if context is not None:
            ctx.print(f"{name}: C_(\"{_escape_quote(context)}\", \"{_escape_quote(cdata)}\");")
        else:
            ctx.print(f"{name}: _(\"{_escape_quote(cdata)}\");")
    elif gir is None or gir.properties.get(name) is None:
        ctx.print(f"{name}: \"{_escape_quote(cdata)}\";")
    else:
        ctx.print_attribute(name, cdata, gir.properties.get(name).type)
    return gir


@decompiler("signal")
def decompile_signal(ctx, gir, name, handler, swapped="false"):
    name = name.replace("_", "-")
    if _truthy(swapped):
        ctx.print(f"{name} => {handler}() swapped;")
    else:
        ctx.print(f"{name} => {handler}();")
    return gir


@decompiler("style")
def decompile_style(ctx, gir):
    ctx.print(f"styles [")


@decompiler("class")
def decompile_class(ctx, gir, name):
    ctx.print(f'"{name}",')


@decompiler("layout")
def decompile_layout(ctx, gir):
    ctx.print("layout {")


@decompiler("menu")
def decompile_menu(ctx, gir, id=None):
    if id:
        ctx.print(f"menu {id} {{")
    else:
        ctx.print("menu {")

@decompiler("submenu")
def decompile_submenu(ctx, gir, id=None):
    if id:
        ctx.print(f"submenu {id} {{")
    else:
        ctx.print("submenu {")

@decompiler("item")
def decompile_item(ctx, gir, id=None):
    if id:
        ctx.print(f"item {id} {{")
    else:
        ctx.print("item {")

@decompiler("section")
def decompile_section(ctx, gir, id=None):
    if id:
        ctx.print(f"section {id} {{")
    else:
        ctx.print("section {")

@decompiler("attribute", cdata=True)
def decompile_attribute(ctx, gir, name, cdata, translatable="false", comments=None, context=None):
    decompile_property(ctx, gir, name, cdata, translatable=translatable, comments=comments, context=context)

@decompiler("accessibility")
def decompile_accessibility(ctx, gir):
    ctx.print("accessibility {")

@decompiler("attributes")
def decompile_attributes(ctx, gir):
    ctx.print("attributes {")

@decompiler("relation", cdata=True)
def decompile_relation(ctx, gir, name, cdata):
    ctx.print_attribute(name, cdata, gtk_a11y.get_types(ctx.gir).get(name))

@decompiler("state", cdata=True)
def decompile_state(ctx, gir, name, cdata, translatable="false"):
    if _truthy(translatable):
        ctx.print(f"{name}: _(\"{_escape_quote(cdata)}\");")
    else:
        ctx.print_attribute(name, cdata, gtk_a11y.get_types(ctx.gir).get(name))


@decompiler("mime-types")
def decompile_mime_types(ctx, gir):
    ctx.print("mime-types [")

@decompiler("mime-type", cdata=True)
def decompile_mime_type(ctx, gir, cdata):
    ctx.print(f'"{cdata}",')

@decompiler("patterns")
def decompile_patterns(ctx, gir):
    ctx.print("patterns [")

@decompiler("pattern", cdata=True)
def decompile_pattern(ctx, gir, cdata):
    ctx.print(f'"{cdata}",')

@decompiler("suffixes")
def decompile_suffixes(ctx, gir):
    ctx.print("suffixes [")

@decompiler("suffix", cdata=True)
def decompile_suffix(ctx, gir, cdata):
    ctx.print(f'"{cdata}",')


@dataclass
class UnsupportedError(Exception):
    message: str = "unsupported feature"
    tag: T.Optional[str] = None

    def print(self, filename: str):
        print(f"\n{Colors.RED}{Colors.BOLD}error: {self.message}{Colors.CLEAR}")
        print(f"in {Colors.UNDERLINE}{filename}{Colors.NO_UNDERLINE}")
        if self.tag:
            print(f"in tag {Colors.BLUE}{self.tag}{Colors.CLEAR}")
        print(f"""{Colors.FAINT}The gtk-blueprint-tool compiler might support this feature, but the
porting tool does not. You probably need to port this file manually.{Colors.CLEAR}\n""")
