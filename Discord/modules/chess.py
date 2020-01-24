
import discord

# import asyncio
import datetime
import io
import subprocess

import chess
import chess.engine
import chess.pgn
import chess.svg
import cpuinfo
from wand.image import Image

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

class ChessMatch(chess.Board):
	
	@classmethod
	async def start(cls, ctx, white_player, black_player):
		self = cls()
		self.ctx = ctx
		self.white_player = white_player
		self.black_player = black_player
		self.bot = ctx.bot
		# TODO: Dynamically load chess engine not locked to version?
		self.engine_transport, self.chess_engine = await chess.engine.popen_uci(f"bin/{STOCKFISH_EXECUTABLE}", 
																				creationflags = subprocess.CREATE_NO_WINDOW)
		self.match_message = None
		self.task = ctx.bot.loop.create_task(self.match_task(), name = "Chess Match")
		return self
	
	# TODO: Cancel task on deletion/bot shutdown
	
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
		while True:
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
		svg = svg.replace("y=\"390\"", "y=\"395\"")
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

