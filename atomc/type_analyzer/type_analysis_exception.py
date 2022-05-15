from atomc.domain_analyzer.symbol import Symbol
from atomc.domain_analyzer.type import Type


class TypeAnalysisException(Exception):

    def __init__(self, msg: str, line=0):
        self.__msg = msg
        self._line = line

    def __str__(self):
        string = "line " + str(self._line) + ": " + self.__msg + " detected:\n"
        return string


class TypeCastException(TypeAnalysisException):

    def __init__(self, symbol: Symbol, invalid_type: Type, line=0):
        super().__init__("cast exception", line)
        self.__symbol = symbol
        self.__invalid_type = invalid_type

    def __str__(self):
        string = super().__str__()
        string += self.__symbol.__str__()
        string += " cannot be cast to "
        string += self.__invalid_type.__str__()
        return string


class UndefinedIdException(TypeAnalysisException):

    def __init__(self, name, line=0):
        super().__init__("undefined id ", line)
        self.__name = name

    def __str__(self):
        string = super().__str__()
        string += self.__name
        return string


class UncallableIdException(TypeAnalysisException):

    def __init__(self, symbol, line=0):
        super().__init__("not a function ", line)
        self.__symbol = symbol

    def __str__(self):
        string = super().__str__()
        string += self.__symbol.get_name()
        return string


class NotLvalException(TypeAnalysisException):

    def __init__(self, name, line=0):
        super().__init__("not a lval ", line)
        self.__name = name

    def __str__(self):
        string = super().__str__()
        string += self.__name
        return string


class ConstantException(TypeAnalysisException):

    def __init__(self, name, line=0):
        super().__init__("expression cannot be a constant ", line)
        self.__name = name

    def __str__(self):
        string = super().__str__()
        string += self.__name
        return string
