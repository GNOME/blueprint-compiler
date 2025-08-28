from blueprintcompiler.annotations import get_annotation_elements
from blueprintcompiler.language.values import Translated, Literal, QuotedLiteral

UI_STRING_PROPERTIES = get_annotation_elements()


class LinterRule:
    def __init__(self, problems):
        self.problems = problems

    def is_ui_string(self, type, property):
        for m_type, m_name in UI_STRING_PROPERTIES:
            if (m_type == type or m_type is None) and m_name == property.name:
                return True
        return False

    def get_string_value(self, property):
        value = property.children[0].child
        if isinstance(value, Translated):
            return (value.string, value.range)
        elif isinstance(value, Literal) and isinstance(value.value, QuotedLiteral):
            return (value.value.value, value.range)
