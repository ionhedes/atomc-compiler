import math
import sys


class Base:

    def get_base_size(self):
        pass

    def get_base_name(self):
        return self.__class__.__name__

    def can_be_returned(self):
        pass

    def __eq__(self, other):
        if isinstance(other, Base):
            return self.get_base_name() == self.get_base_name()


class Integer(Base):
    __BASE_SIZE = 4
    __RETURNABLE = True

    def __str__(self):
        return "int"

    def get_base_size(self):
        return self.__BASE_SIZE

    def can_be_returned(self):
        return self.__RETURNABLE


class Double(Base):
    __BASE_SIZE = 8
    __RETURNABLE = True

    def __str__(self):
        return "double"

    def get_base_size(self):
        return self.__BASE_SIZE

    def can_be_returned(self):
        return self.__RETURNABLE


class Character(Base):
    __BASE_SIZE = 1
    __RETURNABLE = True

    def __str__(self):
        return "char"

    def get_base_size(self):
        return self.__BASE_SIZE

    def can_be_returned(self):
        return self.__RETURNABLE


class Void(Base):
    __BASE_SIZE = 0
    __RETURNABLE = False

    def __str__(self):
        return "void"

    def get_base_size(self):
        return self.__BASE_SIZE

    def can_be_returned(self):
        return self.__RETURNABLE


class Struct(Base):
    __RETURNABLE = False

    def __init__(self, struct):
        self.__struct_definition = struct

    def __str__(self):
        return "struct " + self.__struct_definition.get_name()

    def get_base_size(self):
        return self.__struct_definition.get_symbol_type_size()

    def can_be_returned(self):
        return self.__RETURNABLE

    def has_struct_member(self, name):
        return self.__struct_definition.has_member(name)

    def get_struct_member(self, name):
        return self.__struct_definition.get_member(name)

    def get_struct_definition(self):
        return self.__struct_definition

    def __eq__(self, other):
        if isinstance(other, Struct):
            return self.__struct_definition == other.__struct_definition
        return False


class Type:
    # is the machine on 32 or on 64 bits? need for pointers
    __pointer_width = (math.log2(sys.maxsize) + 1) / 8

    def __init__(self, base, dim):
        self.__base = base
        self.__dim = dim

    def __str__(self):
        string = self.__base.__str__()
        if self.__dim == 0:
            string = string + "[]"
        elif self.__dim > 0:
            string = string + "[" + str(self.__dim) + "]"

        return string

    # computes actual size of the type defined in the current object
    def get_type_size(self):

        # empty array - just a pointer
        if self.__dim == 0:
            return int(self.__pointer_width)

        # array of something
        elif self.__dim > 0:
            base_dim = self.__base.get_base_size()
            return self.__dim * base_dim

        # just a variable
        else:
            return self.__base.get_base_size()

    def is_scalar(self) -> bool:
        return self.__dim == -1

    def is_pointer(self) -> bool:
        return self.__dim == 0

    def get_base_name(self):
        return self.__base.get_base_name()

    def get_base(self):
        return self.__base

    def can_be_cast_to(self, dest_type) -> bool:
        # pointers (empty size arrays: smth[]) can be converted automatically
        if not self.is_scalar() and not dest_type.is_scalar():
            return True

        # non-pointers cannot be converted to pointers
        if not dest_type.is_scalar():
            return False

        available_compatibilities_list = casting_compatibility_table[self.get_base_name()]
        if dest_type.get_base_name() in available_compatibilities_list:

            # struct types can only be converted to themselves
            if dest_type.get_base_name == Struct.__name__ and dest_type != self:
                return False

            # if not a struct type, then at this point a conversion is possible
            return True

        return False

    def can_be_returned(self):
        return self.__base.can_be_returned()

    def __eq__(self, other):
        if isinstance(other, Type):
            return self.get_base_name() == other.get_base_name()


def get_returned_type_of_operation(type_a: Type, type_b: Type):
    # no arithmetic operations with pointers or arrays
    if not type_a.is_scalar() or not type_b.is_scalar():
        # error? - for now just return none
        return None

    # resulted type must not be a pointer or a structure
    returned_type_dimension = -1

    # check if the type of the first operand is good for arithmetic operations
    # structures not allowed
    if type_a.get_base_name() in arithmetic_compatibility_table:
        available_compatibilities_list = arithmetic_compatibility_table[type_a.get_base_name()]

        # check if the type of the second operand is good for arithmetic operations with the first's

        for other_type_base, returned_type_base_name in available_compatibilities_list:
            if type_b.get_base_name() == other_type_base:
                returned_type_base = globals()[returned_type_base_name]()
                return Type(returned_type_base, returned_type_dimension)

    # not compatible
    return None


casting_compatibility_table = {
    Integer.__name__: [Integer.__name__, Double.__name__, Character.__name__],
    Double.__name__: [Integer.__name__, Double.__name__, Character.__name__],
    Character.__name__: [Integer.__name__, Double.__name__, Character.__name__],
    Struct.__name__: [Struct.__name__]
}

arithmetic_compatibility_table = {
    Integer.__name__: [
        (Integer.__name__, Integer.__name__),
        (Double.__name__, Double.__name__),
        (Character.__name__, Integer.__name__)
    ],
    Double.__name__: [
        (Integer.__name__, Double.__name__),
        (Double.__name__, Double.__name__),
        (Character.__name__, Double.__name__)
    ],
    Character.__name__: [
        (Integer.__name__, Integer.__name__),
        (Double.__name__, Double.__name__),
        (Character.__name__, Character.__name__)
    ]
}
