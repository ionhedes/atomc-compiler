from atomc.domain_analyzer.type import Type


class Returned:

    def __init__(self, given_type: Type, is_lval, is_constant):
        self.__name = "dummy"  # work on this later
        self.__type = given_type
        self.__is_lval = is_lval
        self.__is_constant = is_constant  # lvals might also be rvals sometimes, that is why you have flags for lval and const

    def is_lval(self) -> bool:
        return self.__is_lval

    def is_constant(self) -> bool:
        return self.__is_constant

    def get_name(self):
        return self.__name

    def has_scalar_type(self):
        return self.__type.is_scalar()

    def is_compatible_with(self, other):
        return self.__type.can_be_cast_to(other.__type)

    def get_type(self):
        return self.__type
