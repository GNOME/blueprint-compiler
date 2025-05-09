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


import json
import sys
import traceback
import typing as T
from difflib import SequenceMatcher

from . import decompiler, formatter, parser, tokenizer, utils, xml_reader
from .ast_utils import AstNode
from .completions import complete
from .errors import CompileError, MultipleErrors
from .lsp_utils import *
from .outputs.xml import XmlOutput
from .tokenizer import Token


def printerr(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def command(json_method: str):
    def decorator(func):
        func._json_method = json_method
        return func

    return decorator


class OpenFile:
    def __init__(self, uri: str, text: str, version: int) -> None:
        self.uri = uri
        self.text = text
        self.version = version
        self.ast: T.Optional[AstNode] = None
        self.tokens: T.Optional[list[Token]] = None

        self._update()

    def apply_changes(self, changes) -> None:
        for change in changes:
            if "range" not in change:
                self.text = change["text"]
                continue
            start = utils.pos_to_idx(
                change["range"]["start"]["line"],
                change["range"]["start"]["character"],
                self.text,
            )
            end = utils.pos_to_idx(
                change["range"]["end"]["line"],
                change["range"]["end"]["character"],
                self.text,
            )
            self.text = self.text[:start] + change["text"] + self.text[end:]
        self._update()

    def _update(self) -> None:
        self.diagnostics: list[CompileError] = []
        try:
            self.tokens = tokenizer.tokenize(self.text)
            self.ast, errors, warnings = parser.parse(self.tokens)
            self.diagnostics += warnings
            if errors is not None:
                self.diagnostics += errors.errors
        except MultipleErrors as e:
            self.diagnostics += e.errors
        except CompileError as e:
            self.diagnostics.append(e)

    def calc_semantic_tokens(self) -> T.List[int]:
        if self.ast is None:
            return []

        tokens = list(self.ast.get_semantic_tokens())
        token_lists = [
            [
                *utils.idx_to_pos(token.start, self.text),  # line and column
                token.end - token.start,  # length
                token.type,
                0,  # token modifiers
            ]
            for token in tokens
        ]

        # convert line, column numbers to deltas
        for a, b in zip(token_lists[-2::-1], token_lists[:0:-1]):
            b[0] -= a[0]
            if b[0] == 0:
                b[1] -= a[1]

        # flatten the list
        return [x for y in token_lists for x in y]


class LanguageServer:
    commands: T.Dict[str, T.Callable] = {}

    def __init__(self):
        self.client_capabilities = {}
        self.client_supports_completion_choice = False
        self._open_files: T.Dict[str, OpenFile] = {}
        self._exited = False

    def run(self):
        # Read <doc> tags from gir files. During normal compilation these are
        # ignored.
        xml_reader.PARSE_GIR.add("doc")

        try:
            while not self._exited:
                line = ""
                content_len = -1
                while content_len == -1 or (line != "\n" and line != "\r\n"):
                    line = sys.stdin.buffer.readline().decode()
                    if line == "":
                        return
                    if line.startswith("Content-Length:"):
                        content_len = int(line.split("Content-Length:")[1].strip())
                line = sys.stdin.buffer.read(content_len).decode()
                printerr("input: " + line)

                data = json.loads(line)
                method = data.get("method")
                id = data.get("id")
                params = data.get("params")

                if method in self.commands:
                    self.commands[method](self, id, params)
        except Exception as e:
            printerr(traceback.format_exc())

    def _send(self, data):
        data["jsonrpc"] = "2.0"
        line = json.dumps(data, separators=(",", ":"))
        printerr("output: " + line)
        sys.stdout.write(
            f"Content-Length: {len(line.encode())}\r\nContent-Type: application/vscode-jsonrpc; charset=utf-8\r\n\r\n{line}"
        )
        sys.stdout.flush()

    def _send_error(self, id, code, message, data=None):
        self._send(
            {
                "id": id,
                "error": {
                    "code": code,
                    "message": message,
                    "data": data,
                },
            }
        )

    def _send_response(self, id, result):
        self._send(
            {
                "id": id,
                "result": result,
            }
        )

    def _send_notification(self, method, params):
        self._send(
            {
                "method": method,
                "params": params,
            }
        )

    @command("initialize")
    def initialize(self, id, params):
        from . import main

        self.client_capabilities = params.get("capabilities", {})
        self.client_supports_completion_choice = params.get("clientInfo", {}).get(
            "name"
        ) in ["Visual Studio Code", "VSCodium"]
        self._send_response(
            id,
            {
                "capabilities": {
                    "textDocumentSync": {
                        "openClose": True,
                        "change": TextDocumentSyncKind.Incremental,
                    },
                    "semanticTokensProvider": {
                        "legend": {
                            "tokenTypes": ["enumMember"],
                            "tokenModifiers": [],
                        },
                        "full": True,
                    },
                    "completionProvider": {},
                    "codeActionProvider": {},
                    "hoverProvider": True,
                    "documentSymbolProvider": True,
                    "definitionProvider": True,
                    "documentFormattingProvider": True,
                },
                "serverInfo": {
                    "name": "Blueprint",
                    "version": main.VERSION,
                },
            },
        )

    @command("shutdown")
    def shutdown(self, id, params):
        self._send_response(id, None)

    @command("exit")
    def exit(self, id, params):
        self._exited = True

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
        if params is not None:
            open_file = self._open_files[params["textDocument"]["uri"]]
            open_file.apply_changes(params["contentChanges"])
            self._send_file_updates(open_file)

    @command("textDocument/didClose")
    def didClose(self, id, params):
        del self._open_files[params["textDocument"]["uri"]]

    @command("textDocument/hover")
    def hover(self, id, params):
        open_file = self._open_files[params["textDocument"]["uri"]]
        docs = open_file.ast and open_file.ast.get_docs(
            utils.pos_to_idx(
                params["position"]["line"],
                params["position"]["character"],
                open_file.text,
            )
        )
        if docs:
            self._send_response(
                id,
                {
                    "contents": {
                        "kind": "markdown",
                        "value": docs,
                    }
                },
            )
        else:
            self._send_response(id, None)

    @command("textDocument/completion")
    def completion(self, id, params):
        open_file = self._open_files[params["textDocument"]["uri"]]

        if open_file.ast is None:
            self._send_response(id, [])
            return

        idx = utils.pos_to_idx(
            params["position"]["line"], params["position"]["character"], open_file.text
        )
        completions = complete(self, open_file.ast, open_file.tokens, idx)
        self._send_response(
            id, [completion.to_json(True) for completion in completions]
        )

    @command("textDocument/formatting")
    def formatting(self, id, params):
        open_file = self._open_files[params["textDocument"]["uri"]]

        if open_file.text is None:
            self._send_error(id, ErrorCode.RequestFailed, "Document is not open")
            return

        try:
            formatted_blp = formatter.format(
                open_file.text,
                params["options"]["tabSize"],
                params["options"]["insertSpaces"],
            )
        except PrintableError:
            self._send_error(id, ErrorCode.RequestFailed, "Could not format document")
            return

        lst = []
        for tag, i1, i2, j1, j2 in SequenceMatcher(
            None, open_file.text, formatted_blp
        ).get_opcodes():
            if tag in ("replace", "insert", "delete"):
                lst.append(
                    TextEdit(
                        Range(i1, i2, open_file.text),
                        "" if tag == "delete" else formatted_blp[j1:j2],
                    ).to_json()
                )

        self._send_response(id, lst)

    @command("textDocument/x-blueprint-compile")
    def compile(self, id, params):
        open_file = self._open_files[params["textDocument"]["uri"]]

        if open_file.ast is None:
            self._send_error(id, ErrorCode.RequestFailed, "Document is not open")
            return

        xml = None
        try:
            output = XmlOutput()
            xml = output.emit(open_file.ast, indent=2, generated_notice=False)
        except:
            printerr(traceback.format_exc())
            self._send_error(id, ErrorCode.RequestFailed, "Could not compile document")
            return
        self._send_response(id, {"xml": xml})

    @command("x-blueprint/decompile")
    def decompile(self, id, params):
        text = params.get("text")
        blp = None
        if text.strip() == "":
            blp = ""
            printerr("Decompiled to empty blueprint because input was empty")
        else:
            try:
                blp = decompiler.decompile_string(text)
            except decompiler.UnsupportedError as e:
                self._send_error(id, ErrorCode.RequestFailed, e.message)
                return
            except:
                printerr(traceback.format_exc())
                self._send_error(id, ErrorCode.RequestFailed, "Invalid input")
                return

        self._send_response(id, {"blp": blp})

    @command("textDocument/semanticTokens/full")
    def semantic_tokens(self, id, params):
        open_file = self._open_files[params["textDocument"]["uri"]]

        self._send_response(
            id,
            {
                "data": open_file.calc_semantic_tokens(),
            },
        )

    @command("textDocument/codeAction")
    def code_actions(self, id, params):
        open_file = self._open_files[params["textDocument"]["uri"]]

        range = Range(
            utils.pos_to_idx(
                params["range"]["start"]["line"],
                params["range"]["start"]["character"],
                open_file.text,
            ),
            utils.pos_to_idx(
                params["range"]["end"]["line"],
                params["range"]["end"]["character"],
                open_file.text,
            ),
            open_file.text,
        )

        actions = [
            {
                "title": action.title,
                "kind": "quickfix",
                "diagnostics": [self._create_diagnostic(open_file.uri, diagnostic)],
                "edit": {
                    "changes": {
                        open_file.uri: [
                            {
                                "range": (
                                    action.edit_range.to_json()
                                    if action.edit_range
                                    else diagnostic.range.to_json()
                                ),
                                "newText": action.replace_with,
                            }
                        ]
                    }
                },
            }
            for diagnostic in open_file.diagnostics
            if range.overlaps(diagnostic.range)
            for action in diagnostic.actions
        ]

        self._send_response(id, actions)

    @command("textDocument/documentSymbol")
    def document_symbols(self, id, params):
        open_file = self._open_files[params["textDocument"]["uri"]]
        symbols = open_file.ast.get_document_symbols()

        def to_json(symbol: DocumentSymbol):
            result = {
                "name": symbol.name,
                "kind": symbol.kind,
                "range": symbol.range.to_json(),
                "selectionRange": symbol.selection_range.to_json(),
                "children": [to_json(child) for child in symbol.children],
            }
            if symbol.detail is not None:
                result["detail"] = symbol.detail
            return result

        self._send_response(id, [to_json(symbol) for symbol in symbols])

    @command("textDocument/definition")
    def definition(self, id, params):
        open_file = self._open_files[params["textDocument"]["uri"]]
        idx = utils.pos_to_idx(
            params["position"]["line"], params["position"]["character"], open_file.text
        )
        definition = open_file.ast.get_reference(idx)
        if definition is None:
            self._send_response(id, None)
        else:
            self._send_response(
                id,
                definition.to_json(open_file.uri),
            )

    def _send_file_updates(self, open_file: OpenFile):
        self._send_notification(
            "textDocument/publishDiagnostics",
            {
                "uri": open_file.uri,
                "diagnostics": [
                    self._create_diagnostic(open_file.uri, err)
                    for err in open_file.diagnostics
                ],
            },
        )

    def _create_diagnostic(self, uri: str, err: CompileError):
        message = err.message

        assert err.range is not None

        for hint in err.hints:
            message += "\nhint: " + hint

        result = {
            "range": err.range.to_json(),
            "message": message,
            "severity": (
                DiagnosticSeverity.Warning
                if isinstance(err, CompileWarning)
                else DiagnosticSeverity.Error
            ),
        }

        if isinstance(err, DeprecatedWarning):
            result["tags"] = [DiagnosticTag.Deprecated]

        if isinstance(err, UnusedWarning):
            result["tags"] = [DiagnosticTag.Unnecessary]

        if len(err.references) > 0:
            result["relatedInformation"] = [
                {
                    "location": {
                        "uri": uri,
                        "range": ref.range.to_json(),
                    },
                    "message": ref.message,
                }
                for ref in err.references
            ]

        return result


for name in dir(LanguageServer):
    item = getattr(LanguageServer, name)
    if callable(item) and hasattr(item, "_json_method"):
        LanguageServer.commands[item._json_method] = item
