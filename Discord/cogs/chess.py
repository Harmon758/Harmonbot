
import discord
from discord.ext import commands

import asyncio
import datetime
import io
import random
import subprocess
from typing import Union

import chess
import chess.engine
import chess.pgn
import chess.svg
import cpuinfo
try:
	from wand.image import Image
except ImportError as e:
	print(f"Failed to import Wand in Chess cog:\n{e}")

from utilities import checks

# TODO: Dynamically load chess engine not locked to version?
STOCKFISH_EXECUTABLE = "stockfish_20011801_x64"
try:
	CPUID = cpuinfo.CPUID()
	CPU_FLAGS = CPUID.get_flags(CPUID.get_max_extension_support())
	if "bmi2" in CPU_FLAGS:
		STOCKFISH_EXECUTABLE += "_bmi2"
	elif "popcnt" in CPU_FLAGS:
		STOCKFISH_EXECUTABLE += "_modern"
	# BMI2 > modern (POPCNT) > neither
	# http://blog.abrok.eu/stockfish-dev-builds-faq/
	# https://github.com/glinscott/fishtest/wiki/Building-stockfish-on-Windows
	# https://en.wikipedia.org/wiki/Bit_Manipulation_Instruction_Sets
	# https://en.wikipedia.org/wiki/List_of_Intel_CPU_microarchitectures
except:
	pass
STOCKFISH_EXECUTABLE += ".exe"

def setup(bot):
	bot.add_cog(ChessCog())

class ChessCog(commands.Cog, name = "Chess"):
	
	def __init__(self):
		self.matches = []
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	def cog_unload(self):
		# TODO: Persistence - store running chess matches and add way to continue previous ones
		for match in self.matches:
			match.task.cancel()
	
	@commands.group(name = "chess", invoke_without_command = True, case_insensitive = True)
	async def chess_command(self, ctx):
		'''
		Play chess
		Supports standard algebraic and UCI notation
		Example:
		 !chess play you
		 white
		 e2e4
		'''
		await ctx.send_help(ctx.command)
		'''
		else:
			try:
				self._chess_board.push_san(move)
			except ValueError:
				try:
					self._chess_board.push_uci(move)
				except ValueError:
					return await ctx.embed_reply(":no_entry: Invalid move")
			await self._update_chess_board_embed()
		'''
	
	# TODO: Use max concurrency?
	@chess_command.command(aliases = ["start"])
	async def play(self, ctx, *, opponent: Union[discord.Member, str]):
		'''
		Challenge someone to a match
		You can play me as well
		'''
		if self.get_match(ctx.channel, ctx.author):
			return await ctx.embed_reply(":no_entry: You're already playing a chess match here")
		color = None
		if type(opponent) is str:
			if opponent.lower() in ("harmonbot", "you"):
				opponent = ctx.bot.user
			elif opponent.lower() in ("myself", "me"):
				opponent = ctx.author
				color = 'w'
			else:
				return await ctx.embed_reply(":no_entry: Opponent not found")
		if opponent != ctx.bot.user and self.get_match(ctx.channel, opponent):
			return await ctx.embed_reply(":no_entry: Your chosen opponent is playing a chess match here")
		if opponent == ctx.author:
			color = 'w'
		if not color:
			await ctx.embed_reply("Would you like to play white, black, or random?")
			message = await ctx.bot.wait_for("message", 
												check = lambda message: message.author == ctx.author and 
																		message.channel == ctx.channel and 
																		message.content.lower() in ("white", "black", "random", 
																									'w', 'b', 'r'))
			color = message.content.lower()
		if color in ("random", 'r'):
			color = random.choice(('w', 'b'))
		if color in ("white", 'w'):
			white_player = ctx.author
			black_player = opponent
		elif color in ("black", 'b'):
			white_player = opponent
			black_player = ctx.author
		if opponent != ctx.bot.user and opponent != ctx.author:
			await ctx.send(f"{opponent.mention}: {ctx.author} has challenged you to a chess match\n"
							"Would you like to accept? Yes/No")
			try:
				message = await ctx.bot.wait_for("message", 
													check = lambda message: message.author == opponent and 
																			message.channel == ctx.channel and 
																			message.content.lower() in ("yes", "no", 'y', 'n'), 
													timeout = 300)
			except asyncio.TimeoutError:
				return await ctx.send(f"{ctx.author.mention}: {opponent} has declined your challenge")
			if message.content.lower() in ("no", 'n'):
				return await ctx.send(f"{ctx.author.mention}: {opponent} has declined your challenge")
		match = await ChessMatch.start(ctx, white_player, black_player)
		self.matches.append(match)
		await match.ended.wait()
		self.matches.remove(match)
	
	def get_match(self, text_channel, player):
		return discord.utils.find(lambda match: match.ctx.channel == text_channel and 
												(match.white_player == player or match.black_player == player), 
									self.matches)
	
	# TODO: Handle matches in DMs
	# TODO: Allow resignation
	# TODO: Allow draw offers
	
	@chess_command.group(aliases = ["match"], invoke_without_command = True, case_insensitive = True)
	async def board(self, ctx):
		'''Current match/board'''
		match = self.get_match(ctx.channel, ctx.author)
		if not match:
			return await ctx.embed_reply(":no_entry: Chess match not found")
		await match.new_match_embed()
	
	@board.command(name = "text")
	async def board_text(self, ctx):
		'''Text version of the current board'''
		match = self.get_match(ctx.channel, ctx.author)
		if not match:
			return await ctx.embed_reply(":no_entry: Chess match not found")
		await ctx.reply(ctx.bot.CODE_BLOCK.format(match))
	
	@chess_command.command()
	async def fen(self, ctx):
		'''FEN of the current board'''
		match = self.get_match(ctx.channel, ctx.author)
		if not match:
			return await ctx.embed_reply(":no_entry: Chess match not found")
		await ctx.embed_reply(match.fen())
	
	"""
	@chess_command.command(name = "(╯°□°）╯︵", hidden = True)
	async def flip(self, ctx):
		'''Flip the table over'''
		self._chess_board.clear()
		await ctx.say(ctx.author.name + " flipped the table over in anger!")
	"""
	
	@chess_command.command(hidden = True)
	async def pgn(self, ctx):
		'''PGN of the current game'''
		match = self.get_match(ctx.channel, ctx.author)
		if not match:
			return await ctx.embed_reply(":no_entry: Chess match not found")
		await ctx.embed_reply(chess.pgn.Game.from_board(match))
	
	@chess_command.command(aliases = ["last"], hidden = True)
	async def previous(self, ctx):
		'''Previous move'''
		match = self.get_match(ctx.channel, ctx.author)
		if not match:
			return await ctx.embed_reply(":no_entry: Chess match not found")
		try:
			await ctx.embed_reply(match.peek())
		except IndexError:
			await ctx.embed_reply(":no_entry: There was no previous move")
	
	"""
	@chess_command.command()
	async def reset(self, ctx):
		'''Reset the board'''
		self._chess_board.reset()
		await ctx.embed_reply("The board has been reset")
	"""
	
	@chess_command.command(hidden = True)
	async def turn(self, ctx):
		'''Who's turn it is to move'''
		match = self.get_match(ctx.channel, ctx.author)
		if not match:
			return await ctx.embed_reply(":no_entry: Chess match not found")
		if match.turn:
			await ctx.embed_reply("It's white's turn to move")
		else:
			await ctx.embed_reply("It's black's turn to move")
	
	"""
	@chess_command.command()
	async def undo(self, ctx):
		'''Undo the previous move'''
		try:
			self._chess_board.pop()
			await self._display_chess_board(ctx, message = "The previous move was undone")
		except IndexError:
			await ctx.embed_reply(":no_entry: There are no more moves to undo")
	"""

class ChessMatch(chess.Board):
	
	@classmethod
	async def start(cls, ctx, white_player, black_player):
		self = cls()
		self.ctx = ctx
		self.white_player = white_player
		self.black_player = black_player
		self.bot = ctx.bot
		self.ended = asyncio.Event()
		self.engine_transport, self.chess_engine = await chess.engine.popen_uci(f"bin/{STOCKFISH_EXECUTABLE}", 
																				creationflags = subprocess.CREATE_NO_WINDOW)
		self.match_message = None
		self.task = ctx.bot.loop.create_task(self.match_task(), name = "Chess Match")
		return self
	
	def make_move(self, move):
		try:
			self.push_san(move)
		except ValueError:
			try:
				self.push_uci(move)
			except ValueError:
				return False
		return True
	
	def valid_move(self, move):
		try:
			self.parse_san(move)
		except ValueError:
			try:
				self.parse_uci(move)
			except ValueError:
				return False
		return True
	
	async def match_task(self):
		self.match_message = await self.ctx.embed_send("Loading..")
		await self.update_match_embed()
		while not self.ended.is_set():
			player = [self.black_player, self.white_player][int(self.turn)]
			embed = self.match_message.embeds[0]
			if player == self.bot.user:
				await self.match_message.edit(embed = embed.set_footer(text = "I'm thinking.."))
				result = await self.chess_engine.play(self, chess.engine.Limit(time = 2))
				self.push(result.move)
				await self.update_match_embed(footer_text = f"I moved {result.move}")
			else:
				message = await self.bot.wait_for("message", 
													check = lambda msg: msg.author == player and 
																		msg.channel == self.ctx.channel and 
																		self.valid_move(msg.content))
				await self.match_message.edit(embed = embed.set_footer(text = "Processing move.."))
				self.make_move(message.content)
				if self.is_game_over():
					footer_text = discord.Embed.Empty
					self.ended.set()
				else:
					footer_text = f"It is {['black', 'white'][int(self.turn)]}'s ({[self.black_player, self.white_player][int(self.turn)]}'s) turn to move"
				await self.update_match_embed(footer_text = footer_text)
				await self.bot.attempt_delete_message(message)
	
	async def update_match_embed(self, *, flipped = None, footer_text = discord.Embed.Empty):
		if flipped is None:
			flipped = not self.turn
		if self.move_stack:
			lastmove = self.peek()
		else:
			lastmove = None
		if self.is_check():
			check = self.king(self.turn)
		else:
			check = None
		if self.match_message:
			embed = self.match_message.embeds[0]
		else:
			embed = discord.Embed(color = self.bot.bot_color)
		chess_pgn = chess.pgn.Game.from_board(self)
		chess_pgn.headers["Site"] = "Discord"
		chess_pgn.headers["Date"] = datetime.datetime.utcnow().strftime("%Y.%m.%d")
		chess_pgn.headers["White"] = self.white_player.mention
		chess_pgn.headers["Black"] = self.black_player.mention
		embed.description = str(chess_pgn)
		## svg = self._repr_svg_()
		svg = chess.svg.board(self, lastmove = lastmove, check = check, flipped = flipped)
		buffer = io.BytesIO()
		with Image(blob = svg.encode()) as image:
			image.format = "PNG"
			## image.save(filename = self.bot.data_path + "/temp/chess_board.png")
			image.save(file = buffer)
		buffer.seek(0)
		# TODO: Upload into embed + delete and re-send to update?
		## embed.set_image(url = self.bot.imgur_client.upload_from_path(self.bot.data_path + "/temp/chess_board.png")["link"])
		## embed.set_image(url = data["data"]["img_url"])
		image_message = await self.bot.cache_channel.send(file = discord.File(buffer, filename = "chess_board.png"))
		embed.set_image(url = image_message.attachments[0].url)
		embed.set_footer(text = footer_text)
		if self.match_message:
			await self.match_message.edit(embed = embed)
		else:
			self.match_message = await self.ctx.send(embed = embed)
	
	async def new_match_embed(self, *, flipped = None, footer_text = None):
		if flipped is None:
			flipped = not self.turn
		if footer_text is None:
			if self.is_game_over():
				footer_text = discord.Embed.Empty
			else:
				footer_text = f"It's {['black', 'white'][int(self.turn)]}'s ({[self.black_player, self.white_player][int(self.turn)]}'s) turn to move"
		if self.match_message:
			await self.match_message.delete()
		self.match_message = None
		await self.update_match_embed(flipped = flipped, footer_text = footer_text)

