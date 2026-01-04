from ..errors import CompileWarning
from ..language import Property
from .utils import LinterRule


class UseStylesOverCssClasses(LinterRule):
    id = "use_styles"
    severity = "problem"
    category = "technical"

    def check(self, type, child, stack):
        for property in child.content.children[Property]:
            if property.name == "css-classes":
                range = property.range
                self.problems.append(
                    CompileWarning(
                        "Avoid using css-classes. Use styles[] instead.",
                        range,
                        id=self.id,
                    )
                )
