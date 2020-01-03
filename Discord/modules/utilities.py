
import math

def is_hex(characters):
	try:
		int(characters, 16)
		return True
	except ValueError:
		return False

'''
import string
def is_hex(s):
	hex_digits = set(string.hexdigits)
	# if s is long, then it is faster to check against a set
	return all(c in hex_digits for c in s)
'''

def secs_to_duration(secs, limit = 0):
	duration = []
	time_in_secs = [31536000, 604800, 86400, 3600, 60]
	# years, weeks, days, hours, minutes
	for length_of_time in time_in_secs:
		if (limit and length_of_time > limit) or secs < length_of_time:
			duration.append(0)
		else:
			duration.append(int(math.floor(secs / length_of_time)))
			secs -= math.floor(secs / length_of_time) * length_of_time
	duration.append(int(secs))
	return duration

def duration_to_letter_format(duration):
	return ' '.join(filter(None, ["{}{}".format(duration[i], letter) if duration[i] else "" for i, letter in enumerate(['y', 'w', 'd', 'h', 'm', 's'])])) or "0s"

def duration_to_colon_format(duration):
	return ':'.join([str(unit).rjust(2, '0') if unit else "00" for unit in duration]).lstrip("0:").rjust(2, '0').rjust(3, ':').rjust(4, '0')

def secs_to_letter_format(secs, limit = 0):
	return duration_to_letter_format(secs_to_duration(secs, limit = limit))

def secs_to_colon_format(secs, limit = 0):
	return duration_to_colon_format(secs_to_duration(secs, limit = limit))

def remove_symbols(string):
	plain_string = ""
	for character in string:
		if 0 <= ord(character) <= 127:
			plain_string += character
	if plain_string.startswith(' '):
		plain_string = plain_string[1:]
	return plain_string

# https://en.wikipedia.org/wiki/Unicode_subscripts_and_superscripts#Superscripts_and_subscripts_block

def superscript(string):
	superscripts = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹', '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾', 'i': 'ⁱ	', 'n': 'ⁿ'}
	return "".join(superscripts.get(c, c) for c in str(string))

def subscript(string):
	subscripts = {'0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉', '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎', 'a': 'ₐ', 'e': 'ₑ', 'o': 'ₒ', 'x': 'ₓ', 'ə': 'ₔ', 'h': 'ₕ', 'k': 'ₖ', 'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ', 'p': 'ₚ', 's': 'ₛ', 't': 'ₜ'}
	return "".join(subscripts.get(c, c) for c in str(string))

