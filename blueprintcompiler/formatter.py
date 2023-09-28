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
from .tokenizer import TokenType

OPENING_TOKENS = ("{", "[")
CLOSING_TOKENS = ("}", "]")

NEWLINE_AFTER = tuple(";") + OPENING_TOKENS + CLOSING_TOKENS

NO_WHITESPACE_BEFORE = (",", ":", "::", ";", ")", ".", ">", "]")
NO_WHITESPACE_AFTER = ("C_", "_", "(")

# NO_WHITESPACE_BEFORE takes precedence over WHITESPACE_AFTER
WHITESPACE_AFTER = (":", ",", ">", ")")
WHITESPACE_BEFORE = ("{", "$")


class LineType(Enum):
    STATEMENT = 0
    BLOCK_OPEN = 1
    BLOCK_CLOSE = 2
    CHILD_TYPE = 3
    COMMENT = 4


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

        def commit_current_line(
            line_type=prev_line_type, redo_whitespace=False, newlines_before=1
        ):
            nonlocal end_str, current_line, prev_line_type

            indent_whitespace = indent_levels * indent_item
            whitespace_to_add = "\n" + indent_whitespace

            if redo_whitespace or newlines_before != 1:
                end_str = end_str.strip() + ("\n" * newlines_before)
                if newlines_before > 0:
                    end_str += indent_whitespace

            end_str += current_line + whitespace_to_add

            current_line = ""
            prev_line_type = line_type

        for item in tokens:
            if item.type != TokenType.WHITESPACE:
                str_item = str(item)
                if item.type == TokenType.QUOTED and str_item.startswith('"'):
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
                            or last_not_whitespace.type == TokenType.IDENT
                        )
                        and str(last_not_whitespace) not in NO_WHITESPACE_AFTER
                        and str_item not in NO_WHITESPACE_BEFORE
                    )
                    and len(current_line) > 0
                ):
                    current_line += " "

                current_line += str_item

                if str_item in NEWLINE_AFTER or item.type == TokenType.COMMENT:
                    if str_item in OPENING_TOKENS:
                        if str_item == "[":
                            is_child_type = current_line.startswith("[")
                            if is_child_type:
                                if str(last_not_whitespace) not in OPENING_TOKENS:
                                    end_str = (
                                        end_str.strip()
                                        + "\n\n"
                                        + (indent_item * indent_levels)
                                    )
                                last_not_whitespace = item
                                continue

                        indent_levels += 1
                        if not (
                            prev_line_type in [LineType.CHILD_TYPE, LineType.COMMENT]
                            or prev_line_type == LineType.BLOCK_OPEN
                        ):
                            end_str = (
                                end_str.strip()
                                + "\n\n"
                                + (indent_item * (indent_levels - 1))
                            )
                        commit_current_line(
                            LineType.BLOCK_OPEN,
                        )

                    elif str_item == "]" and is_child_type:
                        commit_current_line(
                            LineType.CHILD_TYPE,
                            False,
                        )
                        is_child_type = False

                    elif str_item in CLOSING_TOKENS:
                        if str_item == "]" and last_not_whitespace != ",":
                            current_line = current_line[:-1]
                            commit_current_line()
                            current_line = "]"

                        indent_levels -= 1
                        commit_current_line(
                            LineType.BLOCK_CLOSE,
                            True,
                        )

                    elif str_item == ";":
                        if len(current_line) == 1:
                            newlines = 0
                        elif prev_line_type == LineType.BLOCK_CLOSE:
                            newlines = 2
                        else:
                            newlines = 1

                        commit_current_line(newlines_before=newlines)

                    elif item.type == TokenType.COMMENT:
                        commit_current_line(LineType.COMMENT)

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
