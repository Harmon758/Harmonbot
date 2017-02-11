
character_to_morse = {
	'A' : ".-", 'B' : "-...", 'C' : "-.-.", 'D' : "-..", 'E' : '.', 'F' : "..-.", 'G' : "--.", 'H' : "....", 'I' : "..", 'J' : ".---", 'K' : "-.-", 
	'L' : ".-..", 'M' : "--", 'N' : "-.", 'O' : "---", 'P' : ".--.", 'Q' : "--.-", 'R' : ".-.", 'S' : "...", 'T' : '-', 'U' : "..-", 'V' : "...-", 
	'W' : ".--", 'X' : "-..-", 'Y' : "-.--", 'Z' : "--..", '0' : "----", '1' : ".----", '2' : "..---", '3' : "...--", '4' : "....-", '5' : ".....", 
	'6' : "-....", '7' : "--...", '8' : "---..", '9' : "----.", '.' : ".-.-.-", ',' : "--..--", ':' : "---...", '?' : "..--..", "'" : ".---.", 
	'-' : "-....-", '/' : "-..-.", '!' : "-.-.--", '(' : "-.--.", ')' : "-.--.-", '&' : ".-...", ';' : "-.-.-.", '=' : "-...-", '+' : ".-.-.", 
	'_' : "..--.-", '"' : ".-..-.", '$' : "...-..-", '@' : ".--.-.", ' ' : "/"
}

morse_to_character = {value : key for key, value in character_to_morse.items()}

def encode_morse(message):
	'''
	encoded_message = ""
	for character in message.upper():
		encoded_message += character_to_morse[character] + ' '
	return encoded_message
	'''
	try:
		return ' '.join(character_to_morse[character] for character in message.upper())
	except KeyError:
		return "Error"

def decode_morse(message):
	'''
	decoded_message = ""
	for word in message.split(" / "):
		for character in word.split(' '):
			decoded_message += morse_to_character[character]
		decoded_message += ' '
	return decoded_message
	'''
	try:
		return ' '.join(''.join((morse_to_character[character]) for character in word.split(' ')) for word in message.split(" / "))
	except KeyError:
		return "Error"

def encode_caesar(message, key):
	encoded_message = ""
	for character in message:
		if not ('a' <= character <= 'z' or 'A' <= character <= 'Z'): # .isalpha() ?
			encoded_message += character
			continue
		shifted = ord(character) + int(key)
		if character.islower() and shifted > ord('z') or character.isupper() and shifted > ord('Z'):
			encoded_message += chr(shifted - 26)
		else:
			encoded_message += chr(shifted)
	return encoded_message

def decode_caesar(message, key):
	decoded_message = ""
	for character in message:
		if not ('a' <= character <= 'z' or 'A' <= character <= 'Z'): # .isalpha() ?
			decoded_message += character
			continue
		shifted = ord(character) - int(key)
		if character.islower() and shifted < ord('a') or character.isupper() and shifted < ord('A'):
			decoded_message += chr(shifted + 26)
		else:
			decoded_message += chr(shifted)
	return decoded_message

def brute_force_caesar(message):
	decodes = ""
	for key in range(26):
		decodes += str(key) + ": " + decode_caesar(message, key) + '\n'
	return decodes
