import copy

from atomc.lexer.token import Code
from atomc.syntactic_analyzer.syntax_error_exception import SyntaxErrorException


# rule of thumb:
# any rule function and also the consume function returns a tuple:
# - boolean: if the rule satisfied, token was consumed
# - iterator: the iterator at the new position in the list (after consuming all the tokens of that rule)
#             if the rule was not satisfied / token was not consumed, an iterator object with the initial state of the
#             main iterator is returned, so the iteration does not advance


# for consuming terminal symbols/tokens from the grammar rules
def consume(token_iterator: iter, code: Code):
    # do not forget to deep copy the token_iterator, lest you will end up with an alias
    initial_iterator = copy.deepcopy(token_iterator)

    tk = next(token_iterator)
    if tk.code == code:
        return token_iterator, True

    return initial_iterator, False


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
    token_iterator, rule_result = consume(token_iterator, Code.ID)
    if rule_result:

        # LPAR?
        token_iterator, rule_result = consume(token_iterator, Code.LPAR)
        if rule_result:

            # expr?
            token_iterator, rule_result = rule_expr(token_iterator)
            if rule_result:

                # COMMA*
                while True:
                    token_iterator, rule_result = consume(token_iterator, Code.COMMA)

                    if not rule_result:
                        break

                    # expr
                    token_iterator, rule_result = rule_expr(token_iterator)
                    if not rule_result:
                        raise SyntaxErrorException(next(token_iterator), "missing function parameter after , "
                                                                         "in function call")

            # RPAR
            token_iterator, rule_result = consume(token_iterator, Code.RPAR)
            if rule_result:
                return token_iterator, True

            else:
                raise SyntaxErrorException(next(token_iterator),
                                           "missing ) after ( in function call")

        else:
            return token_iterator, True

    # CT_INT
    token_iterator = copy.deepcopy(fallback_iterator)
    token_iterator, rule_result = consume(token_iterator, Code.CT_INT)
    if rule_result:
        return token_iterator, True

    # CT_REAL
    token_iterator, rule_result = consume(token_iterator, Code.CT_REAL)
    if rule_result:
        return token_iterator, True

    # CT_CHAR
    token_iterator, rule_result = consume(token_iterator, Code.CT_CHAR)
    if rule_result:
        return token_iterator, True

    # CT_STRING
    token_iterator, rule_result = consume(token_iterator, Code.CT_STRING)
    if rule_result:
        return token_iterator, True

    # LPAR
    token_iterator, rule_result = consume(token_iterator, Code.LPAR)
    if rule_result:

        # expr
        token_iterator, rule_result = rule_expr(token_iterator)
        if rule_result:

            # RPAR
            token_iterator, rule_result = consume(token_iterator, Code.RPAR)
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
    token_iterator, rule_result = consume(token_iterator, Code.LBRACKET)
    if rule_result:

        # expr
        token_iterator, rule_result = rule_expr(token_iterator)
        if rule_result:

            # RBRACKET
            token_iterator, rule_result = consume(token_iterator, Code.RBRACKET)
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
    token_iterator, rule_result = consume(token_iterator, Code.DOT)
    if rule_result:

        # ID
        token_iterator, rule_result = consume(token_iterator, Code.ID)
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
    token_iterator, rule_result = consume(token_iterator, Code.SUB)
    if rule_result:

        # exprUnary
        token_iterator, rule_result = rule_expr_unary(token_iterator)
        if rule_result:
            return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "no unary expression after -")

    # NOT
    token_iterator, rule_result = consume(token_iterator, Code.NOT)
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
    token_iterator, rule_result = consume(token_iterator, Code.LPAR)
    if rule_result:

        # typeBase
        token_iterator, rule_result = rule_type_base(token_iterator)
        if rule_result:

            # arrayDecl?
            token_iterator, rule_result = rule_array_decl(token_iterator)

            # RPAR
            token_iterator, rule_result = consume(token_iterator, Code.RPAR)
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
    token_iterator, rule_result = consume(token_iterator, Code.MUL)
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
    token_iterator, rule_result = consume(token_iterator, Code.DIV)
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
    token_iterator, rule_result = consume(token_iterator, Code.ADD)
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
    token_iterator, rule_result = consume(token_iterator, Code.SUB)
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
    token_iterator, rule_result = consume(token_iterator, Code.LESS)
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
    token_iterator, rule_result = consume(token_iterator, Code.LESSEQ)
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
    token_iterator, rule_result = consume(token_iterator, Code.GREATER)
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
    token_iterator, rule_result = consume(token_iterator, Code.GREATEREQ)
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
    token_iterator, rule_result = consume(token_iterator, Code.EQUAL)
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
    token_iterator, rule_result = consume(token_iterator, Code.NOTEQ)
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
    token_iterator, rule_result = consume(token_iterator, Code.AND)
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
    token_iterator, rule_result = consume(token_iterator, Code.OR)
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
        token_iterator, rule_result = consume(token_iterator, Code.ASSIGN)
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
def rule_stm_compound(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # LACC
    token_iterator, rule_result = consume(token_iterator, Code.LACC)
    if rule_result:

        # ( varDef | stm )*
        while True:

            # varDef
            token_iterator, rule_result = rule_var_def(token_iterator)

            # stm
            if not rule_result:
                token_iterator, rule_result = rule_stm(token_iterator)
                if not rule_result:
                    break

        # RACC
        token_iterator, rule_result = consume(token_iterator, Code.RACC)
        if rule_result:

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
def rule_stm(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # stmCompound
    token_iterator, rule_result = rule_stm_compound(token_iterator)
    if rule_result:
        return token_iterator, True

    # IF
    token_iterator, rule_result = consume(token_iterator, Code.IF)
    if rule_result:

        # LPAR
        token_iterator, rule_result = consume(token_iterator, Code.LPAR)
        if rule_result:

            # expr
            token_iterator, rule_result = rule_expr(token_iterator)
            if rule_result:

                # RPAR
                token_iterator, rule_result = consume(token_iterator, Code.RPAR)
                if rule_result:

                    # stm
                    token_iterator, rule_result = rule_stm(token_iterator)
                    if rule_result:

                        # ELSE?
                        token_iterator, rule_result = consume(token_iterator, Code.ELSE)
                        if rule_result:

                            # stm
                            token_iterator, rule_result = rule_stm(token_iterator)
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
    token_iterator, rule_result = consume(token_iterator, Code.WHILE)
    if rule_result:

        # LPAR
        token_iterator, rule_result = consume(token_iterator, Code.LPAR)
        if rule_result:

            # expr
            token_iterator, rule_result = rule_expr(token_iterator)
            if rule_result:

                # RPAR
                token_iterator, rule_result = consume(token_iterator, Code.RPAR)
                if rule_result:

                    # stm
                    token_iterator, rule_result = rule_stm(token_iterator)
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
    token_iterator, rule_result = consume(token_iterator, Code.FOR)
    if rule_result:

        # LPAR
        token_iterator, rule_result = consume(token_iterator, Code.LPAR)
        if rule_result:

            # expr?
            token_iterator, _ = rule_expr(token_iterator)

            # SEMICOLON
            token_iterator, rule_result = consume(token_iterator, Code.SEMICOLON)
            if rule_result:

                # expr?
                token_iterator, _ = rule_expr(token_iterator)

                # SEMICOLON
                token_iterator, rule_result = consume(token_iterator, Code.SEMICOLON)
                if rule_result:

                    # expr?
                    token_iterator, _ = rule_expr(token_iterator)

                    # RPAR
                    token_iterator, rule_result = consume(token_iterator, Code.RPAR)
                    if rule_result:

                        # stm
                        token_iterator, rule_result = rule_stm(token_iterator)
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
    token_iterator, rule_result = consume(token_iterator, Code.BREAK)
    if rule_result:

        # SEMICOLON
        token_iterator, rule_result = consume(token_iterator, Code.SEMICOLON)
        if rule_result:

            return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "no ; after break")

    # RETURN
    token_iterator = copy.deepcopy(fallback_iterator)
    token_iterator, rule_result = consume(token_iterator, Code.RETURN)
    if rule_result:

        # expr?
        token_iterator, _ = rule_expr(token_iterator)

        # SEMICOLON
        token_iterator, rule_result = consume(token_iterator, Code.SEMICOLON)
        if rule_result:

            return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "no ; after return")

    # expr?
    token_iterator = copy.deepcopy(fallback_iterator)
    token_iterator, _ = rule_expr(token_iterator)

    # SEMICOLON
    token_iterator, rule_result = consume(token_iterator, Code.SEMICOLON)
    if rule_result:
        return token_iterator, True

    # we cannot raise an error regarding the semicolon here,
    # because there are others rules which can be satisfied
    # so instead, the error will come from the stm_compound rule,
    # trying to find the } for the function definition

    return fallback_iterator, False


# grammar rule:
# fnParam: typeBase ID arrayDecl?
def rule_fn_param(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # typeBase
    token_iterator, rule_result = rule_type_base(token_iterator)
    if rule_result:

        # ID
        token_iterator, rule_result = consume(token_iterator, Code.ID)
        if rule_result:

            # arrayDecl?
            token_iterator, _ = rule_array_decl(token_iterator)

            return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator),
                                       "no variable name after type declaration in function parameter definition")

    return fallback_iterator, False


# grammar rule:
# fnDef: ( typeBase | VOID ) ID LPAR ( fnParam ( COMMA fnParam )* )? RPAR stmCompound
def rule_fn_def(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # typeBase
    token_iterator, rule_result = rule_type_base(token_iterator)
    if rule_result:

        # ID
        token_iterator, rule_result = consume(token_iterator, Code.ID)
        if rule_result:

            # LPAR
            token_iterator, rule_result = consume(token_iterator, Code.LPAR)
            if rule_result:

                # ( fnParam ( COMMA fnParam )* )?

                # fnParam
                token_iterator, rule_result = rule_fn_param(token_iterator)
                if rule_result:

                    while True:

                        # COMMA
                        token_iterator, rule_result = consume(token_iterator, Code.COMMA)
                        if rule_result:

                            # fnParam
                            token_iterator, rule_result = rule_fn_param(token_iterator)
                            if not rule_result:
                                raise SyntaxErrorException(next(token_iterator),
                                                           "no function parameter after comma")

                        else:
                            break

                # RPAR
                token_iterator, rule_result = consume(token_iterator, Code.RPAR)
                if rule_result:

                    # stm
                    token_iterator, rule_result = rule_stm(token_iterator)
                    if rule_result:

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
    token_iterator, rule_result = consume(token_iterator, Code.VOID)
    if rule_result:

        # ID
        token_iterator, rule_result = consume(token_iterator, Code.ID)
        if rule_result:

            # LPAR
            token_iterator, rule_result = consume(token_iterator, Code.LPAR)
            if rule_result:

                # ( fnParam ( COMMA fnParam )* )?

                # fnParam
                token_iterator, rule_result = rule_fn_param(token_iterator)
                if rule_result:

                    while True:

                        # COMMA
                        token_iterator, rule_result = consume(token_iterator, Code.COMMA)
                        if rule_result:

                            # fnParam
                            token_iterator, rule_result = rule_fn_param(token_iterator)
                            if not rule_result:
                                raise SyntaxErrorException(next(token_iterator),
                                                           "no function parameter after comma")

                        else:
                            break

                # RPAR
                token_iterator, rule_result = consume(token_iterator, Code.RPAR)
                if rule_result:

                    # stm
                    token_iterator, rule_result = rule_stm(token_iterator)
                    if rule_result:

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
    token_iterator, rule_result = consume(token_iterator, Code.LBRACKET)
    if rule_result:

        # CT_INT? (was expr? before)
        token_iterator, _ = consume(token_iterator, Code.CT_INT)

        # RBRACKET
        token_iterator, rule_result = consume(token_iterator, Code.RBRACKET)
        if rule_result:

            return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "no ] after [ in array declaration")

    return fallback_iterator, False


# grammar rule:
# typeBase: INT | DOUBLE | CHAR | STRUCT ID
def rule_type_base(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # INT
    token_iterator, rule_result = consume(token_iterator, Code.INT)
    if rule_result:
        return token_iterator, True

    # DOUBLE
    token_iterator, rule_result = consume(token_iterator, Code.DOUBLE)
    if rule_result:
        return token_iterator, True

    # CHAR
    token_iterator, rule_result = consume(token_iterator, Code.CHAR)
    if rule_result:
        return token_iterator, True

    # STRUCT
    token_iterator, rule_result = consume(token_iterator, Code.STRUCT)
    if rule_result:

        # ID
        token_iterator, rule_result = consume(token_iterator, Code.ID)
        if rule_result:

            return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "no { in struct type definition or no ID after struct")

    return fallback_iterator, False


# grammar rule:
# varDef: typeBase ID arrayDecl? SEMICOLON
def rule_var_def(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # typeBase
    token_iterator, rule_result = rule_type_base(token_iterator)
    if rule_result:

        # ID
        token_iterator, rule_result = consume(token_iterator, Code.ID)
        if rule_result:

            # arrayDecl?
            token_iterator, _ = rule_array_decl(token_iterator)

            # SEMICOLON
            token_iterator, rule_result = consume(token_iterator, Code.SEMICOLON)
            if rule_result:

                return token_iterator, True

            else:
                raise SyntaxErrorException(next(token_iterator), "no ; after variable definition")

        else:
            raise SyntaxErrorException(next(token_iterator), "no identifier after type")

    return fallback_iterator, False


# grammar rule:
# structDef: STRUCT ID LACC varDef* RACC SEMICOLON
def rule_struct_def(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # STRUCT
    token_iterator, rule_result = consume(token_iterator, Code.STRUCT)
    if rule_result:

        # ID
        token_iterator, rule_result = consume(token_iterator, Code.ID)
        if rule_result:

            # LACC
            token_iterator, rule_result = consume(token_iterator, Code.LACC)
            if rule_result:

                # varDef*
                while True:

                    token_iterator, rule_result = rule_var_def(token_iterator)
                    if not rule_result:
                        break

                # RACC
                token_iterator, rule_result = consume(token_iterator, Code.RACC)
                if rule_result:

                    # SEMICOLON
                    token_iterator, rule_result = consume(token_iterator, Code.SEMICOLON)
                    if rule_result:

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
                token_iterator, rule_result = rule_var_def(token_iterator)
                if not rule_result:
                    break

    # END
    token_iterator, rule_result = consume(token_iterator, Code.END)
    if rule_result:

        return token_iterator, True

    else:
        raise SyntaxErrorException(next(token_iterator), "invalid token found")


def analyze(tokens):
    token_iterator = iter(tokens)

    # I don't need to forward the declarations of functions as long as this function is the one which gets called first
    # here I will call the unit rule
    _, analysis_result = rule_unit(token_iterator)
