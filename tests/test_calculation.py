
import unittest

import math

from hypothesis import assume, given
from hypothesis.strategies import characters, integers, lists, text

import pyparsing

from units.calculation import calculate


class TestCalculate(unittest.TestCase):

    @given(integers(min_value = 0))
    def test_identity(self, number):
        assert calculate(str(number)) == number

    @given(lists(integers(min_value = 0), min_size = 2))
    def test_addition(self, summands):
        assert calculate('+'.join(map(str, summands))) == sum(summands)

    @given(integers(min_value = 0), integers(min_value = 0))
    def test_subtraction(self, minuend, subtrahend):
        assert calculate(f"{minuend}-{subtrahend}") == minuend - subtrahend

    @given(lists(integers(min_value = 0), min_size = 2))
    def test_multiplication(self, factors):
        assert calculate('*'.join(map(str, factors))) == math.prod(factors)

    @given(integers(min_value = 0), integers(min_value = 1))
    def test_division(self, dividend, divisor):
        assert calculate(f"{dividend}/{divisor}") == dividend / divisor

    @given(integers(min_value = 0), integers(min_value = 1), integers(min_value = 1))
    def test_order_of_operations(self, operand_1, operand_2, operand_3):
        assert calculate(f"{operand_1}+{operand_2}*{operand_3}") == operand_1 + operand_2 * operand_3
        assert calculate(f"{operand_1}+{operand_2}/{operand_3}") == operand_1 + operand_2 / operand_3
        assert calculate(f"{operand_1}-{operand_2}+{operand_3}") == operand_1 - operand_2 + operand_3
        assert calculate(f"{operand_1}-{operand_2}-{operand_3}") == operand_1 - operand_2 - operand_3
        assert calculate(f"{operand_1}-{operand_2}*{operand_3}") == operand_1 - operand_2 * operand_3
        assert calculate(f"{operand_1}-{operand_2}/{operand_3}") == operand_1 - operand_2 / operand_3
        assert calculate(f"{operand_1}*{operand_2}+{operand_3}") == operand_1 * operand_2 + operand_3
        assert calculate(f"{operand_1}*{operand_2}-{operand_3}") == operand_1 * operand_2 - operand_3
        assert calculate(f"{operand_1}/{operand_2}+{operand_3}") == operand_1 / operand_2 + operand_3
        assert calculate(f"{operand_1}/{operand_2}-{operand_3}") == operand_1 / operand_2 - operand_3
        assert calculate(f"{operand_1}/{operand_2}*{operand_3}") == operand_1 / operand_2 * operand_3
        assert calculate(f"{operand_1}/{operand_2}/{operand_3}") == operand_1 / operand_2 / operand_3

    @given(integers(min_value = 0), integers(min_value = 1), integers(min_value = 1))
    def test_parentheses(self, operand_1, operand_2, operand_3):
        assert calculate(f"({operand_1}+{operand_2})*{operand_3}") == (operand_1 + operand_2) * operand_3
        assert calculate(f"({operand_1}+{operand_2})/{operand_3}") == (operand_1 + operand_2) / operand_3
        assert calculate(f"{operand_1}-({operand_2}+{operand_3})") == operand_1 - (operand_2 + operand_3)
        assert calculate(f"{operand_1}-({operand_2}-{operand_3})") == operand_1 - (operand_2 - operand_3)
        assert calculate(f"({operand_1}-{operand_2})*{operand_3}") == (operand_1 - operand_2) * operand_3
        assert calculate(f"({operand_1}-{operand_2})/{operand_3}") == (operand_1 - operand_2) / operand_3
        assert calculate(f"{operand_1}*({operand_2}+{operand_3})") == operand_1 * (operand_2 + operand_3)
        assert calculate(f"{operand_1}*({operand_2}-{operand_3})") == operand_1 * (operand_2 - operand_3)
        assume(operand_2 != -operand_3)
        assert calculate(f"{operand_1}/({operand_2}+{operand_3})") == operand_1 / (operand_2 + operand_3)
        assume(operand_2 != operand_3)
        assert calculate(f"{operand_1}/({operand_2}-{operand_3})") == operand_1 / (operand_2 - operand_3)
        assert calculate(f"{operand_1}/({operand_2}*{operand_3})") == operand_1 / (operand_2 * operand_3)
        assert calculate(f"{operand_1}/({operand_2}/{operand_3})") == operand_1 / (operand_2 / operand_3)

    @given(lists(integers(min_value = 0), min_size = 2), text(alphabet = ' ', min_size = 1))
    def test_whitespace(self, numbers, whitespace):
        assert calculate(f"{whitespace}{numbers[0]}{whitespace}") == numbers[0]
        assert calculate(f"{whitespace}+{whitespace}".join(map(str, numbers))) == sum(numbers)
        assert calculate(f"{numbers[0]}{whitespace}-{whitespace}{numbers[1]}") == numbers[0] - numbers[1]
        assert calculate(f"{whitespace}*{whitespace}".join(map(str, numbers))) == math.prod(numbers)

    @given(integers(min_value = 0), integers(min_value = 0))
    def test_invalid_operator_syntax(self, operand_1, operand_2):
        self.assertRaises(pyparsing.ParseException, calculate, f"{operand_1}++{operand_2}")
        self.assertRaises(pyparsing.ParseException, calculate, f"{operand_1}--{operand_2}")
        self.assertRaises(pyparsing.ParseException, calculate, f"{operand_1}**{operand_2}")
        self.assertRaises(pyparsing.ParseException, calculate, f"{operand_1}//{operand_2}")
        self.assertRaises(pyparsing.ParseException, calculate, f"{operand_1}+")
        self.assertRaises(pyparsing.ParseException, calculate, f"{operand_1}-")
        self.assertRaises(pyparsing.ParseException, calculate, f"{operand_1}*")
        self.assertRaises(pyparsing.ParseException, calculate, f"{operand_1}/")
        self.assertRaises(pyparsing.ParseException, calculate, f"+{operand_1}")
        self.assertRaises(pyparsing.ParseException, calculate, f"-{operand_1}")
        self.assertRaises(pyparsing.ParseException, calculate, f"*{operand_1}")
        self.assertRaises(pyparsing.ParseException, calculate, f"/{operand_1}")

    @given(text(alphabet = characters(exclude_characters = pyparsing.nums)))
    def test_non_numeric(self, non_numeric):
        self.assertRaises(pyparsing.ParseException, calculate, non_numeric)

    @given(integers(min_value = 0))
    def test_parentheses_mismatch(self, number):
        self.assertRaises(pyparsing.ParseException, calculate, f"({number}")
        self.assertRaises(pyparsing.ParseException, calculate, f"{number})")

    @given(integers(min_value = 0))
    def test_division_by_zero(self, dividend):
        self.assertRaises(ZeroDivisionError, calculate, f"{dividend}/0")


if __name__ == "__main__":
    unittest.main()
