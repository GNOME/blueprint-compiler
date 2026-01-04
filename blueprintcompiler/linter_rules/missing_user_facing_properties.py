from ..annotations import get_annotation_elements
from ..errors import CompileWarning
from ..language import Property
from .utils import LinterRule


class MissingUserFacingProperties(LinterRule):
    id = "missing_user_facing_text"
    severity = "suggestion"
    category = "a11y"

    def check(self, type, child, stack):
        properties = child.content.children[Property]
        # This ensures only the unique elements are run through
        unique_elements = set()
        for user_facing_property, _ in user_facing_properties:
            if user_facing_property not in unique_elements:
                unique_elements.add(user_facing_property)
                if type == user_facing_property or user_facing_property == None:
                    if not properties:
                        self.problems.append(
                            CompileWarning(
                                f"{type} is missing required user-facing text property",
                                child.signature_range,
                                id=self.id,
                            )
                        )


user_facing_properties = get_annotation_elements()
