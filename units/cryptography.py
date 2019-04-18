
from .errors import UnitOutputError

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

morse_to_character = {value: key for key, value in character_to_morse.items()}

def encode_morse_code(message):
	try:
		return ' '.join(character_to_morse[character] for character in message.upper())
	except KeyError as e:
		raise UnitOutputError(f"Unable to encode {e}")

def decode_morse_code(message):
	try:
		return ' '.join("".join(morse_to_character[character] for character in word.split()) 
						for word in message.split(" / "))
	except KeyError as e:
		raise UnitOutputError(f"Unable to decode {e}")

