from ..errors import UnusedWarning
from ..lsp_utils import CodeAction
from .utils import LinterRule


class UnusedWidget(LinterRule):
    id = "unused_widget"
    severity = "suggestion"
    category = "technical"

    def check(self, type, child, stack):
        gtk_widget = child.root.gir.get_type("Widget", "Gtk")
        if (
            len(stack) == 0
            and child.id is None
            and child.gir_class is not None
            and child.gir_class.assignable_to(gtk_widget)
        ):
            self.problems.append(
                UnusedWarning(
                    f"{type} is unused because it has no ID and no parent",
                    range=child.signature_range,
                    actions=[
                        CodeAction(
                            "remove this widget",
                            "",
                            edit_range=child.range.with_preceding_whitespace,
                        )
                    ],
                    id=self.id,
                )
            )
