from lexer import lexer

if __name__ == '__main__':
    try:
        file = open("atomc/resources/test3.c", "r")
        tokens = lexer.tokenize(file)

        for tk in tokens:
            print(tk)

        file.close()
    except FileNotFoundError:
        print("Source file not found")

