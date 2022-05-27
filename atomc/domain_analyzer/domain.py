from atomc.domain_analyzer.domain_error_exception import DomainErrorException, RedefinitionErrorException
from atomc.domain_analyzer.symbol import NonFunctionalSymbol
from atomc.type_analyzer.type_analysis_exception import UndefinedIdException


class Domain:

    def __init__(self):
        self.__symbols = list()
        self.__values = dict()

    def add_symbol_to_domain(self, symbol):
        self.__symbols.append(symbol)

    def get_symbols(self):
        return self.__symbols

    def find_symbol_in_domain(self, name):
        for symbol in self.__symbols:
            if symbol.name_matches(name):
                return symbol

        return None

    def update_symbol_value(self, name, value):
        self.__values[name] = value

    def get_symbol_value(self, name):
        return self.__values[name]


class DomainStack:

    def __init__(self):
        self.__domains = list()
        self.__size = 0

    # iterating over the domain stack should always happen in a LIFO manner
    def __iter__(self):
        return reversed(self.__domains).__iter__()

    def push_domain(self):
        self.__domains.append(Domain())
        self.__size = self.__size + 1

    def pop_domain(self):
        if self.__size == 0:
            raise IndexError()
        self.__domains.pop(self.__size - 1)
        self.__size = self.__size - 1

    def peek_domain(self):
        return self.__domains.__getitem__(self.__size - 1)

    # line refers to the line where the symbol starts in the source file
    def add_symbol_to_current_domain(self, symbol, line=0):

        crt_domain = self.peek_domain()

        for s in crt_domain.get_symbols():
            if s.name_matches(symbol.get_name()):
                raise RedefinitionErrorException(symbol, s, line)

        self.peek_domain().add_symbol_to_domain(symbol)

    def get_symbol_addr(self, name):

        for domain in self.__iter__():
            symbol = domain.find_symbol_in_domain(name)
            if symbol and isinstance(symbol, NonFunctionalSymbol):
                return symbol

        raise UndefinedIdException(name)

    def get_global_addr(self, name):

        domain = self.__domains[len(self.__domains) - 1]

        symbol = domain.find_symbol_in_domain(name)
        if symbol and isinstance(symbol, NonFunctionalSymbol):
            return symbol

        raise UndefinedIdException(name)
