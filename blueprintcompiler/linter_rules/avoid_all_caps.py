from blueprintcompiler.linter_rules.utils import LinterRule
from blueprintcompiler.language.gobject_property import Property
from blueprintcompiler.language.values import Translated, Literal, QuotedLiteral
from blueprintcompiler.errors import CompileWarning
from blueprintcompiler.annotations import get_annotation_elements
# WIP
class AvoidAllCaps(LinterRule):
    def check(self, type, child, stack):
        properties = child.content.children[Property]
        for label_property in label_properties:
            if type == label_property[0] or label_property[0] == None:
                for property in properties:
                    if (property.name == label_property[1]):
                        value = property.children[0].child
                        if (isinstance(value, Translated)):
                           if value.string and value.string.isupper():
                                range = value.range
                                problem = CompileWarning(f'Avoid using all upper case for {type} {property.name}', range)
                                self.problems.append(problem)
                        elif isinstance(value, Literal) and isinstance(value.value, QuotedLiteral):
                        # TODO: Ask which other Literals a Label can have/ are excepted by the compiler
                              if value.value.value.isupper():
                                range = value.range
                                problem = CompileWarning(f'Avoid using all upper case for {type} {property.name}', range)
                                self.problems.append(problem)

label_properties = get_annotation_elements()
