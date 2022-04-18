from pythonfuzz.main import PythonFuzz

from blueprintcompiler import tokenizer, parser, decompiler
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

        if errors is None and len(ast.errors) == 0:
            actual = ast.generate()
    except CompilerBugError as e:
        raise e
    except PrintableError:
        pass
    except UnicodeDecodeError:
        pass

if __name__ == "__main__":
    fuzz()
