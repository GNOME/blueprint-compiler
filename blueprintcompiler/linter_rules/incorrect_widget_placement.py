from ..errors import CompileWarning
from .utils import LinterRule


class IncorrectWidgetPlacement(LinterRule):
    id = "wrong-parent"
    severity = "problem"
    category = "technical"

    def check(self, type, child, stack):
        if type in declared_widgets:
            if len(stack) == 0:
                problem = CompileWarning(
                    f"{type} must be a child of a " + declared_widgets[type],
                    child.signature_range,
                )
                self.problems.append(problem)
            else:
                parent_type = stack[-1].class_name.gir_type
                if (
                    parent_type is None
                    or parent_type.full_name not in declared_widgets[type]
                ):
                    problem = CompileWarning(
                        f"{type} must be a child of a {declared_widgets[type]}",
                        child.signature_range,
                    )
                    self.problems.append(problem)


# Add more test widgets as needed with relevant parents
declared_widgets = {"Gtk.StackPage": "Gtk.Stack"}
