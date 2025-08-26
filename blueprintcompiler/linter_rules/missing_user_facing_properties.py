from blueprintcompiler.linter_rules.utils import LinterRule
from blueprintcompiler.language.gobject_property import Property
from blueprintcompiler.language.values import Translated
from blueprintcompiler.errors import CompileWarning
from blueprintcompiler.annotations import get_annotation_elements

class MissingUserFacingProperties(LinterRule):
    def check(self, type, child, stack):
        properties = child.content.children[Property]
        for user_facing_property in user_facing_properties:
            if type == user_facing_property[0] or user_facing_property[0] == None:
                if not properties:
                    problem = CompileWarning(f'{type} is missing required user-facing text property', child.range)
                    self.problems.append(problem)

user_facing_properties = get_annotation_elements()
