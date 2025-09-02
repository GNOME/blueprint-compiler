from blueprintcompiler import annotations
from blueprintcompiler.errors import CodeAction, CompileWarning
from blueprintcompiler.language.gobject_property import Property
from blueprintcompiler.language.values import Translated
from blueprintcompiler.linter_rules.utils import LinterRule


class UseStylesOverCssClasses(LinterRule):
    def check(self, type, child, stack):
        for property in child.content.children[Property]:
            if property.name == "css-classes":
                range = property.range
                problem = CompileWarning(
                    "Avoid using css-classes. Use styles[] instead.",
                    range,
                )
                self.problems.append(problem)
