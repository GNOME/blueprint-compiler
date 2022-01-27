# attributes.py
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


from .values import Value, TranslatedStringValue
from .common import *


class BaseAttribute(AstNode):
    """ A helper class for attribute syntax of the form `name: literal_value;`"""

    tag_name: str = ""
    attr_name: str = "name"

    def emit_xml(self, xml: XmlEmitter):
        value = self.children[Value][0]
        attrs = { self.attr_name: self.tokens["name"] }

        if isinstance(value, TranslatedStringValue):
            attrs = { **attrs, **value.attrs }

        xml.start_tag(self.tag_name, **attrs)
        value.emit_xml(xml)
        xml.end_tag()


class BaseTypedAttribute(BaseAttribute):
    """ A BaseAttribute whose parent has a value_type property that can assist
    in validation. """
