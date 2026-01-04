from ..errors import CompileError
from ..language import Property
from .utils import LinterRule


class NoGtkSwitchState(LinterRule):
    id = "gtk_switch_state"
    severity = "problem"
    category = "technical"

    def check(self, type, child, stack):
        # rule problem/no-gtkswitch-state
        properties = child.content.children[Property]
        if type == "Gtk.Switch":
            for property in properties:
                if property.name == "state":
                    range = property.range
                    problem = CompileError(
                        f"Use the active property instead of the state property",
                        range,
                        id=self.id,
                    )
                    self.problems.append(problem)
