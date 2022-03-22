
import random
import re

import pyparsing

from .calculation import calculate


def check_valid_numbers(numbers):
	for index_1, number_1 in enumerate(numbers[:-1]):
		for index_2, number_2 in enumerate(numbers[index_1 + 1:], index_1 + 1):
			values = {number_1 + number_2, number_1 * number_2, number_1 - number_2, number_2 - number_1}
			if number_1:
				values.add(number_2 / number_1)
			if number_2:
				values.add(number_1 / number_2)
			if len(numbers) > 2:
				next_items = numbers[:index_1] + numbers[index_1 + 1:index_2] + numbers[index_2 + 1:]
				for value in values:
					if check_valid_numbers(next_items + [value]):
						return True
			else:
				return any(abs(value - 24) < 0.1 for value in values)
	return False

def generate_numbers():
	while not check_valid_numbers(numbers := [random.randint(1,9) for _ in range(4)]):
		pass
	return numbers

def check_solution(numbers, solution):
	if any(character not in numbers + [' ', '+', '-', '*', '/', '(', ')'] for character in solution):
		return False
	if len(list(filter(None, re.split("\W+", solution)))) != 4:
		return False
	for number in set(numbers):
		if solution.count(number) != numbers.count(number):
			return False
	try:
		return round(calculate(solution), 1)
	except pyparsing.ParseException:
		return False
