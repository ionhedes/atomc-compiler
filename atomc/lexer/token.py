from enum import Enum


class Code(Enum):
    DOT = 0
    ID = 1
    CT_INT = 2
    CT_REAL = 3
    CT_CHAR = 4
    CT_STRING = 5
    COMMA = 6
    SEMICOLON = 7
    LPAR =8
    RPAR = 9
    LBRACKET = 10
    RBRACKET = 11
    LACC = 12
    RACC = 13
    END = 14
    ADD = 15
    SUB = 16
    MUL = 17
    DIV = 18
    AND = 19
    OR = 20
    EQUAL = 21
    NOTEQ = 22
    LESSEQ = 23
    GREATEREQ = 24
    ASSIGN = 25
    NOT = 26
    LESS = 27
    GREATER = 28
    SPACE = 29
    LINECOMMENT = 30

    # keywords
    BREAK = 31
    CHAR = 32
    DOUBLE = 33
    ELSE = 34
    FOR = 35
    IF = 36
    INT = 37
    RETURN = 38
    STRUCT = 39
    VOID = 40
    WHILE = 41


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
        string = "line " + str(self.line) + ":  " + str(self.code)
        if (self.code == Code.ID or self.code == Code.CT_INT or
                self.code == Code.CT_REAL or self.code == Code.CT_STRING or
                self.code == Code.CT_CHAR):
            string = string + ": " + str(self.value)

        return string
