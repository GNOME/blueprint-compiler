# utils.py
#
# Copyright 2021 James Westman <james@jwestman.net>
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This file is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import typing as T
from dataclasses import dataclass


class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[33m"
    PURPLE = "\033[35m"
    FAINT = "\033[2m"
    BOLD = "\033[1m"
    BLUE = "\033[34m"
    UNDERLINE = "\033[4m"
    NO_UNDERLINE = "\033[24m"
    CLEAR = "\033[0m"


def terminal_link(text: str, url: str):
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"


def did_you_mean(word: str, options: T.List[str]) -> T.Optional[str]:
    if len(options) == 0:
        return None

    def levenshtein(a, b):
        # see https://en.wikipedia.org/wiki/Levenshtein_distance
        m = len(a)
        n = len(b)

        distances = [[0 for j in range(n)] for i in range(m)]

        for i in range(m):
            distances[i][0] = i
        for j in range(n):
            distances[0][j] = j

        for j in range(1, n):
            for i in range(1, m):
                cost = 0
                if a[i] != b[j]:
                    if a[i].casefold() == b[j].casefold():
                        cost = 1
                    else:
                        cost = 2
                distances[i][j] = min(
                    distances[i - 1][j] + 2,
                    distances[i][j - 1] + 2,
                    distances[i - 1][j - 1] + cost,
                )

        return distances[m - 1][n - 1]

    distances = [(option, levenshtein(word, option)) for option in options]
    closest = min(distances, key=lambda item: item[1])
    if closest[1] <= 5:
        return closest[0]
    return None


def idx_to_pos(idx: int, text: str) -> T.Tuple[int, int]:
    if idx == 0 or len(text) == 0:
        return (0, 0)
    line_num = text.count("\n", 0, idx) + 1
    col_num = idx - text.rfind("\n", 0, idx) - 1
    return (line_num - 1, col_num)


def pos_to_idx(line: int, col: int, text: str) -> int:
    lines = text.splitlines(keepends=True)
    return sum([len(line) for line in lines[:line]]) + col


def idxs_to_range(start: int, end: int, text: str):
    start_l, start_c = idx_to_pos(start, text)
    end_l, end_c = idx_to_pos(end, text)
    return {
        "start": {
            "line": start_l,
            "character": start_c,
        },
        "end": {
            "line": end_l,
            "character": end_c,
        },
    }


@dataclass
class UnescapeError(Exception):
    start: int
    end: int


def escape_quote(string: str) -> str:
    return (
        '"'
        + (
            string.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\t", "\\t")
        )
        + '"'
    )


def adjust_quote_pos(string: str, pos: int):
    """Given the unescaped text of a quote literal (minus the quotes), convert the given index in the escaped string
    to the corresponding index in the unescaped string."""
    i = 0
    for _ in range(pos):
        if string[i] == "\\":
            i += 2
        else:
            i += 1
    return i


def unescape_quote(string: str) -> str:
    string = string[1:-1]

    REPLACEMENTS = {
        "\n": "\n",
        "\\": "\\",
        "n": "\n",
        "t": "\t",
        '"': '"',
        "'": "'",
    }

    result = ""
    i = 0
    while i < len(string):
        c = string[i]
        if c == "\\":
            i += 1

            if i >= len(string):
                from .errors import CompilerBugError

                raise CompilerBugError()

            if r := REPLACEMENTS.get(string[i]):
                result += r
            else:
                raise UnescapeError(i, i + 2)
        else:
            result += c

        i += 1

    return result


@dataclass
class Range:
    start: int
    end: int
    original_text: str

    @property
    def length(self) -> int:
        return self.end - self.start

    @property
    def text(self) -> str:
        return self.original_text[self.start : self.end]

    @property
    def with_trailing_newline(self) -> "Range":
        if len(self.original_text) > self.end and self.original_text[self.end] == "\n":
            return Range(self.start, self.end + 1, self.original_text)
        else:
            return self

    @property
    def with_preceding_whitespace(self) -> "Range":
        start = self.start
        while start > 0 and self.original_text[start - 1].isspace():
            start -= 1
        return Range(start, self.end, self.original_text)

    @staticmethod
    def join(a: T.Optional["Range"], b: T.Optional["Range"]) -> T.Optional["Range"]:
        if a is None:
            return b
        if b is None:
            return a
        return Range(min(a.start, b.start), max(a.end, b.end), a.original_text)

    def __contains__(self, other: T.Union[int, "Range"]) -> bool:
        if isinstance(other, int):
            return self.start <= other <= self.end
        else:
            return self.start <= other.start and self.end >= other.end

    def to_json(self):
        return idxs_to_range(self.start, self.end, self.original_text)

    def overlaps(self, other: "Range") -> bool:
        return not (self.end < other.start or self.start > other.end)


@dataclass
class TextEdit:
    range: Range
    newText: str

    def to_json(self):
        return {"range": self.range.to_json(), "newText": self.newText}

    @staticmethod
    def apply_edits(string: str, edits: T.List["TextEdit"]):
        offset = 0
        edits = sorted(edits, key=lambda e: e.range.start)
        for edit in edits:
            string = (
                string[: edit.range.start + offset]
                + edit.newText
                + string[edit.range.end + offset :]
            )
            offset += len(edit.newText) - edit.range.length

        return string
