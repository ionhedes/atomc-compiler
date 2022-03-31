import sys

from atomc.lexer.lexical_error_exception import LexicalErrorException
from atomc.syntactic_analyzer.analyzer import analyze
from atomc.syntactic_analyzer.syntax_error_exception import SyntaxErrorException
from lexer import lexer

if __name__ == '__main__':
    try:

        # WARNING: setting recursion limit, this may crash the program because we don't know how much C stack
        # we have available
        # with 3000 it overflows, check the code for loops
        # sys.setrecursionlimit(3000)

        file = open("atomc/resources/test5.c", "r")
        tokens = lexer.tokenize(file)

        for tk in tokens:
            print(tk)

        file.close()

        # ce se intampla cu definitiile cu inceput comun? cum se mai intoarce iteratorul??
        analyze(tokens)

    except FileNotFoundError:
        print("Source file not found")
    except LexicalErrorException:
        pass
    except SyntaxErrorException as syntax_err:
        print(str(syntax_err))
