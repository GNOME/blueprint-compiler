from ..errors import UnusedWarning
from ..lsp_utils import CodeAction
from .utils import LinterRule


class UnusedObject(LinterRule):
    id = "unused_object"
    severity = "suggestion"
    category = "technical"

    def check(self, type, child, stack):
        if len(stack) == 0 and child.id is None:
            self.problems.append(
                UnusedWarning(
                    f"{type} is unused because it has no ID and no parent",
                    range=child.signature_range,
                    actions=[
                        CodeAction(
                            "remove this object",
                            "",
                            edit_range=child.range.with_preceding_whitespace,
                        )
                    ],
                    id=self.id,
                )
            )
