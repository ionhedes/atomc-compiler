from atomc.lexer.token import Token, Code
import copy

# rule of thumb:
# any rule function and also the consume function returns a tuple:
# - boolean: if the rule satisfied, token was consumed
# - iterator: the iterator at the new position in the list (after consuming all the tokens of that rule)
#             if the rule was not satisfied / token was not consumed, an iterator object with the initial state of the
#             main iterator is returned, so the iteration does not advance


def print_syntax_error(token: Token, msg: str):
    print("Syntax Error at line " + token.line + ": " + msg)


# for consuming terminal symbols/tokens from the grammar rules
def consume(token_iterator, code):
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
def rule_expr_primary(token_iterator: list):
    rule_result = None

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
                while (True):
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

    else:
        print_syntax_error(next(token_iterator), "invalid primary expression")
        return token_iterator, False


# auxiliary grammar rule:
# exprPostfixAux: LBRACKET expr RBRACKET exprPostfixAux
# | DOT ID exprPostfixAux
# | e
def rule_expr_postfix_aux(token_iterator: list):
    pass


# grammar rule:
# exprPostfix: exprPrimary exprPostfixAux
def rule_expr_postfix(token_iterator: list):
    pass


# grammar rule:
# exprUnary: ( SUB | NOT ) exprUnary | exprPostfix
def rule_expr_unary(token_iterator: list):
    pass


# grammar rule:
# exprCast: LPAR typeBase arrayDecl? RPAR exprCast | exprUnary
def rule_expr_cast(token_iterator: list):
    pass


# auxiliary grammar rule:
# exprMulAux: ( MUL | DIV ) exprCast exprMulAux | e
def rule_expr_mul_aux(token_iterator: list):
    pass


# grammar rule:
# exprMul: exprCast exprMulAux
def rule_expr_mul(token_iterator: list):
    pass


# auxiliary grammar rule:
# exprAddAux: ( ADD | SUB ) exprMul exprAddAux | e
def rule_expr_add_aux(token_iterator: list):
    pass


# grammar rule:
# exprAdd: exprMul exprAddAux
def rule_expr_add(token_iterator: list):
    pass


# auxiliary grammar rule:
# exprRelAux: ( LESS | LESSEQ | GREATER | GREATEREQ ) exprAdd exprRelAux | e
def rule_expr_rel_aux(token_iterator: list):
    pass


# grammar rule:
# exprRel: exprAdd exprRelAux
def rule_expr_rel(token_iterator: list):
    pass


# auxiliary grammar rule:
# exprEqAux: ( EQUAL | NOTEQ ) exprRel exprEqAux | e
def rule_expr_eq_aux(token_iterator: list):
    pass


# grammar rule:
# exprEq: exprRel exprEqAux
def rule_expr_eq(token_iterator: list):
    pass


# auxiliary grammar rule:
# exprAndAux: AND exprEq exprAndAux | e
def rule_expr_and_aux(token_iterator: list):
    pass


# grammar rule:
# exprAnd: exprEq exprAndAux
def rule_expr_and(token_iterator: list):
    pass


# auxiliary grammar rule:
# exprOrAux: OR exprAnd exprOrAux | e
def rule_expr_or_aux(token_iterator: list):
    pass


# grammar rule:
# exprOr: exprAnd exprOrAux
def rule_expr_or(token_iterator: list):
    pass


# grammar rule:
# exprAssign: exprUnary ASSIGN exprAssign | exprOr
def rule_expr_assign(token_iterator: list):
    pass


# grammar rule:
# expr: exprAssign
def rule_expr(token_iterator: list):
    pass


# grammar rule:
# stmCompound: LACC ( varDef | stm )* RACC
def rule_stm_compound(token_iterator: list):
    pass


# grammar rule:
# stm: stmCompound
# | IF LPAR expr RPAR stm ( ELSE stm )?
# | WHILE LPAR expr RPAR stm
# | FOR LPAR expr? SEMICOLON expr? SEMICOLON expr? RPAR stm
# | BREAK SEMICOLON
# | RETURN expr? SEMICOLON
# | expr? SEMICOLON
def rule_stm(token_iterator: list):
    pass


# grammar rule:
# fnParam: typeBase ID arrayDecl?
def rule_fn_param(token_iterator: list):
    pass


# grammar rule:
# fnDef: ( typeBase | VOID ) ID LPAR ( fnParam ( COMMA fnParam )* )? RPAR stmCompound
def rule_fn_def(token_iterator: list):
    pass


# grammar rule:
# arrayDecl: LBRACKET expr? RBRACKET
def rule_array_decl(token_iterator: list):
    pass


# grammar rule:
# typeBase: INT | DOUBLE | CHAR | STRUCT ID
def rule_type_base(token_iterator: list):
    pass


# grammar rule:
# varDef: typeBase ID arrayDecl? SEMICOLON
def rule_var_def(token_iterator: list):
    pass


# grammar rule:
# structDef: STRUCT ID LACC varDef* RACC SEMICOLON
def rule_struct_def(token_iterator: list):
    pass


# grammar rule:
# unit: ( structDef | fnDef | varDef )* END
def rule_unit(token_iterator: list):
    pass


def analyze(tokens):
    token_iterator = iter(tokens)

    # I don't need to forward the declarations of functions as long as this function is the one which gets called first
    # here I will call the unit rule
