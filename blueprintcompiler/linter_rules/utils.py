from blueprintcompiler.annotations import get_annotation_elements
from blueprintcompiler.language.values import Literal, QuotedLiteral, Translated


class LinterRule:
    def __init__(self, problems):
        self.problems = problems

    def get_string_value(self, property):
        value = property.children[0].child
        if isinstance(value, Translated):
            return (value.string, value.range)
        elif isinstance(value, Literal) and isinstance(value.value, QuotedLiteral):
            return (value.value.value, value.range)
