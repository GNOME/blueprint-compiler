import copy
import re

from blueprintcompiler.errors import CompileWarning
from blueprintcompiler.language.gobject_property import Property
from blueprintcompiler.linter_rules.utils import LinterRule

NUMERIC = r'[0-9,.]+[^ ]*'

PATTERNS = {
    'ellipsis': {
        'patterns': [
            re.compile(r'\.{3}')
        ],
        'message': 'Prefer using an ellipsis (<…>, U+2026) instead of <...>'
    },
    'bullet-list': {
        'patterns': [
            re.compile(r'^ *(\*|-) +', re.MULTILINE)
        ],
        'message': 'Prefer using a bullet (<•>, U+2022) instead of <{0}> at the start of a line'
    },
    'quote-marks': {
        'patterns': [
            re.compile(r'"[^\s].*[^\s]"')
        ],
        'message': 'Prefer using genuine quote marks (<“>, U+201C, and <”>, U+201D) instead of <">'
    },
    'multiplication': {
        'patterns': [
            re.compile(fr'({NUMERIC} *x *{NUMERIC})'),
            re.compile(fr'({NUMERIC} *x)(?: |$)'),
        ],
        'message': 'Prefer using a multiplication sign (<×>, U+00D7), instead of <x> in <{0}>'
    }
}

class PreferUnicodeChars(LinterRule):
    def check(self, type, child, stack):
        for property in child.content.children[Property]:
            if self.is_ui_string(type, property):
                self.check_property(property)

    def check_property(self, property):
        (string, range) = self.get_string_value(property)
        for name, config in PATTERNS.items():
            for pattern in config['patterns']:
                match = pattern.search(string)
                if match:
                    message = config['message'].format(*match.groups())
                    problem = CompileWarning(message, range)
                    self.problems.append(problem)
                    break
