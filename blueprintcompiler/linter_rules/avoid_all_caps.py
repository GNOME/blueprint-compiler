from .. import annotations
from ..errors import CompileWarning
from ..language import Property
from .utils import LinterRule


class AvoidAllCaps(LinterRule):
    id = "avoid_all_caps"
    severity = "suggestion"
    category = "hig"

    def check(self, type, child, stack):
        for property in child.content.children[Property]:
            if annotations.is_property_user_facing_string(property.gir_property):
                (string, range) = self.get_string_value(property)
                # Show linter error for upper case and multi letter strings
                if string and string.isupper() and len(string) > 1:
                    self.problems.append(
                        CompileWarning(
                            f"Avoid using all upper case for {type} {property.name}",
                            range,
                            id=self.id,
                        )
                    )
