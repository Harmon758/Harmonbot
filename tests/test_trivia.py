
import unittest

from units.trivia import check_answer


class TestCheckAnswer(unittest.TestCase):

    def test_correct_answer(self):
        self.assertTrue(check_answer("correct", "correct"))

    def test_incorrect_answer(self):
        self.assertFalse(check_answer("correct", "incorrect"))

    def test_parentheses_with_article_prefix(self):
        self.assertTrue(
            check_answer(
                "the ISS (the International Space Station)",
                "International Space Station"
            )
        )
        self.assertTrue(
            check_answer("Holland (The Netherlands)", "Netherlands")
        )

    def test_wrong_encoding(self):
        self.assertTrue(check_answer("a rÃ©sumÃ©", "resume"))


if __name__ == "__main__":
    unittest.main()
