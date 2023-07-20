
import unittest

from units.trivia import check_answer


class TestCheckAnswer(unittest.TestCase):

    def test_correct_answer(self):
        self.assertTrue(check_answer("correct", "correct"))

    def test_incorrect_answer(self):
        self.assertFalse(check_answer("correct", "incorrect"))

    def test_correct_encoding(self):
        self.assertTrue(
            check_answer("Brontë Sisters (The Brontës)", "Brontes")
        )

    def test_incorrect_encoding(self):
        self.assertTrue(check_answer("a rÃ©sumÃ©", "resume"))
        self.assertTrue(check_answer("TenochtitlÃ¡n", "Tenochtitlan"))

    def test_large_number(self):
        self.assertFalse(
            check_answer(
                "33 1/3",
                "128347192834719283561293847129384719238471234"
            )
        )

    def test_only_comma(self):
        self.assertFalse(check_answer("colon", ','))

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

    def test_preceding_possessive_determiner_removal(self):
        self.assertTrue(check_answer("its head", "head"))

    def test_preceding_preposition_removal(self):
        self.assertTrue(check_answer("to carp", "carp"))

    def test_plurality_validation_handling(self):
        self.assertFalse(check_answer("Kellogg's", "'s"))

    def test_plurality_with_partial_slash(self):
        self.assertTrue(
            check_answer("Junior/Community Colleges", "community college")
        )
        self.assertTrue(
            check_answer("Junior/Community Colleges", "junior college")
        )

    def test_plurality_with_parentheses(self):
        self.assertTrue(check_answer("pigs (hogs)", "pig"))
        self.assertTrue(check_answer("pigs (hogs)", "hog"))

    def test_rearranged_list_with_following_word(self):
        self.assertTrue(
            check_answer(
                "North and South Carolina",
                "South and North Carolina"
            )
        )


if __name__ == "__main__":
    unittest.main()
