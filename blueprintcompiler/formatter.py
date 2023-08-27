# decompiler.py
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

from enum import Enum

from . import tokenizer

OPENING_TOKENS = ["{", "["]
CLOSING_TOKENS = ["}", "]"]

NEWLINE_AFTER = [";"] + OPENING_TOKENS + CLOSING_TOKENS

NO_WHITESPACE_BEFORE = [",", ":", ";", ")", "."]
NO_WHITESPACE_AFTER = ["C_", "_", "("]

WHITESPACE_AFTER = [":", ","]
WHITESPACE_BEFORE = ["{"]


class LineType(Enum):
    STATEMENT = 0
    BLOCK_OPEN = 1
    BLOCK_CLOSE = 2
    CHILD_TYPE = 3


class Format:
    def format(data, tab_size=2, insert_space=True):
        indent_levels = 0
        tokens = tokenizer.tokenize(data)
        tokenized_str = ""
        last_not_whitespace = tokens[0]
        current_line = ""
        prev_line_type = None
        is_child_type = False
        indent_item = " " * tab_size if insert_space else "\t"

        def commit_current_line(
            extra_newlines=1, line_type=prev_line_type, indent_decrease=False
        ):
            nonlocal tokenized_str, current_line, prev_line_type

            if indent_decrease:
                tokenized_str = (
                    tokenized_str.strip() + "\n" + (indent_levels * indent_item)
                )

            if extra_newlines > 1:
                tokenized_str = (
                    tokenized_str.strip()
                    + ("\n" * (extra_newlines))
                    + (indent_item * (indent_levels - 1))
                )

            tokenized_str += current_line + "\n" + (indent_levels * indent_item)

            current_line = ""
            prev_line_type = line_type

        for item in tokens:
            if item.type != tokenizer.TokenType.WHITESPACE:
                str_item = str(item)
                if item.type == tokenizer.TokenType.QUOTED and str_item.startswith('"'):
                    str_item = ("'" + str_item[1:-1] + "'").replace('\\"', '"')

                if (
                    str_item in WHITESPACE_BEFORE
                    and str(last_not_whitespace) not in NO_WHITESPACE_AFTER
                ) or (
                    (
                        str(last_not_whitespace) in WHITESPACE_AFTER
                        or last_not_whitespace.type == tokenizer.TokenType.IDENT
                    )
                    and str(last_not_whitespace) not in NO_WHITESPACE_AFTER
                    and str_item not in NO_WHITESPACE_BEFORE
                ):
                    current_line += " "

                current_line += str_item

                if (
                    str_item in NEWLINE_AFTER
                    or item.type == tokenizer.TokenType.COMMENT
                ):
                    if str_item in OPENING_TOKENS:
                        if str_item == "[":
                            is_child_type = (current_line + "[").startswith("[")
                            if is_child_type:
                                NO_WHITESPACE_BEFORE.append("]")
                                if str(last_not_whitespace) not in OPENING_TOKENS:
                                    tokenized_str = (
                                        tokenized_str.strip()
                                        + "\n\n"
                                        + (indent_levels * indent_item)
                                    )
                                last_not_whitespace = item
                                continue
                            else:
                                NEWLINE_AFTER.append(",")
                                WHITESPACE_AFTER.remove(",")

                        indent_levels += 1
                        commit_current_line(
                            1 if prev_line_type == LineType.CHILD_TYPE else 2,
                            LineType.BLOCK_OPEN,
                        )

                    elif str_item in CLOSING_TOKENS:
                        if str_item == "]":
                            if is_child_type:
                                NO_WHITESPACE_BEFORE.remove("]")
                                indent_levels += 1
                            else:
                                WHITESPACE_AFTER.append(",")
                                NEWLINE_AFTER.remove(",")

                        indent_levels -= 1
                        commit_current_line(
                            1,
                            LineType.CHILD_TYPE
                            if is_child_type
                            else LineType.BLOCK_CLOSE,
                            not is_child_type,
                        )

                        is_child_type = False

                    else:
                        commit_current_line()

                last_not_whitespace = item

        return tokenized_str
