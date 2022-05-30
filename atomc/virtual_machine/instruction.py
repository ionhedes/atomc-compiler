from enum import Enum

from atomc.virtual_machine.stack import Stack
from atomc.virtual_machine.vm import call_external_function


class Opcode(Enum):
    HALT = 0
    CALL = 1
    CALL_EXT = 2
    ENTER = 3
    RET = 4
    RET_VOID = 5

    # stack related
    PUSH_I = 6
    PUSH_F = 7
    FPADDR_I = 8
    FPADDR_F = 9
    FPLOAD = 10
    FPSTORE = 11
    LOAD_I = 12
    LOAD_F = 13
    STORE_I = 14
    STORE_F = 15
    ADDR = 16
    DROP = 17

    # conversions
    CONV_I_F = 18
    CONV_F_I = 19

    # jumps
    JMP = 20
    JF = 21
    JT = 22

    # arithmetic and logic ops
    ADD_I = 23
    ADD_F = 24
    SUB_I = 25
    SUB_F = 26
    MUL_I = 27
    MUL_F = 28
    DIV_I = 29
    DIV_F = 30
    LESS_I = 31
    LESS_F = 32


class Instruction:
    def __init__(self, opcode, argument):
        self.__opcode = opcode
        self.__argument = argument

    def get_instruction_handler(self):
        return instruction_map[self.__opcode]

    def execute(self):
        return self.get_instruction_handler()(self.__argument)


def add_instruction(instructions, opcode, argument):
    instructions.append(Instruction(opcode, argument))
    return len(instructions) - 1


#############################################
# OPERATION RELATED VARIABLES AND FUNCTIONS #
#############################################

instruction_list = list()
stack = Stack()
ip = 0


def op_halt(_):
    global ip

    print("{ip:03d}/{ss:02d} HALT".format(ip=int(ip), ss=stack.get_stack_size()))

    # set the ip to -1 to signal eoe
    ip = -1


def op_call(param):
    global ip

    print("{ip:03d}/{ss:02d} CALL\t\t{p}".format(ip=ip, ss=stack.get_stack_size(), p=param))

    # saving return value
    stack.push(ip + 1)

    # the param is the new IP.
    ip = param


def op_call_ext(param):
    global stack
    global ip

    print("{ip:03d}/{ss:02d} CALL_EXT\t{p}".format(ip=ip, ss=stack.get_stack_size(), p=param))

    # builtin functions are just called as their python implementation
    # we consider the param as the function name here (not ip)
    stack = call_external_function(name=param, stack=stack)

    # the param is the new IP
    ip += 1


def op_enter(param):
    global ip

    print("{ip:03d}/{ss:02d} ENTER\t{p}".format(ip=ip, ss=stack.get_stack_size(), p=param))

    # create a frame for the callee function
    # - push the current fp
    # - make space for param local variables
    stack.create_function_frame(local_num=param)

    # increment ip
    ip += 1


def op_ret(param):
    global ip

    # pop the last value from the stack, to use it as return value
    ret_val = stack.pop()

    print("{ip:03d}/{ss:02d} RET\t{p}".format(ip=ip, ss=stack.get_stack_size(), p=param))

    # restore the frame of the caller function
    stack.recover_function_frame()

    # restore the ip
    ip = stack.pop()

    # push the return value on the stack
    stack.push(ret_val)


def op_ret_void(param):
    global ip

    print("{ip:03d}/{ss:02d} RET_VOID\t{p}".format(ip=ip, ss=stack.get_stack_size(), p=param))

    # restore the frame of the caller function
    stack.recover_function_frame()

    # restore the ip
    ip = stack.pop()


def op_push_i(param):
    global ip

    print("{ip:03d}/{ss:02d} PUSH.i\t{p}".format(ip=ip, ss=stack.get_stack_size(), p=param))

    # push the param to the stack
    stack.push(param)

    # increment program counter
    ip += 1


def op_push_f(param):
    global ip

    print("{ip:03d}/{ss:02d} PUSH.f\t{p}".format(ip=ip, ss=stack.get_stack_size(), p=param))

    # push the param to the stack
    stack.push(param)

    # increment program counter
    ip += 1


def op_fpaddr_i(param):
    # for local variables
    pass


def op_fpaddr_f(_):
    # for local variables
    pass


def op_fpload(param):
    global ip

    # get the value from the stack, offset from fp
    value = stack.fp_load(offset=param)

    # push the value in the stack
    stack.push(value)

    print("{ip:03d}/{ss:02d} FPLOAD\t{p}\t\t// {val}".format(ip=ip, ss=stack.get_stack_size(), p=param, val=value))

    # increment ip
    ip += 1


def op_fpstore(param):
    global ip

    # pop the value from the stack
    value = stack.pop()

    # store the value in the stack, offset from fp
    stack.fp_store(value=value, offset=param)

    print("{ip:03d}/{ss:02d} FPSTORE\t{p}\t\t// {val}".format(ip=ip, ss=stack.get_stack_size(), p=param, val=value))

    # increment ip
    ip += 1


def op_load_i(param):
    global ip

    # take the last value from the stack - an address
    addr = stack.pop()

    # find the value from this address
    value = -1  # ???

    # push the value to the stack
    stack.push(value)

    print("{ip:03d}/{ss:02d} LOAD.i\t\t// *(int*){addr} -> {val}".format(ip=ip, ss=stack.get_stack_size(), addr=addr,
                                                                         val=value))

    # increment ip
    ip += 1


def op_load_f(_):
    global ip

    # take the last value from the stack - an address
    addr = stack.pop()

    # find the value from this memory address
    value = -1.0  # ???

    # push the value to the stack
    stack.push(value)

    print("{ip:03d}/{ss:02d} LOAD.f\t\t// *(float*){addr} -> {val}".format(ip=ip, ss=stack.get_stack_size(), addr=addr,
                                                                           val=value))

    # increment ip
    ip += 1


def op_store_i(_):
    global ip

    # take the last value from the stack - an int value
    value = stack.pop()

    # take the last value from the stack - an address
    addr = stack.pop()

    # store the value at the specified memory address
    # ???

    # put the int value back on stack (by specs)
    stack.push(value)

    print("{ip:03d}/{ss:02d} STORE.i\t\t// *(int*){addr} -> {val}".format(ip=ip, ss=stack.get_stack_size(), addr=addr,
                                                                          val=value))

    # increment ip
    ip += 1


def op_store_f(_):
    global ip

    # take the last value from the stack - an int value
    value = stack.pop()

    # take the last value from the stack - an address
    addr = stack.pop()

    # store the value at the specified memory address
    # ???

    # put the int value back on stack (by specs)
    stack.push(value)

    print("{ip:03d}/{ss:02d} STORE.f\t\t// *(float*){addr} -> {val}".format(ip=ip, ss=stack.get_stack_size(), addr=addr,
                                                                          val=value))

    # increment ip
    ip += 1


def op_addr(_):
    # for global variables
    pass


def op_drop(_):
    global ip

    # delete the value from the top of the stack, without doing anything with it
    stack.pop()

    print("{ip:03d}/{ss:02d} DROP".format(ip=ip, ss=stack.get_stack_size()))

    # increment ip
    ip += 1


def op_conv_i_f(_):
    global ip

    # get the value from the stack before casting; cast it
    int_value = stack.pop()
    float_value = float(int_value)

    # push the cast value back to the stack
    stack.push(float_value)

    print("{ip:03d}/{ss:02d} CONV.i.f\t// {pre} -> {post}".format(ip=ip, ss=stack.get_stack_size(), pre=int_value,
                                                                  post=float_value))

    # increment the ip
    ip += 1


def op_conv_f_i(_):
    global ip

    # get the value from the stack before casting; cast it
    float_value = stack.pop()
    int_value = int(float_value)

    # push the cast value back to the stack
    stack.push(int_value)

    print("{ip:03d}/{ss:02d} CONV.i.f\t// {pre} -> {post}".format(ip=ip, ss=stack.get_stack_size(), pre=float_value,
                                                                  post=int_value))

    # increment the ip
    ip += 1


def op_jmp(param):
    global ip

    print("{ip:03d}/{ss:02d} JMP\t\t{p}".format(ip=ip, ss=stack.get_stack_size(), p=param))

    # move the ip
    ip = param


def op_jf(param):
    global ip

    # check if the last comparison was false
    result = stack.get_condition_result()
    print("{ip:03d}/{ss:02d} JF\t\t{p}\t\t// {r}".format(ip=ip, ss=stack.get_stack_size(), p=param, r=result))
    if not result:
        # branch taken
        ip = param
    else:
        # branch not taken
        ip += 1


def op_jt(param):
    global ip

    # check if the last comparison was false
    result = stack.get_condition_result()
    print("{ip:03d}/{ss:02d} JT\t{p}\t\t// {r}".format(ip=ip, ss=stack.get_stack_size(), p=param, r=result))
    if result:
        # branch taken
        ip = param
    else:
        # branch not taken
        ip += 1


def op_add_i(_):
    global ip

    # pop the operands / operands in reverse order
    operand_2 = stack.pop()
    operand_1 = stack.pop()

    # compute the result
    result = operand_1 + operand_2

    # push result to stack
    stack.push(result)

    print(
        "{ip:03d}/{ss:02d} ADD.i\t\t\t// {op1} + {op2} -> {res}".format(ip=ip, ss=stack.get_stack_size(), op1=operand_1,
                                                                        op2=operand_2, res=result))

    # increment the ip
    ip += 1


def op_add_f(_):
    global ip

    # pop the operands / operands in reverse order
    operand_2 = stack.pop()
    operand_1 = stack.pop()

    # compute the result
    result = operand_1 + operand_2

    # push result to stack
    stack.push(result)

    print(
        "{ip:03d}/{ss:02d} ADD.f\t\t\t// {op1} + {op2} -> {res}".format(ip=ip, ss=stack.get_stack_size(), op1=operand_1,
                                                                        op2=operand_2, res=result))

    # increment the ip
    ip += 1


def op_sub_i(_):
    global ip

    # pop the operands / operands in reverse order
    operand_2 = stack.pop()
    operand_1 = stack.pop()

    # compute the result
    result = operand_1 - operand_2

    # push result to stack
    stack.push(result)

    print(
        "{ip:03d}/{ss:02d} SUB.i\t\t\t// {op1} - {op2} -> {res}".format(ip=ip, ss=stack.get_stack_size(), op1=operand_1,
                                                                        op2=operand_2, res=result))

    # increment the ip
    ip += 1


def op_sub_f(_):
    global ip

    # pop the operands / operands in reverse order
    operand_2 = stack.pop()
    operand_1 = stack.pop()

    # compute the result
    result = operand_1 - operand_2

    # push result to stack
    stack.push(result)

    print(
        "{ip:03d}/{ss:02d} SUB.f\t\t\t// {op1} - {op2} -> {res}".format(ip=ip, ss=stack.get_stack_size(), op1=operand_1,
                                                                        op2=operand_2, res=result))

    # increment the ip
    ip += 1


def op_mul_i(_):
    global ip

    # pop the operands / operands in reverse order
    operand_2 = stack.pop()
    operand_1 = stack.pop()

    # compute the result
    result = operand_1 * operand_2

    # push result to stack
    stack.push(result)

    print(
        "{ip:03d}/{ss:02d} MUL.i\t\t\t// {op1} * {op2} -> {res}".format(ip=ip, ss=stack.get_stack_size(), op1=operand_1,
                                                                        op2=operand_2, res=result))

    # increment the ip
    ip += 1


def op_mul_f(_):
    global ip

    # pop the operands / operands in reverse order
    operand_2 = stack.pop()
    operand_1 = stack.pop()

    # compute the result
    result = operand_1 * operand_2

    # push result to stack
    stack.push(result)

    print(
        "{ip:03d}/{ss:02d} MUL.f\t\t\t// {op1} * {op2} -> {res}".format(ip=ip, ss=stack.get_stack_size(), op1=operand_1,
                                                                        op2=operand_2, res=result))

    # increment the ip
    ip += 1


def op_div_i(_):
    global ip

    # pop the operands / operands in reverse order
    operand_2 = stack.pop()
    operand_1 = stack.pop()

    # compute the result
    result = operand_1 // operand_2

    # push result to stack
    stack.push(result)

    print(
        "{ip:03d}/{ss:02d} DIV.i\t\t\t// {op1} / {op2} -> {res}".format(ip=ip, ss=stack.get_stack_size(), op1=operand_1,
                                                                        op2=operand_2, res=result))

    # increment the ip
    ip += 1


def op_div_f(_):
    global ip

    # pop the operands / operands in reverse order
    operand_2 = stack.pop()
    operand_1 = stack.pop()

    # compute the result
    result = operand_1 /operand_2

    # push result to stack
    stack.push(result)

    print(
        "{ip:03d}/{ss:02d} DIV.f\t\t\t// {op1} / {op2} -> {res}".format(ip=ip, ss=stack.get_stack_size(), op1=operand_1,
                                                                        op2=operand_2, res=result))

    # increment the ip
    ip += 1


def op_less_i(_):
    global ip

    # pop the operands / operands in reverse order
    operand_2 = stack.pop()
    operand_1 = stack.pop()

    # compute the result
    result = operand_1 < operand_2

    print("{ip:03d}/{ss:02d} LESS.i\t\t\t// {op1} < {op2} -> {res}".format(ip=ip, ss=stack.get_stack_size(),
                                                                           op1=operand_1, op2=operand_2, res=result))

    # push result to stack
    stack.push(result)

    # increment the ip
    ip += 1


def op_less_f(_):
    global ip

    # pop the operands / operands in reverse order
    operand_2 = stack.pop()
    operand_1 = stack.pop()

    # compute the result
    result = operand_1 < operand_2

    print("{ip:03d}/{ss:02d} LESS.f\t\t\t// {op1} < {op2} -> {res}".format(ip=ip, ss=stack.get_stack_size(),
                                                                           op1=operand_1, op2=operand_2, res=result))

    # push result to stack
    stack.push(result)

    # increment the ip
    ip += 1


instruction_map = {
    Opcode.HALT: op_halt,
    Opcode.CALL: op_call,
    Opcode.CALL_EXT: op_call_ext,
    Opcode.ENTER: op_enter,
    Opcode.RET: op_ret,
    Opcode.RET_VOID: op_ret_void,
    Opcode.PUSH_I: op_push_i,
    Opcode.PUSH_F: op_push_f,
    Opcode.FPADDR_I: op_fpaddr_i,
    Opcode.FPADDR_F: op_fpaddr_f,
    Opcode.FPLOAD: op_fpload,
    Opcode.FPSTORE: op_fpstore,
    Opcode.LOAD_I: op_load_i,
    Opcode.LOAD_F: op_load_f,
    Opcode.STORE_I: op_store_i,
    Opcode.STORE_F: op_store_f,
    Opcode.ADDR: op_addr,
    Opcode.DROP: op_drop,
    Opcode.CONV_I_F: op_conv_i_f,
    Opcode.CONV_F_I: op_conv_f_i,
    Opcode.JMP: op_jmp,
    Opcode.JF: op_jf,
    Opcode.JT: op_jt,
    Opcode.ADD_I: op_add_i,
    Opcode.ADD_F: op_add_f,
    Opcode.SUB_I: op_sub_i,
    Opcode.SUB_F: op_sub_f,
    Opcode.MUL_I: op_mul_i,
    Opcode.MUL_F: op_mul_f,
    Opcode.DIV_I: op_div_i,
    Opcode.DIV_F: op_div_f,
    Opcode.LESS_I: op_less_i,
    Opcode.LESS_F: op_less_f
}


def run(instructions):
    # ip == -1 means that we've passed a halt instruction
    while ip != -1:
        # execute the instruction at ip
        instructions[int(ip)].execute()


def generate_test_vm_code():
    # dummy vm code for testing the vm
    add_instruction(instruction_list, Opcode.PUSH_I, 2)          # 0) |
    add_instruction(instruction_list, Opcode.CALL, 3)            # 1) f(n)
    add_instruction(instruction_list, Opcode.HALT, None)         # 2) ---
    add_instruction(instruction_list, Opcode.ENTER, 1)           # 3) f(int n)
    add_instruction(instruction_list, Opcode.PUSH_I, 0)          # 4)    |
    add_instruction(instruction_list, Opcode.FPSTORE, 1)         # 5)    i = 0
    add_instruction(instruction_list, Opcode.FPLOAD, 1)          # 6)    |
    add_instruction(instruction_list, Opcode.FPLOAD, -2)         # 7)
    add_instruction(instruction_list, Opcode.LESS_I, None)       # 8)    |
    add_instruction(instruction_list, Opcode.JF, 17)             # 9)    while (i >= n) {
    add_instruction(instruction_list, Opcode.FPLOAD, 1)          # 10)    |
    add_instruction(instruction_list, Opcode.CALL_EXT, "put_i")  # 11)   put_i(i)
    add_instruction(instruction_list, Opcode.FPLOAD, 1)          # 12)   |
    add_instruction(instruction_list, Opcode.PUSH_I, 1)          # 13)   |
    add_instruction(instruction_list, Opcode.ADD_I, None)        # 14)   |
    add_instruction(instruction_list, Opcode.FPSTORE, 1)         # 15)   i++
    add_instruction(instruction_list, Opcode.JMP, 6)             # 16)   }
    add_instruction(instruction_list, Opcode.RET_VOID, 1)        # 17)   END: return


def generate_test_vm_code2():
    # dummy instructions for testing the vm
    add_instruction(instruction_list, Opcode.PUSH_F, 2.0)  # 0) |
    add_instruction(instruction_list, Opcode.CALL, 3)  # 1) f(n)
    add_instruction(instruction_list, Opcode.HALT, None)  # 2) ---
    add_instruction(instruction_list, Opcode.ENTER, 1)  # 3) f(int n)
    add_instruction(instruction_list, Opcode.PUSH_F, 0.0)  # 4)    |
    add_instruction(instruction_list, Opcode.FPSTORE, 1)  # 5)    i = 0
    add_instruction(instruction_list, Opcode.FPLOAD, 1)  # 6)    |
    add_instruction(instruction_list, Opcode.FPLOAD, -2)  # 7)
    add_instruction(instruction_list, Opcode.LESS_F, None)  # 8)    |
    add_instruction(instruction_list, Opcode.JF, 17)  # 9)    while (i >= n) {
    add_instruction(instruction_list, Opcode.FPLOAD, 1)  # 10)    |
    add_instruction(instruction_list, Opcode.CALL_EXT, "put_d")  # 11)   put_i(i)
    add_instruction(instruction_list, Opcode.FPLOAD, 1)  # 12)   |
    add_instruction(instruction_list, Opcode.PUSH_F, 0.5)  # 13)   |
    add_instruction(instruction_list, Opcode.ADD_F, None)  # 14)   |
    add_instruction(instruction_list, Opcode.FPSTORE, 1)  # 15)   i++
    add_instruction(instruction_list, Opcode.JMP, 6)  # 16)   }
    add_instruction(instruction_list, Opcode.RET_VOID, 1)  # 17)   END: return


def test_vm():
    run(instruction_list)
