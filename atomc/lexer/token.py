from enum import Enum


class Code(Enum):
    ERR = 0
    ID = 1
    CT_INT = 3
    CT_REAL = 4
    CT_CHAR = 5
    CT_STRING = 6
    COMMA = 7
    SEMICOLON = 8
    LPAR = 9
    RPAR = 10
    LBRACKET = 11
    RBRACKET = 12
    LACC = 13
    RACC = 14
    END = 15
    ADD = 16
    SUB = 17
    MUL = 18
    DIV = 19
    AND = 20
    OR = 21
    EQUAL = 22
    NOTEQ = 23
    LESSEQ = 24
    GREATEREQ = 25
    ASSIGN = 26
    NOT = 27
    LESS = 28
    GREATER = 29
    SPACE = 30


class Token:
    def __init__(self, code, value, line):
        self.code = code
        self.value = value
        self.line = line

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.code == other.code and self.line == other.line and self.value == other.value
        else:
            return False

    def __str__(self):
        string = str(self.code) + ": "
        if (self.code == Code.ID or self.code == Code.CT_INT or
                self.code == Code.CT_REAL or self.code == Code.CT_STRING or
                self.code == Code.CT_CHAR):
            string = string + str(self.value) + ", "
        string = string + "line " + str(self.line)
        return string
