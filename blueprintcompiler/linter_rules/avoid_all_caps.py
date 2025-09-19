from blueprintcompiler import annotations
from blueprintcompiler.errors import CompileWarning
from blueprintcompiler.language.gobject_property import Property
from blueprintcompiler.linter_rules.utils import LinterRule


# WIP
class AvoidAllCaps(LinterRule):
    def check(self, type, child, stack):
        for property in child.content.children[Property]:
            if annotations.is_property_user_facing_string(property.gir_property):
                (string, range) = self.get_string_value(property)
                # Show linter error for upper case and multi letter strings
                if string and string.isupper() and len(string) > 1:
                    problem = CompileWarning(
                        f"Avoid using all upper case for {type} {property.name}", range
                    )
                    self.problems.append(problem)
