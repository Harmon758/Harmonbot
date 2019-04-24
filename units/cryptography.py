
from .errors import UnitExecutionError, UnitOutputError

# Caesar Cipher

def encode_caesar_cipher(message, key):
	encoded_message = ""
	for character in message:
		if not character.isalpha() or not character.isascii():
			encoded_message += character
			continue
		shifted = ord(character) + int(key)
		if character.islower() and shifted > ord('z') or character.isupper() and shifted > ord('Z'):
			encoded_message += chr(shifted - 26)
		else:
			encoded_message += chr(shifted)
	return encoded_message

def decode_caesar_cipher(message, key):
	decoded_message = ""
	for character in message:
		if not character.isalpha() or not character.isascii():
			decoded_message += character
			continue
		shifted = ord(character) - int(key)
		if character.islower() and shifted < ord('a') or character.isupper() and shifted < ord('A'):
			decoded_message += chr(shifted + 26)
		else:
			decoded_message += chr(shifted)
	return decoded_message

def brute_force_caesar_cipher(message):
	decodes = ""
	for key in range(26):
		decodes += f"{key}: {decode_caesar_cipher(message, key)}\n"
	return decodes

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

def encode_morse_code(message):
	if not isinstance(message, str):
		raise UnitExecutionError("message must be str")
	try:
		return ' '.join(character_to_morse[character] for character in message.upper())
	except KeyError as e:
		raise UnitOutputError(f"Unable to encode {e}")

def decode_morse_code(message):
	if not isinstance(message, str):
		raise UnitExecutionError("message must be str")
	try:
		return ' '.join("".join(morse_to_character[character] for character in word.split()) 
						for word in message.split(" / "))
	except KeyError as e:
		raise UnitOutputError(f"Unable to decode {e}")

