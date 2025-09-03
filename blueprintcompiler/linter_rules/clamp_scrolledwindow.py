from blueprintcompiler import annotations
from blueprintcompiler.errors import CompileWarning
from blueprintcompiler.language.gobject_property import Property
from blueprintcompiler.language.gtkbuilder_child import Child
from blueprintcompiler.linter_rules.utils import LinterRule


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
