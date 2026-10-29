# utils.py
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

from collections.abc import Collection
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


def did_you_mean(word: str, options: Collection[str]) -> str | None:
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
    HEX_ESCAPES = {"x": 2, "u": 4, "U": 8}

    result = ""
    i = 0
    while i < len(string):
        c = string[i]
        if c == "\\":
            i += 1

            if i >= len(string):
                from .errors import CompilerBugError

                raise CompilerBugError()

            esc = string[i]

            if digits := HEX_ESCAPES.get(esc):
                hex_value = string[i + 1 : i + 1 + digits].strip()
                if len(hex_value) != digits:
                    raise UnescapeError(i, i + 2 + len(hex_value))
                try:
                    result += chr(int(hex_value, 16))
                except ValueError:
                    raise UnescapeError(i, i + 1 + digits)
                i += digits
            elif r := REPLACEMENTS.get(string[i]):
                result += r
            else:
                raise UnescapeError(i, i + 2)
        else:
            result += c

        i += 1

    return result
