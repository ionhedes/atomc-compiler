from unittest import TestCase
from atomc.lexer.lexer import tokenize
from atomc.lexer.token import Token
from atomc.lexer.token import Code


class Test(TestCase):
    def test_tokenize(self):
        file = open("atomc/resources/test.c")
        actual_tokens = [Token(Code.ID, "bababulea", 1), Token(Code.ID, "pasulea", 1)]
        tokens = tokenize(file)

        file.close()

        assert tokens == actual_tokens
