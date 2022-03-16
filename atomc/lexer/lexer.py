from atomc.lexer.lexical_error_exception import LexicalErrorException
from atomc.lexer.token import Code
from atomc.lexer.token import Token


# RULE OF THUMB:
# else branch - don't consume char
# terminal state - don't consume char

# RETURN VALUE FOR find_next_state():
# (type of new token: Code), (next state: int), (consume char?: boolean)


def state_0(char: str):
    if char == ' ' or char == '\n' or char == '\t' or char == '\r':
        return Code.SPACE, 0, True
    elif char.isalpha() or char == '_':
        return None, 1, True
    elif char.isnumeric():
        return None, 3, True
    elif char == '\'':
        return None, 11, True
    elif char == '\"':
        return None, 14, True
    elif char == ',':
        return None, 16, True
    elif char == ';':
        return None, 17, True
    elif char == '(':
        return None, 18, True
    elif char == ')':
        return None, 19, True
    elif char == '[':
        return None, 20, True
    elif char == ']':
        return None, 21, True
    elif char == '{':
        return None, 22, True
    elif char == '}':
        return None, 23, True
    elif char == '\0':  # eof <=> read() == ""
        return None, 24, True
    elif char == '+':
        return None, 25, True
    elif char == '-':
        return None, 26, True
    elif char == '*':
        return None, 27, True
    elif char == '.':
        return None, 28, True
    elif char == '/':
        return None, 29, True
    elif char == '&':
        return None, 31, True
    elif char == '|':
        return None, 33, True
    elif char == '=':
        return None, 35, True
    elif char == '!':
        return None, 37, True
    elif char == '<':
        return None, 39, True
    elif char == '>':
        return None, 41, True
    else:
        raise LexicalErrorException()


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
        return None, 6, True
    else:
        return None, 10, False


def state_4(char: str):
    if char.isnumeric():
        return None, 5, True
    else:
        raise LexicalErrorException()


def state_5(char: str):
    if char.isnumeric():
        return None, 5, True
    elif char == 'e' or char == 'E':
        return None, 6, True
    else:
        return None, 9, False


def state_6(char: str):
    if char.isnumeric():
        return None, 8, True
    elif char == '+' or char == '-':
        return None, 7, True
    else:
        raise LexicalErrorException()


def state_7(char: str):
    if char.isnumeric():
        return None, 8, True
    else:
        raise LexicalErrorException()


def state_8(char: str):
    if char.isnumeric():
        return None, 8, True
    else:
        return None, 9, False


def state_9(char: str):
    return Code.CT_REAL, 0, False


def state_10(char: str):
    return Code.CT_INT, 0, False


def state_11(char: str):
    if char != '\'':
        return None, 12, True
    else:
        raise LexicalErrorException()


def state_12(char: str):
    if char == '\'':
        return None, 13, True
    else:
        raise LexicalErrorException()


def state_13(char: str):
    return Code.CT_CHAR, 0, False


def state_14(char: str):
    if char != "\"":
        return None, 14, True
    else:
        return None, 15, True


def state_15(char: str):
    return Code.CT_STRING, 0, False


def state_16(char: str):
    return Code.COMMA, 0, False


def state_17(char: str):
    return Code.SEMICOLON, 0, False


def state_18(char: str):
    return Code.LPAR, 0, False


def state_19(char: str):
    return Code.RPAR, 0, False


def state_20(char: str):
    return Code.LBRACKET, 0, False


def state_21(char: str):
    return Code.RBRACKET, 0, False


def state_22(char: str):
    return Code.LACC, 0, False


def state_23(char: str):
    return Code.RACC, 0, False


def state_24(char: str):
    return Code.END, 0, False


def state_25(char: str):
    return Code.ADD, 0, False


def state_26(char: str):
    return Code.SUB, 0, False


def state_27(char: str):
    return Code.MUL, 0, False


def state_28(char: str):
    return Code.DOT, 0, False


def state_29(char: str):
    if char == '/':
        return None, 47, True
    else:
        return None, 30, False


def state_30(char: str):
    return Code.DIV, 0, False


def state_31(char: str):
    if char == '&':
        return None, 32, True
    else:
        raise LexicalErrorException()


def state_32(char: str):
    return Code.AND, 0, False


def state_33(char: str):
    if char == '|':
        return None, 34, True
    else:
        raise LexicalErrorException()


def state_34(char: str):
    return Code.OR, 0, False


def state_35(char: str):
    if char == '=':
        return None, 36, True
    else:
        return None, 43, False


def state_36(char: str):
    return Code.EQUAL, 0, False


def state_37(char: str):
    if char == '=':
        return None, 38, True
    else:
        return None, 44, False


def state_38(char: str):
    return Code.NOTEQ, 0, False


def state_39(char: str):
    if char == '=':
        return None, 40, True
    else:
        return None, 45, False


def state_40(char: str):
    return Code.LESSEQ, 0, False


def state_41(char: str):
    if char == '=':
        return None, 42, True
    else:
        return None, 46, False


def state_42(char: str):
    return Code.GREATEREQ, 0, False


def state_43(char: str):
    return Code.ASSIGN, 0, False


def state_44(char: str):
    return Code.NOT, 0, False


def state_45(char: str):
    return Code.LESS, 0, False


def state_46(char: str):
    return Code.GREATER, 0, False


def state_47(char: str):
    if char == '\n' or char == '\r' or char == '\0':
        return None, 0, False
    else:
        return None, 47, True


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
        11: state_11,
        12: state_12,
        13: state_13,
        14: state_14,
        15: state_15,
        16: state_16,
        17: state_17,
        18: state_18,
        19: state_19,
        20: state_20,
        21: state_21,
        22: state_22,
        23: state_23,
        24: state_24,
        25: state_25,
        26: state_26,
        27: state_27,
        28: state_28,
        29: state_29,
        30: state_30,
        31: state_31,
        32: state_32,
        33: state_33,
        34: state_34,
        35: state_35,
        36: state_36,
        37: state_37,
        38: state_38,
        39: state_39,
        40: state_40,
        41: state_41,
        42: state_42,
        43: state_43,
        44: state_44,
        45: state_45,
        46: state_46,
        47: state_47
    }

    new_token_code, new_state, consume = state_dict[state](char)
    return new_token_code, new_state, consume


def generate_new_token(code: Code, buf: str, line: int):
    keywords = {
        "void": Code.VOID,
        "int": Code.INT,
        "char": Code.CHAR,
        "double": Code.DOUBLE,
        "struct": Code.STRUCT,
        "if": Code.IF,
        "else": Code.ELSE,
        "for": Code.FOR,
        "while": Code.WHILE,
        "break": Code.BREAK
    }

    if code == Code.ID:
        if buf in keywords:
            return Token(keywords[buf], None, line)
        else:
            return Token(code, buf, line)
    elif code == Code.CT_INT:
        return Token(code, int(buf), line)
    elif code == Code.CT_REAL:
        return Token(code, float(buf), line)
    elif code == Code.CT_CHAR:
        return Token(code, buf, line)
    elif code == Code.CT_STRING:
        return Token(code, buf, line)
    else:
        return Token(code, None, line)


def tokenize(file):
    state: int = 0
    line: int = 1
    buf: str = ''
    tokens: list = []

    char = file.read(1)

    while True:
        try:
            # print("DBG: crt char: ", char)
            # compute next state
            new_token_type, state, consume = find_next_state(state, char)
            # print("\tDBG: next state ", state)

            # generate token if necessary
            if consume:
                buf = buf + char

            if new_token_type is not None:
                if new_token_type == Code.SPACE:
                    # print("\tDBG: space detected")
                    buf = ''
                    if char == '\n':
                        line = line + 1

                else:
                    # print("DBG: generating new token")
                    # new_token = Token(new_token_type, buf, line)
                    new_token = generate_new_token(new_token_type, buf, line)
                    tokens.append(new_token)
                    buf = ''

            # consume character
            if consume:
                # print("DBG: consuming next char")
                char = file.read(1)
                if char == '':  # EOF
                    new_token = generate_new_token(Code.END, "", line)
                    tokens.append(new_token)
                    break

        except LexicalErrorException:
            print("Error while parsing at line ", line)
            break

    return tokens
