from ..errors import CompileWarning
from .utils import LinterRule


class IncorrectWidgetPlacement(LinterRule):
    id = "incorrect-widget-placement"
    severity = "problem"
    category = "technical"

    def check(self, type, child, stack):
        if type in declared_widgets:
            if len(stack) == 0:
                problem = CompileWarning(f"{type} must have a parent", child.range)
                self.problems.append(problem)
            elif stack[-1].class_name.gir_type.full_name not in declared_widgets[type]:
                problem = CompileWarning(
                    f"{type} is incorrectly used and must have parents {', '.join(declared_widgets[type])}",
                    child.range,
                )
                self.problems.append(problem)


# Add more test widgets as needed with relevant parents
declared_widgets = {"Gtk.Label": ["Gtk.Box", "Gtk.Window"]}
