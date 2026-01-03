from ..errors import CompileWarning
from ..language import Property
from .utils import LinterRule


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
