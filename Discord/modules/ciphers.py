
def encode_caesar(message, key):
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

def decode_caesar(message, key):
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

def brute_force_caesar(message):
	decodes = ""
	for key in range(26):
		decodes += str(key) + ": " + decode_caesar(message, key) + '\n'
	return decodes
