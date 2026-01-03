from ..errors import CompileError
from ..language import Child
from .utils import LinterRule


class NumberOfChildren(LinterRule):
    id = "number-of-children"
    severity = "problem"
    category = "technical"

    def check(self, type, child, stack):
        # rule problem/number-of-children
        children = child.content.children[Child]
        if type in gir_types_no_children and len(children) > 0:
            range = children[0].range
            problem = CompileError(f"{type} cannot have children", range)
            self.problems.append(problem)
        elif type in gir_types_single_child and len(children) > 1:
            range = children[1].range
            problem = CompileError(f"{type} cannot have more than one child", range)
            self.problems.append(problem)


gir_types_no_children = ["Gtk.Label"]
gir_types_single_child = [
    "Adw.Bin",
    "Adw.StatusPage",
    "Adw.Clamp",
    "Gtk.ScrolledWindow",
]
