class SyntaxErrorException(Exception):
    def __str__(self):
        return "Syntax Error(s) detected"
