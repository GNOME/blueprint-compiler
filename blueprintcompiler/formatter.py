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

newline_after = [";", "]"]
opening_tokens = ["{"]
closing_tokens = ["}"]


class Format:
    def format(data):
        indent_levels = 0
        tokens = tokenizer.tokenize(data)
        tokenized_str = ""

        for index, item in enumerate(tokens):

            if item.type != tokenizer.TokenType.WHITESPACE:

                if str(item) in opening_tokens:
                    indent_levels += 1
                elif str(item) in closing_tokens:
                    tokenized_str = tokenized_str[:-2]
                    indent_levels -= 1

                tokenized_str += str(item)

                if str(item) in newline_after + closing_tokens + opening_tokens:
                    tokenized_str += "\n"
                    tokenized_str += indent_levels * "  "
            else:
                tokenized_str += " "

        return tokenized_str
