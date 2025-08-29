from blueprintcompiler.errors import CompileWarning, CodeAction
from blueprintcompiler.language.gobject_property import Property
from blueprintcompiler.language.values import Translated
from blueprintcompiler.linter_rules.utils import LinterRule


class TranslatableDisplayString(LinterRule):
    def check(self, type, child, stack):
        # rule suggestion/translatable-display-string
        for property in child.content.children[Property]:
            if self.is_ui_string(type, property):
                value = property.children[0].child
                if not isinstance(value, Translated):
                    range = value.range
                    problem = CompileWarning(
                        f'Mark {type} {property.name} as translatable using _("...")',
                        range,
                        actions=[
                            CodeAction(
                                "mark as translatable",
                                "_(" + range.text + ")"
                            )
                        ]
                    )
                    self.problems.append(problem)
