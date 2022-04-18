from atomc.domain_analyzer.symbol import Symbol


class DomainErrorException(Exception):

    def __init__(self, msg: str, line=0):
        self.__msg = msg
        self._line = line

    def __str__(self):
        string = "line " + str(self._line) + ": " + self.__msg + " detected:\n"
        return string


class RedefinitionErrorException(DomainErrorException):

    def __init__(self, symbol: Symbol, redefined_symbol: Symbol, line=0):
        super().__init__("redefinition error", line)
        self.__symbol = symbol
        self.__redefined_symbol = redefined_symbol

    def __str__(self):
        string = super().__str__()
        string += self.__symbol.__str__()
        string += " redefines "
        string += self.__redefined_symbol.__str__()
        return string


class InvalidArraySizeErrorException(DomainErrorException):

    def __init__(self, var_name, line=0):
        super().__init__("array variable with no size", line)
        self.__var_name = var_name

    def __str__(self):
        string = super().__str__()
        string += self.__var_name
        return string


class NoStructDefErrorException(DomainErrorException):

    def __init__(self, struct_name, line=0):
        super().__init__("structure definition not", line)
        self.__struct_name = struct_name

    def __str__(self):
        string = super().__str__()
        string += "name "
        string += self.__struct_name
        return string

