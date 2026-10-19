import os
import sys

from pythonfuzz.main import PythonFuzz

from blueprintcompiler.outputs.xml import XmlOutput
from blueprintcompiler.parse_tree import AstNode
from blueprintcompiler.tokenizer import SourceCode

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from blueprintcompiler import gir, parser
from blueprintcompiler.completions import complete
from blueprintcompiler.errors import (
    CompilerBugError,
    PrintableError,
)
from blueprintcompiler.linter import lint
from blueprintcompiler.lsp import LanguageServer

fuzz_level = int(os.getenv("FUZZ_LEVEL") or "0")


@PythonFuzz
def fuzz(buf: bytes):
    try:
        blueprint = buf.decode("ascii")

        result = parser.parse(blueprint)

        if fuzz_level >= 1:
            assert_ast_doesnt_crash(result.source, result.ast)

        xml = XmlOutput()
        if result.success:
            xml.emit(result.ast)
    except CompilerBugError as e:
        raise e
    except PrintableError:
        pass
    except UnicodeDecodeError:
        pass


def assert_ast_doesnt_crash(source: SourceCode, ast: AstNode):
    lsp = LanguageServer()
    for i in range(len(source.text) + 1):
        ast.get_docs(i)
    for i in range(len(source.text) + 1):
        list(complete(lsp, ast, source, i))
    for i in range(len(source.text) + 1):
        ast.get_reference(i)
    ast.get_document_symbols()
    lint(ast)


if __name__ == "__main__":
    # Make sure Gtk 4.0 is accessible, otherwise every test will fail on that
    # and nothing interesting will be tested
    gir.get_namespace("Gtk", "4.0")

    fuzz()
