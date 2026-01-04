import re
from dataclasses import dataclass

from .. import annotations
from ..errors import CompileWarning
from ..language import Property
from ..lsp_utils import CodeAction
from ..utils import Range, adjust_quote_pos
from .utils import LinterRule


@dataclass
class Subrule:
    pattern: re.Pattern
    message: str
    replace_desc: str
    replace_with: str
    group: int = 0


PATTERNS: dict[str, Subrule] = {
    "ellipsis": Subrule(
        re.compile(r"\S *(\.{3,4})"),
        "Prefer using an ellipsis (<…>, U+2026) instead of <{0}>",
        "replace <{0}> with <\u2026>",
        "\u2026",
        group=1,
    ),
    "bullet-list": Subrule(
        re.compile(r"^ *(\*|-) +.*$", re.MULTILINE),
        "Prefer using a bullet (<•>, U+2022) instead of <{0}> at the start of a line",
        "replace <{0}> with <\u2022>",
        "\u2022",
        group=1,
    ),
    "quote-marks": Subrule(
        re.compile(r'"(\S.*\S)"'),
        'Prefer using genuine quote marks (<“>, U+201C, and <”>, U+201D) instead of <">',
        'replace <"..."> with <\u201c...\u201d>',
        "\u201c{0}\u201d",
    ),
    "apostrophe": Subrule(
        re.compile(r"\S+(')\S*"),
        "Prefer using a right single quote (<’>, U+2019) instead of <'> to denote an apostrophe",
        "replace <'> with <\u2019>",
        "\u2019",
        group=1,
    ),
    "multiplication": Subrule(
        re.compile(r"[0-9,.]*[0-9]\s*\S*\s*(x)\s*([0-9,.]*[0-9]\s*\S*\s)?"),
        "Prefer using a multiplication sign (<×>, U+00D7), instead of <x>",
        "replace <x> with <\u00d7>",
        "\u00d7",
        group=1,
    ),
    "units": Subrule(
        re.compile(r"\b(([0-9,.]*[0-9])(?!x\b)([^0-9\s]+))\b"),
        "When a number is displayed with units, the two should be separated by a narrow no-break space (< >, U+202F)",
        "insert <\u202f>",
        "{1}\u202f{2}",
        group=1,
    ),
}


class PreferUnicodeChars(LinterRule):
    id = "use_unicode"
    severity = "suggestion"
    category = "hig"

    def check(self, type, child, stack):
        for property in child.content.children[Property]:
            if annotations.is_property_user_facing_string(property.gir_property):
                self.check_property(property)

    def check_property(self, property):
        (string, range) = self.get_string_value(property)
        if string is None:
            return

        for name, pattern in PATTERNS.items():
            for match in pattern.pattern.finditer(string):

                def replace(string: str):
                    return string.format(*match.groups())

                message = replace(pattern.message)

                start_adjusted = adjust_quote_pos(
                    range.text, match.start(pattern.group)
                )
                end_adjusted = adjust_quote_pos(range.text, match.end(pattern.group))
                problem_range = Range(
                    range.start + start_adjusted,
                    range.start + end_adjusted,
                    original_text=range.original_text,
                )

                self.problems.append(
                    CompileWarning(
                        message,
                        problem_range,
                        actions=[
                            CodeAction(
                                replace(pattern.replace_desc),
                                replace(pattern.replace_with),
                            )
                        ],
                        id=self.id,
                    )
                )
