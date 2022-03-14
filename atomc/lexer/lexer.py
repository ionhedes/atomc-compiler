from atomc.lexer.token import Code
from atomc.lexer.token import Token


def state_0(char: str):
    if char == ' ' or char == '\n' or char == '\t' or char == '\r':
        return Code.SPACE, 0, True
    elif char.isalpha() or char == '_':
        return None, 1, True
    elif char.isnumeric():
        return None, 3, True
    else:
        return Code.ERR, 0, False


def state_1(char: str):
    if char.isalnum() or char == '_':
        return None, 1, True
    else:
        return None, 2, False


def state_2(char: str):
    return Code.ID, 0, False


def state_3(char: str):
    if char.isnumeric():
        return None, 3, True
    elif char == '.':
        return None, 4, True
    elif char == 'e' or char == 'E':
        print('aaa')
        return None, 6, True
    else:
        return None, 10, False


def state_4(char: str):
    if char.isnumeric():
        return None, 5, True
    else:
        return Code.ERR, 0, False


def state_5(char: str):
    if char.isnumeric():
        return None, 5, True
    elif char == 'e' or char == 'E':
        return None, 6, True
    else:
        return None, 9, True


def state_6(char: str):
    if char.isnumeric():
        return None, 8, True
    elif char == '+' or char == '-':
        return None, 7, True
    else:
        return Code.ERR, 0, False


def state_7(char: str):
    if char.isnumeric():
        return None, 8, True
    else:
        return Code.ERR, 0, False


def state_8(char: str):
    if char.isnumeric():
        return None, 8, True
    else:
        return None, 9, False


def state_9(char: str):
    return Code.CT_REAL, 0, False


def state_10(char: str):
    return Code.CT_INT, 0, False


def find_next_state(state: int, char: str):
    state_dict = {
        0: state_0,
        1: state_1,
        2: state_2,
        3: state_3,
        4: state_4,
        5: state_5,
        6: state_6,
        7: state_7,
        8: state_8,
        9: state_9,
        10: state_10,
    }

    new_token_code, new_state, consume = state_dict[state](char)
    return new_token_code, new_state, consume


def tokenize(file):
    state: int = 0
    advance: bool = True
    consume: bool = True
    line: int = 0
    buf: str = ''
    tokens: list = []

    char = file.read(1)

    while True:
        new_token_type, state, consume = find_next_state(state, char)

        if consume:
            buf = buf + char
            char = file.read(1)
            if char == '':  # EOF
                break

        if new_token_type is not None:
            if new_token_type == Code.ERR:
                print("Error while parsing at line ", line)
            elif new_token_type == Code.SPACE:
                buf = ''
                if char == '\n':
                    line = line + 1
            else:
                new_token = Token(new_token_type, buf, line)
                tokens.append(new_token)
                buf = ''
                char = file.read(1)
                if char == '':
                    break


    return tokens
