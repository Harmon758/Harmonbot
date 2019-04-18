
import unittest

from hypothesis import assume, given
from hypothesis.strategies import characters, text, uuids

from units.cryptography import decode_morse_code, encode_morse_code
from units.errors import UnitExecutionError, UnitOutputError

class TestMorseCode(unittest.TestCase):
	
	@given(uuids())
	def test_decode_invalid_message_type(self, message):
		self.assertRaises(UnitExecutionError, decode_morse_code, message)
	
	@given(uuids())
	def test_encode_invalid_message_type(self, message):
		self.assertRaises(UnitExecutionError, encode_morse_code, message)
	
	@given(text(alphabet = characters(blacklist_characters = ".-/")))
	def test_decode_undefined_characters(self, message):
		assume(message)
		assume(not message.isspace())
		self.assertRaises(UnitOutputError, decode_morse_code, message)
	
	@given(text(alphabet = characters(min_codepoint = 123, 
										whitelist_characters = [chr(code) for code in range(32)] + 
																['#', '%', '*', '<', '>', '[', '\\', ']', '^', '`'])))
	def test_encode_undefined_characters(self, message):
		assume(message)
		self.assertRaises(UnitOutputError, encode_morse_code, message)
	
	@given(text(alphabet = characters(min_codepoint = 32, max_codepoint = 122, 
										blacklist_characters = "#%*<>[\\]^`")))
	def test_decode_inverts_encode(self, message):
		self.assertEqual(message.upper(), decode_morse_code(encode_morse_code(message)))

if __name__ == "__main__":
	unittest.main()
