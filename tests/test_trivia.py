
import unittest

from units.trivia import check_answer


class TestCheckAnswer(unittest.TestCase):

    def test_correct_answer(self):
        self.assertTrue(check_answer("correct", "correct"))

    def test_incorrect_answer(self):
        self.assertFalse(check_answer("correct", "incorrect"))


if __name__ == "__main__":
    unittest.main()
