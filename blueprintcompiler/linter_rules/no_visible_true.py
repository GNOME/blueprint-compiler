from blueprintcompiler.errors import CompileWarning
from blueprintcompiler.language.gobject_property import Property
from blueprintcompiler.linter_rules.utils import LinterRule


class NoVisibleTrue(LinterRule):
    def check(self, type, child, stack):
        # rule suggestion/no-visible-true
        # FIXME GTK4 only
        properties = child.content.children[Property]
        for property in properties:
            if property.name == "visible":
                value = property.children[0].child
                ident = value.value.ident
                if ident == "true":
                    range = value.range
                    problem = CompileWarning(
                        f"In GTK4 widgets are visible by default", range
                    )
                    self.problems.append(problem)
