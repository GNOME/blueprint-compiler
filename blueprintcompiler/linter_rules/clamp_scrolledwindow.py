from ..errors import CompileWarning
from .utils import LinterRule


class ClampScrolledWindow(LinterRule):
    def check(self, type, child, stack):
        if type == "Adw.Clamp":
            if len(stack) > 0:
                parent_widget = stack[-1].class_name.gir_type.full_name
                if parent_widget == "Gtk.ScrolledWindow":
                    problem = CompileWarning(
                        "Clamp should not be nested in ScrolledWindow.",
                        child.range,
                    )
                    self.problems.append(problem)
