
import discord

import asyncio
import datetime

import chess
import chess.pgn
import chess.svg
import chess.uci
from wand.image import Image

import clients

class chess_match(chess.Board):
	
	def initialize(self, client, text_channel, white_player, black_player):
		self.bot = client
		self.text_channel = text_channel
		self.white_player = white_player
		self.black_player = black_player
		self.chess_engine = chess.uci.popen_engine("bin/stockfish_9_x64.exe")
		#self.chess_engine = chess.uci.popen_engine("bin/stockfish_9_x64_popcnt.exe")
		self.chess_engine.uci()
		self.match_message = None
		self.match_embed = None
		self.generated_move = asyncio.Event()
		self.best_move = None
		self.ponder = None
		self.task = self.bot.loop.create_task(self.match_task())
	
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
		self.match_message = await self.bot.send_embed(self.text_channel, "Loading..")
		await self.update_match_embed()
		while True:
			player = [self.black_player, self.white_player][int(self.turn)]
			if player == self.bot.user:
				await self.match_message.edit(embed = self.match_embed.set_footer(text = "I'm thinking.."))
				self.chess_engine.position(self)
				self.chess_engine.go(movetime = 2000, async_callback = self.process_chess_engine_command)
				await self.generated_move.wait()
				self.generated_move.clear()
				self.push(self.best_move)
				await self.update_match_embed(footer_text = "I moved {}".format(self.best_move))
			else:
				message = await self.bot.wait_for("message", check = lambda msg: msg.author == player and msg.channel == self.text_channel and self.valid_move(msg.content))
				await self.match_message.edit(embed = self.match_embed.set_footer(text = "Processing move.."))
				self.make_move(message.content)
				footer_text = discord.Embed.Empty if self.is_game_over() else "It is {}'s ({}'s) turn to move".format(["black", "white"][int(self.turn)], [self.black_player, self.white_player][int(self.turn)])
				await self.update_match_embed(footer_text = footer_text)
				await self.bot.attempt_delete_message(message)
	
	async def update_match_embed(self, *, flipped = None, footer_text = discord.Embed.Empty):
		if flipped is None: flipped = not self.turn
		# svg = self._repr_svg_()
		svg = chess.svg.board(self, lastmove = self.peek() if self.move_stack else None, check = self.king(self.turn) if self.is_check() else None, flipped = flipped)
		svg = svg.replace("y=\"390\"", "y=\"395\"")
		with open(clients.data_path + "/temp/chess_board.svg", 'w') as image:
			print(svg, file = image)
		with Image(filename = clients.data_path + "/temp/chess_board.svg") as img:
			img.format = "png"
			img.save(filename = clients.data_path + "/temp/chess_board.png")
		# asyncio.sleep(0.2) # necessary?, wasn't even awaited
		if not self.match_embed:
			self.match_embed = discord.Embed(color = clients.bot_color)
		# TODO: Upload into embed + delete and re-send to update?
		'''
		self.match_embed.set_image(url = self.bot.imgur_client.upload_from_path(clients.data_path + "/temp/chess_board.png")["link"])
		self.match_embed.set_image(url = data["data"]["img_url"])
		'''
		image_message = await self.bot.cache_channel.send(file = discord.File(clients.data_path + "/temp/chess_board.png"))
		self.match_embed.set_image(url = image_message.attachments[0].url)
		self.match_embed.set_footer(text = footer_text)
		chess_pgn = chess.pgn.Game.from_board(self)
		chess_pgn.headers["Site"] = "Discord"
		chess_pgn.headers["Date"] = datetime.datetime.utcnow().strftime("%Y.%m.%d")
		chess_pgn.headers["White"] = self.white_player.mention
		chess_pgn.headers["Black"] = self.black_player.mention
		self.match_embed.description = str(chess_pgn)
		if not self.match_message:
			self.match_message = await self.text_channel.send(embed = self.match_embed)
		else:
			await self.match_message.edit(embed = self.match_embed)
	
	async def new_match_embed(self, *, flipped = None, footer_text = None):
		if flipped is None: flipped = not self.turn
		if footer_text is None: footer_text = discord.Embed.Empty if self.is_game_over() else "It's {}'s ({}'s) turn to move".format(["black", "white"][int(self.turn)], [self.black_player, self.white_player][int(self.turn)])
		if self.match_message: await self.match_message.delete()
		self.match_message = None
		await self.update_match_embed(flipped = flipped, footer_text = footer_text)
	
	def process_chess_engine_command(self, command):
		self.best_move, self.ponder = command.result()
		self.bot.loop.call_soon_threadsafe(self.generated_move.set)

