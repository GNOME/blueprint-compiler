import typing as T
from abc import abstractmethod

from ..errors import CompileError
from ..language import Literal, Object, Property, QuotedLiteral, Translated, Value


class LinterRule:
    id: str
    severity: T.Union[T.Literal["problem"], T.Literal["suggestion"]]
    platform: T.Optional[str] = None
    category: str

    def __init__(self, problems: list[CompileError]):
        self.problems = problems

    def get_string_value(self, property: Property):
        if not isinstance(property.value, Value):
            return (None, None)

        value = property.value.child
        if isinstance(value, Translated):
            return (value.string, value.string_token.range_without_quotes)
        elif isinstance(value, Literal) and isinstance(value.value, QuotedLiteral):
            return (value.value.value, value.value.value_token.range_without_quotes)
        else:
            return (None, None)

    @abstractmethod
    def check(self, type: str, child: Object, stack: list[Object]): ...
