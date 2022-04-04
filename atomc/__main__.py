import sys

from atomc.lexer.lexical_error_exception import LexicalErrorException
from atomc.syntactic_analyzer.analyzer import analyze
from atomc.syntactic_analyzer.syntax_error_exception import SyntaxErrorException
from lexer import lexer

if __name__ == '__main__':
    try:

        file = open("atomc/resources/test5.c", "r")
        tokens = lexer.tokenize(file)

        for tk in tokens:
            print(tk)

        file.close()

        analyze(tokens)

    except FileNotFoundError:
        print("Source file not found")
    except LexicalErrorException:
        pass
    except SyntaxErrorException as syntax_err:
        print(str(syntax_err))
