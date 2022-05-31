# the execution stack


class Stack:

    def __init__(self):
        self.__container = list()
        self.__address_locator = list()
        self.__bp = -1  # base of stack
        self.__sp = -1  # current tip of stack
        self.__fp = -1  # beginning of the current frame

    def print_container(self):
        print(self.__container)

    def push(self, value):

        self.__sp += 1
        self.__container.append(value)

    def push_with_reference(self, value, is_global):
        self.push(value)
        self.__address_locator.append((is_global, self.__sp))

    def is_entry_with_reference(self, given_sp):
        for (idx, (is_global, sp)) in enumerate(self.__address_locator):
            if sp == given_sp:
                return idx

        return -1

    def get_entry_reference(self, idx):
        for (is_global, sp) in self.__address_locator:
            if sp == idx:
                return is_global

    def get_latest_reference(self):
        is_global, _ = self.__address_locator[len(self.__address_locator) - 1]
        return is_global

    def pop(self):

        if self.__sp == -1:
            raise EmptyStackException()

        value = self.__container[self.__sp]
        self.__container.pop(self.__sp)

        # remove the address reference, if there was one

        ref_idx = self.is_entry_with_reference(self.__sp)
        if ref_idx != - 1:
            self.__address_locator.pop(ref_idx)

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

        if self.__fp + offset < self.__bp or self.__fp + offset > self.__sp:
            raise OutOfBoundsException()
        return self.__container[self.__fp + offset]

    def fp_store(self, value, offset):

        if self.__fp + offset < self.__bp or self.__fp + offset > self.__sp:
            raise OutOfBoundsException()
        self.__container[self.__fp + offset] = value

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
        self.__sp = self.__fp

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


class OutOfBoundsException(Exception):

    def __str__(self):
        return "Trying to access an address not on the stack"
