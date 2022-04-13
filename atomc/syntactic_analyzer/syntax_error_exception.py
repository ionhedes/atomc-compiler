from atomc.lexer.token import Token, Code


class SyntaxErrorException(Exception):

    def __init__(self, token: Token, msg: str):
        self.__token = token
        self.__msg = msg

    def __str__(self):
        string = "Syntax Error(s) detected at line: " + str(self.__token.line) + ", token code " + str(
            self.__token.code)
        if (self.__token.code == Code.ID or self.__token.code == Code.CT_INT
                or self.__token.code == Code.CT_REAL or self.__token.code == Code.CT_CHAR
                or self.__token.code == Code.CT_STRING):
            string += ", token value: " + str(self.__token.value)

        string += ", " + self.__msg
        return string
