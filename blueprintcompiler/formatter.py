# formatter.py
#
# Copyright 2023 James Westman <james@jwestman.net>
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

import re
from enum import Enum

from . import tokenizer

OPENING_TOKENS = ["{", "["]
CLOSING_TOKENS = ["}", "]"]

NEWLINE_AFTER = [";"] + OPENING_TOKENS + CLOSING_TOKENS

NO_WHITESPACE_BEFORE = [",", ":", "::", ";", ")", ".", ">", "]"]
NO_WHITESPACE_AFTER = ["C_", "_", "("]

# NO_WHITESPACE_BEFORE takes precedence over WHITESPACE_AFTER
WHITESPACE_AFTER = [
    ":",
    ",",
    ">",
    ")",
]
WHITESPACE_BEFORE = ["{", "$"]


class LineType(Enum):
    STATEMENT = 0
    BLOCK_OPEN = 1
    BLOCK_CLOSE = 2
    CHILD_TYPE = 3


class Format:
    def format(data, tab_size=2, insert_space=True):
        indent_levels = 0
        tokens = tokenizer.tokenize(data)
        end_str = ""
        last_not_whitespace = tokens[0]
        current_line = ""
        prev_line_type = None
        is_child_type = False
        indent_item = " " * tab_size if insert_space else "\t"
        watch_parentheses = False
        parentheses_balance = 0
        bracket_tracker = [None]

        def another_newline(one_indent_less=False):
            nonlocal end_str
            end_str = (
                end_str.strip()
                + "\n\n"
                + (
                    indent_item
                    * (indent_levels - 1 if one_indent_less else indent_levels)
                )
            )

        def commit_current_line(
            two_newlines=False, line_type=prev_line_type, indent_decrease=False
        ):
            nonlocal end_str, current_line, prev_line_type

            if indent_decrease:
                end_str = end_str.strip() + "\n" + (indent_levels * indent_item)

            if two_newlines:
                another_newline(
                    not (
                        current_line[-1] == ";"
                        and end_str.strip()[-1] in CLOSING_TOKENS
                    )
                )

            end_str += current_line + "\n" + (indent_levels * indent_item)

            current_line = ""
            prev_line_type = line_type

        for item in tokens:
            if item.type != tokenizer.TokenType.WHITESPACE:
                str_item = str(item)
                if item.type == tokenizer.TokenType.QUOTED and str_item.startswith('"'):
                    str_item = (
                        "'"
                        + str_item[1:-1].replace('\\"', '"').replace("'", "\\'")
                        + "'"
                    )

                if (
                    (
                        str_item in WHITESPACE_BEFORE
                        and str(last_not_whitespace) not in NO_WHITESPACE_AFTER
                    )
                    or (
                        (
                            str(last_not_whitespace) in WHITESPACE_AFTER
                            or last_not_whitespace.type == tokenizer.TokenType.IDENT
                        )
                        and str(last_not_whitespace) not in NO_WHITESPACE_AFTER
                        and str_item not in NO_WHITESPACE_BEFORE
                    )
                    and len(current_line) > 0
                ):
                    current_line += " "

                current_line += str_item

                if (
                    str_item in NEWLINE_AFTER
                    or item.type == tokenizer.TokenType.COMMENT
                ):
                    if str_item in OPENING_TOKENS:
                        if str_item == "[":
                            is_child_type = current_line.startswith("[")
                            if is_child_type:
                                if str(last_not_whitespace) not in OPENING_TOKENS:
                                    another_newline()
                                last_not_whitespace = item
                                continue

                        indent_levels += 1
                        commit_current_line(
                            not (
                                prev_line_type == LineType.CHILD_TYPE
                                or end_str.strip()[-1] in OPENING_TOKENS
                            ),
                            LineType.BLOCK_OPEN,
                        )

                    elif str_item == "]" and is_child_type:
                        commit_current_line(
                            line_type=LineType.CHILD_TYPE,
                            indent_decrease=False,
                        )
                        is_child_type = False

                    elif str_item in CLOSING_TOKENS:
                        if str_item == "]" and last_not_whitespace != ",":
                            current_line = current_line[:-1]
                            commit_current_line()
                            current_line = "]"

                        indent_levels -= 1
                        commit_current_line(
                            line_type=LineType.BLOCK_CLOSE,
                            indent_decrease=True,
                        )

                    elif str_item == ";" and len(end_str) > 0:
                        commit_current_line(
                            two_newlines=prev_line_type == LineType.BLOCK_CLOSE
                        )

                    else:
                        commit_current_line()

                elif str_item == "(" and (
                    re.match("^([A-Za-z_\-])+\s*\(", current_line) or watch_parentheses
                ):
                    watch_parentheses = True
                    parentheses_balance += 1

                elif str_item == ")" and watch_parentheses:
                    parentheses_balance -= 1
                    if parentheses_balance == 0:
                        commit_current_line()
                        watch_parentheses = False

                if str_item in ["[", "("]:
                    bracket_tracker.append(str_item)
                elif str_item in ["]", ")"]:
                    bracket_tracker.pop()

                if len(bracket_tracker) > 0:
                    if bracket_tracker[-1] == "[" and str_item == ",":
                        if end_str.strip()[-1] not in ["[", ","]:
                            end_str = end_str.strip()
                        commit_current_line()

                last_not_whitespace = item

        return end_str
