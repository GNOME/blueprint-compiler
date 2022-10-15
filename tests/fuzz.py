import os, sys
from pythonfuzz.main import PythonFuzz

from blueprintcompiler.outputs.xml import XmlOutput

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from blueprintcompiler import tokenizer, parser, decompiler, gir
from blueprintcompiler.completions import complete
from blueprintcompiler.errors import PrintableError, MultipleErrors, CompileError, CompilerBugError
from blueprintcompiler.tokenizer import Token, TokenType, tokenize
from blueprintcompiler import utils

@PythonFuzz
def fuzz(buf):
    try:
        blueprint = buf.decode("ascii")

        tokens = tokenizer.tokenize(blueprint)
        ast, errors, warnings = parser.parse(tokens)

        xml = XmlOutput()
        if errors is None and len(ast.errors) == 0:
            xml.emit(ast)
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
