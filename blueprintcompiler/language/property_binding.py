# property_binding.py
#
# Copyright 2023 James Westman <james@jwestman.net>
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

from .common import *
from .contexts import ScopeCtx
from .gobject_object import Object


class PropertyBindingFlag(AstNode):
    grammar = [
        AnyOf(
            UseExact("flag", "inverted"),
            UseExact("flag", "bidirectional"),
            UseExact("flag", "no-sync-create"),
            UseExact("flag", "sync-create"),
        )
    ]

    @property
    def flag(self) -> str:
        return self.tokens["flag"]

    @validate()
    def sync_create(self):
        if self.flag == "sync-create":
            raise UpgradeWarning(
                "'sync-create' is now the default. Use 'no-sync-create' if this is not wanted.",
                actions=[CodeAction("remove 'sync-create'", "")],
            )

    @validate()
    def unique(self):
        self.validate_unique_in_parent(
            f"Duplicate flag '{self.flag}'", lambda x: x.flag == self.flag
        )


class PropertyBinding(AstNode):
    grammar = AnyOf(
        [
            Keyword("bind-property"),
            UseIdent("source"),
            ".",
            UseIdent("property"),
            ZeroOrMore(PropertyBindingFlag),
        ],
        [
            Keyword("bind"),
            UseIdent("source"),
            ".",
            UseIdent("property"),
            PropertyBindingFlag,
            ZeroOrMore(PropertyBindingFlag),
        ],
    )

    @property
    def source(self) -> str:
        return self.tokens["source"]

    @property
    def source_obj(self) -> T.Optional[Object]:
        if self.root.is_legacy_template(self.source):
            return self.root.template
        return self.context[ScopeCtx].objects.get(self.source)

    @property
    def property_name(self) -> str:
        return self.tokens["property"]

    @property
    def flags(self) -> T.List[PropertyBindingFlag]:
        return self.children[PropertyBindingFlag]

    @property
    def inverted(self) -> bool:
        return any([f.flag == "inverted" for f in self.flags])

    @property
    def bidirectional(self) -> bool:
        return any([f.flag == "bidirectional" for f in self.flags])

    @property
    def no_sync_create(self) -> bool:
        return any([f.flag == "no-sync-create" for f in self.flags])

    @validate("source")
    def source_object_exists(self) -> None:
        if self.source_obj is None:
            raise CompileError(
                f"Could not find object with ID {self.source}",
                did_you_mean=(self.source, self.context[ScopeCtx].objects.keys()),
            )

    @validate("property")
    def property_exists(self) -> None:
        if self.source_obj is None:
            return

        gir_class = self.source_obj.gir_class

        if gir_class is None or gir_class.incomplete:
            # Objects that we have no gir data on should not be validated
            # This happens for classes defined by the app itself
            return

        if (
            isinstance(gir_class, gir.Class)
            and gir_class.properties.get(self.property_name) is None
        ):
            raise CompileError(
                f"{gir_class.full_name} does not have a property called {self.property_name}"
            )

    @validate("bind")
    def old_bind(self):
        if self.tokens["bind"]:
            raise UpgradeWarning(
                "Use 'bind-property', introduced in blueprint 0.8.0, to use binding flags",
                actions=[CodeAction("Use 'bind-property'", "bind-property")],
            )

    @validate("source")
    def legacy_template(self):
        if self.root.is_legacy_template(self.source):
            raise UpgradeWarning(
                "Use 'template' instead of the class name (introduced in 0.8.0)",
                actions=[CodeAction("Use 'template'", "template")],
            )
