from blueprintcompiler import annotations
from blueprintcompiler.errors import CodeAction, CompileWarning
from blueprintcompiler.language.gobject_property import Property
from blueprintcompiler.language.values import Translated
from blueprintcompiler.linter_rules.utils import LinterRule


class TranslatableDisplayString(LinterRule):
    def check(self, type, child, stack):
        # rule suggestion/translatable-display-string
        for property in child.content.children[Property]:
            if annotations.is_property_user_facing_string(property.gir_property):
                value = property.children[0].child
                if not isinstance(value, Translated):
                    range = value.range
                    problem = CompileWarning(
                        f'Mark {type} {property.name} as translatable using _("...")',
                        range,
                        actions=[
                            CodeAction("mark as translatable", "_(" + range.text + ")")
                        ],
                    )
                    self.problems.append(problem)
