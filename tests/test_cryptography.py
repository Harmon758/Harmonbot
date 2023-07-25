
import unittest

from hypothesis import assume, given
from hypothesis.strategies import characters, integers, text, uuids

from units.cryptography import (
    decode_caesar_cipher, encode_caesar_cipher,
    decode_morse_code, encode_morse_code
)


class TestCaesarCipher(unittest.TestCase):

    @given(uuids(), integers())
    def test_decode_invalid_message_type(self, message, key):
        with self.assertRaises(TypeError):
            decode_caesar_cipher(message, key)

    @given(uuids(), integers())
    def test_encode_invalid_message_type(self, message, key):
        with self.assertRaises(TypeError):
            encode_caesar_cipher(message, key)

    @given(text(), uuids())
    def test_decode_invalid_key_type(self, message, key):
        with self.assertRaises(TypeError):
            decode_caesar_cipher(message, key)

    @given(text(), uuids())
    def test_encode_invalid_key_type(self, message, key):
        with self.assertRaises(TypeError):
            encode_caesar_cipher(message, key)

    @given(text(), integers())
    def test_decode_inverts_encode(self, message, key):
        self.assertEqual(
            message,
            decode_caesar_cipher(encode_caesar_cipher(message, key), key)
        )


invalid_morse_code_characters = [
    '#', '%', '*', '<', '>', '[', '\\', ']', '^', '`'
]

class TestMorseCode(unittest.TestCase):

    @given(uuids())
    def test_decode_invalid_message_type(self, message):
        with self.assertRaises(TypeError):
            decode_morse_code(message)

    @given(uuids())
    def test_encode_invalid_message_type(self, message):
        with self.assertRaises(TypeError):
            encode_morse_code(message)

    @given(text(alphabet = characters(blacklist_characters = ".-/")))
    def test_decode_undefined_characters(self, message):
        assume(message)
        assume(not message.isspace())
        with self.assertRaises(ValueError):
            decode_morse_code(message)

    @given(text(
        alphabet = characters(
            min_codepoint = 123,
            whitelist_characters = (
                [chr(code) for code in range(32)] +
                invalid_morse_code_characters
            )
        )
    ))
    def test_encode_undefined_characters(self, message):
        assume(message)
        assume(
            not all(32 <= ord(character) <= 122 and
            character not in invalid_morse_code_characters
            for character in message.upper())
        )
        # Ignore test failure for ligatures
        assume(len(message.upper()) == len(message))
        with self.assertRaises(ValueError):
            encode_morse_code(message)

    @given(text(
        alphabet = characters(
            min_codepoint = 32, max_codepoint = 122,
            blacklist_characters = invalid_morse_code_characters
        )
    ))
    def test_decode_inverts_encode(self, message):
        self.assertEqual(
            message.upper(), decode_morse_code(encode_morse_code(message))
        )


if __name__ == "__main__":
    unittest.main()

