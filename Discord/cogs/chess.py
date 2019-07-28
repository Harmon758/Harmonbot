
import discord
from discord.ext import commands

import asyncio
import random

import chess.pgn

from modules.chess import ChessMatch
from modules import utilities
from utilities import checks

def setup(bot):
	bot.add_cog(Chess(bot))

class Chess(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.matches = []
	
	def cog_check(self, ctx):
		return checks.not_forbidden_predicate(ctx)
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	async def chess(self, ctx):
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
					await ctx.embed_reply(":no_entry: Invalid move")
					return
			await self._update_chess_board_embed()
		'''
	
	@chess.command(aliases = ["start"])
	async def play(self, ctx, *, opponent : str = ""):
		'''
		Challenge someone to a match
		You can play me as well
		'''
		# check if already playing a match in this channel
		if self.get_match(ctx.channel, ctx.author):
			await ctx.embed_reply(":no_entry: You're already playing a chess match here")
			return
		# prompt for opponent
		if not opponent:
			await ctx.embed_reply("Who would you like to play?")
			message = await self.bot.wait_for("message", check = lambda m: m.author == ctx.author and m.channel == ctx.channel)
			opponent = message.content
		color = None
		if opponent.lower() in ("harmonbot", "you"):
			opponent = self.bot.user
		elif opponent.lower() in ("myself", "me"):
			opponent = ctx.author
			color = 'w'
		else:
			opponent = await utilities.get_user(ctx, opponent)
			if not opponent:
				await ctx.embed_reply(":no_entry: Opponent not found")
				return
		# check if opponent already playing a match in this channel
		if opponent != self.bot.user and self.get_match(ctx.channel, opponent):
			await ctx.embed_reply(":no_entry: Your chosen opponent is playing a chess match here")
			return
		# prompt for color
		if opponent == ctx.author:
			color = 'w'
		if not color:
			await ctx.embed_reply("Would you like to play white, black, or random?")
			message = await self.bot.wait_for("message", check = lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ("white", "black", "random", 'w', 'b', 'r'))
			color = message.content.lower()
		if color in ("random", 'r'):
			color = random.choice(('w', 'b'))
		if color in ("white", 'w'):
			white_player = ctx.author
			black_player = opponent
		elif color in ("black", 'b'):
			white_player = opponent
			black_player = ctx.author
		# prompt opponent
		if opponent != self.bot.user and opponent != ctx.author:
			await ctx.send("{}: {} has challenged you to a chess match\nWould you like to accept? Yes/No".format(opponent.mention, ctx.author))
			try:
				message = await self.bot.wait_for("message", check = lambda m: m.author == opponent and m.channel == ctx.channel and m.content.lower() in ("yes", "no", 'y', 'n'), timeout = 300)
			except asyncio.TimeoutError:
				await ctx.send("{}: {} has declined your challenge".format(ctx.author.mention, opponent))
				return
			if message.content.lower() in ("no", 'n'):
				await ctx.send("{}: {} has declined your challenge".format(ctx.author.mention, opponent))
				return
		match = await ChessMatch.start(ctx, white_player, black_player)
		self.matches.append(match)
	
	def get_match(self, text_channel, player):
		return discord.utils.find(lambda match: match.ctx.channel == text_channel and (match.white_player == player or match.black_player == player), self.matches)
	
	# TODO: Handle matches in DMs
	# TODO: Handle end of match: check mate, draw, etc.
	
	@chess.group(aliases = ["match"], invoke_without_command = True, case_insensitive = True)
	async def board(self, ctx):
		'''Current match/board'''
		match = self.get_match(ctx.channel, ctx.author)
		if not match:
			await ctx.embed_reply(":no_entry: Chess match not found")
			return
		await match.new_match_embed()
	
	@board.command(name = "text")
	async def board_text(self, ctx):
		'''Text version of the current board'''
		match = self.get_match(ctx.channel, ctx.author)
		if not match:
			await ctx.embed_reply(":no_entry: Chess match not found")
			return
		await ctx.reply(ctx.bot.CODE_BLOCK.format(match))
	
	@chess.command()
	async def fen(self, ctx):
		'''FEN of the current board'''
		match = self.get_match(ctx.channel, ctx.author)
		if not match:
			await ctx.embed_reply(":no_entry: Chess match not found")
			return
		await ctx.embed_reply(match.fen())
	
	@chess.command(hidden = True)
	async def pgn(self, ctx):
		'''PGN of the current game'''
		match = self.get_match(ctx.channel, ctx.author)
		if not match:
			await ctx.embed_reply(":no_entry: Chess match not found")
			return
		await ctx.embed_reply(chess.pgn.Game.from_board(match))
	
	@chess.command(hidden = True)
	async def turn(self, ctx):
		'''Who's turn it is to move'''
		match = self.get_match(ctx.channel, ctx.author)
		if not match:
			await ctx.embed_reply(":no_entry: Chess match not found")
			return
		if match.turn:
			await ctx.embed_reply("It's white's turn to move")
		else:
			await ctx.embed_reply("It's black's turn to move")
	
	"""
	@chess.command()
	async def reset(self, ctx):
		'''Reset the board'''
		self._chess_board.reset()
		await ctx.embed_reply("The board has been reset")
	"""
	
	"""
	@chess.command()
	async def undo(self, ctx):
		'''Undo the previous move'''
		try:
			self._chess_board.pop()
			await self._display_chess_board(ctx, message = "The previous move was undone")
		except IndexError:
			await ctx.embed_reply(":no_entry: There are no more moves to undo")
	"""
	
	@chess.command(aliases = ["last"], hidden = True)
	async def previous(self, ctx):
		'''Previous move'''
		match = self.get_match(ctx.channel, ctx.author)
		if not match:
			await ctx.embed_reply(":no_entry: Chess match not found")
			return
		try:
			await ctx.embed_reply(match.peek())
		except IndexError:
			await ctx.embed_reply(":no_entry: There was no previous move")
	
	"""
	@chess.command(name = "(╯°□°）╯︵", hidden = True)
	async def flip(self, ctx):
		'''Flip the table over'''
		self._chess_board.clear()
		await ctx.say(ctx.author.name + " flipped the table over in anger!")
	"""

