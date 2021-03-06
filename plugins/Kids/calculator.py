# fourFn.py
#
# Demonstration of the pyparsing module, implementing a simple 4-function expression parser,
# with support for scientific notation, and symbols for e and pi.
# Extended to add exponentiation and simple built-in functions.
# Extended test cases, simplified pushFirst method.
#
# Copyright 2003-2006 by Paul McGuire
#
from pyparsing import Literal,CaselessLiteral,Word,Combine,Group,Optional,\
    oneOf,OneOrMore,ZeroOrMore,Forward,nums,alphas
import math
import sys
import operator

exprStack = []

def pushFirst( strg, loc, toks ):
    exprStack.append( toks[0] )
def pushUMinus( strg, loc, toks ):
    if toks and toks[0]=='-':
        exprStack.append( 'unary -' )
        #~ exprStack.append( '-1' )
        #~ exprStack.append( '*' )

bnf = None
def BNF():
    """
    expop   :: '^'
    multop  :: '*' | '/' | '>>' | '<<' | '|' | '&'
    addop   :: '+' | '-'
    hex     :: '0x' + integer
    integer :: ['+' | '-'] '0'..'9'+
    atom    :: PI | E | real | fn '(' expr ')' | '(' expr ')'
    factor  :: atom [ expop factor ]*
    term    :: factor [ multop factor ]*
    expr    :: term [ addop term ]*
    """
    global bnf

    if not bnf:
        point = Literal( "." )
        e     = CaselessLiteral( "E" )
        hexnum = CaselessLiteral("0x") + OneOrMore(oneOf(nums + 'a b c d e f A B C D E F'))
        hexnum.setParseAction(lambda s,l,t:str(int(''.join(t),16)))
        fnumber = Combine( Word( "+-"+nums, nums ) +
                           Optional( point + Optional( Word( nums ) ) ) +
                           Optional( e + Word( "+-"+nums, nums ) ) )
        ident = Word(alphas, alphas+nums+"_$")

        plus  = Literal( "+" )
        minus = Literal( "-" )
        mult  = Literal( "*" )
        div   = Literal( "/" )
        lshift  = Literal( "<<" )
        rshift  = Literal( ">>" )
        or_  = Literal( "|" )
        and_  = Literal( "&" )
        lpar  = Literal( "(" ).suppress()
        rpar  = Literal( ")" ).suppress()
        addop  = plus | minus
        multop = mult | div | lshift | rshift | or_ | and_
        expop = Literal( "^" )
        pi    = CaselessLiteral( "PI" )

        expr = Forward()
        atom = (Optional("-") + ( pi | e | hexnum | fnumber | ident + lpar + expr + rpar ).setParseAction( pushFirst ) | ( lpar + expr.suppress() + rpar )).setParseAction(pushUMinus)

        # by defining exponentiation as "atom [ ^ factor ]..." instead of "atom [ ^ atom ]...", we get right-to-left exponents, instead of left-to-righ
        # that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = Forward()
        factor << atom + ZeroOrMore( ( expop + factor ).setParseAction( pushFirst ) )

        term = factor + ZeroOrMore( ( multop + factor ).setParseAction( pushFirst ) )
        expr << term + ZeroOrMore( ( addop + term ).setParseAction( pushFirst ) )
        bnf = expr
    return bnf

# map operator symbols to corresponding arithmetic operations
epsilon = 1e-12
opn = { "+" : operator.add,
        "-" : operator.sub,
        "*" : operator.mul,
        "/" : operator.truediv,
        ">>" : lambda x,y: operator.rshift(int(x),int(y)),
        "<<" : lambda x,y: operator.lshift(int(x),int(y)),
        "|" : lambda x,y: operator.or_(int(x),int(y)),
        "&" : lambda x,y: operator.and_(int(x),int(y)),
        "^" : operator.pow }
fn  = { "sin" : math.sin,
        "cos" : math.cos,
        "tan" : math.tan,
        "abs" : abs,
        "trunc" : lambda a: int(a),
        "round" : round,
        "sgn" : lambda a: abs(a)>epsilon and cmp(a,0) or 0}
def evaluateStack( s ):
    op = s.pop()
    if op == 'unary -':
        return -evaluateStack( s )
    if op in "+-*/^<<>>|&":
        op2 = evaluateStack( s )
        op1 = evaluateStack( s )
        return opn[op]( op1, op2 )
    elif op == "PI":
        return math.pi # 3.1415926535
    elif op == "E":
        return math.e  # 2.718281828
    elif op in fn:
        return fn[op]( evaluateStack( s ) )
    elif op[0].isalpha():
        return 0
    else:
        return float( op )

def parse_and_calc( s ):
    """
    >>> parse_and_calc("(405-396)*3")
    27.0
    """
    global exprStack
    exprStack = []
    results = BNF().parseString( s )
    return evaluateStack( exprStack[:] )

if __name__ == "__main__":

    def test( s, expVal ):
        global exprStack
        exprStack = []
        results = BNF().parseString( s )
        val = evaluateStack( exprStack[:] )
        if val == expVal:
            print s, "=", val, results, "=>", exprStack
        else:
            print s+"!!!", val, "!=", expVal, results, "=>", exprStack

    test( "9", 9 )
    test( "-9", -9 )
    test( "--9", 9 )
    test( "-E", -math.e )
    test( "9 + 3 + 6", 9 + 3 + 6 )
    test( "9 + 3 / 11", 9 + 3.0 / 11 )
    test( "(9 + 3)", (9 + 3) )
    test( "(9+3) / 11", (9+3.0) / 11 )
    test( "9 - 12 - 6", 9 - 12 - 6 )
    test( "9 - (12 - 6)", 9 - (12 - 6) )
    test( "2*3.14159", 2*3.14159 )
    test( "3.1415926535*3.1415926535 / 10", 3.1415926535*3.1415926535 / 10 )
    test( "PI * PI / 10", math.pi * math.pi / 10 )
    test( "PI*PI/10", math.pi*math.pi/10 )
    test( "PI^2", math.pi**2 )
    test( "round(PI^2)", round(math.pi**2) )
    test( "6.02E23 * 8.048", 6.02E23 * 8.048 )
    test( "e / 3", math.e / 3 )
    test( "sin(PI/2)", math.sin(math.pi/2) )
    test( "trunc(E)", int(math.e) )
    test( "trunc(-E)", int(-math.e) )
    test( "round(E)", round(math.e) )
    test( "round(-E)", round(-math.e) )
    test( "E^PI", math.e**math.pi )
    test( "2^3^2", 2**3**2 )
    test( "2^3+2", 2**3+2 )
    test( "2^9", 2**9 )
    test( "sgn(-2)", -1 )
    test( "sgn(0)", 0 )
    test( "sgn(0.1)", 1 )
    test( "8>>2", 2 )
    test( "8<<2", 32 )
    test( "8|2", 10 )
    test( "8&2", 0 )
    test( "4 + 0xb", 15 )
    test( "4 + 0xb4", 184 )
    import doctest
    doctest.testmod()


"""
Test output:
>pythonw -u fourFn.py
9 = 9.0 ['9'] => ['9']
9 + 3 + 6 = 18.0 ['9', '+', '3', '+', '6'] => ['9', '3', '+', '6', '+']
9 + 3 / 11 = 9.27272727273 ['9', '+', '3', '/', '11'] => ['9', '3', '11', '/', '+']
(9 + 3) = 12.0 [] => ['9', '3', '+']
(9+3) / 11 = 1.09090909091 ['/', '11'] => ['9', '3', '+', '11', '/']
9 - 12 - 6 = -9.0 ['9', '-', '12', '-', '6'] => ['9', '12', '-', '6', '-']
9 - (12 - 6) = 3.0 ['9', '-'] => ['9', '12', '6', '-', '-']
2*3.14159 = 6.28318 ['2', '*', '3.14159'] => ['2', '3.14159', '*']
3.1415926535*3.1415926535 / 10 = 0.986960440053 ['3.1415926535', '*', '3.1415926535', '/', '10'] => ['3.1415926535', '3.1415926535', '*', '10', '/']
PI * PI / 10 = 0.986960440109 ['PI', '*', 'PI', '/', '10'] => ['PI', 'PI', '*', '10', '/']
PI*PI/10 = 0.986960440109 ['PI', '*', 'PI', '/', '10'] => ['PI', 'PI', '*', '10', '/']
PI^2 = 9.86960440109 ['PI', '^', '2'] => ['PI', '2', '^']
6.02E23 * 8.048 = 4.844896e+024 ['6.02E23', '*', '8.048'] => ['6.02E23', '8.048', '*']
e / 3 = 0.90609394282 ['E', '/', '3'] => ['E', '3', '/']
sin(PI/2) = 1.0 ['sin', 'PI', '/', '2'] => ['PI', '2', '/', 'sin']
trunc(E) = 2 ['trunc', 'E'] => ['E', 'trunc']
E^PI = 23.1406926328 ['E', '^', 'PI'] => ['E', 'PI', '^']
2^3^2 = 512.0 ['2', '^', '3', '^', '2'] => ['2', '3', '2', '^', '^']
2^3+2 = 10.0 ['2', '^', '3', '+', '2'] => ['2', '3', '^', '2', '+']
2^9 = 512.0 ['2', '^', '9'] => ['2', '9', '^']
sgn(-2) = -1 ['sgn', '-2'] => ['-2', 'sgn']
sgn(0) = 0 ['sgn', '0'] => ['0', 'sgn']
sgn(0.1) = 1 ['sgn', '0.1'] => ['0.1', 'sgn']
>Exit code: 0
"""

