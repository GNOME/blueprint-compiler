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
    category = "error"

    def __init__(self, message, start, end=None):
        super().__init__(message)

        self.message = message
        self.start = start
        self.end = end

    def pretty_print(self, filename, code):
        sp = code[:self.start+1].splitlines(keepends=True)
        line_num = len(sp)
        col_num = len(sp[-1])
        line = code.splitlines(True)[line_num-1]

        print(f"""{_colors.RED}{_colors.BOLD}{self.category}: {self.message}{_colors.CLEAR}
at {filename} line {line_num} column {col_num}:
{_colors.FAINT}{line_num :>4} |{_colors.CLEAR}{line.rstrip()}\n     {_colors.FAINT}|{" "*(col_num-1)}^{_colors.CLEAR}
""")


class TokenizeError(CompileError):
    def __init__(self, start):
        super().__init__("Could not determine what kind of syntax is meant here", start)


class ParseError(CompileError):
    pass


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

