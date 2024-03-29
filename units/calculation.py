
import operator

from pyparsing import Forward, Group, Literal, nums, Suppress, Word


expression_stack = []

def push_first(tokens):
    expression_stack.append(tokens[0])

"""
atom       :: '0'..'9'+ | '(' expression ')'
term       :: atom [ ('*' | '/') atom ]*
expression :: term [ ('+' | '-') term ]*
"""
expression = Forward()
atom = (Word(nums)).set_parse_action(push_first) | Group(Suppress('(') + expression + Suppress(')'))
term = atom + ((Literal('*') | Literal('/')) + atom).set_parse_action(push_first)[...]
expression <<= term + ((Literal('+') | Literal('-')) + term).set_parse_action(push_first)[...]

operations = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv
}

def evaluate_stack(stack):
    token = stack.pop()
    if token in "+-*/":
        # Operands are pushed onto the stack in reverse order
        operand_2 = evaluate_stack(stack)
        operand_1 = evaluate_stack(stack)
        return operations[token](operand_1, operand_2)
    else:
        return int(token)

def calculate(input_string: str):
    expression_stack.clear()
    expression.parse_string(
        input_string, parse_all = True
    )  # Can raise pyparsing.ParseException
    return evaluate_stack(expression_stack)  # Can raise ZeroDivisionError

