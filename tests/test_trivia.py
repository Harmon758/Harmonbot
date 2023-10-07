
import unittest

from units.trivia import check_answer


class TestCheckAnswer(unittest.TestCase):

    def test_correct_answer(self):
        self.assertTrue(check_answer(answer = "correct", response = "correct"))

    def test_incorrect_answer(self):
        self.assertFalse(
            check_answer(answer = "correct", response = "incorrect")
        )

    def test_correct_encoding(self):
        self.assertTrue(
            check_answer(
                answer = "Brontë Sisters (The Brontës)", response = "Brontes"
            )
        )
        self.assertFalse(
            check_answer(
                answer = "(Antonín) Dvořák", response = "stravinsky"
            )
        )

    def test_incorrect_encoding(self):
        self.assertTrue(
            check_answer(answer = "a rÃ©sumÃ©", response = "resume")
        )
        self.assertTrue(
            check_answer(answer = "TenochtitlÃ¡n", response = "Tenochtitlan")
        )

    def test_and_with_and_in_item(self):
        self.assertTrue(
            check_answer(
                answer = "Rhode Island & Delaware",
                response = "delaware and rhode island"
            )
        )

    def test_ampersand(self):
        self.assertTrue(check_answer(answer = "AT&T", response = "at&t"))

    def test_clue_text_plural_subject_redundancy(self):
        for clue, answer, response in (
            (
                (
                    'From the Latin for "thigh", these main arteries of the '
                    "thigh supply blood to the lower extremities"
                ),
                "the femoral arteries",
                "femoral"
            ),
            (
                (
                    "These glands secrete an oily substance which lubricates "
                    "your hair & keeps it soft"
                ),
                "the sebaceous glands",
                "sebaceous"
            )
        ):
            self.assertTrue(
                check_answer(clue = clue, answer = answer, response = response)
            )

    def test_clue_text_subject_redundancy(self):
        for clue, answer, response in (
            (
                (
                    "During WWII the Army trained its first 2 airborne "
                    "divisions at this N.C. fort"
                ),
                "Fort Bragg",
                "bragg"
            ),
            (
                (
                    "A job of Roman tribunes was to protect this class from "
                    "Patrician judicial abuses"
                ),
                "Plebeian class",
                "plebeian"
            ),
            (
                (
                    "With about 8 million, this East Coast city is the most "
                    "populous U.S. city"
                ),
                "New York City",
                "new york"
            ),
            (
                (
                    "The nation with the fewest people, about 890, is this "
                    '"City" where the pope lives'
                ),
                "Vatican City",
                "vatican"
            ),
            (
                (
                    "Around 3,000 Americans lost their lives in the war, most "
                    "to typhoid & this fever rather than combat"
                ),
                "yellow fever",
                "yellow"
            ),
            (
                (
                    "This gland which regulates growth is also called the "
                    "hypophysis"
                ),
                "the pituitary gland",
                "pituitary"
            ),
            (
                (
                    "This gland that controls cell metabolism has 2 lobes, 1 "
                    "on each side of your trachea"
                ),
                "the thyroid gland",
                "thyroid"
            )
        ):
            self.assertTrue(
                check_answer(clue = clue, answer = answer, response = response)
            )

    def test_dash_removal_with_article_prefix(self):
        self.assertTrue(
            check_answer(
                answer = '"A-Tisket, A-Tasket"', response = "a tisket a tasket"
            )
        )

    def test_honorific(self):
        self.assertTrue(
            check_answer(
                answer = "Sir Isaac Newton", response = "Isaac Newton"
            )
        )

    def test_large_number(self):
        self.assertFalse(
            check_answer(
                answer = "33 1/3",
                response = "128347192834719283561293847129384719238471234"
            )
        )

    def test_matching_named_entity(self):
        for answer, response in (
            ("the Appalachian Mountains", "appalachians"),
            ("Benjamin Franklin", "ben franklin"),
            ("Creedence Clearwater Revival", "ccr"),
            ("Cosmo Kramer", "kramer"),
            ("the gall bladder", "gallbladder"),
            ("Harry S. Truman", "truman"),
            ("Judas Iscariot", "judas"),
            ("Louis Pasteur", "pasteur"),
            ("Sam Adams", "samuel adams"),
            ("Spielberg", "steven spielberg"),
            ("Theodore Roosevelt", "teddy roosevelt"),
            ("the University of Southern California", "usc")
        ):
            self.assertTrue(
                check_answer(answer = answer, response = response),
                f'answer: "{answer}", response: "{response}"'
            )

    def test_partial_matching_named_entity(self):
        self.assertFalse(
            check_answer(answer = "bean sprouts", response = "soy beans")
        )

    def test_only_comma(self):
        self.assertFalse(check_answer(answer = "colon", response = ','))

    def test_parentheses_with_article_prefix(self):
        self.assertTrue(
            check_answer(
                answer = "the ISS (the International Space Station)",
                response = "International Space Station"
            )
        )
        self.assertTrue(
            check_answer(
                answer = "Holland (The Netherlands)", response = "Netherlands"
            )
        )

    def test_preceding_possessive_determiner_removal(self):
        self.assertTrue(check_answer(answer = "its head", response = "head"))

    def test_preceding_preposition_removal(self):
        self.assertTrue(check_answer(answer = "to carp", response = "carp"))

    def test_plurality_validation_handling(self):
        self.assertFalse(check_answer(answer = "Kellogg's", response = "'s"))

    def test_plurality_with_partial_slash(self):
        self.assertTrue(
            check_answer(
                answer = "Junior/Community Colleges",
                response = "community college"
            )
        )
        self.assertTrue(
            check_answer(
                answer = "Junior/Community Colleges",
                response = "junior college"
            )
        )

    def test_plurality_with_parentheses(self):
        self.assertTrue(check_answer(answer = "pigs (hogs)", response = "pig"))
        self.assertTrue(check_answer(answer = "pigs (hogs)", response = "hog"))

    def test_rearranged_list_with_following_word(self):
        self.assertTrue(
            check_answer(
                answer = "North and South Carolina",
                response = "South and North Carolina"
            )
        )


if __name__ == "__main__":
    unittest.main()
