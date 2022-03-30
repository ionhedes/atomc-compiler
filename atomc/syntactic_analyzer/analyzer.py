from atomc.lexer.token import Token, Code
from atomc.syntactic_analyzer.syntax_error_exception import SyntaxErrorException
import copy


# rule of thumb:
# any rule function and also the consume function returns a tuple:
# - boolean: if the rule satisfied, token was consumed
# - iterator: the iterator at the new position in the list (after consuming all the tokens of that rule)
#             if the rule was not satisfied / token was not consumed, an iterator object with the initial state of the
#             main iterator is returned, so the iteration does not advance


def print_syntax_error(token: Token, msg: str):
    print("Syntax Error at line " + str(token.line) + ", token type: " + str(token.code) + ": " + msg)


# for consuming terminal symbols/tokens from the grammar rules
def consume(token_iterator: iter, code: Code):
    # do not forget to deep copy the token_iterator, lest you will end up with an alias
    initial_iterator = copy.deepcopy(token_iterator)

    if next(token_iterator).code == code:
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
                        print_syntax_error(next(token_iterator), "missing expression after ,")
                        return token_iterator, False

                return token_iterator, True

            # RPAR
            token_iterator, rule_result = consume(token_iterator, Code.LPAR)
            if rule_result:
                return token_iterator, True

            else:
                print_syntax_error(next(token_iterator), "missing ) after (")  # merge asa cu next(token_iterator)?
                return token_iterator, False

        else:
            return token_iterator, True

    # CT_INT
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
                print_syntax_error(next(token_iterator), "missing ) after (")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "missing expression after (")
            return token_iterator, False

    return token_iterator, False


# auxiliary grammar rule:
# exprPostfixAux: LBRACKET expr RBRACKET exprPostfixAux
# | DOT ID exprPostfixAux
# | e
def rule_expr_postfix_aux(token_iterator: iter):
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

                else:
                    print_syntax_error(next(token_iterator), "invalid postfix expression")
                    return token_iterator, False

            else:
                print_syntax_error(next(token_iterator), "no ] after expression")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "no expression after [")
            return token_iterator, False

    # DOT
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
                print_syntax_error(next(token_iterator), "invalid expression after ID")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "no ID after .")
            return token_iterator, False

    # e
    return token_iterator, True


# grammar rule:
# exprPostfix: exprPrimary exprPostfixAux
def rule_expr_postfix(token_iterator: iter):
    # exprPrimary
    token_iterator, rule_result = rule_expr_primary(token_iterator)
    if rule_result:

        # exprPostfixAux
        token_iterator, rule_result = rule_expr_postfix_aux(token_iterator)
        if rule_result:
            return token_iterator, True

    return token_iterator, False


# grammar rule:
# exprUnary: ( SUB | NOT ) exprUnary | exprPostfix
def rule_expr_unary(token_iterator: iter):
    # SUB
    token_iterator, rule_result = consume(token_iterator, Code.SUB)
    if rule_result:

        # exprUnary
        token_iterator, rule_result = rule_expr_unary(token_iterator)
        if rule_result:

            return token_iterator, True

        else:
            print_syntax_error(next(token_iterator), "no unary expression after -")
            return token_iterator, False

    # NOT
    token_iterator, rule_result = consume(token_iterator, Code.NOT)
    if rule_result:

        # exprUnary
        token_iterator, rule_result = rule_expr_unary(token_iterator)
        if rule_result:

            return token_iterator, True

        else:
            print_syntax_error(next(token_iterator), "no unary expression after ! (not)")
            return token_iterator, False

    # exprPostfix
    token_iterator, rule_result = rule_expr_postfix(token_iterator)
    if rule_result:
        return token_iterator, True

    return token_iterator, False


# grammar rule:
# exprCast: LPAR typeBase arrayDecl? RPAR exprCast | exprUnary
def rule_expr_cast(token_iterator: iter):
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
                    print_syntax_error(next(token_iterator), "invalid expression after cast type")
                    return token_iterator, False

            else:
                print_syntax_error(next(token_iterator), "no ) after type in cast")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "no type after ) in cast")
            return token_iterator, False

    # exprUnary
    token_iterator, rule_result = rule_expr_unary(token_iterator)
    if rule_result:
        return token_iterator, True

    print_syntax_error(next(token_iterator), "invalid cast expression")
    return token_iterator, False


# auxiliary grammar rule:
# exprMulAux: ( MUL | DIV ) exprCast exprMulAux | e
def rule_expr_mul_aux(token_iterator: iter):
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
                print_syntax_error(next(token_iterator), "malformed multiplication expression")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "invalid expression after *")
            return token_iterator, False

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
                print_syntax_error(next(token_iterator), "malformed division expression")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "invalid expression after /")
            return token_iterator, False

    # e
    return token_iterator, True


# grammar rule:
# exprMul: exprCast exprMulAux
def rule_expr_mul(token_iterator: iter):
    # exprCast
    token_iterator, rule_result = rule_expr_cast(token_iterator)
    if rule_result:

        # exprMulAux
        token_iterator, rule_result = rule_expr_mul_aux(token_iterator)
        if rule_result:
            return token_iterator, True

    return token_iterator, False


# auxiliary grammar rule:
# exprAddAux: ( ADD | SUB ) exprMul exprAddAux | e
def rule_expr_add_aux(token_iterator: iter):
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
                print_syntax_error(next(token_iterator), "malformed addition expression")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "invalid expression after +")
            return token_iterator, False

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
                print_syntax_error(next(token_iterator), "malformed subtraction expression")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "invalid expression after -")
            return token_iterator, False

    # e
    return token_iterator, True


# grammar rule:
# exprAdd: exprMul exprAddAux
def rule_expr_add(token_iterator: iter):
    # exprMul
    token_iterator, rule_result = rule_expr_mul(token_iterator)
    if rule_result:

        # exprAddAux
        token_iterator, rule_result = rule_expr_add_aux(token_iterator)
        if rule_result:
            return token_iterator, True

    return token_iterator, False


# auxiliary grammar rule:
# exprRelAux: ( LESS | LESSEQ | GREATER | GREATEREQ ) exprAdd exprRelAux | e
def rule_expr_rel_aux(token_iterator: iter):
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
                print_syntax_error(next(token_iterator), "malformed comparison (<) expression")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "invalid expression after <")
            return token_iterator, False

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
                print_syntax_error(next(token_iterator), "malformed comparison (<=) expression")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "invalid expression after <=")
            return token_iterator, False

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
                print_syntax_error(next(token_iterator), "malformed comparison (>) expression")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "invalid expression after >")
            return token_iterator, False

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
                print_syntax_error(next(token_iterator), "malformed comparison (>=) expression")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "invalid expression after >=")
            return token_iterator, False

    # e
    return token_iterator, True


# grammar rule:
# exprRel: exprAdd exprRelAux
def rule_expr_rel(token_iterator: iter):
    # exprAdd
    token_iterator, rule_result = rule_expr_add(token_iterator)
    if rule_result:

        # exprRelAux
        token, rule_result = rule_expr_rel_aux(token_iterator)
        if rule_result:
            return token_iterator, True

    return token_iterator, False


# auxiliary grammar rule:
# exprEqAux: ( EQUAL | NOTEQ ) exprRel exprEqAux | e
def rule_expr_eq_aux(token_iterator: iter):
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
                print_syntax_error(next(token_iterator), "malformed equality (==) expression")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "invalid expression after ==")
            return token_iterator, False

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
                print_syntax_error(next(token_iterator), "malformed inequality (!=) expression")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "invalid expression after !=")
            return token_iterator, False

    # e
    return token_iterator, True


# grammar rule:
# exprEq: exprRel exprEqAux
def rule_expr_eq(token_iterator: iter):
    # exprRel
    token_iterator, rule_result = rule_expr_rel(token_iterator)
    if rule_result:

        # exprEqAux
        token_iterator, rule_result = rule_expr_eq_aux(token_iterator)
        if rule_result:
            return token_iterator, True

    return token_iterator, False


# auxiliary grammar rule:
# exprAndAux: AND exprEq exprAndAux | e
def rule_expr_and_aux(token_iterator: iter):
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
                print_syntax_error(next(token_iterator), "malformed and (&&) expression")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "invalid expression after &&")
            return token_iterator, False

    # e
    return token_iterator, True


# grammar rule:
# exprAnd: exprEq exprAndAux
def rule_expr_and(token_iterator: iter):
    # exprEq
    token_iterator, rule_result = rule_expr_eq(token_iterator)
    if rule_result:

        # exprAndAux
        token_iterator, rule_result = rule_expr_and_aux(token_iterator)
        if rule_result:
            return token_iterator, True

    return token_iterator, False


# auxiliary grammar rule:
# exprOrAux: OR exprAnd exprOrAux | e
def rule_expr_or_aux(token_iterator: iter):
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
                print_syntax_error(next(token_iterator), "malformed or (||) expression")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "invalid expression after ||")
            return token_iterator, False

    # e
    return token_iterator, True


# grammar rule:
# exprOr: exprAnd exprOrAux
def rule_expr_or(token_iterator: iter):
    # exprAnd
    token_iterator, rule_result = rule_expr_and(token_iterator)
    if rule_result:

        # exprOrAux
        token_iterator, rule_result = rule_expr_or_aux(token_iterator)
        if rule_result:
            return token_iterator, True

    return token_iterator, False


# grammar rule:
# exprAssign: exprUnary ASSIGN exprAssign | exprOr
def rule_expr_assign(token_iterator: iter):
    # exprUnary
    token_iterator, rule_result = rule_expr_unary(token_iterator)
    if rule_result:

        # ASSIGN
        print("check for assign token")
        token_iterator, rule_result = consume(token_iterator, Code.ASSIGN)
        if rule_result:

            # exprAssign
            print("check for assign expr")
            token_iterator, rule_result = rule_expr_assign(token_iterator)
            if rule_result:

                return token_iterator, True

            else:
                print_syntax_error(next(token_iterator), "invalid expression after assignment (=)")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "no = after unary expression in assignment")
            return token_iterator, False

    # exprOr
    token_iterator, rule_result = rule_expr_or(token_iterator)
    if rule_result:
        return token_iterator, True

    return token_iterator, False


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
    # LACC
    token_iterator, rule_result = consume(token_iterator, Code.LACC)
    if rule_result:

        # ( varDef | stm )*
        while True:
            may_end = False

            # varDef
            token_iterator, rule_result = rule_var_def(token_iterator)
            if not rule_result:
                may_end = True

            # stm
            token_iterator, rule_result = rule_stm(token_iterator)
            if not rule_result and may_end:
                break

        # RACC
        token_iterator, rule_result = consume(token_iterator, Code.RACC)
        if rule_result:

            return token_iterator, True

        else:
            print_syntax_error(next(token_iterator), "no } after {")
            return token_iterator, False

    return token_iterator, False


# grammar rule:
# stm: stmCompound
# | IF LPAR expr RPAR stm ( ELSE stm )?
# | WHILE LPAR expr RPAR stm
# | FOR LPAR expr? SEMICOLON expr? SEMICOLON expr? RPAR stm
# | BREAK SEMICOLON
# | RETURN expr? SEMICOLON
# | expr? SEMICOLON
def rule_stm(token_iterator: iter):
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
            print("check for expression in if")
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
                                print_syntax_error(next(token_iterator), "no statement after else")
                                return token_iterator, False

                    else:
                        print_syntax_error(next(token_iterator), "no statement after if")
                        return token_iterator, False

                else:
                    print_syntax_error(next(token_iterator), "no ( after ) in statement")
                    return token_iterator, False

            else:
                print_syntax_error(next(token_iterator), "no expression after ) in statement")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "no ( after IF")
            return token_iterator, False

    # WHILE
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
                        print_syntax_error(next(token_iterator), "no statement after while")
                        return token_iterator, False

                else:
                    print_syntax_error(next(token_iterator), "no ) after ( in while")
                    return token_iterator, False

            else:
                print_syntax_error(next(token_iterator), "no expression after ( in while")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "no ( after while")
            return token_iterator, False

    # FOR
    token_iterator, rule_result = consume(token_iterator, Code.FOR)
    if rule_result:

        # LPAR
        token_iterator, rule_result = consume(token_iterator, Code.LPAR)
        if rule_result:

            # expr?
            print("check for expr in for init")
            token_iterator, _ = rule_expr(token_iterator)

            # SEMICOLON
            token_iterator, rule_result = consume(token_iterator, Code.SEMICOLON)
            if rule_result:

                # expr?
                print("check for expr in for condition")
                token_iterator, _ = rule_expr(token_iterator)

                # SEMICOLON
                token_iterator, rule_result = consume(token_iterator, Code.SEMICOLON)
                if rule_result:

                    # expr?
                    print("check for expr in for update")
                    token_iterator, _ = rule_expr(token_iterator)

                    # RPAR
                    token_iterator, rule_result = consume(token_iterator, Code.RPAR)
                    if rule_result:

                        # stm
                        token_iterator, rule_result = rule_stm(token_iterator)
                        if rule_result:

                            return token_iterator, True

                        else:
                            print_syntax_error(next(token_iterator), "no statement after for")
                            return token_iterator, False

                    else:
                        print_syntax_error(next(token_iterator), "no ) after ( in for")
                        return token_iterator, False

                else:
                    print_syntax_error(next(token_iterator), "no ; after condition in for")
                    return token_iterator, False

            else:
                print_syntax_error(next(token_iterator), "no ; after init in for")
                return token_iterator, False

        print_syntax_error(next(token_iterator), "no ( after FOR")
        return token_iterator, False

    # BREAK
    token_iterator, rule_result = consume(token_iterator, Code.BREAK)
    if rule_result:

        # SEMICOLON
        token_iterator, rule_result = consume(token_iterator, Code.SEMICOLON)
        if rule_result:

            return token_iterator, True

        else:
            print_syntax_error(next(token_iterator), "no ; after break")
            return token_iterator, False

    # RETURN
    token_iterator, rule_result = consume(token_iterator, Code.RETURN)
    if rule_result:

        # expr?
        print("check for expr in return")
        token_iterator, _ = rule_expr(token_iterator)

        # SEMICOLON
        token_iterator, rule_result = consume(token_iterator, Code.SEMICOLON)
        if rule_result:

            return token_iterator, True

        else:
            print_syntax_error(next(token_iterator), "no ; after return")
            return token_iterator, False

    # expr?
    token_iterator, _ = rule_expr(token_iterator)

    # SEMICOLON
    token_iterator, rule_result = consume(token_iterator, Code.SEMICOLON)
    if rule_result:

        return token_iterator, True

    return token_iterator, False


# grammar rule:
# fnParam: typeBase ID arrayDecl?
def rule_fn_param(token_iterator: iter):
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
            print_syntax_error(next(token_iterator), "no ID after type declaration in function parameter definition")
            return token_iterator, False

    return token_iterator, False


# grammar rule:
# fnDef: ( typeBase | VOID ) ID LPAR ( fnParam ( COMMA fnParam )* )? RPAR stmCompound
def rule_fn_def(token_iterator: iter):
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
                                print_syntax_error(next(token_iterator),
                                                   "no function parameter after comma")
                                return token_iterator, False

                        else:
                            break

                # RPAR
                token_iterator, rule_result = consume(token_iterator, Code.RPAR)
                if rule_result:

                    # stm
                    print("check for function body")
                    token_iterator, rule_result = rule_stm(token_iterator)
                    if rule_result:

                        return token_iterator, True

                    else:
                        print_syntax_error(next(token_iterator), "function has no body")
                        return token_iterator, False

                else:
                    print_syntax_error(next(token_iterator), "no ) after ( in function definition")
                    return token_iterator, False

            else:
                print_syntax_error(next(token_iterator), "no ( after function name in function definition")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "no function name after returned type")
            return token_iterator, False

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
                                print_syntax_error(next(token_iterator),
                                                   "no function parameter after comma")
                                return token_iterator, False

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
                        print_syntax_error(next(token_iterator), "function has no body")
                        return token_iterator, False

                else:
                    print_syntax_error(next(token_iterator), "no ) after ( in function definition")
                    return token_iterator, False

            else:
                print_syntax_error(next(token_iterator), "no ( after function name in function definition")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "no function name after returned type")
            return token_iterator, False

    return token_iterator, False


# grammar rule:
# arrayDecl: LBRACKET expr? RBRACKET
def rule_array_decl(token_iterator: iter):
    # LBRACKET
    token_iterator, rule_result = consume(token_iterator, Code.LBRACKET)
    if rule_result:

        # expr?
        token_iterator, _ = rule_expr(token_iterator)

        # RBRACKET
        token_iterator, rule_result = consume(token_iterator, Code.RBRACKET)
        if rule_result:

            return token_iterator, True

        else:
            print_syntax_error(next(token_iterator), "no ] after [ in array declaration")
            return token_iterator, False

    return token_iterator, False


# grammar rule:
# typeBase: INT | DOUBLE | CHAR | STRUCT ID
def rule_type_base(token_iterator: iter):
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
            print_syntax_error(next(token_iterator), "unnamed struct declared")
            return token_iterator, False

    return token_iterator, False


# grammar rule:
# varDef: typeBase ID arrayDecl? SEMICOLON
def rule_var_def(token_iterator: iter):
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
                print_syntax_error(next(token_iterator), "no ; after variable definition")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "no variable name in variable definition")
            return token_iterator, False

    return token_iterator, False


# grammar rule:
# structDef: STRUCT ID LACC varDef* RACC SEMICOLON
def rule_struct_def(token_iterator: iter):
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
                        print_syntax_error(next(token_iterator), "no semicolon after struct definition")
                        return token_iterator, False

                else:
                    print_syntax_error(next(token_iterator), "no } after { in struct definition")
                    return token_iterator, False

            else:
                print_syntax_error(next(token_iterator), "no { in struct definition")
                return token_iterator, False

        else:
            print_syntax_error(next(token_iterator), "unnamed struct")
            return token_iterator, False

    return token_iterator, False


# grammar rule:
# unit: ( structDef | fnDef | varDef )* END
def rule_unit(token_iterator: iter):
    # ( structDef | fnDef | varDef )*
    while True:
        struct_not_found = False
        function_not_found = False
        variable_not_found = False

        # structDef
        token_iterator, rule_result = rule_struct_def(token_iterator)
        if not rule_result:
            struct_not_found = True

        # fnDef
        print("check for func def")
        token_iterator, rule_result = rule_fn_def(token_iterator)
        if not rule_result:
            function_not_found = True

        # varDef
        token_iterator, rule_result = rule_var_def(token_iterator)
        if not rule_result:
            variable_not_found = True

        if struct_not_found and function_not_found and variable_not_found:
            break

    # END
    token_iterator, rule_result = consume(token_iterator, Code.END)
    if rule_result:

        return token_iterator, True

    else:
        print_syntax_error(next(token_iterator), "missing end of file token")
        return token_iterator, False


def analyze(tokens):
    token_iterator = iter(tokens)

    # I don't need to forward the declarations of functions as long as this function is the one which gets called first
    # here I will call the unit rule
    _, analysis_result = rule_unit(token_iterator)

    if not analysis_result:
        raise SyntaxErrorException()
