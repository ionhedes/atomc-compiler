class LexicalErrorException(Exception):

    def __str__(self):
        return "Lexical Error"


class InvalidRealNumberException(LexicalErrorException):

    def __str__(self):
        return "Invalid Real Number format"
