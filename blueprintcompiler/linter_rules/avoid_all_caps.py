from blueprintcompiler.linter_rules.utils import LinterRule
from blueprintcompiler.language.gobject_property import Property
from blueprintcompiler.errors import CompileWarning
# WIP
class AvoidAllCaps(LinterRule):
    def check(self, type, child, stack):
        for property in child.content.children[Property]:
            if self.is_ui_string(type, property):
                (string, range) = self.get_string_value(property)
                if string and string.isupper():
                    problem = CompileWarning(f'Avoid using all upper case for {type} {property.name}', range)
                    self.problems.append(problem)
