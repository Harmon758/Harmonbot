
from random import shuffle, randint

class maze:

	def __init__(self, columns, rows):
		if columns < 2:
			self.number_of_columns = 2
		elif columns > 15:
			self.number_of_columns = 15
		else:
			self.number_of_columns = columns
		if rows < 2:
			self.number_of_rows = 2
		elif rows > 15:
			self.number_of_rows = 15
		else:
			self.number_of_rows = rows
		self.directions = [[[False, False, False, False] for r in range(self.number_of_rows)] for c in range(self.number_of_columns)]
		self.generate_visited = [[False for r in range(self.number_of_rows)] for c in range(self.number_of_columns)]
		self.generate_connection(randint(0, self.number_of_columns - 1), randint(0, self.number_of_rows - 1))
		self.maze_string = ""
		for r in range(self.number_of_rows):
			for c in range(self.number_of_columns):
				if self.directions[c][r][0]:
					self.maze_string += "+   "
				else:
					self.maze_string += "+---"
			self.maze_string += "+\n"
			for c in range(self.number_of_columns):
				if self.directions[c][r][3]:
					self.maze_string += "    "
				else:
					self.maze_string += "|   "
			self.maze_string += "|\n"
		for c in range(self.number_of_columns):
			self.maze_string += "+---"
		self.maze_string += "+\n"
		self.visited = [[False for r in range(self.number_of_rows)] for c in range(self.number_of_columns)]
		self.visited[0][0] = True
		self.current_position = [0, 0]
		self.maze_string_array = self.maze_string.split('\n')
		visible_string = ""
		for r in range(self.number_of_rows):
			for c in range(self.number_of_columns):
				visible_string += "+---"
			visible_string += "+\n"
			for c in range(self.number_of_columns):
				visible_string += "| X "
			visible_string += "|\n"
		for c in range(self.number_of_columns):
			visible_string += "+---"
		visible_string += "+\n"
		self.visible_string_array = visible_string.split('\n')
		for r in range(3):
			self.visible_string_array[r] = self.maze_string_array[r][:5] + self.visible_string_array[r][5:]
		self.visible_string_array[1] = self.visible_string_array[1][:2] + 'I' + self.visible_string_array[1][3:]
		self.visible_string_array[2 * self.number_of_rows - 1] = self.visible_string_array[2 * self.number_of_rows - 1][:4 * self.number_of_columns - 2] + 'E' + self.visible_string_array[2 * self.number_of_rows - 1][4 * self.number_of_columns - 1:]

	def __repr__(self):
		return self.maze_string

	def move(self, direction):
		if direction.lower() == 'n':
			if not self.directions[self.current_position[0]][self.current_position[1]][0]:
				return False
			else:
				self.visible_string_array[2 * self.current_position[1] + 1] = self.visible_string_array[2 * self.current_position[1] + 1][:4 * self.current_position[0] + 2] + " " + self.visible_string_array[2 * self.current_position[1] + 1][4 * self.current_position[0] + 3:]
				self.current_position = [self.current_position[0], self.current_position[1] - 1]
		elif direction.lower() == 'e':
			if not self.directions[self.current_position[0]][self.current_position[1]][1]:
				return False
			else:
				self.visible_string_array[2 * self.current_position[1] + 1] = self.visible_string_array[2 * self.current_position[1] + 1][:4 * self.current_position[0] + 2] + " " + self.visible_string_array[2 * self.current_position[1] + 1][4 * self.current_position[0] + 3:]
				self.current_position = [self.current_position[0] + 1, self.current_position[1]]
		elif direction.lower() == 's':
			if not self.directions[self.current_position[0]][self.current_position[1]][2]:
				return False
			else:
				self.visible_string_array[2 * self.current_position[1] + 1] = self.visible_string_array[2 * self.current_position[1] + 1][:4 * self.current_position[0] + 2] + " " + self.visible_string_array[2 * self.current_position[1] + 1][4 * self.current_position[0] + 3:]
				self.current_position = [self.current_position[0], self.current_position[1] + 1]
		elif direction.lower() == 'w':
			if not self.directions[self.current_position[0]][self.current_position[1]][3]:
				return False
			else:
				self.visible_string_array[2 * self.current_position[1] + 1] = self.visible_string_array[2 * self.current_position[1] + 1][:4 * self.current_position[0] + 2] + " " + self.visible_string_array[2 * self.current_position[1] + 1][4 * self.current_position[0] + 3:]
				self.current_position = [self.current_position[0] - 1, self.current_position[1]]
		else:
			return False
		self.visited[self.current_position[0]][self.current_position[1]] = True
		for r in range(3):
			self.visible_string_array[2 * self.current_position[1] + r] = self.visible_string_array[2 * self.current_position[1] + r][:4 * self.current_position[0]] + self.maze_string_array[2 * self.current_position[1] + r][4 * self.current_position[0]:4 * self.current_position[0] + 5] + self.visible_string_array[2 * self.current_position[1] + r][4 * self.current_position[0] + 5:]
		self.visible_string_array[2 * self.current_position[1] + 1] = self.visible_string_array[2 * self.current_position[1] + 1][:4 * self.current_position[0] + 2] + "I" + self.visible_string_array[2 * self.current_position[1] + 1][4 * self.current_position[0] + 3:]
		return True

	def print_visible(self):
		return '\n'.join(self.visible_string_array)
	
	def reached_end(self):
		if self.current_position[0] == self.number_of_columns - 1 and self.current_position[1] == self.number_of_rows - 1:
			return True
		else:
			return False
	
	'''
	def test_print(self):
		maze_print = [["" for r in range(self.number_of_rows)] for c in range(self.number_of_columns)]
		for c in range(self.number_of_columns):
			for r in range(self.number_of_rows):
				if self.directions[c][r][0]:
					maze_print[c][r] += "N"
				if self.directions[c][r][1]:
					maze_print[c][r] += "E"
				if self.directions[c][r][2]:
					maze_print[c][r] += "S"
				if self.directions[c][r][3]:
					maze_print[c][r] += "W"
		return zip(*maze_print)
	'''
	# def __str__(self):

	def generate_connection(self, c, r):
		self.generate_visited[c][r] = True
		directions = [[0, -1], [1, 0], [0, 1], [-1, 0]]
		shuffle(directions)
		for direction in directions:
			if 0 <= c + direction[0] < self.number_of_columns and 0 <= r + direction[1] < self.number_of_rows and not self.generate_visited[c + direction[0]][r + direction[1]]:
				if direction[0] == 0 and direction[1] == -1:
					self.directions[c][r][0] = True
					self.directions[c][r - 1][2] = True
				elif direction[0] == 1 and direction[1] == 0:
					self.directions[c][r][1] = True
					self.directions[c + 1][r][3] = True
				elif direction[0] == 0 and direction[1] == 1:
					self.directions[c][r][2] = True
					self.directions[c][r + 1][0] = True
				elif direction[0] == -1 and direction[1] == 0:
					self.directions[c][r][3] = True
					self.directions[c - 1][r][1] = True
				self.generate_connection(c + direction[0], r + direction[1])
