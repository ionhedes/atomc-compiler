class Symbol:

    def __init__(self, name):
        self.__name = name

    def __str__(self):
        return str(self.__name)

    def is_structured(self):
        return False

    def is_function(self):
        return False

    def is_non_functional(self):
        return False

    def is_non_void(self):
        pass

    def name_matches(self, name):
        return self.__name == name

    def get_name(self):
        return self.__name

    def get_symbol_type_size(self):
        pass

    def can_return_value(self):
        return False

    def get_type(self):
        pass


class NonFunctionalSymbol(Symbol):
    def __init__(self, name, type_obj, index=0, owner=None):
        super().__init__(name)
        self._index = index
        self._type = type_obj
        self._owner = owner

        # setting a field where we'll store the type of the
        if type_obj.is_array():
            self._value = [None] * type_obj.get_type_dim()
        else:
            self._value = None

    def get_symbol_type_size(self):
        return self._type.get_type_size()

    def set_index(self, index):
        self._index = index

    def get_type(self):
        return self._type

    def is_non_functional(self):
        return True

    def update_value(self, value):
        self._value = value


class Variable(NonFunctionalSymbol):

    def __init__(self, name, type_obj, owner=None):
        super().__init__(name, type_obj, owner)

    def __str__(self):
        owner_str = ""
        if self._owner is not None:
            owner_str = ", owner: " + self._owner.get_owner_signature()
        return "var " + super().__str__() + ": " \
               + self._type.__str__() \
               + owner_str \
               + ", size: " \
               + str(self._type.get_type_size()) \
               + ", index: " \
               + str(self._index)


class Parameter(NonFunctionalSymbol):

    def __init__(self, name, type_obj, owner, index=0):
        super().__init__(name, type_obj, index, owner)

    def __str__(self):
        owner_str = ""
        if self._owner is not None:
            owner_str = ", owner: " + self._owner.get_owner_signature()
        return "param " + super().__str__() + ": " \
               + self._type.__str__() \
               + owner_str \
               + ", size: " \
               + str(self._type.get_type_size()) \
               + ", index: " \
               + str(self._index)


class Function(Symbol):

    def add_function_parameter(self, param: Parameter):
        self.__params.append(param)
        param.set_index(self.__param_idx)
        # the params are indexed by position, not size
        self.__param_idx += 1

    def add_local_variable(self, var: Variable):
        self.__locals.append(var)
        var.set_index(self.__local_idx)
        self.__local_idx += var.get_symbol_type_size()

    def __init__(self, name, type_obj):
        super().__init__(name)
        self.__params = list()
        self.__param_idx = 0  # byte-offset index for function parameters
        self.__locals = list()
        self.__local_idx = 0  # byte-offset index for local variables
        self.__type = type_obj

    def __str__(self):
        local_str = ''
        for local in self.__locals:
            local_str = local_str + "\t" + local.__str__() + "\n"

        param_str = ''
        for param in self.__params:
            param_str = param_str + "\t" + param.__str__() + "\n"

        return "func " + super().__str__() + ": " \
               + self.__type.__str__() + "\n" \
               + param_str \
               + local_str

    def get_owner_signature(self):
        return self.get_name() + "()"

    def get_symbol_type_size(self):
        return self.__type.get_type_size()

    def is_function(self):
        return True

    def can_return_value(self):
        return self.__type.can_be_returned()

    def get_type(self):
        return self.__type

    def get_params(self):
        return self.__params


class ExternalFunction(Function):

    def __init__(self, name, type_obj, implementation):
        super().__init__(name, type_obj)
        self.__pointer = implementation


class StructDef(Symbol):

    def __init__(self, name):
        super().__init__(name)
        self.__members = list()
        self.__member_index = 0

    def __str__(self):

        member_str = ''
        for member in self.__members:
            member_str = member_str + "\t" + member.__str__() + "\n"

        return "struct " + super().__str__() + ":\n" \
               + member_str \
               + "size: " \
               + str(self.get_symbol_type_size())

    def get_owner_signature(self):
        return "struct " + self.get_name()

    def add_struct_member(self, member: Variable):
        self.__members.append(member)
        member.set_index(self.__member_index)
        self.__member_index += member.get_symbol_type_size()

    def get_symbol_type_size(self):
        size = 0
        for member in self.__members:
            size = size + member.get_symbol_type_size()

        return size

    def is_structured(self):
        return True

    def get_type(self):
        return self

    def get_member(self, name):

        for member in self.__members:
            if member.name_matches(name):
                return member

        return None

    def has_member(self, name):

        for member in self.__members:
            if member.name_matches(name):
                return True

        return False
