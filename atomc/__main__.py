from lexer import lexer

if __name__ == '__main__':
    try:
        file = open("atomc/resources/test2.c", "r")
        lexer.tokenize(file)
    except FileNotFoundError:
        print("Source file not found")

