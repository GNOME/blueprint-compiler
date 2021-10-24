# lsp.py
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


import json, sys, traceback

from .errors import PrintableError, CompileError, MultipleErrors
from .lsp_utils import *
from . import tokenizer, parser, utils


def command(json_method):
    def decorator(func):
        func._json_method = json_method
        return func
    return decorator


class LanguageServer:
    commands = {}

    def __init__(self):
        self.client_capabilities = {}
        self._open_files: {str: OpenFile} = {}

    def run(self):
        try:
            while True:
                line = ""
                content_len = -1
                while content_len == -1 or (line != "\n" and line != "\r\n"):
                    line = sys.stdin.readline()
                    if line == "":
                        return
                    if line.startswith("Content-Length:"):
                        content_len = int(line.split("Content-Length:")[1].strip())
                line = sys.stdin.read(content_len)
                self._log("input: " + line)

                data = json.loads(line)
                method = data.get("method")
                id = data.get("id")
                params = data.get("params")

                if method in self.commands:
                    self.commands[method](self, id, params)
        except Exception as e:
            self._log(traceback.format_exc())


    def _send(self, data):
        data["jsonrpc"] = "2.0"
        line = json.dumps(data, separators=(",", ":")) + "\r\n"
        self._log("output: " + line)
        sys.stdout.write(f"Content-Length: {len(line)}\r\nContent-Type: application/vscode-jsonrpc; charset=utf-8\r\n\r\n{line}")
        sys.stdout.flush()

    def _log(self, msg):
        pass

    def _send_response(self, id, result):
        self._send({
            "id": id,
            "result": result,
        })

    def _send_notification(self, method, params):
        self._send({
            "method": method,
            "params": params,
        })


    @command("initialize")
    def initialize(self, id, params):
        self.client_capabilities = params.get("capabilities")
        self._send_response(id, {
            "capabilities": {
                "textDocumentSync": {
                    "openClose": True,
                    "change": TextDocumentSyncKind.Incremental,
                }
            }
        })

    @command("textDocument/didOpen")
    def didOpen(self, id, params):
        doc = params.get("textDocument")
        uri = doc.get("uri")
        version = doc.get("version")
        text = doc.get("text")

        open_file = OpenFile(uri, text, version)
        self._open_files[uri] = open_file
        self._send_file_updates(open_file)

    @command("textDocument/didChange")
    def didChange(self, id, params):
        open_file = self._open_files[params.textDocument.uri]

        open_file.apply_changes(params.contentChanges)
        self._send_file_updates(open_file)

    @command("textDocument/didClose")
    def didClose(self, id, params):
        del self._open_files[params.textDocument.uri]


    def _send_file_updates(self, open_file: OpenFile):
        self._send_notification("textDocument/publishDiagnostics", {
            "uri": uri,
            "diagnostics": [self._create_diagnostic(open_file.text, err) for err in open_file.diagnostics],
        })

    def _create_diagnostic(self, text, err):
        start_l, start_c = utils.idx_to_pos(err.start, text)
        end_l, end_c = utils.idx_to_pos(err.end or err.start, text)
        return {
            "range": {
                "start": { "line": start_l - 1, "character": start_c },
                "end": { "line": end_l - 1, "character": end_c },
            },
            "message": err.message,
            "severity": 1,
        }


for name in dir(LanguageServer):
    item = getattr(LanguageServer, name)
    if callable(item) and hasattr(item, "_json_method"):
        LanguageServer.commands[item._json_method] = item

