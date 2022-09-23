
import html
import re
import unicodedata

from bs4 import BeautifulSoup
import inflect
from pyparsing import Forward, Group, printables, OneOrMore, Suppress, Word, ZeroOrMore


def capwords(string):
    '''string.capwords with abbreviation handling'''
    return ' '.join(
        word.upper() if word.count('.') > 1 and not word.endswith("..")
        or word == "tv"
        else word.capitalize()
        for word in string.split()
    )


def check_answer(answer, response, inflect_engine = None):
    if not inflect_engine:
        inflect_engine = inflect.engine()

    # Unescape HTML entities in answer and extract text between HTML tags
    answer = BeautifulSoup(html.unescape(answer), "html.parser").get_text()
    # Replace in answer: \' -> '
    # Replace in response: ’ -> '
    # Replace: & -> and
    answer = answer.replace("\\'", "'").replace('&', "and")
    response = response.replace('’', "'").replace('&', "and")
    # Remove exclamation marks, periods, quotation marks, and interpuncts
    for character in '!."·':
        if character in answer:
            answer = answer.replace(character, "")
        if character in response:
            response = response.replace(character, "")
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
    # Make lowercase
    answer = ' '.join(answer.split()).lower()
    response = ' '.join(response.split()).lower()

    # Check removal of/replacement of - with space (prior to removing article prefixes)
    # Remove commas beforehand
    answer_copy = answer.replace(',', "")
    response_copy = response.replace(',', "")
    if answer_copy.replace('-', ' ') == response_copy.replace('-', ' '):
        return True
    if answer_copy.replace('-', "") == response_copy.replace('-', ""):
        return True

    # Remove article prefixes
    answer = remove_article_prefix(answer)
    response = remove_article_prefix(response)
    # Return False if empty response or answer
    if not response or not answer:
        return False

    # Get items in lists
    answer_items = [item.strip() for item in answer.split(',')]
    answer_items[-1:] = [
        item.strip() for item in answer_items[-1].split("and") if item
    ]
    response_items = [item.strip() for item in response.split(',')]
    response_items[-1:] = [
        item.strip() for item in response_items[-1].split("and") if item
    ]
    # Return False if only "and"
    if not response_items:
        return False
    # Remove article prefixes
    for index, item in enumerate(answer_items):
        answer_items[index] = remove_article_prefix(item)
    for index, item in enumerate(response_items):
        response_items[index] = remove_article_prefix(item)
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
    if answer == inflect_engine.plural(response):
        return True
    # Check XX and YY ZZ
    last = answer_items[-1].split()
    if len(last) > 1:
        suffix = last[-1]
        if set([f"{item} {suffix}" for item in answer_items[:-1]] + [answer_items[-1]]) == set(response_items):
            return True
    last = response_items[-1].split()
    if len(last) > 1:
        suffix = last[-1]
        if set(answer_items) == set([f"{item} {suffix}" for item in response_items[:-1]] + [response_items[-1]]):
            return True
    # Remove commas
    if ',' in answer:
        answer = answer.replace(',', "")
    if ',' in response:
        response = response.replace(',', "")
    # Check for list separated by /
    if set(item.strip() for item in answer.split('/')) == set(item.strip() for item in response.split('/')):
        return True
    # Check removal of/replacement of - with space
    if answer.replace('-', ' ') == response.replace('-', ' '):
        return True
    if answer.replace('-', "") == response.replace('-', ""):
        return True
    # Check removal of parentheses
    if response == remove_article_prefix(answer.replace('(', "").replace(')', "")):
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
            answers = [f"{permutation} {word}" for permutation in answers for word in answer_word.split('/')]
        else:
            answers = [f"{permutation} {answer_word}" for permutation in answers]
    if response in answers:
        return True
    # Check numbers to words conversion
    response_words = response.split()
    for words in (answer_words, response_words):
        for index, word in enumerate(words):
            if word[0].isdigit():
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
            for accepted_index, accepted_item in enumerate(accepted[initial_length:]):
                accepted[initial_length + accepted_index] = f"{accepted_item} {item}".lstrip()
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
            accepted.append(remove_article_prefix(item[3:]))
        if item.endswith(" accepted"):
            accepted.append(item[:-9])
            accepted.append(remove_article_prefix(item[:-9]))
    accepted = set(accepted)
    for item in accepted.copy():
        accepted.add(remove_article_prefix(item))
    if response in accepted:
        return True
    # Check XX YY (or ZZ accepted)
    matches = re.search(r"(.+?)\s?\((?:or )?(?:a |an |the )?(.+?)(?: accepted)?\)", answer)
    if matches and response == f"{matches.group(1).rsplit(' ', 1)[0]} {matches.group(2)}":
        return True
    # Check abbreviations
    for abbreviation, word in (("dr", "doctor"), ("mt", "mount"), ("st", "saint")):
        if (re.sub(fr"(^|\W)({abbreviation})($|\W)", fr"\1{word}\3", answer) == 
            re.sub(fr"(^|\W)({abbreviation})($|\W)", fr"\1{word}\3", response)):
            return True
    return False


def remove_article_prefix(string):
    for article in ("a ", "an ", "the "):
        if string.startswith(article):
            return string[len(article):]
    return string

