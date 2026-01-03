from abc import abstractmethod

from blueprintcompiler.annotations import get_annotation_elements
from blueprintcompiler.errors import CompileError
from blueprintcompiler.language import Object, Property, Value
from blueprintcompiler.language.values import Literal, QuotedLiteral, Translated


class LinterRule:
    def __init__(self, problems: list[CompileError]):
        self.problems = problems

    def get_string_value(self, property: Property):
        if not isinstance(property.value, Value):
            return (None, None)

        value = property.value.child
        if isinstance(value, Translated):
            return (value.string, value.range)
        elif isinstance(value, Literal) and isinstance(value.value, QuotedLiteral):
            return (value.value.value, value.range)
        else:
            return (None, None)

    @abstractmethod
    def check(self, type: str, child: Object, stack: list[Object]): ...
