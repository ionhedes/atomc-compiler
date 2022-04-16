from atomc.domain_analyzer.symbol import Symbol


class DomainErrorException(Exception):

    def __init__(self, msg: str, symbol: Symbol, init_symbol: Symbol):
        self.__init_symbol = init_symbol
        self.__symbol = symbol
        self.__msg = msg

    def __str__(self):
        string = "Domain Error detected for symbol "
        string += self.__init_symbol.__str__()
        string += ", redefined as "
        string += self.__symbol.__str__()
        string += ", " + self.__msg
        return string
