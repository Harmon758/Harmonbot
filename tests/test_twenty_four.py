
import unittest

from units.twenty_four import check_solution


class TestCheckSolution(unittest.TestCase):

    def test_correct_solution(self):
        self.assertEqual(
            check_solution(['1', '2', '3', '4'], "1 * 2 * 3 * 4"), 24
        )

    def test_incorrect_solution(self):
        self.assertEqual(
            check_solution(['1', '2', '3', '4'], "1 + 2 + 3 + 4"), 10
        )

    def test_invalid_solution(self):
        self.assertFalse(check_solution(['1', '2', '3', '4'], "test"))

    def test_combine_numbers_as_digits(self):
        self.assertFalse(check_solution(['1', '1', '2', '4'], "1 * 1 * 24"))

    def test_parentheses_at_end(self):
        self.assertEqual(
            check_solution(['2', '2', '3', '7'], "3 * (7 + 2 / 2)"), 24
        )


if __name__ == "__main__":
    unittest.main()
