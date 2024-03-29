
import contextlib
import html
import re
import unicodedata
import warnings

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
import inflect
import pydantic
from pyparsing import (
    Forward, Group, OneOrMore, printables, Suppress, Word, ZeroOrMore
)
import spacy


nlp = spacy.load("en_core_web_md")
nlp.add_pipe("entityLinker", last = True)  # spacy-entity-linker


def capwords(string: str) -> str:
    """string.capwords with abbreviation handling"""
    return ' '.join(
        word.upper() if (
            word.count('.') > 1 and not word.endswith("..")
            or word.upper() in ("DC-3", "NBA", "TV")
        )
        else word.capitalize()
        for word in string.split()
    )


def check_answer(*, answer, response, clue = None, inflect_engine = None):
    if not inflect_engine:
        inflect_engine = inflect.engine()

    # Unescape HTML entities in answer and extract text between HTML tags
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", category = MarkupResemblesLocatorWarning
        )
        answer = BeautifulSoup(html.unescape(answer), "lxml").get_text()
    # Replace in answer: \' -> '
    answer = answer.replace("\\'", "'")
    # Replace in response: ’ -> '  # noqa: RUF003 (ambiguous-unicode-character-comment)
    response = response.replace('’', "'")  # noqa: RUF001 (ambiguous-unicode-character-string)
    # Replace: & -> and
    answer = answer.replace('&', "and")
    response = response.replace('&', "and")
    # Remove exclamation marks, quotation marks, asterisks, periods, and
    # interpuncts
    for character in '!"*.·':
        if character in answer:
            answer = answer.replace(character, "")
        if character in response:
            response = response.replace(character, "")
    # Fix wrong encoding
    with contextlib.suppress(UnicodeDecodeError, UnicodeEncodeError):
        answer = answer.encode("ISO-8859-1").decode("UTF-8")
    # Remove diacritics
    answer = "".join(
        character for character in unicodedata.normalize("NFD", answer) 
        if not unicodedata.combining(character)
    )
    response = "".join(
        character for character in unicodedata.normalize("NFD", response) 
        if not unicodedata.combining(character)
    )
    # Remove extra whitespace
    answer = ' '.join(answer.split())
    response = ' '.join(response.split())

    # Check removal of/replacement of - with space
    # (prior to removing article prefixes)
    # Remove commas and make lowercase beforehand
    answer_copy = answer.replace(',', "").lower()
    response_copy = response.replace(',', "").lower()
    if answer_copy.replace('-', ' ') == response_copy.replace('-', ' '):
        return True
    if answer_copy.replace('-', "") == response_copy.replace('-', ""):
        return True

    # Remove preceding words
    answer = remove_preceding_words(answer)
    response = remove_preceding_words(response)
    # Return False if empty response or answer
    if not response or not answer:
        return False

    # Make lowercase
    case_sensitive_answer = answer
    answer = answer.lower()
    response = response.lower()

    # Get items in lists
    one_of = False
    if answer.startswith("(1 of) "):
        answer = answer[7:]  # 7 == len("(1 of) ")
        one_of = True
    answer_items = answer.split(',')
    answer_items[-1:] = [
        item for item in answer_items[-1].split(" and ") if item
    ]
    answer_items = [item.strip() for item in answer_items]
    if one_of and response in answer_items:
        return True
    response_items = response.split(',')
    response_items[-1:] = [
        item for item in response_items[-1].split(" and ") if item
    ]
    response_items = [item.strip() for item in response_items]
    # Return False if only "and"
    if not response_items:
        return False
    # Return False if only ','
    if not any(response_items):
        return False
    # Remove preceding words
    for index, item in enumerate(answer_items):
        answer_items[index] = remove_preceding_words(item)
    for index, item in enumerate(response_items):
        response_items[index] = remove_preceding_words(item)
    # Check equivalence
    if set(answer_items) == set(response_items):
        return True
    # Check replacement of - with space
    answer_items_copy = {item.replace('-', ' ') for item in answer_items}
    response_items_copy = {item.replace('-', ' ') for item in response_items}
    if answer_items_copy == response_items_copy:
        return True
    # Check removal of -
    answer_items_copy = {item.replace('-', "") for item in answer_items}
    response_items_copy = {item.replace('-', "") for item in response_items}
    if answer_items_copy == response_items_copy:
        return True

    # Check plurality
    if response == inflect_engine.plural(answer):
        return True
    with contextlib.suppress(pydantic.ValidationError):
        if answer == inflect_engine.plural(response):
            return True
    # Check XX and YY ZZ
    answer_last = answer_items[-1].split()
    if (
        len(answer_last) > 1 and
        set(response_items) == set(
            [f"{item} {answer_last[-1]}" for item in answer_items[:-1]] +
            [answer_items[-1]]
        )
    ):
        return True
    response_last = response_items[-1].split()
    if (
        len(response_last) > 1 and
        set(answer_items) == set(
            [f"{item} {response_last[-1]}" for item in response_items[:-1]] +
            [response_items[-1]]
        )
    ):
        return True
    if (
        answer_last[-1] == response_last[-1] and
        set(
            answer_items[:-1] + [' '.join(answer_last[:-1])]
        ) == set(
            response_items[:-1] + [' '.join(response_last[:-1])]
        )
    ):
        return True
    # Remove commas
    if ',' in answer:
        answer = answer.replace(',', "")
    if ',' in response:
        response = response.replace(',', "")
    # Check for list separated by /
    if (
        set(item.strip() for item in answer.split('/')) ==
        set(item.strip() for item in response.split('/'))
    ):
        return True
    # Check removal of/replacement of - with space
    if answer.replace('-', ' ') == response.replace('-', ' '):
        return True
    if answer.replace('-', "") == response.replace('-', ""):
        return True
    # Check removal of parentheses
    if response == remove_preceding_words(
        answer.replace('(', "").replace(')', "")
    ):
        return True
    # Check XX or YY
    if response in answer.split(" or "):
        return True
    # Check XX/YY
    if response in answer.split('/'):
        return True
    # Check XX and/or YY
    if response in answer.split(" and/or "):
        return True
    # Check XX/YY ZZ
    answer_words = answer.split()
    answers = answer_words[0].split('/')
    for answer_word in answer_words[1:]:
        if '/' in answer_word:
            answers = [
                f"{permutation} {word}"
                for permutation in answers
                for word in answer_word.split('/')
            ]
        else:
            answers = [
                f"{permutation} {answer_word}"
                for permutation in answers
            ]
    for answer in answers:
        if response == answer:
            return True
        if response == inflect_engine.plural(answer):
            return True
        with contextlib.suppress(pydantic.ValidationError):
            if answer == inflect_engine.plural(response):
                return True
    # Check numbers to words conversion
    response_words = response.split()
    for words in (answer_words, response_words):
        for index, word in enumerate(words):
            if word[0].isdigit():
                with contextlib.suppress(inflect.NumOutOfRangeError):
                    words[index] = inflect_engine.number_to_words(word)
    if ' '.join(answer_words) == ' '.join(response_words):
        return True
    # Handle optional parentheses
    word = Word(printables, excludeChars = "()")
    token = Forward()
    token << ( word | Group(Suppress('(') + OneOrMore(token) + Suppress(')')) )
    expression = ZeroOrMore(token)
    parsed = expression.parseString(answer).asList()
    def add_accepted(accepted, item, initial_length = 0):
        if isinstance(item, list):
            accepted = add_optional_accepted(accepted, item)
        else:
            for accepted_index, accepted_item in enumerate(
                accepted[initial_length:]
            ):
                accepted[initial_length + accepted_index] = (
                    f"{accepted_item} {item}".lstrip()
                )
        return accepted
    def add_optional_accepted(accepted, optional):
        initial_length = len(accepted)
        if isinstance(optional[0], list):
            accepted = add_optional_accepted(accepted, optional[0])
        else:
            for accepted_item in accepted.copy():
                accepted.append(f"{accepted_item} {optional[0]}".lstrip())
        for item in optional[1:]:
            add_accepted(accepted, item, initial_length = initial_length)
        return accepted
    accepted = [""]
    for item in parsed:
        accepted = add_accepted(accepted, item)
    for item in parsed:
        if isinstance(item, list):
            accepted.extend(add_optional_accepted([""], item)[1:])
    for item in accepted:
        if item.startswith("or "):
            accepted.append(item[3:])
            accepted.append(remove_preceding_words(item[3:]))
        if item.endswith(" accepted"):
            accepted.append(item[:-9])
            accepted.append(remove_preceding_words(item[:-9]))
    accepted = set(accepted)
    for item in accepted.copy():
        accepted.add(remove_preceding_words(item))
    if response in accepted:
        return True
    with contextlib.suppress(pydantic.ValidationError):
        if inflect_engine.plural(response) in accepted:
            return True
    # Check XX YY (or ZZ accepted)
    matches = re.search(
        r"(.+?)\s?\((?:or )?(?:a |an |the )?(.+?)(?: accepted)?\)",
        answer
    )
    if (
        matches and
        response == f"{matches.group(1).rsplit(' ', 1)[0]} {matches.group(2)}"
    ):
        return True
    # Check abbreviations
    for abbreviation, word in (
        ("dr", "doctor"), ("mt", "mount"), ("st", "saint")
    ):
        if (
            re.sub(
                fr"(^|\W)({abbreviation})($|\W)", fr"\1{word}\3",
                answer.replace('(', "").replace(')', "")
            ) == re.sub(
                fr"(^|\W)({abbreviation})($|\W)", fr"\1{word}\3",
                response.replace('(', "").replace(')', "")
            )
        ):
            return True
    # Check for clue text subject redundancy
    if clue:
        doc = nlp(clue)
        for noun_chunk in doc.noun_chunks:
            if noun_chunk.text.lower().startswith(("this ", "these ")):
                subject = noun_chunk.root.text.lower()
                if remove_preceding_words(answer) in (
                    f"{response} {subject}", f"{subject} {response}"
                ):
                    return True
                if response in (
                    f"{remove_preceding_words(answer)} {subject}",
                    f"{subject} {remove_preceding_words(answer)}"
                ):
                    return True
    # Check for matching named entity
    for answer_entity in nlp(case_sensitive_answer)._.linkedEntities:
        if len(answer_entity.get_span().text) == len(case_sensitive_answer):
            for response_entity in nlp(response)._.linkedEntities:
                if response_entity.identifier == answer_entity.identifier:
                    return True
            break

    return False


def remove_preceding_words(string: str) -> str:
    for word in (
        ("a ", "an ", "the ") +  # articles
        ("her ", "his ", "its ", "their ", "your ") +  # possessive determiners
        ("to ",) +  # prepositions
        ("dr ", "sir ")  # honorifics
    ):
        if string.startswith(word):
            return string[len(word):]
    return string

