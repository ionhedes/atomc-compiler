from atomc.domain_analyzer.domain_error_exception import DomainErrorException


class Domain:

    def __init__(self):
        self.__symbols = list()

    def add_symbol_to_domain(self, symbol):
        self.__symbols.append(symbol)

    def get_symbols(self):
        return self.__symbols


class DomainStack:

    def __init__(self):
        self.__domains = list()
        self.__size = 0

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

    def add_symbol_to_current_domain(self, symbol):

        crt_domain = self.peek_domain()

        for s in crt_domain.get_symbols():
            if s.name_matches(symbol.get_name()):
                raise DomainErrorException("name already used", symbol, s)

        self.peek_domain().add_symbol_to_domain(symbol)
