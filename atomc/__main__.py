import sys

from atomc.domain_analyzer.domain_error_exception import DomainErrorException
from atomc.lexer.lexical_error_exception import LexicalErrorException
from atomc.syntactic_analyzer.analyzer import analyze
from atomc.syntactic_analyzer.syntax_error_exception import SyntaxErrorException
from atomc.type_analyzer.type_analysis_exception import TypeAnalysisException
from lexer import lexer

if __name__ == '__main__':
    try:

        file = open("atomc/resources/test8.c", "r")
        tokens = lexer.tokenize(file)

        # for tk in tokens:
        #     print(tk)

        file.close()

        symbols = analyze(tokens)

        for s in symbols:
            print(s)

    except FileNotFoundError:
        print("Source file not found")
    except LexicalErrorException:
        pass
    except SyntaxErrorException as syntax_err:
        print(str(syntax_err))
    except DomainErrorException as domain_err:
        print(str(domain_err))
    except TypeAnalysisException as type_err:
        print(str(type_err))
