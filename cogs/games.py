
from discord.ext import commands

import asyncio
from bs4 import BeautifulSoup
# import cairosvg
import chess
import chess.pgn
import chess.svg
import chess.uci
import cleverbot
import html
import json
import pydealer
import random
import string
from wand.image import Image

from modules import utilities
from modules import adventure
#from modules import gofish
from modules.maze import maze
from modules import war
from utilities import checks
from clients import wait_time
from clients import code_block
from clients import aiohttp_session
from clients import cleverbot_instance
from clients import inflect_engine

def setup(bot):
	bot.add_cog(Games(bot))

class Games:
	
	def __init__(self, bot):
		self.bot = bot
		self._chess_board = chess.Board()
		self.chess_engine = chess.uci.popen_engine("bin/stockfish 7 x64")
		#self.chess_engine = chess.uci.popen_engine("bin/stockfish 7 x64 popcnt")
		self.chess_engine.uci()
		self.chess_engine_context, self.chess_engine_message = None, None
		self.war_channel, self.war_players = None, []
		self.gofish_channel, self.gofish_players = None, []
		self.taboo_players = []
		self.maze_started, self.maze_maze = False, None
		self.jeopardy_active, self.jeopardy_question_active, self.jeopardy_board, self.jeopardy_answer, self.jeopardy_answered, self.jeopardy_scores, self.jeopardy_board_output, self.jeopardy_max_width = False, False, [], None, None, {}, None, None
		self.trivia_active, self.trivia_countdown, self.bet_countdown = False, None, None
		#check default values
		
		self.adventure_players = {}
		
		utilities.create_file("trivia_points")
	
	# Adventure
	
	@commands.group(aliases = ["rpg"], invoke_without_command = True, hidden = True)
	@checks.not_forbidden()
	async def adventure(self):
		'''WIP'''
		pass
	
	def get_adventure_player(self, user_id):
		player = self.adventure_players.get(user_id)
		if not player:
			player = adventure.AdventurePlayer(user_id)
			self.adventure_players[user_id] = player
		return player
	
	@adventure.group(name = "stats", aliases = ["stat", "levels", "level", "lvls", "lvl"], pass_context = True, invoke_without_command = True)
	@checks.not_forbidden()
	async def adventure_stats(self, ctx):
		'''Stats'''
		player = self.get_adventure_player(ctx.message.author.id)
		await self.bot.reply("\n:fishing_pole_and_fish: Fishing xp: {} (Level {})"
		"\n:herb: Foraging xp: {} (Level {})"
		"\n:pick: Mining xp: {} (Level {})"
		"\n:evergreen_tree: Woodcutting xp: {} (Level {})".format(player.fishing_xp, player.fishing_lvl, player.foraging_xp, player.foraging_lvl, player.mining_xp, player.mining_lvl, player.woodcutting_xp, player.woodcutting_lvl))
		# time started/played
	
	@adventure_stats.command(name = "woodcutting", aliases = ["wc"], pass_context = True)
	@checks.not_forbidden()
	async def stats_woodcutting(self, ctx):
		'''Woodcutting stats'''
		player = self.get_adventure_player(ctx.message.author.id)
		woodcutting_xp = player.woodcutting_xp
		await self.bot.reply("\n:evergreen_tree: Woodcutting xp: {}\n{}\n{} xp to next level".format(woodcutting_xp, self.level_bar(woodcutting_xp), adventure.xp_left_to_next_lvl(woodcutting_xp)))
	
	@adventure_stats.command(name = "foraging", aliases = ["forage", "gather", "gathering"], pass_context = True)
	@checks.not_forbidden()
	async def stats_foraging(self, ctx):
		'''Foraging stats'''
		player = self.get_adventure_player(ctx.message.author.id)
		foraging_xp = player.foraging_xp
		await self.bot.reply("\n:herb: Foraging xp: {}\n{}\n{} xp to next level".format(foraging_xp, self.level_bar(foraging_xp), adventure.xp_left_to_next_lvl(foraging_xp)))
	
	def level_bar(self, xp):
		lvl = adventure.xp_to_lvl(xp)
		previous_xp = adventure.lvl_to_xp(lvl)
		next_xp = adventure.lvl_to_xp(lvl + 1)
		difference = next_xp - previous_xp
		shaded = int((xp - previous_xp) / difference * 10)
		bar = chr(9632) * shaded + chr(9633) * (10 - shaded)
		return "Level {0} ({3} xp) [{2}] Level {1} ({4} xp)".format(lvl, lvl + 1, bar, previous_xp, next_xp)
	
	@adventure.command(name = "inventory", pass_context = True)
	@checks.not_forbidden()
	async def adventure_inventory(self, ctx, *, item : str = ""):
		'''Inventory'''
		player = self.get_adventure_player(ctx.message.author.id)
		inventory = player.inventory
		if item in inventory:
			await self.bot.reply("{}: {}".format(item, inventory[item]))
		else:
			await self.bot.reply(", ".join(["{}: {}".format(item, amount) for item, amount in sorted(inventory.items())]))
	
	@adventure.command(name = "examine", pass_context = True)
	@checks.not_forbidden()
	async def adventure_examine(self, ctx, *, item : str):
		'''Examine items'''
		player = self.get_adventure_player(ctx.message.author.id)
		inventory = player.inventory
		if item in inventory:
			if item in adventure.examine_messages:
				await self.bot.reply("{}".format(adventure.examine_messages[item]))
			else:
				await self.bot.reply("{}".format(item))
		else:
			await self.bot.reply(":no_entry: You don't have that item")
	
	@adventure.group(name = "forage", aliases = ["gather"], pass_context = True, invoke_without_command = True)
	@checks.not_forbidden()
	async def adventure_forage(self, ctx, *, item : str = ""):
		'''Foraging'''
		player = self.get_adventure_player(ctx.message.author.id)
		started = player.start_foraging(item)
		if started == "foraging":
			stopped = player.stop_foraging()
			output = "\n:herb: You were foraging {0[0]} for {0[1]:.2f} min. and received {0[2]} {0[0]} and xp. While you were foraging, you also found {0[3]} {1}".format(stopped, adventure.forageables[stopped[0]][0])
			if stopped[4]:
				output += " and {0[4]} {1}!".format(stopped, adventure.forageables[stopped[0]][1])
			await self.bot.reply(output)
			if item:
				started = player.start_foraging(item)
			else:
				return
		if started is True:
			await self.bot.reply("\n:herb: You have started foraging for {}".format(item))
			# active?
		elif started is False:
			await self.bot.reply(":no_entry: That item type doesn't exist")
		else:
			await self.bot.reply(":no_entry: You're currently {}! You can't start/stop foraging right now".format(started))
	
	@adventure_forage.command(name = "start", aliases = ["on"], pass_context = True)
	@checks.not_forbidden()
	async def forage_start(self, ctx, *, item : str):
		'''Start foraging'''
		player = self.get_adventure_player(ctx.message.author.id)
		started = player.start_foraging(item)
		if started is True:
			await self.bot.reply("\n:herb: You have started foraging for {}".format(item))
			# active?
		elif started is False:
			await self.bot.reply(":no_entry: That item type doesn't exist")
		else:
			await self.bot.reply(":no_entry: You're currently {}! You can't start foraging right now".format(started))
	
	@adventure_forage.command(name = "stop", aliases = ["off"], pass_context = True)
	@checks.not_forbidden()
	async def forage_stop(self, ctx):
		'''Stop foraging'''
		player = self.get_adventure_player(ctx.message.author.id)
		stopped = player.stop_foraging()
		if stopped[0]:
			output = "\n:herb: You were foraging {0[0]} for {0[1]:.2f} min. and received {0[2]} {0[0]} and xp. While you were foraging, you also found {0[3]} {1}".format(stopped, adventure.forageables[stopped[0]][0])
			if stopped[4]:
				output += " and {0[4]} {1}!".format(stopped, adventure.forageables[stopped[0]][1])
			await self.bot.reply(output)
		elif stopped[1]:
			await self.bot.reply(":no_entry: You're currently {}! You aren't foraging right now")
		else:
			await self.bot.reply(":no_entry: You aren't foraging")
	
	@adventure_forage.command(name = "items")
	@checks.not_forbidden()
	async def forage_items(self):
		'''Forageable items'''
		await self.bot.reply(", ".join(adventure.forageables.keys()))
	
	@adventure.group(name = "chop", aliases = ["woodcutting", "wc"], pass_context = True, invoke_without_command = True)
	@checks.not_forbidden()
	async def adventure_woodcutting(self, ctx, *, wood_type : str = ""):
		'''Woodcutting'''
		player = self.get_adventure_player(ctx.message.author.id)
		started = player.start_woodcutting(wood_type)
		if started == "woodcutting":
			stopped = player.stop_woodcutting()
			await self.bot.reply("\n:evergreen_tree: You were chopping {0[0]} for {0[1]:.2f} min. and received {0[2]} {0[0]} and {0[3]} xp".format(stopped))
			if wood_type:
				started = player.start_woodcutting(wood_type)
			else:
				return
		if started is True:
			await self.bot.reply("\n:evergreen_tree: You have started chopping {} trees".format(wood_type))
			await self.woodcutting_active(ctx, wood_type)
		elif started is False:
			await self.bot.reply(":no_entry: That wood type doesn't exist")
		else:
			await self.bot.reply(":no_entry: You're currently {}! You can't start/stop woodcutting right now".format(started))
	
	@adventure_woodcutting.command(name = "start", aliases = ["on"], pass_context = True)
	@checks.not_forbidden()
	async def woodcutting_start(self, ctx, *, wood_type : str):
		'''Start chopping wood'''
		player = self.get_adventure_player(ctx.message.author.id)
		started = player.start_woodcutting(wood_type)
		if started is True:
			await self.bot.reply("\n:evergreen_tree: You have started chopping {} trees".format(wood_type))
			await self.woodcutting_active(ctx, wood_type)
		elif started is False:
			await self.bot.reply(":no_entry: That wood type doesn't exist")
		else:
			await self.bot.reply(":no_entry: You're currently {}! You can't start woodcutting right now".format(started))
	
	async def woodcutting_active(self, ctx, wood_type):
		player = self.get_adventure_player(ctx.message.author.id)
		ask_message = await self.bot.reply("\n:grey_question: Would you like to chop {} trees actively? Yes/No".format(wood_type))
		message = await self.bot.wait_for_message(timeout = 60, author = ctx.message.author, check = lambda m: m.content.lower() in ('y', "yes", 'n', "no"))
		await self.bot.delete_message(ask_message)
		if not message or message.content.lower() in ('n', "no"):
			if message:
				await self.bot.delete_message(message)
			return
		rate = player.wood_rate(wood_type) * player.woodcutting_rate
		if rate == 0:
			await self.bot.reply(":no_entry: You can't chop this wood yet")
			return
		time = int(60 / rate)
		chopped_message = None
		while message:
			chopping = await self.bot.reply("\n:evergreen_tree: Chopping.. (this could take up to {} sec.)".format(time))
			await asyncio.sleep(random.randint(1, time))
			await self.bot.delete_message(message)
			await self.bot.delete_message(chopping)
			prompt = random.choice(["chop", "whack", "swing", "cut"])
			prompt_message = await self.bot.reply('Reply with "{}" in the next 10 sec. to continue'.format(prompt))
			message = await self.bot.wait_for_message(timeout = 10, author = ctx.message.author, content = prompt)
			if message:
				chopped = player.chop_once(wood_type)
				if chopped_message:
					await self.bot.delete_message(chopped_message)
				chopped_message = await self.bot.reply("\n:evergreen_tree: You chopped a {0} tree. You now have {1[0]} {0} and {1[1]} woodcutting xp".format(wood_type, chopped))
			else:
				await self.bot.reply("\n:stop_sign: You have stopped actively chopping {}".format(wood_type))
			await self.bot.delete_message(prompt_message)
	
	@adventure_woodcutting.command(name = "stop", aliases = ["off"], pass_context = True)
	@checks.not_forbidden()
	async def woodcutting_stop(self, ctx):
		'''Stop chopping wood'''
		player = self.get_adventure_player(ctx.message.author.id)
		stopped = player.stop_woodcutting()
		if stopped[0]:
			await self.bot.reply("\n:evergreen_tree: You were chopping {0[0]} for {0[1]:.2f} min. and received {0[2]} {0[0]} and {0[3]} xp".format(stopped))
		elif stopped[1]:
			await self.bot.reply(":no_entry: You're currently {}! You aren't woodcutting right now")
		else:
			await self.bot.reply(":no_entry: You aren't woodcutting")
	
	@adventure_woodcutting.command(name = "types", aliases = ["type"])
	@checks.not_forbidden()
	async def woodcutting_types(self):
		'''Types of wood'''
		await self.bot.reply(", ".join(adventure.wood_types))
	
	@adventure_woodcutting.command(name = "rate", aliases = ["rates"], pass_context = True)
	@checks.not_forbidden()
	async def woodcutting_rate(self, ctx, *, wood_type : str):
		'''Rate of chopping certain wood'''
		player = self.get_adventure_player(ctx.message.author.id)
		if wood_type in adventure.wood_types:
			await self.bot.reply("You will get {:.2f} {}/min. at your current level".format(player.wood_rate(wood_type) * player.woodcutting_rate, wood_type))
		else:
			await self.bot.reply(":no_entry: That wood type doesn't exist")
	
	# Not Adventure
	
	@commands.command(pass_context = True)
	@checks.not_forbidden()
	async def blackjack(self, ctx):
		'''Play a game of blackjack'''
		deck = pydealer.Deck()
		deck.shuffle()
		dealer = deck.deal(2)
		hand = deck.deal(2)
		dealer_string = ""
		hand_string = ""
		for card in dealer.cards:
			dealer_string += card.value + " :" + card.suit.lower() + ": "
		for card in hand.cards:
			hand_string += card.value + " :" + card.suit.lower() + ": "
		dealer_total = sum([pydealer.const.DEFAULT_RANKS["values"][card.value] + 1 for card in dealer.cards])
		hand_total = sum([pydealer.const.DEFAULT_RANKS["values"][card.value] + 1 for card in hand.cards])
		await self.bot.say("Dealer: " + dealer_string + '(' + str(dealer_total) + ')\n' + ctx.message.author.mention + ": " + hand_string + '(' + str(hand_total) + ')\n' )
		while True:
			action = await self.bot.wait_for_message(author = ctx.message.author, check = lambda msg: msg.content in ["hit", "stay"])
			if action.content == "hit":
				hand_string = ""
				hand.add(deck.deal())
				for card in hand.cards:
					hand_string += card.value + " :" + card.suit.lower() + ": "
				hand_total = sum([pydealer.const.DEFAULT_RANKS["values"][card.value] + 1 for card in hand.cards])
				await self.bot.say("Dealer: " + dealer_string + '(' + str(dealer_total) + ')\n' + ctx.message.author.mention + ": " + hand_string + '(' + str(hand_total) + ')\n' )
				if hand_total > 21:
					await self.bot.reply("You have busted. You lost :(")
					return
			else:
				if dealer_total > 21:
					await self.bot.reply("The dealer busted. You win!")
					return
				elif dealer_total > hand_total:
					await self.bot.reply("The dealer beat you. You lost :(")
					return
				while True:
					dealer_string = ""
					dealer.add(deck.deal())
					for card in dealer.cards:
						dealer_string += card.value + " :" + card.suit.lower() + ": "
					dealer_total = sum([pydealer.const.DEFAULT_RANKS["values"][card.value] + 1 for card in dealer.cards])
					await self.bot.say("Dealer: " + dealer_string + '(' + str(dealer_total) + ')\n' + ctx.message.author.mention + ": " + hand_string + '(' + str(hand_total) + ')\n' )
					if dealer_total > 21:
						await self.bot.reply("The dealer busted. You win!")
						return
					elif dealer_total > hand_total:
						await self.bot.reply("The dealer beat you. You lost :(")
						return
					await asyncio.sleep(5)
	
	@commands.group(pass_context = True, invoke_without_command = True)
	@checks.not_forbidden()
	async def chess(self, ctx, *move : str):
		'''
		Play chess
		Supports standard algebraic and UCI notation
		'''
		if not move:
			await self.bot.reply("See {}help chess".format(ctx.prefix))
		else:
			try:
				self._chess_board.push_san(move[0])
			except ValueError:
				try:
					self._chess_board.push_uci(move[0])
				except ValueError:
					await self.bot.reply("Invalid move.")
					return
			await self._display_chess_board(ctx)
	
	#dm
	#check mate, etc.
	
	@chess.command(name = "play_harmonbot", pass_context = True)
	async def chess_play_harmonbot(self, ctx, *color):
		'''Play chess with Harmonbot'''
		self._chess_board.reset()
		if not color or color[0] not in ("white", "black"):
			await self.bot.reply("Would you like to play white or black?")
			message = await self.bot.wait_for_message(author = ctx.message.author, channel = ctx.message.channel, check = lambda msg: msg.content.lower() in ("white", "black"))
			color = [message.content]
		if color[0].lower() == "black":
			self.chess_engine.position(self._chess_board)
			self.chess_engine.go(movetime = 2000, async_callback = self.process_chess_engine_command)
			self.chess_engine_message = await self.bot.reply("I'm thinking..")
			self.chess_engine_context = ctx
			flipped = True
		else:
			await self._display_chess_board(ctx)
			flipped = False
		while True:
			message = await self.bot.wait_for_message(author = ctx.message.author, channel = ctx.message.channel, check = lambda msg: self.valid_move(msg.content))
			try:
				self._chess_board.push_san(message.content)
			except ValueError:
				try:
					self._chess_board.push_uci(message.content)
				except ValueError:
					await self.bot.reply("Error: Invalid move.")
					return
			await self._display_chess_board(ctx, flipped = flipped)
			self.chess_engine.position(self._chess_board)
			self.chess_engine.go(movetime = 2000, async_callback = self.process_chess_engine_command)
			self.chess_engine_message = await self.bot.reply("I'm thinking..")
			self.chess_engine_context = ctx
	
	def valid_move(self, move):
		try:
			self._chess_board.parse_san(move)
		except ValueError:
			try:
				self._chess_board.parse_uci(move)
			except ValueError:
				return False
		return True
	
	@chess.group(name = "board", pass_context = True, invoke_without_command = True)
	async def chess_board(self, ctx, *options : str):
		'''
		Current board
		Options: flipped
		'''
		flipped = options and options[0].lower() == "flipped"
		await self._display_chess_board(ctx, flipped = flipped)
	
	async def _display_chess_board(self, ctx, *, message = None, flipped = False):
		# svg = self._chess_board._repr_svg_()
		svg = chess.svg.board(self._chess_board, flipped = flipped)
		with open("data/temp/chess_board.svg", 'w') as image:
			# print(svg[:40] + 'xmlns:xlink="http://www.w3.org/1999/xlink" ' + svg[40:], file = image)
			print(svg.replace('class="square light', 'fill="#ffce9e" class="square light').replace('class="square dark', 'fill="#d18b47" class="square dark'), file = image)
		'''
		with open("data/temp/chess_board.png", 'wb') as image:
			cairosvg.svg2png(svg[:40] + 'xmlns:xlink="http://www.w3.org/1999/xlink" ' + svg[40:])
		with open("data/temp/chess_board.png", 'r') as image:
			await self.bot.send_file(ctx.message.channel, image)
		'''
		with Image(filename = "data/temp/chess_board.svg") as img:
			img.format = "png"
			img.save(filename = "data/temp/chess_board.png")
		asyncio.sleep(0.1)
		with open("data/temp/chess_board.png", 'rb') as image:
			await self.bot.send_file(ctx.message.channel, image, content = message)
	
	@chess_board.command(name = "text")
	async def chess_board_text(self):
		'''Text version of the current board'''
		await self.bot.reply("\n```" + str(self._chess_board) + "```")
	
	@chess.command(name = "fen")
	async def chess_fen(self):
		'''FEN of the current board'''
		await self.bot.reply(self._chess_board.fen())
	
	@chess.command(name = "pgn")
	async def chess_pgn(self):
		'''PGN of the current game'''
		await self.bot.reply(chess.pgn.Game.from_board(self._chess_board))
	
	@chess.command(name = "turn")
	async def chess_turn(self):
		'''Who's turn it is to move'''
		if self._chess_board.turn:
			await self.bot.reply("It's white's turn to move.")
		else:
			await self.bot.reply("It's black's turn to move.")
	
	@chess.command(name = "harmonbot", aliases = ["computer", "engine"], pass_context = True)
	async def chess_harmonbot(self, ctx):
		'''Ask Harmonbot to make a move'''
		self.chess_engine.position(self._chess_board)
		self.chess_engine.go(movetime = 2000, async_callback = self.process_chess_engine_command)
		self.chess_engine_message = await self.bot.reply("I'm thinking..")
		self.chess_engine_context = ctx
	
	def process_chess_engine_command(self, command):
		bestmove, ponder = command.result()
		coro = self.bot.edit_message(self.chess_engine_message, "I moved " + str(bestmove))
		fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
		fut.result()
		self._chess_board.push(bestmove)
		if self._chess_board.turn:
			coro = self._display_chess_board(self.chess_engine_context, flipped = False)
		else:
			coro = self._display_chess_board(self.chess_engine_context, flipped = True)
		fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
		fut.result()
	
	@chess.command(name = "reset", pass_context = True)
	async def chess_reset(self, ctx):
		'''Reset the board'''
		self._chess_board.reset()
		await self.bot.reply("The board has been reset.")
	
	@chess.command(name = "undo", pass_context = True)
	async def chess_undo(self, ctx):
		'''Undo the previous move'''
		try:
			self._chess_board.pop()
			await self._display_chess_board(ctx, message = "The previous move was undone.")
		except IndexError:
			await self.bot.reply("There's no more moves to undo.")
	
	@chess.command(name = "previous", aliases = ["last"])
	async def chess_last(self):
		'''Previous move'''
		try:
			await self.bot.reply(self._chess_board.peek())
		except IndexError:
			await self.bot.reply("There was no previous move.")
	
	@chess.command(name = "(╯°□°）╯︵", pass_context = True, hidden = True)
	async def chess_flip(self, ctx):
		'''Flip the table over'''
		self._chess_board.clear()
		await self.bot.say(ctx.message.author.name + " flipped the table over in anger!")
	
	@commands.command(aliases = ["talk", "ask"])
	@checks.not_forbidden()
	async def cleverbot(self, *, message : str):
		'''Talk to Cleverbot'''
		await self.bot.reply(cleverbot_instance.ask(message))
	
	@commands.command(name = "8ball", aliases = ["eightball", "\U0001f3b1"])
	@checks.not_forbidden()
	async def eightball(self):
		'''
		Ask 8ball a yes or no question
		Also triggers on :8ball: without prefix
		'''
		await self.bot.reply(":8ball: {}".format(self._eightball()))
	
	def _eightball(self):
		responses = ["It is certain", "It is decidedly so", "Without a doubt", "Yes, definitely", "You may rely on it", "As I see it, yes", "Most likely", "Outlook good", "Yes", "Signs point to yes", "Reply hazy try again", "Ask again later", "Better not tell you now", "Cannot predit now", "Concentrate and ask again", "Don't count on it", "My reply is no", "My sources say no", "Outlook not so good", "Very doubtful"]
		return(random.choice(responses))
	
	@commands.group(hidden = True, pass_context = True)
	@checks.not_forbidden()
	async def gofish(self, ctx): #WIP
		'''WIP'''
		return
	
	@gofish.command(hidden = True, name = "start", pass_context = True, no_pm = True)
	@checks.is_owner()
	async def gofish_start(self, ctx, *players : str): #WIP
		'''WIP'''
		self.gofish_channel = ctx.message.channel
		if ctx.message.server:
			for member in ctx.message.server.members:
				if member.name in players:
					self.gofish_players.append(member)
					break
		else:
			await self.bot.reply("Please use that command in a server.")
			pass
		gofish.start(len(players))
		gofish_players_string = ""
		for player in self.gofish_players:
			gofish_players_string += player.name + " and "
		await self.bot.reply(message.author.name + " has started a game of Go Fish between " + gofish_players_string[:-5] + "!")
	
	@gofish.command(hidden = True, name = "hand", pass_context = True)
	async def gofish_hand(self, ctx): #WIP
		'''WIP'''
		if ctx.message.author in gofish_players:
			await self.bot.whisper("Your hand: " + gofish.hand(gofish_players.index(ctx.message.author) + 1))
	
	@gofish.command(hidden = True, name = "ask", pass_context = True)
	async def gofish_ask(self, ctx): #WIP
		'''WIP'''
		if ctx.message.author in gofish_players:
			pass
	
	@commands.command(pass_context = True)
	@checks.not_forbidden()
	async def guess(self, ctx, *options : str):
		'''
		Guessing game
		Guess <max> <tries>
		'''
		tries = False
		if len(options) >= 2 and utilities.is_digit_gtz(options[1]):
			tries = int(options[1])
		if len(options) >= 1 and utilities.is_digit_gtz(options[0]):
			max_value = int(options[0])
		else:
			await self.bot.reply("What range of numbers would you like to guess to? 1 to _")
			max_value = await self.bot.wait_for_message(timeout = wait_time, author = ctx.message.author, check = utilities.message_is_digit_gtz)
			if max_value is None:
				max_value = 10
			else:
				max_value = int(max_value.content)
		answer = random.randint(1, max_value)
		if not tries:
			await self.bot.reply("How many tries would you like?")
			tries = await self.bot.wait_for_message(timeout = wait_time, author = ctx.message.author, check = utilities.message_is_digit_gtz)
			if tries is None:
				tries = 1
			else:
				tries = int(tries.content)
		await self.bot.reply("Guess a number between 1 to " + str(max_value))
		while tries != 0:
			guess = await self.bot.wait_for_message(timeout = wait_time, author = ctx.message.author, check = utilities.message_is_digit_gtz)
			if guess is None:
				await self.bot.reply("Sorry, you took too long. It was " + str(answer))
				return
			if int(guess.content) == answer:
				await self.bot.reply("You are right!")
				return
			elif tries != 1 and int(guess.content) > answer:
				await self.bot.reply("It's less than " + guess.content)
				tries -= 1
			elif tries != 1 and int(guess.content) < answer:
				await self.bot.reply("It's greater than " + guess.content)
				tries -= 1
			else:
				await self.bot.reply("Sorry, it was actually " + str(answer))
				return
	
	@commands.group(invoke_without_command = True, pass_context = True)
	@checks.not_forbidden()
	async def jeopardy(self, ctx, *options : str):
		if len(options) >= 2 and self.jeopardy_active and not self.jeopardy_question_active:
			category = int(options[0])
			value = options[1]
			if 1 <= category <= 6 and value in ["200", "400", "600", "800", "1000"]:
				value_index = ["200", "400", "600", "800", "1000"].index(value)
				if not self.jeopardy_board[category - 1][value_index + 1]:
					self.jeopardy_question_active = True
					self.jeopardy_answered = None
					url = "http://jservice.io/api/category?id=" + str(self.jeopardy_board[category - 1][0])
					async with aiohttp_session.get(url) as resp:
						data = await resp.json()
					self.jeopardy_answer = data["clues"][value_index]["answer"]
					await self.bot.say("Category: " + string.capwords(data["title"]) + "\n" + data["clues"][value_index]["question"])
					counter = int(wait_time)
					answer_message = await self.bot.say("You have {} seconds left to answer.".format(str(counter)))
					self.bot.loop.create_task(self.jeopardy_wait_for_answer())
					while counter:
						await asyncio.sleep(1)
						counter -= 1
						await self.bot.edit_message(answer_message, "You have {} seconds left to answer.". format(str(counter)))
						if self.jeopardy_answered:
							break
					await self.bot.edit_message(answer_message, "Time's up!")
					if self.jeopardy_answered:
						if self.jeopardy_answered in self.jeopardy_scores:
							self.jeopardy_scores[self.jeopardy_answered] += int(value)
						else:
							self.jeopardy_scores[self.jeopardy_answered] = int(value)
						answered_message = "{} was right! They now have ${}.".format(self.jeopardy_answered.name, str(self.jeopardy_scores[self.jeopardy_answered]))
					else:
						answered_message = "Nobody got it right."
					score_output = ""
					for player, score in self.jeopardy_scores.items():
						score_output += "{}: ${}, ".format(player.name, str(score))
					score_output = score_output[:-2]
					self.jeopardy_board[category - 1][value_index + 1] = True
					clue_delete_cursor = (self.jeopardy_max_width + 2) * category + 1 * (category - 1) + 20 * (category - 1) + 4 * value_index
					if value_index == 4:
						self.jeopardy_board_output = self.jeopardy_board_output[:clue_delete_cursor] + "    " + self.jeopardy_board_output[clue_delete_cursor + 4:]
					else:
						self.jeopardy_board_output = self.jeopardy_board_output[:clue_delete_cursor] + "   " + self.jeopardy_board_output[clue_delete_cursor + 3:]
					await self.bot.say("The answer was " + BeautifulSoup(html.unescape(self.jeopardy_answer), "html.parser").get_text() + "\n" + answered_message + "\n" + score_output + "\n```" + self.jeopardy_board_output + "```")
					self.jeopardy_question_active = False
			else:
				await self.bot.reply("Syntax error.")
		else:
			await self.bot.reply("Error.")
	
	async def jeopardy_wait_for_answer(self):
		if self.jeopardy_question_active:
			message = await self.bot.wait_for_message(timeout = wait_time, check = lambda m: self.jeopardy_answer.lower() in [s + m.content.lower() for s in ["", "a ", "an ", "the "]] or m.content.lower() == BeautifulSoup(html.unescape(self.jeopardy_answer.lower()), "html.parser").get_text().lower())
			if message and not message.content.startswith('>'):
				self.jeopardy_answered = message.author
	
	#jeopardy stats
	
	@jeopardy.command(name = "start", pass_context = True)
	async def jeopardy_start(self, ctx):
		if not self.jeopardy_active:
			self.jeopardy_active = True
			categories = []
			category_titles = []
			self.jeopardy_board_output = ""
			url = "http://jservice.io/api/random"
			for i in range(6):
				async with aiohttp_session.get(url) as resp:
					data = await resp.json()
				categories.append(data[0]["category_id"])
			for category in categories:
				url = "http://jservice.io/api/category?id=" + str(category)
				async with aiohttp_session.get(url) as resp:
					data = await resp.json()
				category_titles.append(string.capwords(data["title"]))
				self.jeopardy_board.append([category, False, False, False, False, False])
			self.jeopardy_max_width = max(len(category_title) for category_title in category_titles)
			for category_title in category_titles:
				self.jeopardy_board_output += category_title.ljust(self.jeopardy_max_width) + "  200 400 600 800 1000\n"
			await self.bot.say("```" + self.jeopardy_board_output + "```")
	
	@commands.command(pass_context = True)
	@checks.not_forbidden()
	async def maze(self, ctx, *options : str):
		'''
		Maze game
		options: start <width> <height>, current, [w, a, s, d] to move
		'''
		if not options:
			await self.bot.reply("Please enter an option (start/current)")
		elif options[0] == "start":
			if self.maze_started:
				await self.bot.reply("There's already a maze game going on.")
			elif len(options) >= 3 and options[1].isdigit() and options[2].isdigit():
				self.maze_started = True
				self.maze_maze = maze(int(options[1]), int(options[2]))
				await self.bot.reply(code_block.format(self.maze_maze.print_visible()))
				'''
				maze_print = ""
				for r in maze_maze.test_print():
					row_print = ""
					for cell in r:
						row_print += cell + ' '
					maze_print += row_print + "\n"
				await self.bot.reply(code_block.format(maze_print))
				'''
				# await self.bot.reply(code_block.format(repr(maze_maze)))
				convert_move = {'w' : 'n', 'a' : 'w', 's' : 's', 'd' : 'e'}
				while not self.maze_maze.reached_end():
					moved = False
					move = await self.bot.wait_for_message(check = lambda message: message.content.lower() in ['w', 'a', 's', 'd']) # author = ctx.message.author
					moved = self.maze_maze.move(convert_move[move.content.lower()])
					await self.bot.reply(code_block.format(self.maze_maze.print_visible()))
					if not moved:
						await self.bot.reply("You can't go that way.")
				await self.bot.reply("Congratulations! You reached the end of the maze.")
				self.maze_started = False
			else:
				await self.bot.reply("Please enter a valid maze size. (e.g. !maze start 2 2)")
		elif options[0] == "current":
			if self.maze_started:
				await self.bot.reply(code_block.format(self.maze_maze.print_visible()))
			else:
				await self.bot.reply("There's no maze game currently going on.")
		else:
			await self.bot.reply("Please enter a valid option (start/current).")
	
	@commands.group(hidden = True)
	@checks.not_forbidden()
	async def taboo(self): #WIP
		'''WIP'''
		return
	
	@taboo.command(hidden = True, name = "start", pass_context = True, no_pm = True)
	async def taboo_start(self, ctx, player : str): #WIP
		'''WIP'''
		self.taboo_players.append(ctx.message.author)
		for member in self.message.server.members:
			if member.name == player:
				self.taboo_players.append(member)
				break
		await self.bot.reply(" has started a game of Taboo with " + taboo_players[1].mention)
		await self.bot.whisper("You have started a game of Taboo with " + taboo_players[1].name)
		await self.bot.send_message(taboo_players[1], ctx.message.author.name + " has started a game of Taboo with you.")
	
	@taboo.command(hidden = True, name = "nextround") # no_pm = True ?
	async def taboo_nextround(self): #WIP
		'''WIP'''
		if message.server:
			pass
	
	@commands.group(invoke_without_command = True, pass_context = True)
	@checks.not_forbidden()
	async def trivia(self, ctx, *options : str):
		'''Trivia game'''
		if not self.trivia_active:
			bet, bets = options and options[0] == "bet", {}
			self.trivia_active, responses = True, {}
			async with aiohttp_session.get("http://jservice.io/api/random") as resp:
				data = (await resp.json())[0]
			if bet:
				await self.bot.say("Category: " + string.capwords(data["category"]["title"]))
				self.bet_countdown = int(wait_time)
				bet_message = await self.bot.say("You have {} seconds left to bet.".format(str(self.bet_countdown)))
				self.bot.loop.create_task(self._bet_countdown(bet_message))
				while self.bet_countdown:
					message = await self.bot.wait_for_message(timeout = self.bet_countdown, channel = ctx.message.channel, check = lambda m: m.content.isdigit())
					if message:
						with open("data/trivia_points.json", "r") as trivia_file:
							score = json.load(trivia_file)
						if int(message.content) <= score[message.author.id][2]:
							bets[message.author] = int(message.content)
							await self.bot.say(message.author.display_name + " has bet $" + message.content)
						else:
							await self.bot.reply("You don't have that much money to bet!")
				await self.bot.edit_message(bet_message, "Betting is over.")
			await self.bot.say("Category: " + string.capwords(data["category"]["title"]) + "\n" + data["question"])
			self.trivia_countdown = int(wait_time)
			answer_message = await self.bot.say("You have {} seconds left to answer.".format(str(self.trivia_countdown)))
			self.bot.loop.create_task(self._trivia_countdown(answer_message))
			while self.trivia_countdown:
				message = await self.bot.wait_for_message(timeout = self.trivia_countdown, channel = ctx.message.channel)
				if message and not message.content.startswith('>'):
					responses[message.author] = message.content
			await self.bot.edit_message(answer_message, "Time's up!")
			correct_players = []
			incorrect_players = []
			for player, response in responses.items():
				if data["answer"].lower() in [s + response.lower() for s in ["", "a ", "an ", "the "]] or response.lower() == BeautifulSoup(html.unescape(data["answer"]), "html.parser").get_text().lower():
					correct_players.append(player)
				else:
					incorrect_players.append(player)
			if len(correct_players) == 0:
				correct_players_output = "Nobody got it right!"
			else:
				correct_players_output = inflect_engine.join([correct_player.name for correct_player in correct_players]) + ' ' + inflect_engine.plural("was", len(correct_players)) + " right!"
			with open("data/trivia_points.json", "r") as trivia_file:
				score = json.load(trivia_file)
			for correct_player in correct_players:
				if correct_player.id in score:
					score[correct_player.id][0] += 1
				else:
					score[correct_player.id] = [1, 0, 100000]
			for incorrect_player in incorrect_players:
				if incorrect_player.id in score:
					score[incorrect_player.id][1] += 1
				else:
					score[incorrect_player.id] = [0, 1, 100000]
			if bet:
				trivia_bets_output = ""
				for trivia_player in bets:
					if trivia_player in correct_players:
						score[correct_player.id][2] += bets[correct_player]
						trivia_bets_output += trivia_player.name + " won $" + utilities.add_commas(bets[trivia_player]) + " and now has $" + utilities.add_commas(score[trivia_player.id][2]) + ". "
					else:
						score[trivia_player.id][2] -= bets[trivia_player]
						trivia_bets_output += trivia_player.name + " lost $" + utilities.add_commas(bets[trivia_player]) + " and now has $" + utilities.add_commas(score[trivia_player.id][2]) + ". "
				trivia_bets_output = trivia_bets_output[:-1]
			with open("data/trivia_points.json", "w") as trivia_file:
				json.dump(score, trivia_file, indent = 4)
			await self.bot.say("The answer was " + BeautifulSoup(html.unescape(data["answer"]), "html.parser").get_text() + "\n" + correct_players_output)
			if bet and trivia_bets_output:
				await self.bot.say(trivia_bets_output)
			self.trivia_active = False
		else:
			await self.bot.reply("There is already an ongoing game of trivia. Other options: score money")
	
	async def _bet_countdown(self, bet_message):
		while self.bet_countdown:
			await asyncio.sleep(1)
			self.bet_countdown -= 1
			await self.bot.edit_message(bet_message, "You have {} seconds left to bet.".format(str(self.bet_countdown)))
	
	async def _trivia_countdown(self, answer_message):
		while self.trivia_countdown:
			await asyncio.sleep(1)
			self.trivia_countdown -= 1
			await self.bot.edit_message(answer_message, "You have {} seconds left to answer.".format(str(self.trivia_countdown)))
	
	# url = "http://api.futuretraxex.com/v1/getRandomQuestion
	# await self.bot.say(BeautifulSoup(html.unescape(data["q_text"]), "html.parser").get_text() + "\n1. " + data["q_options_1"] + "\n2. " + data["q_options_2"] + "\n3. " + data["q_options_3"] + "\n4. " + data["q_options_4"])
	# if answer == data["q_correct_option"]:
	# await self.bot.say("The answer was " + str(data["q_correct_option"]) + ". " + data["q_options_" + str(data["q_correct_option"])] + "\n" + correct_players_output)
	
	@trivia.command(name = "score", aliases = ["points"], pass_context = True)
	async def trivia_score(self, ctx):
		with open("data/trivia_points.json", "r") as trivia_file:
			score = json.load(trivia_file)
		correct = score[ctx.message.author.id][0]
		incorrect = score[ctx.message.author.id][1]
		correct_percentage = round(float(correct) / (float(correct) + float(incorrect)) * 100, 2)
		await self.bot.reply("You have answered {}/{} ({}%) correctly.".format(str(correct), str(correct + incorrect), str(correct_percentage)))
	
	@trivia.command(name = "money", aliases = ["cash"], pass_context = True)
	async def trivia_money(self, ctx):
		with open("data/trivia_points.json", "r") as trivia_file:
			score = json.load(trivia_file)
		cash = score[ctx.message.author.id][2]
		await self.bot.reply("You have $" + utilities.add_commas(cash))
	
	@commands.group(pass_context = True)
	@checks.not_forbidden()
	async def war(self, ctx):
		'''Based on the War card game'''
		return
	
	@war.command(name = "start", pass_context = True, no_pm = True)
	@checks.is_owner()
	async def war_start(self, ctx, *players : str):
		'''Start a game of War'''
		self.war_players = []
		for member in ctx.message.server.members:
			if member.name in players:
				self.war_players.append(member)
				break
		war.start(len(players))
		self.war_channel = ctx.message.channel
		war_players_string = ""
		for player in self.war_players:
			war_players_string += player.name + " and "
		await self.bot.reply(ctx.message.author.name + " has started a game of War between " + war_players_string[:-5] + "!")
	
	@war.command(name = "hand", pass_context = True)
	async def war_hand(self, ctx):
		'''See your current hand'''
		if ctx.message.author in self.war_players:
			await self.bot.whisper("Your hand: " + war.hand(self.war_players.index(ctx.message.author) + 1))
	
	@war.command(name = "left", pass_context = True)
	async def war_left(self, ctx):
		'''See how many cards you have left'''
		if ctx.message.author in self.war_players:
			await self.bot.reply("You have " + str(war.card_count(self.war_players.index(ctx.message.author) + 1)) + " cards left.")
	
	@war.command(name = "play", pass_context = True)
	async def war_play(self, ctx, *card : str):
		'''Play a card'''
		if ctx.message.author in self.war_players:
			player_number = self.war_players.index(message.author) + 1
			winner, cardsplayed, tiedplayers = war.play(player_number, ' '.join(card))
			if winner == -1:
				await self.bot.reply("You have already chosen your card for this battle.")
			elif winner == -3:
				await self.bot.reply("You are not in this battle.")
			elif winner == -4:
				await self.bot.reply("Card not found in your hand.")
			else:
				await self.bot.reply("You chose the " + cardsplayed[player_number - 1].value + " of " + cardsplayed[player_number - 1].suit)
				await self.bot.whisper("Your hand: " + war.hand(player_number))
			if winner > 0:
				winner_name = self.war_players[winner - 1].name
				cards_played_print = ""
				for i in range(len(self.war_players)):
					cards_played_print += self.war_players[i].name + " played " + cardsplayed[i].value + " of " + cardsplayed[i].suit + " and "
				cards_played_print = cards_played_print[:-5] + "."
				await self.bot.send_message(self.war_channel, winner_name + " wins the battle.\n" + cards_played_print)
				for war_player in self.war_players:
					await self.bot.send_message(war_player, winner_name + " wins the battle.\n" + cards_played_print)
			if winner == -2:
				cards_played_print = ""
				for i in range(len(self.war_players)):
					cards_played_print += self.war_players[i].name + " played " + cardsplayed[i].value + " of " + cardsplayed[i].suit + " and "
				cards_played_print = cards_played_print[:-5] + "."
				tiedplayers_print = ""
				for tiedplayer in tiedplayers:
					tiedplayers_print += self.war_players[tiedplayer - 1].name + " and "
				tiedplayers_print = tiedplayers_print[:-5] + " tied.\n"
				await self.bot.send_message(self.war_channel, tiedplayers_print + cards_played_print)
				for war_player in self.war_players:
					await self.bot.send_message(war_player, tiedplayers_print + cards_played_print)
				pass

