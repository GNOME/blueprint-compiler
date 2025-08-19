import copy
import re

from blueprintcompiler.errors import CompileWarning
from blueprintcompiler.language.gobject_property import Property
from blueprintcompiler.linter_rules.utils import LinterRule

PATTERNS = {
    'ellipsis': {
        'patterns': [
            re.compile(r'\.{3}')
        ],
        'message': 'Prefer using an ellipsis ("…", U+2026) instead of "..."'
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
                for match in pattern.finditer(string):
                    problem = CompileWarning(config['message'], range)
                    self.problems.append(problem)
