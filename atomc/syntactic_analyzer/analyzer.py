import copy

from atomc.domain_analyzer.domain import DomainStack
from atomc.domain_analyzer.domain_error_exception import InvalidArraySizeErrorException, NoStructDefErrorException
from atomc.domain_analyzer.symbol import Variable, Function, Parameter, StructDef
from atomc.domain_analyzer.type import Integer, Double, Character, Struct, Type, Void
from atomc.lexer.token import Code
from atomc.syntactic_analyzer.syntax_error_exception import SyntaxErrorException

# rule of thumb:
# any rule function and also the consume function returns a tuple:
# - boolean: if the rule satisfied, token was consumed
# - iterator: the iterator at the new position in the list (after consuming all the tokens of that rule)
#             if the rule was not satisfied / token was not consumed, an iterator object with the initial state of the
#             main iterator is returned, so the iteration does not advance


global_symbols = list()
domain_stack = DomainStack()


def find_struct_def_with_id(name):
    for symbol in global_symbols:
        if symbol.is_structured() and symbol.name_matches(name):
            return symbol

    raise NoStructDefErrorException(name)


# for consuming terminal symbols/tokens from the grammar rules
def consume(token_iterator: iter, code: Code):
    # do not forget to deep copy the token_iterator, lest you will end up with an alias
    initial_iterator = copy.deepcopy(token_iterator)

    tk = next(token_iterator)
    if tk.code == code:
        if tk.value is not None:
            return token_iterator, True, tk.value
        else:
            return token_iterator, True, None

    return initial_iterator, False, None


# grammar rule:
# exprPrimary: ID ( LPAR ( expr ( COMMA expr )* )? RPAR )?
# | CT_INT
# | CT_REAL
# | CT_CHAR
# | CT_STRING
# | LPAR expr RPAR
def rule_expr_primary(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # ID
    token_iterator, rule_result, _ = consume(token_iterator, Code.ID)
    if rule_result:

        # LPAR?
        token_iterator, rule_result, _ = consume(token_iterator, Code.LPAR)
        if rule_result:

            # expr?
            token_iterator, rule_result = rule_expr(token_iterator)
            if rule_result:

                # COMMA*
                while True:
                    token_iterator, rule_result, _ = consume(token_iterator, Code.COMMA)

                    if not rule_result:
                        break

                    # expr
                    token_iterator, rule_result = rule_expr(token_iterator)
                    if not rule_result:
                        raise SyntaxErrorException(next(token_iterator), "missing function parameter after , "
                                                                         "in function call")

            # RPAR
            token_iterator, rule_result, _ = consume(token_iterator, Code.RPAR)
            if rule_result:
                return token_iterator, True

            else:
                raise SyntaxErrorException(next(token_iterator),
                                           "missing ) after ( in function call")

        else:
            return token_iterator, True

    # CT_INT
    token_iterator = copy.deepcopy(fallback_iterator)
    token_iterator, rule_result, _ = consume(token_iterator, Code.CT_INT)
    if rule_result:
        return token_iterator, True

    # CT_REAL
    token_iterator, rule_result, _ = consume(token_iterator, Code.CT_REAL)
    if rule_result:
        return token_iterator, True

    # CT_CHAR
    token_iterator, rule_result, _ = consume(token_iterator, Code.CT_CHAR)
    if rule_result:
        return token_iterator, True

    # CT_STRING
    token_iterator, rule_result, _ = consume(token_iterator, Code.CT_STRING)
    if rule_result:
        return token_iterator, True

    # LPAR
    token_iterator, rule_result, _ = consume(token_iterator, Code.LPAR)
    if rule_result:

        # expr
        token_iterator, rule_result = rule_expr(token_iterator)
        if rule_result:

            # RPAR
            token_iterator, rule_result, _ = consume(token_iterator, Code.RPAR)
            if rule_result:
                return token_iterator, True

            else:
                raise SyntaxErrorException(next(token_iterator), "missing ) after (")

        else:
            # not an error, might be just a cast
            return fallback_iterator, False

    return fallback_iterator, False


# auxiliary grammar rule:
# exprPostfixAux: LBRACKET expr RBRACKET exprPostfixAux
# | DOT ID exprPostfixAux
# | e
def rule_expr_postfix_aux(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # LBRACKET
    token_iterator, rule_result, _ = consume(token_iterator, Code.LBRACKET)
    if rule_result:

        # expr
        token_iterator, rule_result = rule_expr(token_iterator)
        if rule_result:

            # RBRACKET
            token_iterator, rule_result, _ = consume(token_iterator, Code.RBRACKET)
            if rule_result:

                # exprPostfixAux
                token_iterator, rule_result = rule_expr_postfix_aux(token_iterator)
                if rule_result:
                    return token_iterator, True

                # else:
                #     raise SyntaxErrorException(next(token_iterator), "invalid postfix expression")

            else:
                raise SyntaxErrorException(next(token_iterator), "no ] in array variable in expression")

        else:
            raise SyntaxErrorException(next(token_iterator), "no array index after [ in expression")

    # DOT
    token_iterator = copy.deepcopy(fallback_iterator)
    token_iterator, rule_result, _ = consume(token_iterator, Code.DOT)
    if rule_result:

        # ID
        token_iterator, rule_result, _ = consume(token_iterator, Code.ID)
        if rule_result:

            # exprPostfixAux
            token_iterator, rule_result = rule_expr_postfix_aux(token_iterator)
            if rule_result:
                return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "no field name after .")

    # e
    return fallback_iterator, True


# grammar rule:
# exprPostfix: exprPrimary exprPostfixAux
def rule_expr_postfix(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # exprPrimary
    token_iterator, rule_result = rule_expr_primary(token_iterator)
    if rule_result:

        # exprPostfixAux
        token_iterator, rule_result = rule_expr_postfix_aux(token_iterator)
        if rule_result:
            return token_iterator, True

    return fallback_iterator, False


# grammar rule:
# exprUnary: ( SUB | NOT ) exprUnary | exprPostfix
def rule_expr_unary(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # SUB
    token_iterator, rule_result, _ = consume(token_iterator, Code.SUB)
    if rule_result:

        # exprUnary
        token_iterator, rule_result = rule_expr_unary(token_iterator)
        if rule_result:
            return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "no unary expression after -")

    # NOT
    token_iterator, rule_result, _ = consume(token_iterator, Code.NOT)
    if rule_result:

        # exprUnary
        token_iterator, rule_result = rule_expr_unary(token_iterator)
        if rule_result:
            return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "no unary expression after ! (not)")

    # exprPostfix
    token_iterator = copy.deepcopy(fallback_iterator)
    token_iterator, rule_result = rule_expr_postfix(token_iterator)
    if rule_result:
        return token_iterator, True

    return fallback_iterator, False


# grammar rule:
# exprCast: LPAR typeBase arrayDecl? RPAR exprCast | exprUnary
def rule_expr_cast(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # LPAR
    token_iterator, rule_result, _ = consume(token_iterator, Code.LPAR)
    if rule_result:

        # typeBase
        token_iterator, rule_result = rule_type_base(token_iterator)
        if rule_result:

            # arrayDecl?
            token_iterator, rule_result = rule_array_decl(token_iterator)

            # RPAR
            token_iterator, rule_result, _ = consume(token_iterator, Code.RPAR)
            if rule_result:

                # exprCast
                token_iterator, rule_result = rule_expr_cast(token_iterator)
                if rule_result:

                    return token_iterator, True

                else:
                    raise SyntaxErrorException(next(token_iterator), "invalid expression after cast type")

            else:
                raise SyntaxErrorException(next(token_iterator), "no ) after type in cast")

        # cannot raise an exception here, there are other things after ( aside from cast types,
        # such as exprUnary

    # exprUnary
    token_iterator = copy.deepcopy(fallback_iterator)
    token_iterator, rule_result = rule_expr_unary(token_iterator)
    if rule_result:
        return token_iterator, True

    return fallback_iterator, False


# auxiliary grammar rule:
# exprMulAux: ( MUL | DIV ) exprCast exprMulAux | e
def rule_expr_mul_aux(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # MUL
    token_iterator, rule_result, _ = consume(token_iterator, Code.MUL)
    if rule_result:

        # exprCast
        token_iterator, rule_result = rule_expr_cast(token_iterator)
        if rule_result:

            # exprMulAux
            token_iterator, rule_result = rule_expr_mul_aux(token_iterator)
            if rule_result:
                return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after *")

    # DIV
    token_iterator, rule_result, _ = consume(token_iterator, Code.DIV)
    if rule_result:

        # exprCast
        token_iterator, rule_result = rule_expr_cast(token_iterator)
        if rule_result:

            # exprMulAux
            token_iterator, rule_result = rule_expr_mul_aux(token_iterator)
            if rule_result:
                return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after /")

    # e
    return fallback_iterator, True


# grammar rule:
# exprMul: exprCast exprMulAux
def rule_expr_mul(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # exprCast
    token_iterator, rule_result = rule_expr_cast(token_iterator)
    if rule_result:

        # exprMulAux
        token_iterator, rule_result = rule_expr_mul_aux(token_iterator)
        if rule_result:
            return token_iterator, True

    return fallback_iterator, False


# auxiliary grammar rule:
# exprAddAux: ( ADD | SUB ) exprMul exprAddAux | e
def rule_expr_add_aux(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # ADD
    token_iterator, rule_result, _ = consume(token_iterator, Code.ADD)
    if rule_result:

        # exprMul
        token_iterator, rule_result = rule_expr_mul(token_iterator)
        if rule_result:

            # exprAddAux
            token_iterator, rule_result = rule_expr_add_aux(token_iterator)
            if rule_result:
                return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after +")

    # SUB
    token_iterator, rule_result, _ = consume(token_iterator, Code.SUB)
    if rule_result:

        # exprMul
        token_iterator, rule_result = rule_expr_mul(token_iterator)
        if rule_result:

            # exprAddAux
            token_iterator, rule_result = rule_expr_add_aux(token_iterator)
            if rule_result:
                return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after -")

    # e
    return fallback_iterator, True


# grammar rule:
# exprAdd: exprMul exprAddAux
def rule_expr_add(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # exprMul
    token_iterator, rule_result = rule_expr_mul(token_iterator)
    if rule_result:

        # exprAddAux
        token_iterator, rule_result = rule_expr_add_aux(token_iterator)
        if rule_result:
            return token_iterator, True

    return fallback_iterator, False


# auxiliary grammar rule:
# exprRelAux: ( LESS | LESSEQ | GREATER | GREATEREQ ) exprAdd exprRelAux | e
def rule_expr_rel_aux(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # LESS
    token_iterator, rule_result, _ = consume(token_iterator, Code.LESS)
    if rule_result:

        # exprAdd
        token_iterator, rule_result = rule_expr_add(token_iterator)
        if rule_result:

            # exprRelAux
            token_iterator, rule_result = rule_expr_rel_aux(token_iterator)
            if rule_result:
                return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after <")

    # LESSEQ
    token_iterator, rule_result, _ = consume(token_iterator, Code.LESSEQ)
    if rule_result:

        # exprAdd
        token_iterator, rule_result = rule_expr_add(token_iterator)
        if rule_result:

            # exprRelAux
            token_iterator, rule_result = rule_expr_rel_aux(token_iterator)
            if rule_result:
                return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after <=")

    # GREATER
    token_iterator, rule_result, _ = consume(token_iterator, Code.GREATER)
    if rule_result:

        # exprAdd
        token_iterator, rule_result = rule_expr_add(token_iterator)
        if rule_result:

            # exprRelAux
            token_iterator, rule_result = rule_expr_rel_aux(token_iterator)
            if rule_result:
                return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after >")

    # GREATEREQ
    token_iterator, rule_result, _ = consume(token_iterator, Code.GREATEREQ)
    if rule_result:

        # exprAdd
        token_iterator, rule_result = rule_expr_add(token_iterator)
        if rule_result:

            # exprRelAux
            token_iterator, rule_result = rule_expr_rel_aux(token_iterator)
            if rule_result:
                return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after >=")

    # e
    return fallback_iterator, True


# grammar rule:
# exprRel: exprAdd exprRelAux
def rule_expr_rel(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # exprAdd
    token_iterator, rule_result = rule_expr_add(token_iterator)
    if rule_result:

        # exprRelAux
        token_iterator, rule_result = rule_expr_rel_aux(token_iterator)
        if rule_result:
            return token_iterator, True

    return fallback_iterator, False


# auxiliary grammar rule:
# exprEqAux: ( EQUAL | NOTEQ ) exprRel exprEqAux | e
def rule_expr_eq_aux(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # EQUAL
    token_iterator, rule_result, _ = consume(token_iterator, Code.EQUAL)
    if rule_result:

        # exprRel
        token_iterator, rule_result = rule_expr_rel(token_iterator)
        if rule_result:

            # exprEqAux
            token_iterator, rule_result = rule_expr_eq_aux(token_iterator)
            if rule_result:
                return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after ==")

    # NOTEQ
    token_iterator, rule_result, _ = consume(token_iterator, Code.NOTEQ)
    if rule_result:

        # exprRel
        token_iterator, rule_result = rule_expr_rel(token_iterator)
        if rule_result:

            # exprEqAux
            token_iterator, rule_result = rule_expr_eq_aux(token_iterator)
            if rule_result:
                return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after !=")

    # e
    return fallback_iterator, True


# grammar rule:
# exprEq: exprRel exprEqAux
def rule_expr_eq(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # exprRel
    token_iterator, rule_result = rule_expr_rel(token_iterator)
    if rule_result:

        # exprEqAux
        token_iterator, rule_result = rule_expr_eq_aux(token_iterator)
        if rule_result:
            return token_iterator, True

    return fallback_iterator, False


# auxiliary grammar rule:
# exprAndAux: AND exprEq exprAndAux | e
def rule_expr_and_aux(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # AND
    token_iterator, rule_result, _ = consume(token_iterator, Code.AND)
    if rule_result:

        # exprEq
        token_iterator, rule_result = rule_expr_eq(token_iterator)
        if rule_result:

            # exprAndAux
            token_iterator, rule_result = rule_expr_and_aux(token_iterator)
            if rule_result:
                return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after &&")

    # e
    return fallback_iterator, True


# grammar rule:
# exprAnd: exprEq exprAndAux
def rule_expr_and(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # exprEq
    token_iterator, rule_result = rule_expr_eq(token_iterator)
    if rule_result:

        # exprAndAux
        token_iterator, rule_result = rule_expr_and_aux(token_iterator)
        if rule_result:
            return token_iterator, True

    return fallback_iterator, False


# auxiliary grammar rule:
# exprOrAux: OR exprAnd exprOrAux | e
def rule_expr_or_aux(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # OR
    token_iterator, rule_result, _ = consume(token_iterator, Code.OR)
    if rule_result:

        # exprAnd
        token_iterator, rule_result = rule_expr_and(token_iterator)
        if rule_result:

            # exprOrAux
            token_iterator, rule_result = rule_expr_or_aux(token_iterator)
            if rule_result:
                return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after ||")

    # e
    return fallback_iterator, True


# grammar rule:
# exprOr: exprAnd exprOrAux
def rule_expr_or(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # exprAnd
    token_iterator, rule_result = rule_expr_and(token_iterator)
    if rule_result:

        # exprOrAux
        token_iterator, rule_result = rule_expr_or_aux(token_iterator)
        if rule_result:
            return token_iterator, True

    return fallback_iterator, False


# grammar rule:
# exprAssign: exprUnary ASSIGN exprAssign | exprOr
def rule_expr_assign(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # exprUnary
    token_iterator, rule_result = rule_expr_unary(token_iterator)
    if rule_result:

        # ASSIGN
        token_iterator, rule_result, _ = consume(token_iterator, Code.ASSIGN)
        if rule_result:

            # exprAssign
            token_iterator, rule_result = rule_expr_assign(token_iterator)
            if rule_result:

                return token_iterator, True

            else:
                # return fallback_iterator, False
                raise SyntaxErrorException(next(token_iterator),
                                           "invalid expression after =")

            # exprOr can be reduced to an unary expression, so every exprOr will be considered assignation unless
            # you let both the branches check

    # exprOr
    token_iterator = copy.deepcopy(fallback_iterator)
    token_iterator, rule_result = rule_expr_or(token_iterator)
    if rule_result:
        return token_iterator, True

    return fallback_iterator, False


# grammar rule:
# expr: exprAssign
def rule_expr(token_iterator: list):
    # exprAssign
    token_iterator, rule_result = rule_expr_assign(token_iterator)
    if rule_result:
        return token_iterator, True

    return token_iterator, False


# grammar rule:
# stmCompound: LACC ( varDef | stm )* RACC
#
# for domain analysis:
# stmCompound[in bool new_domain]: LACC ( varDef | stm )* RACC
def rule_stm_compound(token_iterator: iter, owner=None, new_domain=False):
    fallback_iterator = copy.deepcopy(token_iterator)

    # LACC
    token_iterator, rule_result, _ = consume(token_iterator, Code.LACC)
    if rule_result:

        # 1. if the boolean called with rule_stm_compound is true, define a new domain () for the {} block
        if new_domain:
            domain_stack.push_domain()

        # ( varDef | stm )*
        while True:

            # varDef
            token_iterator, rule_result, new_variable = rule_var_def(token_iterator, owner)
            if rule_result:
                owner.add_local_variable(new_variable)

            # stm
            if not rule_result:
                token_iterator, rule_result = rule_stm(token_iterator, owner)
                if not rule_result:
                    break

        # RACC
        token_iterator, rule_result, _ = consume(token_iterator, Code.RACC)
        if rule_result:

            # 2. if a new domain was created, close the domain and go back to its parent
            if new_domain:
                domain_stack.pop_domain()

            return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "no } after {")

    return fallback_iterator, False


# grammar rule:
# stm: stmCompound
# | IF LPAR expr RPAR stm ( ELSE stm )?
# | WHILE LPAR expr RPAR stm
# | FOR LPAR expr? SEMICOLON expr? SEMICOLON expr? RPAR stm
# | BREAK SEMICOLON
# | RETURN expr? SEMICOLON
# | expr? SEMICOLON
def rule_stm(token_iterator: iter, owner=None):
    fallback_iterator = copy.deepcopy(token_iterator)

    # stmCompound
    token_iterator, rule_result = rule_stm_compound(token_iterator, owner, True)  # must call with 'true' for new domain
    if rule_result:
        return token_iterator, True

    # IF
    token_iterator, rule_result, _ = consume(token_iterator, Code.IF)
    if rule_result:

        # LPAR
        token_iterator, rule_result, _ = consume(token_iterator, Code.LPAR)
        if rule_result:

            # expr
            token_iterator, rule_result = rule_expr(token_iterator)
            if rule_result:

                # RPAR
                token_iterator, rule_result, _ = consume(token_iterator, Code.RPAR)
                if rule_result:

                    # stm
                    token_iterator, rule_result = rule_stm(token_iterator, owner)
                    if rule_result:

                        # ELSE?
                        token_iterator, rule_result, _ = consume(token_iterator, Code.ELSE)
                        if rule_result:

                            # stm
                            token_iterator, rule_result = rule_stm(token_iterator, owner)
                            if rule_result:

                                return token_iterator, True

                            else:
                                raise SyntaxErrorException(next(token_iterator), "no statement after else")

                        return token_iterator, True

                    else:
                        raise SyntaxErrorException(next(token_iterator), "no statement after if")

                else:
                    raise SyntaxErrorException(next(token_iterator), "no ( after ) in if")

            else:
                raise SyntaxErrorException(next(token_iterator), "invalid or missing expression in if")

        else:
            raise SyntaxErrorException(next(token_iterator), "no ( after if")

    # WHILE
    token_iterator = copy.deepcopy(fallback_iterator)
    token_iterator, rule_result, _ = consume(token_iterator, Code.WHILE)
    if rule_result:

        # LPAR
        token_iterator, rule_result, _ = consume(token_iterator, Code.LPAR)
        if rule_result:

            # expr
            token_iterator, rule_result = rule_expr(token_iterator)
            if rule_result:

                # RPAR
                token_iterator, rule_result, _ = consume(token_iterator, Code.RPAR)
                if rule_result:

                    # stm
                    token_iterator, rule_result = rule_stm(token_iterator, owner)
                    if rule_result:

                        return token_iterator, True

                    else:
                        raise SyntaxErrorException(next(token_iterator), "no statement after while")

                else:
                    raise SyntaxErrorException(next(token_iterator), "no ) after ( in while")

            else:
                raise SyntaxErrorException(next(token_iterator), "invalid or missing expression after ( in while")

        else:
            raise SyntaxErrorException(next(token_iterator), "no ( after while")

    # FOR
    token_iterator = copy.deepcopy(fallback_iterator)
    token_iterator, rule_result, _ = consume(token_iterator, Code.FOR)
    if rule_result:

        # LPAR
        token_iterator, rule_result, _ = consume(token_iterator, Code.LPAR)
        if rule_result:

            # expr?
            token_iterator, _ = rule_expr(token_iterator)

            # SEMICOLON
            token_iterator, rule_result, _ = consume(token_iterator, Code.SEMICOLON)
            if rule_result:

                # expr?
                token_iterator, _ = rule_expr(token_iterator)

                # SEMICOLON
                token_iterator, rule_result, _ = consume(token_iterator, Code.SEMICOLON)
                if rule_result:

                    # expr?
                    token_iterator, _ = rule_expr(token_iterator)

                    # RPAR
                    token_iterator, rule_result, _ = consume(token_iterator, Code.RPAR)
                    if rule_result:

                        # stm
                        token_iterator, rule_result = rule_stm(token_iterator, owner)
                        if rule_result:

                            return token_iterator, True

                        else:
                            raise SyntaxErrorException(next(token_iterator), "no statement after for")

                    else:
                        raise SyntaxErrorException(next(token_iterator), "no ) after ( in for")

                else:
                    raise SyntaxErrorException(next(token_iterator), "no ; after condition in for")

            else:
                raise SyntaxErrorException(next(token_iterator), "no ; after init in for")

        raise SyntaxErrorException(next(token_iterator), "no ( after FOR")

    # BREAK
    token_iterator = copy.deepcopy(fallback_iterator)
    token_iterator, rule_result, _ = consume(token_iterator, Code.BREAK)
    if rule_result:

        # SEMICOLON
        token_iterator, rule_result, _ = consume(token_iterator, Code.SEMICOLON)
        if rule_result:

            return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "no ; after break")

    # RETURN
    token_iterator = copy.deepcopy(fallback_iterator)
    token_iterator, rule_result, _ = consume(token_iterator, Code.RETURN)
    if rule_result:

        # expr?
        token_iterator, _ = rule_expr(token_iterator)

        # SEMICOLON
        token_iterator, rule_result, _ = consume(token_iterator, Code.SEMICOLON)
        if rule_result:

            return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "no ; after return")

    # expr?
    token_iterator = copy.deepcopy(fallback_iterator)
    token_iterator, _ = rule_expr(token_iterator)

    # SEMICOLON
    token_iterator, rule_result, _ = consume(token_iterator, Code.SEMICOLON)
    if rule_result:
        return token_iterator, True

    # we cannot raise an error regarding the semicolon here,
    # because there are others rules which can be satisfied
    # so instead, the error will come from the stm_compound rule,
    # trying to find the } for the function definition

    return fallback_iterator, False


# grammar rule:
# fnParam: typeBase ID arrayDecl?
#
# for domain analysis:
# fnParam: {Type t;} typeBase[&t] ID[tkName] arrayDecl?[&t]
def rule_fn_param(token_iterator: iter, owner=None):
    fallback_iterator = copy.deepcopy(token_iterator)

    # typeBase
    token_iterator, rule_result, type_base = rule_type_base(token_iterator)
    if rule_result:

        # ID
        token_iterator, rule_result, param_id = consume(token_iterator, Code.ID)
        if rule_result:

            # arrayDecl?
            # if the array size exists in an array declaration, ignore it
            token_iterator, rule_result, array_size = rule_array_decl(token_iterator)
            if array_size is not None:
                new_param_type = Type(type_base, 0)
            else:
                new_param_type = Type(type_base, -1)  # -1 so it knows it's a variable (<0)

            new_param = Parameter(param_id, new_param_type, owner)

            # check that parameter name is unique in the function domain
            # (automatically done when the parameter is added to the domain)
            domain_stack.add_symbol_to_current_domain(new_param)
            return token_iterator, True, new_param

        else:
            raise SyntaxErrorException(next(token_iterator),
                                       "no variable name after type declaration in function parameter definition")

    return fallback_iterator, False, None


# grammar rule:
# fnDef: ( typeBase | VOID ) ID LPAR ( fnParam ( COMMA fnParam )* )? RPAR stmCompound
#
# for domain analysis:
# fnDef: ( typeBase[] | VOID{} ) ID LPAR ( fnParam ( COMMA fnParam )* )? RPAR stmCompound
def rule_fn_def(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # typeBase
    token_iterator, rule_result, type_base = rule_type_base(token_iterator)
    if rule_result:

        # ID
        token_iterator, rule_result, function_id = consume(token_iterator, Code.ID)
        if rule_result:

            # create new symbol for the new function and add it to the current domain
            # (will also check if the name of the function is unique)
            new_function_type = Type(type_base, -1)  # will never be a pointer or an array
            new_function = Function(function_id, new_function_type)

            # LPAR
            token_iterator, rule_result, _ = consume(token_iterator, Code.LPAR)
            if rule_result:

                # create new domain for the function and switch to it
                domain_stack.push_domain()

                # ( fnParam ( COMMA fnParam )* )?

                # fnParam
                token_iterator, rule_result, new_function_param = rule_fn_param(token_iterator, new_function)
                if rule_result:

                    new_function.add_function_parameter(new_function_param)

                    while True:

                        # COMMA
                        token_iterator, rule_result, _ = consume(token_iterator, Code.COMMA)
                        if rule_result:

                            # fnParam
                            token_iterator, rule_result, new_function_param = rule_fn_param(token_iterator, new_function)
                            if not rule_result:
                                raise SyntaxErrorException(next(token_iterator),
                                                           "no function parameter after comma")
                            else:
                                new_function.add_function_parameter(new_function_param)

                        else:
                            break

                # RPAR
                token_iterator, rule_result, _ = consume(token_iterator, Code.RPAR)
                if rule_result:

                    # stm
                    token_iterator, rule_result = rule_stm(token_iterator, new_function)
                    if rule_result:

                        # go back to global domain
                        domain_stack.pop_domain()
                        global_symbols.append(new_function)
                        domain_stack.add_symbol_to_current_domain(new_function)

                        return token_iterator, True

                    else:
                        raise SyntaxErrorException(next(token_iterator),
                                                   "missing { after function definition")

                else:
                    raise SyntaxErrorException(next(token_iterator), "no ) after ( in function definition")

            else:
                # not error, might be variable declaration
                return fallback_iterator, False

        else:
            # not error, might be cast
            return fallback_iterator, False

    # VOID
    token_iterator, rule_result, _ = consume(token_iterator, Code.VOID)
    if rule_result:

        # ID
        token_iterator, rule_result, function_id = consume(token_iterator, Code.ID)
        if rule_result:

            # create new symbol for the new function and add it to the current domain
            # (will also check if the name of the function is unique)
            new_function_type = Type(Void(), -1)  # will never be a pointer or an array
            new_function = Function(function_id, new_function_type)

            # LPAR
            token_iterator, rule_result, _ = consume(token_iterator, Code.LPAR)
            if rule_result:

                # create new domain for the function and switch to it
                domain_stack.push_domain()

                # ( fnParam ( COMMA fnParam )* )?

                # fnParam
                token_iterator, rule_result, new_function_param = rule_fn_param(token_iterator, new_function)
                if rule_result:

                    new_function.add_function_parameter(new_function_param)
                    domain_stack.add_symbol_to_current_domain(new_function_param)

                    while True:

                        # COMMA
                        token_iterator, rule_result, _ = consume(token_iterator, Code.COMMA)
                        if rule_result:

                            # fnParam
                            token_iterator, rule_result, new_function_param = rule_fn_param(token_iterator)
                            if not rule_result:
                                raise SyntaxErrorException(next(token_iterator),
                                                           "no function parameter after comma")
                            else:
                                new_function.add_function_parameter(new_function_param)
                                domain_stack.add_symbol_to_current_domain(new_function_param)

                        else:
                            break

                # RPAR
                token_iterator, rule_result, _ = consume(token_iterator, Code.RPAR)
                if rule_result:

                    # stm
                    token_iterator, rule_result = rule_stm(token_iterator, new_function)
                    if rule_result:

                        # go back to global domain
                        domain_stack.pop_domain()
                        global_symbols.append(new_function)
                        domain_stack.add_symbol_to_current_domain(new_function)

                        return token_iterator, True

                    else:
                        raise SyntaxErrorException(next(token_iterator),
                                                   "missing { after function definition")

                else:
                    raise SyntaxErrorException(next(token_iterator), "no ) after ( in function definition")

            else:
                # not error, might be variable declaration
                return fallback_iterator, False

        else:
            # not error, might be cast?
            return fallback_iterator, False

    return fallback_iterator, False


# grammar rule:
# arrayDecl: LBRACKET CT_INT? RBRACKET
def rule_array_decl(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # LBRACKET
    token_iterator, rule_result, _ = consume(token_iterator, Code.LBRACKET)
    if rule_result:

        # CT_INT? (was expr? before)
        token_iterator, rule_result, array_size = consume(token_iterator, Code.CT_INT)
        if not rule_result:
            array_size = 0

        # RBRACKET
        token_iterator, rule_result, _ = consume(token_iterator, Code.RBRACKET)
        if rule_result:

            return token_iterator, True, array_size

        else:
            raise SyntaxErrorException(next(token_iterator), "no ] after [ in array declaration")

    return fallback_iterator, False, None


# grammar rule:
# typeBase: INT | DOUBLE | CHAR | STRUCT ID
def rule_type_base(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # INT
    token_iterator, rule_result, _ = consume(token_iterator, Code.INT)
    if rule_result:
        return token_iterator, True, Integer()

    # DOUBLE
    token_iterator, rule_result, _ = consume(token_iterator, Code.DOUBLE)
    if rule_result:
        return token_iterator, True, Double()

    # CHAR
    token_iterator, rule_result, _ = consume(token_iterator, Code.CHAR)
    if rule_result:
        return token_iterator, True, Character()

    # STRUCT
    token_iterator, rule_result, _ = consume(token_iterator, Code.STRUCT)
    if rule_result:

        # ID
        token_iterator, rule_result, struct_id = consume(token_iterator, Code.ID)
        if rule_result:

            # if the base type is a struct type, check that it is defined
            # find_struct_def_with_id() does this for us

            struct_def = find_struct_def_with_id(struct_id)
            return token_iterator, True, Struct(struct_def)

        else:
            raise SyntaxErrorException(next(token_iterator), "no { in struct type definition or no ID after struct")

    return fallback_iterator, False, None


# grammar rule:
# varDef: typeBase ID arrayDecl? SEMICOLON
def rule_var_def(token_iterator: iter, owner=None):
    fallback_iterator = copy.deepcopy(token_iterator)

    # typeBase
    token_iterator, rule_result, type_base = rule_type_base(token_iterator)
    if rule_result:

        # ID
        token_iterator, rule_result, variable_id = consume(token_iterator, Code.ID)
        if rule_result:

            # arrayDecl?
            token_iterator, rule_result, array_size = rule_array_decl(token_iterator)

            # SEMICOLON
            token_iterator, rule_result, _ = consume(token_iterator, Code.SEMICOLON)
            if rule_result:

                # create a type for the new variable and create a new symbol object
                # array variables must have a size defined. check for that if the array declaration is present
                if array_size is not None:
                    if array_size > 0:
                        new_variable_type = Type(type_base, array_size)
                    else:
                        raise InvalidArraySizeErrorException(variable_id)
                else:
                    new_variable_type = Type(type_base, -1)  # -1 so it knows it's a variable (<0)

                new_variable = Variable(variable_id, new_variable_type, owner)

                # add the symbol to the current domain (will check if name is unique)
                # and add it to the list of variables of its owner
                domain_stack.add_symbol_to_current_domain(new_variable)

                if owner is None:
                    global_symbols.append(new_variable)
                return token_iterator, True, new_variable

            else:
                raise SyntaxErrorException(next(token_iterator), "no ; after variable definition")

        else:
            raise SyntaxErrorException(next(token_iterator), "no identifier after type")

    return fallback_iterator, False, None


# grammar rule:
# structDef: STRUCT ID LACC varDef* RACC SEMICOLON
def rule_struct_def(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # STRUCT
    token_iterator, rule_result, _ = consume(token_iterator, Code.STRUCT)
    if rule_result:

        # ID
        token_iterator, rule_result, new_struct_type_name = consume(token_iterator, Code.ID)
        if rule_result:

            # LACC
            token_iterator, rule_result, _ = consume(token_iterator, Code.LACC)
            if rule_result:

                # create new struct definition symbol
                new_struct_def = StructDef(new_struct_type_name)

                # create new domain for the struct variables
                domain_stack.push_domain()

                # varDef*
                while True:

                    token_iterator, rule_result, struct_member = rule_var_def(token_iterator, new_struct_def)
                    if not rule_result:
                        break
                    else:
                        new_struct_def.add_struct_member(struct_member)

                # RACC
                token_iterator, rule_result, _ = consume(token_iterator, Code.RACC)
                if rule_result:

                    # SEMICOLON
                    token_iterator, rule_result, _ = consume(token_iterator, Code.SEMICOLON)
                    if rule_result:

                        # close struct domain and go back to the global domain
                        domain_stack.pop_domain()

                        # add the struct definition to the global domain (also checks that name is unique)
                        # and append the symbol to the global symbols list
                        domain_stack.add_symbol_to_current_domain(new_struct_def)
                        global_symbols.append(new_struct_def)

                        return token_iterator, True

                    else:
                        raise SyntaxErrorException(next(token_iterator), "no semicolon after struct type definition")

                else:
                    raise SyntaxErrorException(next(token_iterator), "no } after { in struct type definition")

            else:
                # don't raise exception here, it might be a struct type definition, not a struct variable declaration
                # raise SyntaxErrorException(next(token_iterator), "unnamed struct declared")
                return fallback_iterator, False

        else:
            raise SyntaxErrorException(next(token_iterator), "unnamed struct")

    return fallback_iterator, False


# grammar rule:
# unit: ( structDef | fnDef | varDef )* END
def rule_unit(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # ( structDef | fnDef | varDef )*
    while True:

        # structDef
        token_iterator, rule_result = rule_struct_def(token_iterator)
        if not rule_result:

            # fnDef
            token_iterator, rule_result = rule_fn_def(token_iterator)
            if not rule_result:

                # varDef
                token_iterator, rule_result, _ = rule_var_def(token_iterator, None)
                if not rule_result:
                    break

    # END
    token_iterator, rule_result, _ = consume(token_iterator, Code.END)
    if rule_result:

        return token_iterator, True

    else:
        raise SyntaxErrorException(next(token_iterator), "invalid token found")


def analyze(tokens):

    token_iterator = iter(tokens)

    # I don't need to forward the declarations of functions as long as this function is the one which gets called first
    # here I will call the unit rule
    domain_stack.push_domain()

    _, analysis_result = rule_unit(token_iterator)

    for symbol in global_symbols:
        print(symbol.__str__())
