import copy

from atomc.domain_analyzer.domain import DomainStack
from atomc.domain_analyzer.domain_error_exception import InvalidArraySizeErrorException, NoStructDefErrorException
from atomc.domain_analyzer.symbol import Variable, Function, Parameter, StructDef
from atomc.domain_analyzer.type import Integer, Double, Character, Struct, Type, Void, get_returned_type_of_operation
from atomc.lexer.token import Code
from atomc.syntactic_analyzer.syntax_error_exception import SyntaxErrorException

# rule of thumb for the syntax analyzer:
# any rule function and also the consume function returns a tuple:
# - boolean: if the rule satisfied, token was consumed
# - iterator: the iterator at the new position in the list (after consuming all the tokens of that rule)
#             if the rule was not satisfied / token was not consumed, an iterator object with the initial state of the
#             main iterator is returned, so the iteration does not advance
# this code also implements domain analysis


# necessary for the global domain, which is not covered by functions in symbol.py
from atomc.type_analyzer.returned import Returned
from atomc.type_analyzer.type_analysis_exception import UndefinedIdException, UncallableIdException, NotLvalException, \
    TypeAnalysisException, InvalidTypeException

global_symbols = list()
global_variable_index = 0

# instantiation of the domain stack
domain_stack = DomainStack()


# used to find struct definition symbols when they need to be referenced for variable types
def find_struct_def_with_id(name, line=0):
    for symbol in global_symbols:
        if symbol.is_structured() and symbol.name_matches(name):
            return symbol

    raise NoStructDefErrorException(name, line)


def find_symbol_in_list(symbol_list, name, line=0):
    for symbol in global_symbols:
        if symbol.name_matches(name):
            return symbol

    raise UndefinedIdException(name, line)


# the domain stack always contains all the 'opened' domains, so the current one and its parent, up to the root
def find_symbol(name, line=0):
    # we must reverse the domain stack before iterating to start from the current domain
    for domain in domain_stack:
        symbol = domain.find_symbol_in_domain(name)
        if symbol:
            return symbol

    raise UndefinedIdException(name, line)


# used to set the index for global variables (local variables, struct members and parameters have this set up by their
# owner)
def set_global_variable_index(symbol: Variable):
    global global_variable_index
    symbol.set_index(global_variable_index)
    global_variable_index += symbol.get_symbol_type_size()


def get_current_line(token_iterator: iter):
    iterator_copy = copy.deepcopy(token_iterator)

    return next(iterator_copy).line


# for consuming terminal symbols/tokens from the grammar rules
def consume(token_iterator: iter, code: Code):
    # do not forget to deep copy the token_iterator, lest you will end up with an alias
    initial_iterator = copy.deepcopy(token_iterator)

    tk = next(token_iterator)
    if tk.code == code:
        if tk.value is not None:
            return token_iterator, True, tk.value, tk.line
        else:
            return token_iterator, True, None, tk.line

    return initial_iterator, False, None, None


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
    token_iterator, rule_result, symbol_id, symbol_line = consume(token_iterator, Code.ID)
    if rule_result:

        # check if symbol was defined
        # the call will raise an exception if the ID is not found
        # the symbol may be a variable or a function
        symbol = find_symbol(symbol_id, symbol_line)

        # LPAR?
        token_iterator, rule_result, _, _ = consume(token_iterator, Code.LPAR)
        if rule_result:

            # function call

            # check if symbol is function
            if not symbol.is_function():
                raise UncallableIdException(symbol, symbol_line)

            # get the param list of the function
            params = symbol.get_params()
            remaining_untreated_params = len(params)
            param_iterator = iter(params)

            # expr?
            current_line = get_current_line(token_iterator)
            token_iterator, rule_result, resulted_return = rule_expr(token_iterator)
            if rule_result:

                # got first parameter, check it
                remaining_untreated_params -= 1
                if remaining_untreated_params == -1:
                    raise TypeAnalysisException("too many arguments in function call", current_line)
                param = next(param_iterator)
                if not param.get_type().can_be_cast_to(resulted_return.get_type()):
                    raise InvalidTypeException("parameter incompatible with argument ", param.get_name(), current_line)

                # COMMA*
                while True:
                    token_iterator, rule_result, _, _ = consume(token_iterator, Code.COMMA)

                    if not rule_result:
                        break

                    # expr
                    current_line = get_current_line(token_iterator)
                    token_iterator, rule_result, resulted_return = rule_expr(token_iterator)
                    if not rule_result:
                        raise SyntaxErrorException(next(token_iterator), "missing function parameter after , "
                                                                         "in function call")

                    # got parameter, check it
                    remaining_untreated_params -= 1
                    if remaining_untreated_params == -1:
                        raise TypeAnalysisException("too many arguments in function call", current_line)
                    param = next(param_iterator)
                    if not param.get_type().can_be_cast_to(resulted_return.get_type()):

                        raise InvalidTypeException("parameter incompatible with function argument ", param.get_name(), current_line)

            if remaining_untreated_params > 0:
                raise TypeAnalysisException("too few arguments in function call", current_line)

            # RPAR
            token_iterator, rule_result, _, _ = consume(token_iterator, Code.RPAR)
            if rule_result:
                return token_iterator, True, Returned(symbol.get_type(), False, True)

            else:
                raise SyntaxErrorException(next(token_iterator),
                                           "missing ) after ( in function call")

        else:

            current_line = get_current_line(token_iterator)
            if symbol.is_structured():
                raise TypeAnalysisException("using struct type name" + symbol.get_name() + " as id", current_line)

            if symbol.is_function():
                raise TypeAnalysisException("symbol " + symbol.get_name() + "is a function and can only be calledS", current_line)

            return token_iterator, True, Returned(symbol.get_type(), True, not symbol.get_type().is_scalar())

    # CT_INT
    token_iterator = copy.deepcopy(fallback_iterator)
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.CT_INT)
    if rule_result:
        return token_iterator, True, Returned(Type(Integer(), -1), False, True)

    # CT_REAL
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.CT_REAL)
    if rule_result:
        return token_iterator, True, Returned(Type(Double(), -1), False, True)

    # CT_CHAR
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.CT_CHAR)
    if rule_result:
        return token_iterator, True, Returned(Type(Character(), -1), False, True)

    # CT_STRING
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.CT_STRING)
    if rule_result:
        return token_iterator, True, Returned(Type(Character(), 0), False, True)

    # LPAR
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.LPAR)
    if rule_result:

        # expr
        token_iterator, rule_result, resulted_return = rule_expr(token_iterator)
        if rule_result:

            # RPAR
            token_iterator, rule_result, _, _ = consume(token_iterator, Code.RPAR)
            if rule_result:
                return token_iterator, True, resulted_return

            else:
                raise SyntaxErrorException(next(token_iterator), "missing ) after (")

        else:
            # not an error, might be just a cast
            return fallback_iterator, False, None

    return fallback_iterator, False, None


# auxiliary grammar rule:
# exprPostfixAux: LBRACKET expr RBRACKET exprPostfixAux
# | DOT ID exprPostfixAux
# | e
def rule_expr_postfix_aux(token_iterator: iter, left_return):
    fallback_iterator = copy.deepcopy(token_iterator)

    # LBRACKET
    current_line = get_current_line(token_iterator)
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.LBRACKET)
    if rule_result:

        # only arrays can be indexed, check that the left expression is an array ID
        # even though we only know it's an ID so far, its type should have a bigger dimensionality
        if left_return.has_scalar_type():
            raise TypeAnalysisException("only an array can be indexed", current_line)

        # expr
        current_line = get_current_line(token_iterator)
        token_iterator, rule_result, resulted_return = rule_expr(token_iterator)
        if rule_result:

            # check if the index expression can be converted to int
            int_type = Type(Integer(), -1)
            resulted_type = resulted_return.get_type()
            if not resulted_type.can_be_cast_to(int_type):
                raise TypeAnalysisException("the index is not convertible to int", current_line)

            # RBRACKET
            token_iterator, rule_result, _, _ = consume(token_iterator, Code.RBRACKET)
            if rule_result:

                if left_return.get_type().get_base_name() == Struct.__name__:
                    combined_return_base_type = globals()[left_return.get_type().get_base_name()](
                        left_return.get_type().get_base().get_struct_definition())
                else:
                    combined_return_base_type = globals()[left_return.get_type().get_base_name()]()
                # an array entry is a scalar (that's why we have -1)
                combined_return = Returned(
                    Type(combined_return_base_type, -1),
                    True,
                    False
                )

                # exprPostfixAux
                token_iterator, rule_result, resulted_return = rule_expr_postfix_aux(token_iterator, combined_return)
                if rule_result:
                    return token_iterator, True, resulted_return

            else:
                raise SyntaxErrorException(next(token_iterator), "no ] in array variable in expression")

        else:
            raise SyntaxErrorException(next(token_iterator), "no array index after [ in expression")

    # DOT
    token_iterator = copy.deepcopy(fallback_iterator)
    current_line = get_current_line(token_iterator)
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.DOT)
    if rule_result:

        # dots may only come as selectors after structs, check if the left return comes from a struct
        if not left_return.get_type().get_base_name() == Struct.__name__:
            raise TypeAnalysisException("a field can only be selected from a struct", current_line)


        # ID
        current_line = get_current_line(token_iterator)
        token_iterator, rule_result, member_id, _ = consume(token_iterator, Code.ID)
        if rule_result:

            # check if the specified ID is a field inside the structure

            if not left_return.get_type().get_base().has_struct_member(member_id):
                raise TypeAnalysisException("the structure " + left_return.get_type().get_base().get_struct_definition().get_name() + " does not have a field " + member_id, current_line)

            member = left_return.get_type().get_base().get_struct_member(member_id)

            combined_return = Returned(member.get_type(), True, not member.get_type().is_scalar())
            # exprPostfixAux
            token_iterator, rule_result, resulted_return = rule_expr_postfix_aux(token_iterator, combined_return)
            if rule_result:
                return token_iterator, True, resulted_return

        else:
            raise SyntaxErrorException(next(token_iterator), "no field name after .")

    # e
    return fallback_iterator, True, left_return


# grammar rule:
# exprPostfix: exprPrimary exprPostfixAux
def rule_expr_postfix(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # exprPrimary
    token_iterator, rule_result, left_return = rule_expr_primary(token_iterator)
    if rule_result:

        # exprPostfixAux
        token_iterator, rule_result, resulted_return = rule_expr_postfix_aux(token_iterator, left_return)
        if rule_result:
            return token_iterator, True, resulted_return

    return fallback_iterator, False, None


# grammar rule:
# exprUnary: ( SUB | NOT ) exprUnary | exprPostfix
def rule_expr_unary(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # SUB
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.SUB)
    if rule_result:

        # exprUnary
        current_line = get_current_line(token_iterator)
        token_iterator, rule_result, resulted_return = rule_expr_unary(token_iterator)
        if rule_result:

            # check if the unary expression can be evaluated to a scalar type
            if not resulted_return.has_scalar_type():
                raise TypeAnalysisException("unary - must be followed by a scalar typed expression", current_line)

            return token_iterator, True, resulted_return

        else:
            raise SyntaxErrorException(next(token_iterator), "no unary expression after -")

    # NOT
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.NOT)
    if rule_result:

        # exprUnary
        current_line = get_current_line(token_iterator)
        token_iterator, rule_result, resulted_return = rule_expr_unary(token_iterator)
        if rule_result:

            # check if the unary expression can be evaluated to a scalar type
            if not resulted_return.has_scalar_type():
                raise TypeAnalysisException("unary ! must be followed by a scalar typed expression", current_line)

            return token_iterator, True, resulted_return

        else:
            raise SyntaxErrorException(next(token_iterator), "no unary expression after ! (not)")

    # exprPostfix
    token_iterator = copy.deepcopy(fallback_iterator)
    token_iterator, rule_result, resulted_return = rule_expr_postfix(token_iterator)
    if rule_result:
        return token_iterator, True, resulted_return

    return fallback_iterator, False, None


# grammar rule:
# exprCast: LPAR typeBase arrayDecl? RPAR exprCast | exprUnary
def rule_expr_cast(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # LPAR
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.LPAR)
    if rule_result:

        # typeBase
        token_iterator, rule_result, type_base = rule_type_base(token_iterator)
        if rule_result:

            # arrayDecl?
            token_iterator, rule_result, array_size = rule_array_decl(token_iterator)

            # RPAR
            token_iterator, rule_result, _, _ = consume(token_iterator, Code.RPAR)
            if rule_result:

                # create a type object for the cast operation
                if array_size is not None:
                    destination_type = Type(type_base, array_size) # pointer or array
                else:
                    destination_type = Type(type_base, -1)  # -1 so it knows it's a scalar (<0)

                # exprCast
                current_line = get_current_line(token_iterator)
                token_iterator, rule_result, resulted_return = rule_expr_cast(token_iterator)
                if rule_result:

                    current_type = resulted_return.get_type()
                    if destination_type.get_base_name() == Struct.__name__:
                        raise TypeAnalysisException("cannot convert to a struct type ", current_line)
                    if not current_type.can_be_cast_to(destination_type):
                        raise TypeAnalysisException("type ... cannot be cast to ...", current_line)

                    # build the returned object with the casted type
                    resulted_return = Returned(destination_type, False, True)

                    return token_iterator, True, resulted_return

                else:
                    raise SyntaxErrorException(next(token_iterator), "invalid expression after cast type")

            else:
                raise SyntaxErrorException(next(token_iterator), "no ) after type in cast")

        # cannot raise an exception here, there are other things after ( aside from cast types,
        # such as exprUnary

    # exprUnary
    token_iterator = copy.deepcopy(fallback_iterator)
    token_iterator, rule_result, resulted_return = rule_expr_unary(token_iterator)
    if rule_result:
        return token_iterator, True, resulted_return

    return fallback_iterator, False, None


# auxiliary grammar rule:
# exprMulAux: ( MUL | DIV ) exprCast exprMulAux | e
def rule_expr_mul_aux(token_iterator: iter, left_return):
    fallback_iterator = copy.deepcopy(token_iterator)

    # MUL
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.MUL)
    if rule_result:

        # exprCast
        current_line = get_current_line(token_iterator)
        token_iterator, rule_result, right_return = rule_expr_cast(token_iterator)
        if rule_result:

            # check if the two expressions can be *//'d
            type_of_result = get_returned_type_of_operation(left_return.get_type(), right_return.get_type())
            if not type_of_result:
                raise TypeAnalysisException("invalid operand type for *", current_line)

            # create a Return object based on the combination of the operation between the l/r expressions of the *//
            combined_return = Returned(type_of_result, False, True)

            # pass the combined object along to the next term

            # exprMulAux
            token_iterator, rule_result, resulted_return = rule_expr_mul_aux(token_iterator, combined_return)
            if rule_result:
                return token_iterator, True, resulted_return

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after *")

    # DIV
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.DIV)
    if rule_result:

        # exprCast
        token_iterator, rule_result, right_return = rule_expr_cast(token_iterator)
        if rule_result:

            # check if the two expressions can be *//'d
            current_line = get_current_line(token_iterator)
            type_of_result = get_returned_type_of_operation(left_return.get_type(), right_return.get_type())
            if not type_of_result:
                raise TypeAnalysisException("invalid operand type for /", current_line)

            # create a Return object based on the combination of the operation between the l/r expressions of the *//
            combined_return = Returned(type_of_result, False, True)

            # pass the combined object along to the next term

            # exprMulAux
            token_iterator, rule_result, resulted_return = rule_expr_mul_aux(token_iterator, combined_return)
            if rule_result:
                return token_iterator, True, resulted_return

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after /")

    # e
    return fallback_iterator, True, left_return


# grammar rule:
# exprMul: exprCast exprMulAux
def rule_expr_mul(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # exprCast
    token_iterator, rule_result, left_return = rule_expr_cast(token_iterator)
    if rule_result:

        # exprMulAux
        token_iterator, rule_result, resulted_return = rule_expr_mul_aux(token_iterator, left_return)
        if rule_result:
            return token_iterator, True, resulted_return

    return fallback_iterator, False, None


# auxiliary grammar rule:
# exprAddAux: ( ADD | SUB ) exprMul exprAddAux | e
def rule_expr_add_aux(token_iterator: iter, left_return):
    fallback_iterator = copy.deepcopy(token_iterator)

    # ADD
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.ADD)
    if rule_result:

        # exprMul
        token_iterator, rule_result, right_return = rule_expr_mul(token_iterator)
        if rule_result:

            # check if the two expressions can be +/-'d
            current_line = get_current_line(token_iterator)
            type_of_result = get_returned_type_of_operation(left_return.get_type(), right_return.get_type())
            if not type_of_result:
                raise TypeAnalysisException("invalid operand type for +", current_line)

            # create a Return object based on the combination of the operation between the l/r expressions of the +/-
            combined_return = Returned(type_of_result, False, True)

            # pass the combined object along to the next term

            # exprAddAux
            token_iterator, rule_result, resulted_return = rule_expr_add_aux(token_iterator, combined_return)
            if rule_result:
                return token_iterator, True, resulted_return

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after +")

    # SUB
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.SUB)
    if rule_result:

        # exprMul
        token_iterator, rule_result, right_return = rule_expr_mul(token_iterator)
        if rule_result:

            # check if the two expressions can be +/-'d
            current_line = get_current_line(token_iterator)
            type_of_result = get_returned_type_of_operation(left_return.get_type(), right_return.get_type())
            if not type_of_result:
                raise TypeAnalysisException("invalid operand type for -", current_line)

            # create a Return object based on the combination of the operation between the l/r expressions of the +/-
            combined_return = Returned(type_of_result, False, True)

            # pass the combined object along to the next term

            # exprAddAux
            token_iterator, rule_result, resulted_return = rule_expr_add_aux(token_iterator, combined_return)
            if rule_result:
                return token_iterator, True, resulted_return

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after -")

    # e
    return fallback_iterator, True, left_return


# grammar rule:
# exprAdd: exprMul exprAddAux
def rule_expr_add(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # exprMul
    token_iterator, rule_result, left_return = rule_expr_mul(token_iterator)
    if rule_result:

        # exprAddAux
        token_iterator, rule_result, resulted_return = rule_expr_add_aux(token_iterator, left_return)
        if rule_result:
            return token_iterator, True, resulted_return

    return fallback_iterator, False, None


# auxiliary grammar rule:
# exprRelAux: ( LESS | LESSEQ | GREATER | GREATEREQ ) exprAdd exprRelAux | e
def rule_expr_rel_aux(token_iterator: iter, left_return):
    fallback_iterator = copy.deepcopy(token_iterator)

    # LESS
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.LESS)
    if rule_result:

        # exprAdd
        token_iterator, rule_result, right_return = rule_expr_add(token_iterator)
        if rule_result:

            # check if the two expressions can be </>/<=/>='d
            current_line = get_current_line(token_iterator)
            type_of_result = get_returned_type_of_operation(left_return.get_type(), right_return.get_type())
            if not type_of_result:
                raise TypeAnalysisException("invalid operand type for <", current_line)

            # create a Return object based on the combination of the operation between the l/r expressions of the </>..
            combined_return = Returned(type_of_result, False, True)

            # pass the combined object along to the next term

            # exprRelAux
            token_iterator, rule_result, resulted_return = rule_expr_rel_aux(token_iterator, combined_return)
            if rule_result:
                return token_iterator, True, resulted_return

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after <")

    # LESSEQ
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.LESSEQ)
    if rule_result:

        # exprAdd
        token_iterator, rule_result, right_return = rule_expr_add(token_iterator)
        if rule_result:

            # check if the two expressions can be </>/<=/>='d
            current_line = get_current_line(token_iterator)
            type_of_result = get_returned_type_of_operation(left_return.get_type(), right_return.get_type())
            if not type_of_result:
                raise TypeAnalysisException("invalid operand type for <=", current_line)

            # create a Return object based on the combination of the operation between the l/r expressions of the </>..
            combined_return = Returned(type_of_result, False, True)

            # pass the combined object along to the next term

            # exprRelAux
            token_iterator, rule_result, resulted_return = rule_expr_rel_aux(token_iterator, combined_return)
            if rule_result:
                return token_iterator, True, resulted_return

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after <=")

    # GREATER
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.GREATER)
    if rule_result:

        # exprAdd
        token_iterator, rule_result, right_return = rule_expr_add(token_iterator)
        if rule_result:

            # check if the two expressions can be </>/<=/>='d
            current_line = get_current_line(token_iterator)
            type_of_result = get_returned_type_of_operation(left_return.get_type(), right_return.get_type())
            if not type_of_result:
                raise TypeAnalysisException("invalid operand type for >", current_line)

            # create a Return object based on the combination of the operation between the l/r expressions of the </>..
            combined_return = Returned(type_of_result, False, True)

            # pass the combined object along to the next term

            # exprRelAux
            token_iterator, rule_result, resulted_return = rule_expr_rel_aux(token_iterator, combined_return)
            if rule_result:
                return token_iterator, True, resulted_return

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after >")

    # GREATEREQ
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.GREATEREQ)
    if rule_result:

        # exprAdd
        token_iterator, rule_result, right_return = rule_expr_add(token_iterator)
        if rule_result:

            # check if the two expressions can be </>/<=/>='d
            current_line = get_current_line(token_iterator)
            type_of_result = get_returned_type_of_operation(left_return.get_type(), right_return.get_type())
            if not type_of_result:
                raise TypeAnalysisException("invalid operand type for >=", current_line)

            # create a Return object based on the combination of the operation between the l/r expressions of the </>..
            combined_return = Returned(type_of_result, False, True)

            # pass the combined object along to the next term

            # exprRelAux
            token_iterator, rule_result, resulted_return = rule_expr_rel_aux(token_iterator, combined_return)
            if rule_result:
                return token_iterator, True, resulted_return

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after >=")

    # e
    return fallback_iterator, True, left_return


# grammar rule:
# exprRel: exprAdd exprRelAux
def rule_expr_rel(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # exprAdd
    token_iterator, rule_result, left_return = rule_expr_add(token_iterator)
    if rule_result:

        # exprRelAux
        token_iterator, rule_result, resulted_return = rule_expr_rel_aux(token_iterator, left_return)
        if rule_result:
            return token_iterator, True, resulted_return

    return fallback_iterator, False, None


# auxiliary grammar rule:
# exprEqAux: ( EQUAL | NOTEQ ) exprRel exprEqAux | e
def rule_expr_eq_aux(token_iterator: iter, left_return):
    fallback_iterator = copy.deepcopy(token_iterator)

    # EQUAL
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.EQUAL)
    if rule_result:

        # exprRel
        token_iterator, rule_result, right_return = rule_expr_rel(token_iterator)
        if rule_result:

            # check if the two expressions can be ==/!='d
            current_line = get_current_line(token_iterator)
            type_of_result = get_returned_type_of_operation(left_return.get_type(), right_return.get_type())
            if not type_of_result:
                raise TypeAnalysisException("invalid operand type for ==", current_line)

            # create a Return object based on the combination of the operation between the l/r expressions of the ==/!=
            combined_return = Returned(type_of_result, False, True)

            # pass the combined object along to the next ==/!= term

            # exprEqAux
            token_iterator, rule_result, resulted_return = rule_expr_eq_aux(token_iterator, combined_return)
            if rule_result:
                return token_iterator, True, resulted_return

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after ==")

    # NOTEQ
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.NOTEQ)
    if rule_result:

        # exprRel
        token_iterator, rule_result, right_return = rule_expr_rel(token_iterator)
        if rule_result:

            # check if the two expressions can be ==/!='d
            current_line = get_current_line(token_iterator)
            type_of_result = get_returned_type_of_operation(left_return.get_type(), right_return.get_type())
            if not type_of_result:
                raise TypeAnalysisException("invalid operand type for !=", current_line)

            # create a Return object based on the combination of the operation between the l/r expressions of the ==/!=
            combined_return = Returned(type_of_result, False, True)

            # pass the combined object along to the next ==/!= term

            # exprEqAux
            token_iterator, rule_result, resulted_return = rule_expr_eq_aux(token_iterator, combined_return)
            if rule_result:
                return token_iterator, True, resulted_return

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after !=")

    # e
    return fallback_iterator, True, left_return


# grammar rule:
# exprEq: exprRel exprEqAux
def rule_expr_eq(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # exprRel
    token_iterator, rule_result, left_return = rule_expr_rel(token_iterator)
    if rule_result:

        # exprEqAux
        token_iterator, rule_result, resulted_return = rule_expr_eq_aux(token_iterator, left_return)
        if rule_result:
            return token_iterator, True, resulted_return

    return fallback_iterator, False, None


# auxiliary grammar rule:
# exprAndAux: AND exprEq exprAndAux | e
def rule_expr_and_aux(token_iterator: iter, left_return):
    fallback_iterator = copy.deepcopy(token_iterator)

    # AND
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.AND)
    if rule_result:

        # exprEq
        token_iterator, rule_result, right_return = rule_expr_eq(token_iterator)
        if rule_result:

            # check if the two expressions can be AND'd
            current_line = get_current_line(token_iterator)
            type_of_result = get_returned_type_of_operation(left_return.get_type(), right_return.get_type())
            if not type_of_result:
                raise TypeAnalysisException("invalid operand type for &&", current_line)

            # create a Return object based on the combination of the operation between the l/r expressions of the &&
            combined_return = Returned(type_of_result, False, True)

            # pass the combined object along to the next && term

            # exprAndAux
            token_iterator, rule_result, resulted_return = rule_expr_and_aux(token_iterator, combined_return)
            if rule_result:
                return token_iterator, True, resulted_return

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after &&")

    # e
    return fallback_iterator, True, left_return


# grammar rule:
# exprAnd: exprEq exprAndAux
def rule_expr_and(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # exprEq
    token_iterator, rule_result, left_return = rule_expr_eq(token_iterator)
    if rule_result:

        # exprAndAux
        token_iterator, rule_result, resulted_return = rule_expr_and_aux(token_iterator, left_return)
        if rule_result:
            return token_iterator, True, resulted_return

    return fallback_iterator, False, None


# auxiliary grammar rule:
# exprOrAux: OR exprAnd exprOrAux | e
def rule_expr_or_aux(token_iterator: iter, left_return):
    fallback_iterator = copy.deepcopy(token_iterator)

    # OR
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.OR)
    if rule_result:

        # exprAnd
        token_iterator, rule_result, right_return = rule_expr_and(token_iterator)
        if rule_result:

            # check if the two expressions can be OR'd
            current_line = get_current_line(token_iterator)
            type_of_result = get_returned_type_of_operation(left_return, right_return)
            if not type_of_result:
                raise TypeAnalysisException("invalid operand type for ||", current_line)

            # create a Return object based on the combination of the operation between the l/r expressions of the ||
            combined_return = Returned(type_of_result, False, True)

            # pass the combined object along to the next || term
            # exprOrAux
            token_iterator, rule_result, resulted_return = rule_expr_or_aux(token_iterator, combined_return)
            if rule_result:
                return token_iterator, True, resulted_return

        else:
            raise SyntaxErrorException(next(token_iterator), "invalid expression after ||")

    # e
    return fallback_iterator, True, left_return


# grammar rule:
# exprOr: exprAnd exprOrAux
def rule_expr_or(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # exprAnd
    token_iterator, rule_result, left_return = rule_expr_and(token_iterator)
    if rule_result:

        # exprOrAux
        token_iterator, rule_result, resulted_return = rule_expr_or_aux(token_iterator, left_return)
        if rule_result:
            return token_iterator, True, resulted_return

    return fallback_iterator, False, None


# grammar rule:
# exprAssign: exprUnary ASSIGN exprAssign | exprOr
def rule_expr_assign(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # exprUnary
    token_iterator, rule_result, lval = rule_expr_unary(token_iterator)
    if rule_result:

        # aici e problema, porneste de la branch-urile astea care se suprapun
        # solutie posibila: muti verificarile semantice mai jos, dupa ce stii ca e asign?

        # ASSIGN
        current_line = get_current_line(token_iterator)
        token_iterator, rule_result, _, _ = consume(token_iterator, Code.ASSIGN)
        if rule_result:

            # check if the left-hand expression is valid
            # work on exceptions
            if not lval.is_lval():
                raise TypeAnalysisException("the assign destination must be a left-value", current_line)

            if lval.is_constant():
                raise TypeAnalysisException("the assign destination cannot be a constant", current_line)

            if not lval.has_scalar_type():
                raise TypeAnalysisException("the assign destination must have a scalar type", current_line)

            # exprAssign
            current_line = get_current_line(token_iterator)
            token_iterator, rule_result, rval = rule_expr_assign(token_iterator)
            if rule_result:

                # check if the right-hand expression is valid
                if not rval.has_scalar_type():
                    raise TypeAnalysisException("the assign source must have a scalar type", current_line)

                if not rval.is_compatible_with(lval):
                    raise TypeAnalysisException("the assign source cannot be converted to destination", current_line)

                return_value = Returned(lval.get_type(), False, True)

                return token_iterator, True, return_value

            else:
                # return fallback_iterator, False
                raise SyntaxErrorException(next(token_iterator),
                                           "invalid expression after =")

            # exprOr can be reduced to an unary expression, so every exprOr will be considered assignation unless
            # you let both the branches check

    # exprOr
    token_iterator = copy.deepcopy(fallback_iterator)
    token_iterator, rule_result, return_value = rule_expr_or(token_iterator)
    if rule_result:
        return token_iterator, True, return_value

    return fallback_iterator, False, None


# grammar rule:
# expr: exprAssign
def rule_expr(token_iterator: list):

    # exprAssign
    token_iterator, rule_result, resulted_return = rule_expr_assign(token_iterator)
    if rule_result:
        return token_iterator, True, resulted_return

    return token_iterator, False, None


# grammar rule:
# stmCompound: LACC ( varDef | stm )* RACC
#
# for domain analysis:
# stmCompound[in bool new_domain]: LACC ( varDef | stm )* RACC
def rule_stm_compound(token_iterator: iter, owner=None, new_domain=False):
    fallback_iterator = copy.deepcopy(token_iterator)

    # LACC
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.LACC)
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
        token_iterator, rule_result, _, _ = consume(token_iterator, Code.RACC)
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
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.IF)
    if rule_result:

        # LPAR
        token_iterator, rule_result, _, _ = consume(token_iterator, Code.LPAR)
        if rule_result:

            # expr
            current_line = get_current_line(token_iterator)
            token_iterator, rule_result, if_condition = rule_expr(token_iterator)
            if rule_result:

                # check if the IF evaluates evaluated to a scalar type
                if not if_condition.has_scalar_type():
                    raise TypeAnalysisException("the if condition must evaluate to a scalar type", current_line)

                # RPAR
                token_iterator, rule_result, _, _ = consume(token_iterator, Code.RPAR)
                if rule_result:

                    # stm
                    token_iterator, rule_result = rule_stm(token_iterator, owner)
                    if rule_result:

                        # ELSE?
                        token_iterator, rule_result, _, _ = consume(token_iterator, Code.ELSE)
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
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.WHILE)
    if rule_result:

        # LPAR
        token_iterator, rule_result, _, _ = consume(token_iterator, Code.LPAR)
        if rule_result:

            # expr
            current_line = get_current_line(token_iterator)
            token_iterator, rule_result, while_condition = rule_expr(token_iterator)
            if rule_result:

                # check if the WHILE condition evaluates to a scalar type
                if not while_condition.has_scalar_type():
                    raise TypeAnalysisException("the while condition must evaluate to a scalar type", current_line)

                # RPAR
                token_iterator, rule_result, _, _ = consume(token_iterator, Code.RPAR)
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
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.FOR)
    if rule_result:

        # LPAR
        token_iterator, rule_result, _, _ = consume(token_iterator, Code.LPAR)
        if rule_result:

            # expr?
            token_iterator, _, _ = rule_expr(token_iterator)

            # SEMICOLON
            token_iterator, rule_result, _, _ = consume(token_iterator, Code.SEMICOLON)
            if rule_result:

                # expr?
                current_line = get_current_line(token_iterator)
                token_iterator, rule_result, for_condition = rule_expr(token_iterator)

                # check if the FOR condition evaluates to a scalar type
                if not for_condition.has_scalar_type():
                    raise TypeAnalysisException("the for condition must evaluate to a scalar type", current_line)

                # SEMICOLON
                token_iterator, rule_result, _, _ = consume(token_iterator, Code.SEMICOLON)
                if rule_result:

                    # expr?
                    token_iterator, _ = rule_expr(token_iterator)

                    # RPAR
                    token_iterator, rule_result, _, _ = consume(token_iterator, Code.RPAR)
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
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.BREAK)
    if rule_result:

        # SEMICOLON
        token_iterator, rule_result, _, _ = consume(token_iterator, Code.SEMICOLON)
        if rule_result:

            return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "no ; after break")

    # RETURN
    token_iterator = copy.deepcopy(fallback_iterator)
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.RETURN)
    if rule_result:

        # expr?
        current_line = get_current_line(token_iterator)
        token_iterator, rule_result, return_expression = rule_expr(token_iterator)
        if rule_result:

            # check if the function type is not void
            if not owner.can_return_value():
                raise TypeAnalysisException("a void function cannot return a value", current_line)

            # check if the expression can be evaluated to the returned type of the function
            if not return_expression.get_type().can_be_cast_to(owner.get_type()):
                raise TypeAnalysisException("cannot convert the return expression type to the function return type", current_line)

        else:

            if owner.can_return_value():
                raise TypeAnalysisException("a non-void function must return a value", current_line)

        # SEMICOLON
        token_iterator, rule_result, _, _ = consume(token_iterator, Code.SEMICOLON)
        if rule_result:

            return token_iterator, True

        else:
            raise SyntaxErrorException(next(token_iterator), "no ; after return")

    # expr?
    token_iterator = copy.deepcopy(fallback_iterator)
    token_iterator, _, _ = rule_expr(token_iterator)

    # SEMICOLON
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.SEMICOLON)
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
        token_iterator, rule_result, param_id, param_id_line = consume(token_iterator, Code.ID)
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
            # param id line is the line where the parameter id is found, used for error messages
            domain_stack.add_symbol_to_current_domain(new_param, param_id_line)
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
        token_iterator, rule_result, function_id, function_id_line = consume(token_iterator, Code.ID)
        if rule_result:

            # create new symbol for the new function and add it to the current domain
            # (will also check if the name of the function is unique)
            new_function_type = Type(type_base, -1)  # will never be a pointer or an array
            new_function = Function(function_id, new_function_type)

            # LPAR
            token_iterator, rule_result, _, _ = consume(token_iterator, Code.LPAR)
            if rule_result:

                # adding function definition to the symbol list
                global_symbols.append(new_function)
                # function id line is the line where the function id is found, used for error messages
                domain_stack.add_symbol_to_current_domain(new_function, function_id_line)

                # create new domain for the function and switch to it
                domain_stack.push_domain()

                # ( fnParam ( COMMA fnParam )* )?

                # fnParam
                token_iterator, rule_result, new_function_param = rule_fn_param(token_iterator, new_function)
                if rule_result:

                    new_function.add_function_parameter(new_function_param)

                    while True:

                        # COMMA
                        token_iterator, rule_result, _, _ = consume(token_iterator, Code.COMMA)
                        if rule_result:

                            # fnParam
                            token_iterator, rule_result, new_function_param = rule_fn_param(token_iterator,
                                                                                            new_function)
                            if not rule_result:
                                raise SyntaxErrorException(next(token_iterator),
                                                           "no function parameter after comma")
                            else:
                                new_function.add_function_parameter(new_function_param)

                        else:
                            break

                # RPAR
                token_iterator, rule_result, _, _ = consume(token_iterator, Code.RPAR)
                if rule_result:

                    # stmCompound
                    token_iterator, rule_result = rule_stm_compound(token_iterator, new_function, False)
                    if rule_result:

                        # go back to global domain
                        domain_stack.pop_domain()

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
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.VOID)
    if rule_result:

        # ID
        token_iterator, rule_result, function_id, function_id_line = consume(token_iterator, Code.ID)
        if rule_result:

            # create new symbol for the new function and add it to the current domain
            # (will also check if the name of the function is unique)
            new_function_type = Type(Void(), -1)  # will never be a pointer or an array
            new_function = Function(function_id, new_function_type)

            # LPAR
            token_iterator, rule_result, _, _ = consume(token_iterator, Code.LPAR)
            if rule_result:

                # adding function definition to the symbol list
                global_symbols.append(new_function)
                # function id line is the line where the function id is found, used for error messages
                domain_stack.add_symbol_to_current_domain(new_function, function_id_line)

                # create new domain for the function and switch to it
                domain_stack.push_domain()

                # ( fnParam ( COMMA fnParam )* )?

                # fnParam
                token_iterator, rule_result, new_function_param = rule_fn_param(token_iterator, new_function)
                if rule_result:

                    new_function.add_function_parameter(new_function_param)

                    while True:

                        # COMMA
                        token_iterator, rule_result, _, _ = consume(token_iterator, Code.COMMA)
                        if rule_result:

                            # fnParam
                            token_iterator, rule_result, new_function_param = rule_fn_param(token_iterator)
                            if not rule_result:
                                raise SyntaxErrorException(next(token_iterator),
                                                           "no function parameter after comma")
                            else:
                                new_function.add_function_parameter(new_function_param)

                        else:
                            break

                # RPAR
                token_iterator, rule_result, _, _ = consume(token_iterator, Code.RPAR)
                if rule_result:

                    # stmCompound
                    token_iterator, rule_result = rule_stm_compound(token_iterator, new_function, False)
                    if rule_result:

                        # go back to global domain
                        domain_stack.pop_domain()

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
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.LBRACKET)
    if rule_result:

        # CT_INT? (was expr? before)
        token_iterator, rule_result, array_size, _ = consume(token_iterator, Code.CT_INT)
        if not rule_result:
            array_size = 0

        # RBRACKET
        token_iterator, rule_result, _, _ = consume(token_iterator, Code.RBRACKET)
        if rule_result:

            return token_iterator, True, array_size

        else:
            raise SyntaxErrorException(next(token_iterator), "no ] after [ in array declaration")

    # last returned value array size
    return fallback_iterator, False, None


# grammar rule:
# typeBase: INT | DOUBLE | CHAR | STRUCT ID
def rule_type_base(token_iterator: iter):
    fallback_iterator = copy.deepcopy(token_iterator)

    # INT
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.INT)
    if rule_result:
        return token_iterator, True, Integer()

    # DOUBLE
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.DOUBLE)
    if rule_result:
        return token_iterator, True, Double()

    # CHAR
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.CHAR)
    if rule_result:
        return token_iterator, True, Character()

    # STRUCT
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.STRUCT)
    if rule_result:

        # ID
        token_iterator, rule_result, struct_id, struct_id_line = consume(token_iterator, Code.ID)
        if rule_result:

            # if the base type is a struct type, check that it is defined
            # find_struct_def_with_id() does this for us

            struct_def = find_struct_def_with_id(struct_id, struct_id_line)
            return token_iterator, True, Struct(struct_def)

        else:
            raise SyntaxErrorException(next(token_iterator), "no { in struct type definition or no ID after struct")

    # last returned ref returned type base
    return fallback_iterator, False, None


# grammar rule:
# varDef: typeBase ID arrayDecl? SEMICOLON
def rule_var_def(token_iterator: iter, owner=None):
    fallback_iterator = copy.deepcopy(token_iterator)

    # typeBase
    token_iterator, rule_result, type_base = rule_type_base(token_iterator)
    if rule_result:

        # ID
        token_iterator, rule_result, variable_id, variable_id_line = consume(token_iterator, Code.ID)
        if rule_result:

            # arrayDecl?
            token_iterator, rule_result, array_size = rule_array_decl(token_iterator)

            # SEMICOLON
            token_iterator, rule_result, _, _ = consume(token_iterator, Code.SEMICOLON)
            if rule_result:

                # create a type for the new variable and create a new symbol object
                # array variables must have a size defined. check for that if the array declaration is present
                if array_size is not None:
                    if array_size > 0:
                        new_variable_type = Type(type_base, array_size)
                    else:  # array_size == 0 -> pointer, not permitted
                        # var id line is the line where the var id is found, used for error messages
                        raise InvalidArraySizeErrorException(variable_id, variable_id_line)
                else:
                    new_variable_type = Type(type_base, -1)  # -1 so it knows it's a variable (<0)

                new_variable = Variable(variable_id, new_variable_type, owner)

                # add the symbol to the current domain (will check if name is unique)
                # and add it to the list of variables of its owner
                # var id line is the line where the var id is found, used for error messages
                domain_stack.add_symbol_to_current_domain(new_variable, variable_id_line)

                if owner is None:
                    global_symbols.append(new_variable)
                    set_global_variable_index(new_variable)
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
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.STRUCT)
    if rule_result:

        # ID
        token_iterator, rule_result, struct_type_id, new_struct_type_id_line = consume(token_iterator, Code.ID)
        if rule_result:

            # LACC
            token_iterator, rule_result, _, _ = consume(token_iterator, Code.LACC)
            if rule_result:

                # create new struct definition symbol
                new_struct_def = StructDef(struct_type_id)

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
                token_iterator, rule_result, _, _ = consume(token_iterator, Code.RACC)
                if rule_result:

                    # SEMICOLON
                    token_iterator, rule_result, _, _ = consume(token_iterator, Code.SEMICOLON)
                    if rule_result:

                        # close struct domain and go back to the global domain
                        domain_stack.pop_domain()

                        # add the struct definition to the global domain (also checks that name is unique)
                        # and append the symbol to the global symbols list
                        # new struct def name line is the line where the struct name is found, used for error messages
                        domain_stack.add_symbol_to_current_domain(new_struct_def, new_struct_type_id_line)
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
    token_iterator, rule_result, _, _ = consume(token_iterator, Code.END)
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

    return global_symbols
