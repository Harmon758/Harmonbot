
from random import shuffle, randint

class maze:

	def __init__(self, columns, rows, random_start = False, random_end = False):
		self.columns = 2 if columns < 2 else 100 if columns > 100 else columns
		self.rows = 2 if rows < 2 else 100 if rows > 100 else rows
		self.random_start = random_start
		self.random_end = random_end
		self.move_counter = 0
		
		self.directions = [[[False] * 4 for r in range(self.rows)] for c in range(self.columns)]
		self.generate_visited = [[False for r in range(self.rows)] for c in range(self.columns)]
		self.generate_connection(randint(0, self.columns - 1), randint(0, self.rows - 1))
		
		# self.visited = [[False for r in range(self.rows)] for c in range(self.columns)]
		if not self.random_start:
			self.column = 0
			self.row = 0
		else:
			self.column = randint(0, self.columns - 1)
			self.row = randint(0, self.rows - 1)
		# self.visited[self.column][self.row] = True
		if self.random_end:
			self.e_column = randint(0, self.columns - 1)
			self.e_row = randint(0, self.rows - 1)
		
		self.maze_string = ""
		for r in range(self.rows):
			for c in range(self.columns):
				if self.directions[c][r][0]:
					self.maze_string += "+   "
				else:
					self.maze_string += "+---"
			self.maze_string += "+\n"
			for c in range(self.columns):
				if self.directions[c][r][3]:
					self.maze_string += "    "
				else:
					self.maze_string += "|   "
			self.maze_string += "|\n"
		self.maze_string += "+---" * self.columns + "+\n"
		self.maze_string_array = self.maze_string.split('\n')
		
		self.visible = [None] * (2 * self.rows + 1)
		self.visible[::2] = ["+---" * self.columns + "+"] * (self.rows + 1)
		self.visible[1::2] = ["| X " * self.columns + "|"] * self.rows
		if not self.random_start:
			for r in range(3):
				self.visible[r] = self.maze_string_array[r][:5] + self.visible[r][5:]
			self.visible[1] = self.visible[1][:2] + 'I' + self.visible[1][3:]
		else:
			for r in range(2 * self.row, 2 * self.row + 3):
				self.visible[r] = self.visible[r][:self.column * 4] + self.maze_string_array[r][self.column * 4:self.column * 4 + 5] + self.visible[r][self.column * 4 + 5:]
			self.visible[2 * self.row + 1] = self.visible[2 * self.row + 1][:self.column * 4 + 2] + 'I' + self.visible[2 * self.row + 1][4 * self.column + 3:]
		if not self.random_end:
			self.visible[2 * self.rows - 1] = self.visible[2 * self.rows - 1][:4 * self.columns - 2] + 'E' + self.visible[2 * self.rows - 1][4 * self.columns - 1:]
		else:
			self.visible[2 * self.e_row + 1] = self.visible[2 * self.e_row + 1][:self.e_column * 4 + 2] + 'E' + self.visible[2 * self.e_row + 1][4 * self.e_column + 3:]

	def __repr__(self):
		return self.maze_string

	def move(self, direction):
		if direction.lower() == 'n':
			if not self.directions[self.column][self.row][0]:
				return False
			else:
				self.visible[2 * self.row + 1] = self.visible[2 * self.row + 1][:4 * self.column + 2] + " " + self.visible[2 * self.row + 1][4 * self.column + 3:]
				self.row -= 1
		elif direction.lower() == 'e':
			if not self.directions[self.column][self.row][1]:
				return False
			else:
				self.visible[2 * self.row + 1] = self.visible[2 * self.row + 1][:4 * self.column + 2] + " " + self.visible[2 * self.row + 1][4 * self.column + 3:]
				self.column += 1
		elif direction.lower() == 's':
			if not self.directions[self.column][self.row][2]:
				return False
			else:
				self.visible[2 * self.row + 1] = self.visible[2 * self.row + 1][:4 * self.column + 2] + " " + self.visible[2 * self.row + 1][4 * self.column + 3:]
				self.row += 1
		elif direction.lower() == 'w':
			if not self.directions[self.column][self.row][3]:
				return False
			else:
				self.visible[2 * self.row + 1] = self.visible[2 * self.row + 1][:4 * self.column + 2] + " " + self.visible[2 * self.row + 1][4 * self.column + 3:]
				self.column -= 1
		else:
			return False
		# self.visited[self.column][self.row] = True
		self.move_counter += 1
		for r in range(3):
			self.visible[2 * self.row + r] = self.visible[2 * self.row + r][:4 * self.column] + self.maze_string_array[2 * self.row + r][4 * self.column:4 * self.column + 5] + self.visible[2 * self.row + r][4 * self.column + 5:]
		self.visible[2 * self.row + 1] = self.visible[2 * self.row + 1][:4 * self.column + 2] + "I" + self.visible[2 * self.row + 1][4 * self.column + 3:]
		return True

	def print_visible(self):
		if self.rows <= 10 and self.columns <= 10:
			return '\n'.join(self.visible)
		start_row = 10 * (self.row // 10)
		start_column = 10 * (self.column // 10)
		visible = self.visible[2 * start_row:2 * start_row + 21]
		for row in range(len(visible)):
			visible[row] = visible[row][4 * start_column:4 * start_column + 41]
		return '\n'.join(visible)
	
	def reached_end(self):
		if not self.random_end:
			return (self.column == self.columns - 1 and self.row == self.rows - 1)
		else:
			return self.column == self.e_column and self.row == self.e_row
	
	'''
	def test_print(self):
		maze_print = [["" for r in range(self.rows)] for c in range(self.columns)]
		for c in range(self.columns):
			for r in range(self.rows):
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
			if 0 <= c + direction[0] < self.columns and 0 <= r + direction[1] < self.rows and not self.generate_visited[c + direction[0]][r + direction[1]]:
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
