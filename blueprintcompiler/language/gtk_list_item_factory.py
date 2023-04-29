from .gobject_object import ObjectContent, validate_parent_type
from ..parse_tree import Keyword
from ..ast_utils import AstNode, validate
from .common import *
from .contexts import ScopeCtx


class ListItemFactory(AstNode):
    grammar = [Keyword("template"), ObjectContent]

    @property
    def gir_class(self):
        return self.root.gir.get_type("ListItem", "Gtk")

    @validate("template")
    def container_is_builder_list(self):
        validate_parent_type(
            self,
            "Gtk",
            "BuilderListItemFactory",
            "sub-templates",
        )

    @context(ScopeCtx)
    def scope_ctx(self) -> ScopeCtx:
        return ScopeCtx(node=self)

    @validate()
    def unique_ids(self):
        self.context[ScopeCtx].validate_unique_ids()

    @property
    def content(self) -> ObjectContent:
        return self.children[ObjectContent][0]

    @property
    def action_widgets(self):
        """
        The sub-template shouldn't have it`s own actions this is
        just hear to satisfy XmlOutput._emit_object_or_template
        """
        return None
