import math
import sys

from atomc.domain_analyzer.symbol import StructDef


class Base:

    def get_base_size(self):
        pass


class Integer(Base):
    __BASE_SIZE = 4

    def __str__(self):
        return "int"

    def get_base_size(self):
        return self.__BASE_SIZE


class Double(Base):
    __BASE_SIZE = 8

    def __str__(self):
        return "double"

    def get_base_size(self):
        return self.__BASE_SIZE


class Character(Base):
    __BASE_SIZE = 1

    def __str__(self):
        return "char"

    def get_base_size(self):
        return self.__BASE_SIZE


class Void(Base):
    __BASE_SIZE = 0

    def __str__(self):
        return "void"

    def get_base_size(self):
        return self.__BASE_SIZE


class Struct(Base):

    def __init__(self, struct):
        self.__struct_definition = struct

    def __str__(self):
        return "struct " + self.__struct_definition.get_name()

    def get_base_size(self):
        return self.__struct_definition.get_symbol_type_size()


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
