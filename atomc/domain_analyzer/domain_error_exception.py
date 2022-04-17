from atomc.domain_analyzer.symbol import Symbol


class DomainErrorException(Exception):

    def __init__(self, msg: str):
        self.__msg = msg

    def __str__(self):
        string = self.__msg + " detected: "
        return string


class RedefinitionErrorException(DomainErrorException):

    def __init__(self, symbol: Symbol, redefined_symbol: Symbol):
        super().__init__("Redefinition error")
        self.__symbol = symbol
        self.__redefined_symbol = redefined_symbol

    def __str__(self):
        string = super().__str__()
        string += self.__symbol.__str__()
        string += ", redefines "
        string += self.__redefined_symbol.__str__()
        return string


class InvalidArraySizeErrorException(DomainErrorException):

    def __init__(self, var_name):
        super().__init__("Array variable with no size")
        self.__var_name = var_name

    def __str__(self):
        string = super().__str__()
        string += self.__var_name
        return string


class NoStructDefErrorException(DomainErrorException):

    def __init__(self, struct_name):
        super().__init__("Structure definition not")
        self.__struct_name = struct_name

    def __str__(self):
        string = super().__str__()
        string += "name "
        string += self.__struct_name
        return string

