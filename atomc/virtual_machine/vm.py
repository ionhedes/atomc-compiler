from atomc.domain_analyzer.symbol import ExternalFunction, Parameter
from atomc.domain_analyzer.type import Type, Void, Integer, Double
from atomc.virtual_machine.stack import Stack


external_function_map = {}


def external_put_i(stack: Stack):
    # it is not cool, but by passing the stack we let the ext function take its variables and all
    operand = stack.pop()

    # effect of external function
    print("=> {res}".format(res=operand))

    # must return the stack, so it updates
    return stack


def external_put_d(stack: Stack):
    # it is not cool, but by passing the stack we let the ext function take its variables and all
    operand = stack.pop()

    # effect of external function
    print("=> {res}".format(res=operand))

    # must return the stack, so it updates
    return stack


def init_vm():
    external_function_list = list()

    # when you want to define predefined functions, define them in this file and add them
    # to the external_function_list in the same manner put_i was added

    # put_i
    put_i = ExternalFunction(name="put_i", type_obj=Type(base=Void(), dim=-1), implementation=external_put_i)
    put_i.add_function_parameter(param=Parameter(name="x", owner=put_i, type_obj=Type(base=Integer(), dim=-1)))
    external_function_list.append(put_i)
    external_function_map["put_i"] = external_put_i

    # put_d
    put_d = ExternalFunction(name="put_i", type_obj=Type(base=Void(), dim=-1), implementation=external_put_i)
    put_d.add_function_parameter(param=Parameter(name="x", owner=put_d, type_obj=Type(base=Double(), dim=-1)))
    external_function_list.append(put_d)
    external_function_map["put_d"] = external_put_d

    return external_function_list


def call_external_function(name, stack):
    return external_function_map[name](stack)
