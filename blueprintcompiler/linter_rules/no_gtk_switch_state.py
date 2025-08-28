from blueprintcompiler.errors import CompileError
from blueprintcompiler.language.gobject_property import Property
from blueprintcompiler.linter_rules.utils import LinterRule


class NoGtkSwitchState(LinterRule):
    def check(self, type, child, stack):
        # rule problem/no-gtkswitch-state
        properties = child.content.children[Property]
        if type == "Gtk.Switch":
            for property in properties:
                if property.name == "state":
                    range = property.range
                    problem = CompileError(
                        f"Use the active property instead of the state property", range
                    )
                    self.problems.append(problem)
