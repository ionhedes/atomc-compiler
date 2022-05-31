from atomc.domain_analyzer.domain_error_exception import DomainErrorException
from atomc.lexer import lexer
from atomc.lexer.lexical_error_exception import LexicalErrorException
from atomc.syntactic_analyzer.analyzer import analyze
from atomc.syntactic_analyzer.syntax_error_exception import SyntaxErrorException
from atomc.type_analyzer.type_analysis_exception import TypeAnalysisException
from atomc.virtual_machine.instruction import generate_test_vm_code2, test_vm, run
from atomc.virtual_machine.vm import init_vm

if __name__ == '__main__':
    try:
        file = open("atomc/resources/test9.c", "r")
        tokens = lexer.tokenize(file)

        file.close()

        instructions = analyze(tokens)

        run(instructions)

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
