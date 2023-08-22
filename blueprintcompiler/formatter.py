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
    def format(data):
        indent_levels = 0
        tokens = tokenizer.tokenize(data)
        tokenized_str = ""
        last_not_whitespace = tokens[0]
        current_line = ""
        prev_line_type = None

        def commit_current_line(extra_newlines, line_type, new_indent_levels):
            nonlocal tokenized_str, current_line, prev_line_type
            current_line += "\n" + (new_indent_levels * "  ")
            tokenized_str += (
                current_line
                if extra_newlines == 0
                else ("\n" * extra_newlines) + ("  " * indent_levels) + current_line
            )
            current_line = ""
            prev_line_type = line_type

        for item in tokens:
            if item.type != tokenizer.TokenType.WHITESPACE:
                item_as_string = str(item)

                if (
                    item_as_string in WHITESPACE_BEFORE
                    and str(last_not_whitespace) not in NO_WHITESPACE_AFTER
                ) or (
                    (
                        str(last_not_whitespace) in WHITESPACE_AFTER
                        or last_not_whitespace.type == tokenizer.TokenType.IDENT
                    )
                    and str(last_not_whitespace) not in NO_WHITESPACE_AFTER
                    and item_as_string not in NO_WHITESPACE_BEFORE
                ):
                    current_line += " "

                current_line += item_as_string

                if (
                    item_as_string in NEWLINE_AFTER
                    or item.type == tokenizer.TokenType.COMMENT
                ):
                    if item_as_string in OPENING_TOKENS:
                        # num_newlines = 1 if prev_line_type == LineType.CHILD_TYPE else 2
                        # prev_line_type = LineType.BLOCK_OPEN
                        # tokenized_str = (
                        #     tokenized_str.strip()
                        #     + (num_newlines * "\n")
                        #     + (indent_levels * "  ")
                        # )
                        # current_line += "\n" + (indent_levels * "  ")
                        # tokenized_str += current_line
                        # current_line = ""
                        commit_current_line(
                            0 if prev_line_type == LineType.CHILD_TYPE else 1,
                            LineType.BLOCK_OPEN,
                            indent_levels + 1,
                        )

                        indent_levels += 1
                    elif item_as_string in CLOSING_TOKENS:
                        # tokenized_str = (
                        #     tokenized_str.strip() + "\n" + (indent_levels * "  ")
                        # )
                        # current_line += "\n" + (indent_levels * "  ")
                        # tokenized_str += current_line
                        # current_line = ""
                        indent_levels -= 1
                        commit_current_line(
                            0,
                            # LineType.CHILD_TYPE
                            # if current_line.strip().startswith("[")
                            # else LineType.BLOCK_CLOSE,
                            LineType.BLOCK_CLOSE,
                            indent_levels - 1,
                        )
                        # indent_levels -= 1

                        # prev_line_type = (
                        # LineType.CHILD_TYPE
                        # if current_line.strip().startswith("[")
                        # else LineType.BLOCK_CLOSE
                        # )

                    else:
                        commit_current_line(0, prev_line_type, indent_levels)

                last_not_whitespace = item

        print(tokenized_str)  # TODO: Remove this when the MR is ready to be merged

        return tokenized_str
