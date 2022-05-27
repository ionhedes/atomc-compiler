# the execution stack
import sys


class Stack:

    def __init__(self):
        self.__container = list()
        self.__bp = -1  # base of stack
        self.__sp = -1  # current tip of stack
        self.__fp = -1  # beginning of the current frame

    def push(self, value):

        self.__sp += 1
        self.__container.append(value)
        # print("pushed {v} at {s}; stack: {l}".format(v=value, s=self.__sp, l=self.__container))

    def pop(self):

        if self.__sp == -1:
            raise EmptyStackException()

        value = self.__container[self.__sp]
        self.__container.pop(self.__sp)
        # print("popped {v} at {s}; stack: {l}".format(v=value, s=self.__sp, l=self.__container))
        self.__sp -= 1

        return value

    def peek(self):

        if self.__sp == -1:
            raise EmptyStackException()

        value = self.__container[self.__sp]

        return value

    def fp_load(self, offset):

        if self.__sp == -1:
            raise EmptyStackException()

        # print("fpload {val}; stack: {l}".format(val=self.__container[self.__fp + offset], l=self.__container))
        return self.__container[self.__fp + offset]

    def fp_store(self, value, offset):

        self.__container[self.__fp + offset] = value
        # print("fpstore {val} at {ad}; stack: {l}".format(val=self.__container[self.__fp + offset], ad=self.__fp + offset, l=self.__container))

    def get_condition_result(self):
        return self.pop()

    def create_function_frame(self, local_num):

        # push the current FP
        self.push(self.__fp)

        # move the frame pointer
        self.__fp = self.__sp

        # make space for the local variables in the new frame
        for _ in range(self.__sp, self.__sp + local_num):
            self.__container.append(None)
        self.__sp += local_num

    def recover_function_frame(self):

        # clear the local variables
        self.__sp -= self.__fp

        # restore the old fp
        self.__fp = self.pop()

    def get_stack_size(self):
        return self.__sp + 1


class EmptyStackException(Exception):

    def __str__(self):
        return "Trying to pop a value from empty stack."


class FullStackException(Exception):

    def __str__(self):
        return "Trying to push a value into a full stack."
