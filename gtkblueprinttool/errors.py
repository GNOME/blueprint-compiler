# errors.py
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


import sys, traceback
from . import utils


class _colors:
    RED = '\033[91m'
    YELLOW = '\033[33m'
    FAINT = '\033[2m'
    BOLD = '\033[1m'
    CLEAR = '\033[0m'

class PrintableError(Exception):
    """ Parent class for errors that can be pretty-printed for the user, e.g.
    compilation warnings and errors. """

    def pretty_print(self, filename, code):
        raise NotImplementedError()


class CompileError(PrintableError):
    """ A PrintableError with a start/end position and optional hints """

    category = "error"

    def __init__(self, message, start=None, end=None, did_you_mean=None, hints=None):
        super().__init__(message)

        self.message = message
        self.start = start
        self.end = end
        self.hints = hints or []

        if did_you_mean is not None:
            self._did_you_mean(*did_you_mean)

    def hint(self, hint: str):
        self.hints.append(hint)
        return self


    def _did_you_mean(self, word: str, options: [str]):
        if word.replace("_", "-") in options:
            self.hint(f"use '-', not '_': `{word.replace('_', '-')}`")
            return

        recommend = utils.did_you_mean(word, options)
        if recommend is not None:
            if word.casefold() == recommend.casefold():
                self.hint(f"Did you mean `{recommend}` (note the capitalization)?")
            else:
                self.hint(f"Did you mean `{recommend}`?")
        else:
            self.hint("Did you check your spelling?")
            self.hint("Are your dependencies up to date?")

    def line_col_from_index(self, code, index):
        sp = code[:index].splitlines(keepends=True)
        line_num = len(sp)
        col_num = len(sp[-1])
        return (line_num, col_num)

    def pretty_print(self, filename, code):
        line_num, col_num = self.line_col_from_index(code, self.start + 1)
        line = code.splitlines(True)[line_num-1]

        print(f"""{_colors.RED}{_colors.BOLD}{self.category}: {self.message}{_colors.CLEAR}
at {filename} line {line_num} column {col_num}:
{_colors.FAINT}{line_num :>4} |{_colors.CLEAR}{line.rstrip()}\n     {_colors.FAINT}|{" "*(col_num-1)}^{_colors.CLEAR}""")

        for hint in self.hints:
            print(f"{_colors.FAINT}hint: {hint}{_colors.CLEAR}")
        print()


class AlreadyCaughtError(Exception):
    """ Emitted when a validation has already failed and its error message
    should not be repeated. """


class MultipleErrors(PrintableError):
    """ If multiple errors occur during compilation, they can be collected into
    a list and re-thrown using the MultipleErrors exception. It will
    pretty-print all of the errors and a count of how many errors there are. """

    def __init__(self, errors: [CompileError]):
        super().__init__()
        self.errors = errors

    def pretty_print(self, filename, code) -> str:
        for error in self.errors:
            error.pretty_print(filename, code)
        if len(self.errors) != 1:
            print(f"{len(self.errors)} errors")


class CompilerBugError(Exception):
    """ Emitted on assertion errors """


def assert_true(truth: bool, message:str=None):
    if not truth:
        raise CompilerBugError(message)


def report_compile_error():
    """ Report an error and ask people to report it. """

    print(traceback.format_exc())
    print(f"Arguments: {sys.argv}\n")
    print(f"""{_colors.BOLD}{_colors.RED}***** COMPILER BUG *****
The gtk-blueprint-tool program has crashed. Please report the above stacktrace
to the maintainers, along with the input file(s) if possible.{_colors.CLEAR}""")

