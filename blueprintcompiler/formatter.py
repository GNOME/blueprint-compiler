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

from . import tokenizer

OPENING_TOKENS = ["{"]
CLOSING_TOKENS = ["}"]

NEWLINE_AFTER = [";", "]", "{", "}"]

NO_WHITESPACE_BEFORE = [",", ":", ";", ")"]
NO_WHITESPACE_AFTER = ["C_", "_", "(", "["]

WHITESPACE_AFTER = [":", ","]
WHITESPACE_BEFORE = ["{"]


class Format:
    def format(data):
        indent_levels = 0
        tokens = tokenizer.tokenize(data)
        tokenized_str = ""
        last_not_whitespace = None

        for item in tokens:
            if item.type != tokenizer.TokenType.WHITESPACE:
                item_as_string = str(item)

                if item_as_string in OPENING_TOKENS:
                    split_string = tokenized_str.splitlines()

                    index = -1
                    if "[" in split_string[-2] and "]" in split_string[-2]:
                        index = -2

                    split_string.insert(index, "")
                    tokenized_str = "\n".join(split_string)

                    indent_levels += 1
                elif item_as_string in CLOSING_TOKENS:
                    tokenized_str = tokenized_str[:-2]
                    indent_levels -= 1

                if item_as_string in WHITESPACE_BEFORE:
                    tokenized_str = tokenized_str.strip() + " "
                elif (
                    item_as_string in NO_WHITESPACE_BEFORE
                    or str(last_not_whitespace) in NO_WHITESPACE_AFTER
                ):
                    tokenized_str = tokenized_str.strip()

                tokenized_str += item_as_string

                if item_as_string in NEWLINE_AFTER:
                    tokenized_str += "\n" + (indent_levels * "  ")
                elif item_as_string in WHITESPACE_AFTER:
                    tokenized_str += " "

                last_not_whitespace = item

            elif tokenized_str == tokenized_str.strip():
                tokenized_str += " "

        print(tokenized_str)  # TODO: Remove this when the MR is ready to be merged

        return tokenized_str
