from ..errors import CompileWarning
from ..language import Child
from .utils import LinterRule


class PreferAdwBin(LinterRule):
    def check(self, type, child, stack):
        # rule suggestion/prefer-adwbin
        # FIXME: Only if use Adw is in scope and no Gtk.Box properties are used
        children = child.content.children[Child]
        if type == "Gtk.Box" and len(children) == 1:
            range = children[0].range
            problem = CompileWarning(
                f"Use Adw.Bin instead of a Gtk.Box for a single child", range
            )
            self.problems.append(problem)
