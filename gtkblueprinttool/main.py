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


import argparse, json, os, sys

from .errors import PrintableError, report_compile_error, MultipleErrors
from .lsp import LanguageServer
from . import parser, tokenizer
from .xml_emitter import XmlEmitter


VERSION = "0.1.0"


class BlueprintApp:
    def main(self):
        self.parser = argparse.ArgumentParser()
        self.subparsers = self.parser.add_subparsers(metavar="command")
        self.parser.set_defaults(func=self.cmd_help)

        compile = self.add_subcommand("compile", "Compile blueprint files", self.cmd_compile)
        compile.add_argument("--output", dest="output", default="-")
        compile.add_argument("input", metavar="filename", default=sys.stdin, type=argparse.FileType('r'))

        batch_compile = self.add_subcommand("batch-compile", "Compile many blueprint files at once", self.cmd_batch_compile)
        batch_compile.add_argument("output_dir", metavar="output-dir")
        batch_compile.add_argument("inputs", nargs="+", metavar="filenames", default=sys.stdin, type=argparse.FileType('r'))

        lsp = self.add_subcommand("lsp", "Run the language server (for internal use by IDEs)", self.cmd_lsp)

        self.add_subcommand("help", "Show this message", self.cmd_help)

        try:
            opts = self.parser.parse_args()
            opts.func(opts)
        except SystemExit as e:
            raise e
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
            xml = self._compile(data)

            if opts.output == "-":
                print(xml)
            else:
                with open(opts.output, "w") as file:
                    file.write(xml)
        except PrintableError as e:
            e.pretty_print(opts.input.name, data)
            sys.exit(1)


    def cmd_batch_compile(self, opts):
        for file in opts.inputs:
            data = file.read()

            try:
                xml = self._compile(data)

                name = os.path.splitext(os.path.basename(file.name))[0] + ".ui"
                with open(os.path.join(opts.output_dir, name), "w") as file:
                    file.write(xml)
            except PrintableError as e:
                e.pretty_print(file.name, data)
                sys.exit(1)


    def cmd_lsp(self, opts):
        langserv = LanguageServer()
        langserv.run()


    def _compile(self, data: str) -> str:
        tokens = tokenizer.tokenize(data)
        ast = parser.parse(tokens)

        if len(ast.errors):
            raise MultipleErrors(ast.errors)

        return ast.generate()


def main():
    BlueprintApp().main()
