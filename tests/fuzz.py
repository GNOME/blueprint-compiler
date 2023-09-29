import os
import sys

from pythonfuzz.main import PythonFuzz

from blueprintcompiler.outputs.xml import XmlOutput

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from blueprintcompiler import gir, parser, tokenizer
from blueprintcompiler.completions import complete
from blueprintcompiler.errors import CompilerBugError, PrintableError
from blueprintcompiler.lsp import LanguageServer


def assert_ast_doesnt_crash(text, tokens, ast):
    for i in range(len(text)):
        ast.get_docs(i)
    for i in range(len(text)):
        list(complete(LanguageServer(), ast, tokens, i))
    ast.get_document_symbols()


@PythonFuzz
def fuzz(buf):
    try:
        blueprint = buf.decode("ascii")

        tokens = tokenizer.tokenize(blueprint)
        ast, errors, warnings = parser.parse(tokens)

        xml = XmlOutput()
        if errors is None and ast is not None:
            xml.emit(ast)
            assert_ast_doesnt_crash(blueprint, tokens, ast)
    except CompilerBugError as e:
        raise e
    except PrintableError:
        pass
    except UnicodeDecodeError:
        pass


if __name__ == "__main__":
    # Make sure Gtk 4.0 is accessible, otherwise every test will fail on that
    # and nothing interesting will be tested
    gir.get_namespace("Gtk", "4.0")

    fuzz()
