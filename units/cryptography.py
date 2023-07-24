
from string import ascii_lowercase, ascii_uppercase

from .errors import UnitExecutionError, UnitOutputError

# Caesar Cipher

def encode_caesar_cipher(message: str, key: int):
	if not isinstance(message, str):
		raise TypeError("message must be str")
	if not isinstance(key, int):
		raise TypeError("key must be int")
	encoded_message = ""
	for character in message:
		if not character.isalpha() or not character.isascii():
			encoded_message += character
		elif character.islower():
			encoded_message += ascii_lowercase[(ascii_lowercase.index(character) + key) % 26]
		else:
			encoded_message += ascii_uppercase[(ascii_uppercase.index(character) + key) % 26]
	return encoded_message

def decode_caesar_cipher(message: str, key: int):
	if not isinstance(message, str):
		raise TypeError("message must be str")
	if not isinstance(key, int):
		raise TypeError("key must be int")
	return encode_caesar_cipher(message, -key)

# Morse Code

character_to_morse = {
	'A': ".-", 'B': "-...", 'C': "-.-.", 'D': "-..", 'E': '.', 'F': "..-.", 'G': "--.", 'H': "....", 
	'I': "..", 'J': ".---", 'K': "-.-", 'L': ".-..", 'M': "--", 'N': "-.", 'O': "---", 'P': ".--.", 
	'Q': "--.-", 'R': ".-.", 'S': "...", 'T': '-', 'U': "..-", 'V': "...-", 'W': ".--", 'X': "-..-", 
	'Y': "-.--", 'Z': "--..", '0': "----", '1': ".----", '2': "..---", '3': "...--", '4': "....-", 
	'5': ".....", '6': "-....", '7': "--...", '8': "---..", '9': "----.", '.': ".-.-.-", ',': "--..--", 
	':': "---...", '?': "..--..", "'": ".---.", '-': "-....-", '/': "-..-.", '!': "-.-.--", 
	'(': "-.--.", ')': "-.--.-", '&': ".-...", ';': "-.-.-.", '=': "-...-", '+': ".-.-.", 
	'_': "..--.-", '"': ".-..-.", '$': "...-..-", '@': ".--.-.", ' ': '/'
}
# TODO: Add non-English extensions

morse_to_character = {value: key for key, value in character_to_morse.items()}

def encode_morse_code(message: str):
	if not isinstance(message, str):
		raise TypeError("message must be str")
	try:
		return ' '.join(character_to_morse[character] for character in message.upper())
	except KeyError as e:
		raise UnitOutputError(f"Unable to encode {e}")

def decode_morse_code(message: str):
	if not isinstance(message, str):
		raise UnitExecutionError("message must be str")
	try:
		return ' '.join("".join(morse_to_character[character] for character in word.split()) 
						for word in message.split(" / "))
	except KeyError as e:
		raise UnitOutputError(f"Unable to decode {e}")

