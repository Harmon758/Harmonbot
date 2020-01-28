
import discord
from discord.ext import commands, menus

from enum import IntEnum
import io
import random

from utilities import checks
from utilities.menu import Menu

def setup(bot):
	bot.add_cog(MazeCog())

class Direction(IntEnum):
	UP = 0
	RIGHT = 1
	DOWN = 2
	LEFT = 3
	
	@property
	def reverse(self):
		return {self.UP: self.DOWN, self.LEFT: self.RIGHT, self.DOWN: self.UP, self.RIGHT: self.LEFT}[self]
	
	@property
	def vector(self):
		# (-y, x) to match vertical, horizontal / row, column
		return {self.UP: (-1, 0), self.RIGHT: (0, 1), self.DOWN: (1, 0), self.LEFT: (0, -1)}[self]

class Maze:
	
	def __init__(self, rows, columns, random_start = False, random_end = False):
		self.rows = min(max(2, rows), 100)
		self.columns = min(max(2, columns), 100)
		self.move_counter = 0
		
		# Generate connections
		self.connections = [[[False] * 4 for column in range(self.columns)] for row in range(self.rows)]
		visited = [[False] * self.columns for row in range(self.rows)]
		to_visit = [(random.randint(0, self.rows - 1), random.randint(0, self.columns - 1))]
		while to_visit:
			row, column = to_visit[-1]
			visited[row][column] = True
			for direction in random.sample(tuple(Direction), 4):
				vertical, horizontal = direction.vector
				new_row, new_column = row + vertical, column + horizontal
				if not (0 <= new_row < self.rows and 0 <= new_column < self.columns):
					continue
				if visited[new_row][new_column]:
					continue
				self.connections[row][column][direction] = True
				self.connections[new_row][new_column][direction.reverse] = True
				to_visit.append((new_row, new_column))
				break
			else:
				to_visit.pop()
		
		# self.visited = [[False] * self.columns for row in range(self.rows)]
		if random_start:
			self.row = random.randint(0, self.rows - 1)
			self.column = random.randint(0, self.columns - 1)
		else:
			self.row = 0
			self.column = 0
		# self.visited[self.row][self.column] = True
		if random_end:
			self.end_row = random.randint(0, self.rows - 1)
			self.end_column = random.randint(0, self.columns - 1)
		else:
			self.end_row = self.rows - 1
			self.end_column = self.columns - 1
		
		self.string = ""
		for row in range(self.rows):
			for column in range(self.columns):
				if self.connections[row][column][Direction.UP]:
					self.string += "+   "
				else:
					self.string += "+---"
			self.string += "+\n"
			for column in range(self.columns):
				if self.connections[row][column][Direction.LEFT]:
					self.string += "    "
				else:
					self.string += "|   "
			self.string += "|\n"
		self.string += "+---" * self.columns + "+\n"
		self.row_strings = self.string.split('\n')
		
		self.visible = [None] * (2 * self.rows + 1)
		self.visible[::2] = ["+---" * self.columns + '+'] * (self.rows + 1)
		self.visible[1::2] = ["| X " * self.columns + '|'] * self.rows
		self.update_visible()
		row_offset = 2 * self.end_row + 1
		column_offset = 4 * self.end_column + 2
		self.visible[row_offset] = self.visible[row_offset][:column_offset] + 'E' + self.visible[row_offset][column_offset + 1:]
	
	def __repr__(self):
		return self.string
		# Tuple of connection directions for each cell:
		# return str(
		# 	tuple(
		# 		tuple(
		# 			tuple(
		# 				filter(
		# 					None, (
		# 						direction.name if self.connections[row][column][direction] else None
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
		# 				direction.name[0] if self.connections[row][column][direction] else ""
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
	
	def update_visible(self):
		row_offset = 2 * self.row
		column_offset = 4 * self.column
		for row in range(row_offset, row_offset + 3):
			self.visible[row] = self.visible[row][:column_offset] + self.row_strings[row][column_offset:column_offset + 5] + self.visible[row][column_offset + 5:]
		row_offset += 1
		column_offset += 2
		self.visible[row_offset] = self.visible[row_offset][:column_offset] + 'I' + self.visible[row_offset][column_offset + 1:]
	
	def move(self, direction):
		'''Move inside the maze'''
		if not isinstance(direction, Direction) or not self.connections[self.row][self.column][direction]:
			return False
		
		row_offset = 2 * self.row + 1
		column_offset = 4 * self.column + 2
		self.visible[row_offset] = self.visible[row_offset][:column_offset] + ' ' + self.visible[row_offset][column_offset + 1:]
		if direction is Direction.UP:
			self.row -= 1
		elif direction is Direction.RIGHT:
			self.column += 1
		elif direction is direction.DOWN:
			self.row += 1
		elif direction is direction.LEFT:
			self.column -= 1
		
		# self.visited[self.row][self.column] = True
		self.move_counter += 1
		self.update_visible()
		return True
	
	@property
	def reached_end(self):
		return self.row == self.end_row and self.column == self.end_column

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
	async def start(self, ctx, height: int = 5, width: int = 5, random_start: bool = False, random_end: bool = False):
		'''
		Start a maze game
		height: 2 - 100
		width: 2 - 100
		'''
		# TODO: Add option to restrict to command invoker
		if ctx.channel.id in self.mazes:
			return await ctx.embed_reply(":no_entry: There's already a maze game going on")
		self.mazes[ctx.channel.id] = maze = Maze(height, width, random_start = random_start, random_end = random_end)
		message = await ctx.embed_reply(ctx.bot.CODE_BLOCK.format(str(maze)), 
										footer_text = f"Your current position: {maze.column + 1}, {maze.row + 1}")
		reached_end = False
		while not reached_end:
			move = await ctx.bot.wait_for(
				"message", 
				check = lambda message: 
					message.channel == ctx.channel and message.content.lower() in self.move_mapping.keys()
					# author = ctx.author
			)
			moved = maze.move(self.move_mapping[move.content.lower()])
			response = ctx.bot.CODE_BLOCK.format(str(maze))
			if not moved:
				response += "\n:no_entry: You can't go that way"
			elif (reached_end := maze.reached_end):
				response += f"\nCongratulations! You reached the end of the maze in {maze.move_counter} moves"
			new_message = await ctx.embed_reply(response, 
												footer_text = f"Your current position: {maze.column + 1}, {maze.row + 1}")
			await ctx.bot.attempt_delete_message(move)
			await ctx.bot.attempt_delete_message(message)
			message = new_message
		del self.mazes[ctx.channel.id]
	
	@maze.command()
	async def current(self, ctx):
		'''Current maze game'''
		if maze := self.mazes.get(ctx.channel.id):
			await ctx.embed_reply(ctx.bot.CODE_BLOCK.format(str(maze)))
		else:
			await ctx.embed_reply(":no_entry: There's no maze game currently going on")
	
	@maze.command(aliases = ["print"])
	async def file(self, ctx):
		if maze := self.mazes.get(ctx.channel.id):
			await ctx.reply("Your maze is attached", 
							file = discord.File(io.BytesIO(('\n'.join(maze.visible)).encode()), 
												filename = "maze.txt"))
		else:
			await ctx.embed_reply(":no_entry: There's no maze game currently going on")
	
	@maze.command(aliases = ['m', "menus", 'r', "reaction", "reactions"])
	async def menu(self, ctx, height: int = 5, width: int = 5, random_start: bool = False, random_end: bool = False):
		'''
		Maze game menu
		height: 2 - 100
		width: 2 - 100
		React with an arrow key to move
		'''
		await MazeMenu(height, width, random_start, random_end).start(ctx)
	
	# TODO: maze stats

class MazeMenu(Menu):
	
	def __init__(self, height, width, random_start, random_end):
		super().__init__(timeout = None, clear_reactions_after = True, check_embeds = True)
		self.maze = Maze(height, width, random_start, random_end)
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
		elif self.maze.reached_end:
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

