from blueprintcompiler.annotations import get_annotation_elements
from blueprintcompiler.errors import CompileWarning
from blueprintcompiler.language.gobject_property import Property
from blueprintcompiler.language.values import Translated
from blueprintcompiler.linter_rules.utils import LinterRule


class MissingUserFacingProperties(LinterRule):
    def check(self, type, child, stack):
        properties = child.content.children[Property]
        # This ensures only the unique elements are run through
        unique_elements = set()
        for user_facing_property, _ in user_facing_properties:
            if user_facing_property not in unique_elements:
                unique_elements.add(user_facing_property)
                if type == user_facing_property or user_facing_property == None:
                    if not properties:
                        problem = CompileWarning(
                            f"{type} is missing required user-facing text property",
                            child.range,
                        )
                        self.problems.append(problem)


user_facing_properties = get_annotation_elements()
