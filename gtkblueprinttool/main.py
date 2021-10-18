# main.py
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


import argparse, sys

from .errors import PrintableError, report_compile_error
from .pipeline import Pipeline
from . import parser, tokenizer


VERSION = "0.1.0"


class BlueprintApp:
    def main(self):
        self.parser = argparse.ArgumentParser()
        self.subparsers = self.parser.add_subparsers(metavar="command")
        self.parser.set_defaults(func=self.cmd_help)

        compile = self.add_subcommand("compile", "Compile blueprint files", self.cmd_compile)
        compile.add_argument("--output", dest="output", default="-")
        compile.add_argument("input", metavar="filename", default=sys.stdin, type=argparse.FileType('r'))

        self.add_subcommand("help", "Show this message", self.cmd_help)

        try:
            opts = self.parser.parse_args()
            opts.func(opts)
        except:
            report_compile_error()


    def add_subcommand(self, name, help, func):
        parser = self.subparsers.add_parser(name, help=help)
        parser.set_defaults(func=func)
        return parser

    def cmd_help(self, opts):
        self.parser.print_help()

    def cmd_compile(self, opts):
        data = opts.input.read()
        try:
            tokens = tokenizer.tokenize(data)
            ast = parser.parse(tokens)
            xml = ast.generate()
            if opts.output == "-":
                print(xml)
            else:
                with open(opts.output, "w") as file:
                    file.write(xml)
        except PrintableError as e:
            e.pretty_print(opts.input.name, data)
            sys.exit(1)


def main():
    BlueprintApp().main()
