from ..errors import CompileWarning
from ..lsp_utils import CodeAction
from .utils import LinterRule

SCROLL_CONTAINERS = ("Gtk.ScrolledWindow", "Adw.ClampScrollable")


class ScrollableParent(LinterRule):
    id = "scrollable_parent"
    severity = "problem"
    category = "technical"

    def check(self, type, child, stack):
        if child.gir_class is not None and child.gir_class.assignable_to(
            child.root.gir.get_type("Scrollable", "Gtk")
        ):
            if len(stack) > 0:
                parent_class_name = stack[-1].class_name
                if (
                    parent_class_name.gir_type is not None
                    and parent_class_name.gir_type.full_name not in SCROLL_CONTAINERS
                ):
                    actions = []
                    if parent_class_name.gir_type.full_name == "Adw.Clamp":
                        actions.append(
                            CodeAction(
                                "use Adw.ClampScrollable",
                                "Adw.ClampScrollable",
                                parent_class_name.range,
                            )
                        )

                    self.problems.append(
                        CompileWarning(
                            "Scrollable widget should be placed in a scroll container",
                            range=child.signature_range,
                            hints=[
                                "scroll containers: " + ", ".join(SCROLL_CONTAINERS)
                            ],
                            actions=actions,
                            id=self.id,
                        )
                    )
