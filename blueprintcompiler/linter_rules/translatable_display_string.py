from .. import annotations
from ..errors import CodeAction, CompileWarning
from ..language import Property, Translated, Value
from .utils import LinterRule


class TranslatableDisplayString(LinterRule):
    id = "translate_display_string"
    severity = "suggestion"
    category = "hig"

    def check(self, type, child, stack):
        # rule suggestion/translatable-display-string
        for property in child.content.children[Property]:
            if not annotations.is_property_user_facing_string(property.gir_property):
                continue

            value = property.value
            if not isinstance(value, Value):
                continue

            if not isinstance(value.child, Translated):
                range = value.range
                self.problems.append(
                    CompileWarning(
                        f'Mark {type} {property.name} as translatable using _("...")',
                        range,
                        actions=[
                            CodeAction("mark as translatable", "_(" + range.text + ")")
                        ],
                        id=self.id,
                    )
                )
