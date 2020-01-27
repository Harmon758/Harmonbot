
import discord
from discord.ext import commands, menus

from enum import IntEnum
import io
import random
import sys

from utilities import checks
from utilities.menu import Menu

# Necessary for maze generation
sys.setrecursionlimit(5000)

def setup(bot):
	bot.add_cog(MazeCog())

class Direction(IntEnum):
	UP = 0
	RIGHT = 1
	DOWN = 2
	LEFT = 3

class Maze:
	
	def __init__(self, columns, rows, random_start = False, random_end = False):
		self.columns = 2 if columns < 2 else 80 if columns > 80 else columns
		self.rows = 2 if rows < 2 else 80 if rows > 80 else rows
		# TODO: optimize generation algorithm?, previous upper limit of 100x100
		self.random_start = random_start
		self.random_end = random_end
		self.move_counter = 0
		
		self.directions = [[[False] * 4 for r in range(self.rows)] for c in range(self.columns)]
		self.generate_visited = [[False for r in range(self.rows)] for c in range(self.columns)]
		self.generate_connection(random.randint(0, self.columns - 1), random.randint(0, self.rows - 1))
		
		# self.visited = [[False for r in range(self.rows)] for c in range(self.columns)]
		if not self.random_start:
			self.column = 0
			self.row = 0
		else:
			self.column = random.randint(0, self.columns - 1)
			self.row = random.randint(0, self.rows - 1)
		# self.visited[self.column][self.row] = True
		if self.random_end:
			self.e_column = random.randint(0, self.columns - 1)
			self.e_row = random.randint(0, self.rows - 1)
		
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
		# Tuple of connection directions for each cell:
		# return str(
		# 	tuple(
		# 		tuple(
		# 			tuple(
		# 				filter(
		# 					None, (
		# 						direction.name if self.directions[column][row][direction] else None
		# 						for direction in Direction
		# 					)
		# 				)
		# 			) for column in range(self.columns)
		# 		) for row in range(self.rows)
		# 	)
		# )
		# Grid of first letter of connection directions:
		# return (
		# 	'\n'.join(
		# 		"".join(
		# 			"".join(
		# 				direction.name[0] if self.directions[column][row][direction] else ""
		# 				for direction in Direction
		# 			).ljust(5, ' ') for column in range(self.columns)
		# 		) for row in range(self.rows)
		# 	)
		# )
	
	def __str__(self):
		if self.rows <= 10 and self.columns <= 10:
			return '\n'.join(self.visible)
		start_row = self.row - self.row % 10
		start_column = self.column - self.column % 10
		visible = self.visible[2 * start_row:2 * start_row + 21]
		for row_number, row in enumerate(visible):
			visible[row_number] = row[4 * start_column:4 * start_column + 41]
		return '\n'.join(visible)
	
	def generate_connection(self, c, r):
		'''Generate connections for the maze'''
		self.generate_visited[c][r] = True
		for horizontal, vertical in random.sample(((-1, 0), (0, -1), (0, 1), (1, 0)), 4):
			if not (0 <= c + horizontal < self.columns and 0 <= r + vertical < self.rows):
				continue
			if self.generate_visited[c + horizontal][r + vertical]:
				continue
			if horizontal == 0 and vertical == -1:
				self.directions[c][r][Direction.UP] = True
				self.directions[c][r - 1][Direction.DOWN] = True
			elif horizontal == 1 and vertical == 0:
				self.directions[c][r][Direction.RIGHT] = True
				self.directions[c + 1][r][Direction.LEFT] = True
			elif horizontal == 0 and vertical == 1:
				self.directions[c][r][Direction.DOWN] = True
				self.directions[c][r + 1][Direction.UP] = True
			elif horizontal == -1 and vertical == 0:
				self.directions[c][r][Direction.LEFT] = True
				self.directions[c - 1][r][Direction.RIGHT] = True
			self.generate_connection(c + horizontal, r + vertical)
	
	def move(self, direction):
		'''Move inside the maze'''
		if not isinstance(direction, Direction) or not self.directions[self.column][self.row][direction]:
			return False
		
		self.visible[2 * self.row + 1] = self.visible[2 * self.row + 1][:4 * self.column + 2] + " " + self.visible[2 * self.row + 1][4 * self.column + 3:]
		if direction is Direction.UP:
			self.row -= 1
		elif direction is Direction.RIGHT:
			self.column += 1
		elif direction is direction.DOWN:
			self.row += 1
		elif direction is direction.LEFT:
			self.column -= 1
		
		# self.visited[self.column][self.row] = True
		self.move_counter += 1
		for r in range(3):
			self.visible[2 * self.row + r] = self.visible[2 * self.row + r][:4 * self.column] + self.maze_string_array[2 * self.row + r][4 * self.column:4 * self.column + 5] + self.visible[2 * self.row + r][4 * self.column + 5:]
		self.visible[2 * self.row + 1] = self.visible[2 * self.row + 1][:4 * self.column + 2] + "I" + self.visible[2 * self.row + 1][4 * self.column + 3:]
		return True
	
	def reached_end(self):
		if not self.random_end:
			return (self.column == self.columns - 1 and self.row == self.rows - 1)
		else:
			return self.column == self.e_column and self.row == self.e_row

class MazeCog(commands.Cog, name = "Maze"):
	
	def __init__(self):
		self.mazes = {}
		self.move_mapping = {'w': Direction.UP, 'a': Direction.LEFT, 's': Direction.DOWN, 'd': Direction.RIGHT, 
								"up": Direction.UP, "left": Direction.LEFT, "down": Direction.DOWN, "right": Direction.RIGHT}
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	async def maze(self, ctx):
		'''
		Maze game
		[w, a, s, d] or [up, left, down, right] to move
		'''
		await ctx.send_help(ctx.command)
	
	# TODO: Use max concurrency
	@maze.command(aliases = ["begin"])
	async def start(self, ctx, width: int = 5, height: int = 5, random_start: bool = False, random_end: bool = False):
		'''
		Start a maze game
		width: 2 - 80
		height: 2 - 80
		'''
		# TODO: Add option to restrict to command invoker
		if ctx.channel.id in self.mazes:
			return await ctx.embed_reply(":no_entry: There's already a maze game going on")
		self.mazes[ctx.channel.id] = Maze(width, height, random_start = random_start, random_end = random_end)
		maze_instance = self.mazes[ctx.channel.id]
		maze_message = await ctx.embed_reply(ctx.bot.CODE_BLOCK.format(str(maze_instance)))
		while not maze_instance.reached_end():
			move = await ctx.bot.wait_for("message", check = lambda message: message.content.lower() in self.move_mapping.keys() and message.channel == ctx.channel)
			# author = ctx.author
			moved = maze_instance.move(self.move_mapping[move.content.lower()])
			response = ctx.bot.CODE_BLOCK.format(str(maze_instance))
			if not moved:
				response += "\n:no_entry: You can't go that way"
			new_maze_message = await ctx.embed_reply(response)
			await ctx.bot.attempt_delete_message(move)
			await ctx.bot.attempt_delete_message(maze_message)
			maze_message = new_maze_message
		embed = maze_message.embeds[0]
		embed.description += f"\nCongratulations! You reached the end of the maze in {maze_instance.move_counter} moves"
		await maze_message.edit(embed = embed)
		del self.mazes[ctx.channel.id]
	
	@maze.command()
	async def current(self, ctx):
		'''Current maze game'''
		if ctx.channel.id in self.mazes:
			await ctx.embed_reply(ctx.bot.CODE_BLOCK.format(str(self.mazes[ctx.channel.id])))
		else:
			await ctx.embed_reply(":no_entry: There's no maze game currently going on")
	
	@maze.command(aliases = ['m', "menus", 'r', "reaction", "reactions"])
	async def menu(self, ctx, width: int = 5, height: int = 5, random_start: bool = False, random_end: bool = False):
		'''
		Maze game menu
		width: 2 - 80
		height: 2 - 80
		React with an arrow key to move
		'''
		await MazeMenu(width, height, random_start, random_end).start(ctx)
	
	# TODO: maze print, position?, stats

class MazeMenu(Menu):
	
	def __init__(self, width, height, random_start, random_end):
		super().__init__(timeout = None, clear_reactions_after = True, check_embeds = True)
		self.maze = Maze(width, height, random_start, random_end)
		self.arrows = {'\N{LEFTWARDS BLACK ARROW}': Direction.LEFT, '\N{UPWARDS BLACK ARROW}': Direction.UP, 
						'\N{DOWNWARDS BLACK ARROW}': Direction.DOWN, '\N{BLACK RIGHTWARDS ARROW}': Direction.RIGHT}
		for number, emoji in enumerate(self.arrows.keys(), start = 1):
			self.add_button(menus.Button(emoji, self.on_direction, position = number))
	
	async def send_initial_message(self, ctx, channel):
		return await ctx.embed_reply(ctx.bot.CODE_BLOCK.format(str(self.maze)), 
										footer_text = f"Your current position: {self.maze.column + 1}, {self.maze.row + 1}")
	
	async def on_direction(self, payload):
		embed = self.message.embeds[0]
		if not self.maze.move(self.arrows[str(payload.emoji)]):
			embed.description = (self.bot.CODE_BLOCK.format(str(self.maze))
									+ "\n:no_entry: You can't go that way")
		elif self.maze.reached_end():
			embed.description = (self.bot.CODE_BLOCK.format(str(self.maze))
									+ f"\nCongratulations! You reached the end of the maze in {self.maze.move_counter} moves")
			self.stop()
		else:
			embed.description = self.bot.CODE_BLOCK.format(str(self.maze))
		embed.set_footer(text = f"Your current position: {self.maze.column + 1}, {self.maze.row + 1}")
		await self.message.edit(embed = embed)
	
	@menus.button("\N{PRINTER}", position = 5, lock = False)
	async def on_printer(self, payload):
		await self.message.channel.send(content = f"{self.ctx.author.display_name}:\n"
													"Your maze is attached", 
										file = discord.File(io.BytesIO(('\n'.join(self.maze.visible)).encode()), 
															filename = "maze.txt"))

