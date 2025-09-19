import copy
import re

from blueprintcompiler import annotations
from blueprintcompiler.errors import CompileWarning
from blueprintcompiler.language.gobject_property import Property
from blueprintcompiler.linter_rules.utils import LinterRule

NUMERIC = r"[0-9,.]+\S*"

PATTERNS = {
    "ellipsis": {
        "patterns": [re.compile(r"(\S+ *\.{3})")],
        "message": "Prefer using an ellipsis (<…>, U+2026) instead of <...> in <{0}>",
    },
    "bullet-list": {
        "patterns": [re.compile(r"^( *(\*|-) +.*)$", re.MULTILINE)],
        "message": "Prefer using a bullet (<•>, U+2022) instead of <{1}> at the start of a line in <{0}>",
    },
    "quote-marks": {
        "patterns": [re.compile(r'("\S.*\S")')],
        "message": 'Prefer using genuine quote marks (<“>, U+201C, and <”>, U+201D) instead of <"> in <{0}>',
    },
    "apostrophe": {
        "patterns": [re.compile(r"(\S+'\S*)")],
        "message": "Prefer using a right single quote (<’>, U+2019) instead of <'> to denote an apostrophe in <{0}>",
    },
    "multiplication": {
        "patterns": [
            re.compile(rf"({NUMERIC} *x *{NUMERIC})"),
            re.compile(rf"({NUMERIC} *x)\b"),
        ],
        "message": "Prefer using a multiplication sign (<×>, U+00D7), instead of <x> in <{0}>",
    },
    "units": {
        "patterns": [re.compile(r"\b([0-9,.]+[^0-9\s]+)\b")],
        "message": "When a number is displayed with units, e.g. <{0}>, the two should be separated by a narrow no-break space (< >, U+202F)",
    },
}


class PreferUnicodeChars(LinterRule):
    def check(self, type, child, stack):
        for property in child.content.children[Property]:
            if annotations.is_property_user_facing_string(property.gir_property):
                self.check_property(property)

    def check_property(self, property):
        (string, range) = self.get_string_value(property)
        for name, config in PATTERNS.items():
            for pattern in config["patterns"]:
                matches = 0

                for match in pattern.finditer(string):
                    message = config["message"].format(*match.groups())
                    problem = CompileWarning(message, range)
                    self.problems.append(problem)
                    matches += 1

                if matches > 0:
                    break
