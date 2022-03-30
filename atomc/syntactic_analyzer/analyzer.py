from atomc.lexer.token import Token, Code


# for consuming terminal symbols/tokens from the grammar rules
def consume(token, code):
    if token.code == code:
        return True
    return False


# grammar rule:
# exprPrimary: ID ( LPAR ( expr ( COMMA expr )* )? RPAR )?
# | CT_INT
# | CT_REAL
# | CT_CHAR
# | CT_STRING
# | LPAR expr RPAR
def rule_expr_primary(token_iterator: list):
    pass


# grammar rule:
# exprPostfix: exprPostfix LBRACKET expr RBRACKET
# | exprPostfix DOT ID
# | exprPrimary
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


# grammar rule:
# exprMul: exprMul ( MUL | DIV ) exprCast | exprCast
def rule_expr_mul(token_iterator: list):
    pass


# grammar rule:
# exprAdd: exprAdd ( ADD | SUB ) exprMul | exprMul
def expr_add(token_iterator: list):
    pass


# grammar rule:
# exprRel: exprRel ( LESS | LESSEQ | GREATER | GREATEREQ ) exprAdd | exprAdd
def rule_expr_rel(token_iterator: list):
    pass


# grammar rule:
# exprEq: exprEq ( EQUAL | NOTEQ ) exprRel | exprRel
def rule_expr_eq(token_iterator: list):
    pass


# grammar rule:
# exprAnd: exprAnd AND exprEq | exprEq
def rule_expr_and(token_iterator: list):
    pass


# grammar rule:
# exprOr: exprOr OR exprAnd | exprAnd
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
