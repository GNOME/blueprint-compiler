from ..errors import CompileWarning
from ..language import Property, Value
from ..lsp_utils import CodeAction
from .utils import LinterRule


class NoVisibleTrue(LinterRule):
    id = "visible_true"
    severity = "suggestion"
    category = "technical"

    def check(self, type, child, stack):
        if not child.gir_class.assignable_to(child.root.gir.get_type("Widget", "Gtk")):
            return

        properties = child.content.children[Property]
        for property in properties:
            if property.name != "visible":
                continue

            if not isinstance(property.value, Value):
                continue

            ident = property.value.range.text
            if ident == "true":
                self.problems.append(
                    CompileWarning(
                        f"In GTK 4, widgets are visible by default, so this property is unnecessary",
                        property.value.range,
                        actions=[
                            CodeAction(
                                "remove the property",
                                "",
                                edit_range=property.range.with_preceding_whitespace,
                            )
                        ],
                        id=self.id,
                    )
                )
