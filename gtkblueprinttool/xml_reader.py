# xml_reader.py
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


from collections import defaultdict
from xml import sax

from .utils import lazy_prop


PARSE_GIR = set([
    "repository", "namespace", "class", "interface", "property", "glib:signal",
    "include", "implements",
])


class Element:
    def __init__(self, tag, attrs):
        self.tag = tag
        self.attrs = attrs
        self.children = defaultdict(list)
        self.cdata_chunks = []

    @lazy_prop
    def cdata(self):
        return ''.join(self.cdata_chunks)

    def get_elements(self, name):
        return self.children.get(name, [])

    def __getitem__(self, key):
        return self.attrs.get(key)


class Handler(sax.handler.ContentHandler):
    def __init__(self, parse_type):
        self.root = None
        self.stack = []
        self._interesting_elements = parse_type

    def startElement(self, name, attrs):
        if name not in self._interesting_elements:
            return

        element = Element(name, attrs.copy())

        if len(self.stack):
            last = self.stack[-1]
            last.children[name].append(element)
        else:
            self.root = element

        self.stack.append(element)


    def endElement(self, name):
        if name in self._interesting_elements:
            self.stack.pop()

    def characters(self, content):
        self.stack[-1].cdata_chunks.append(content)


def parse(filename, parse_type):
    parser = sax.make_parser()
    handler = Handler(parse_type)
    parser.setContentHandler(handler)
    parser.parse(filename)
    return handler.root
