
import discord
from discord.ext import commands

import asyncio
from bs4 import BeautifulSoup
# import chess
import chess.pgn
import cleverbot
import copy
import html
import json
import pydealer
import random
import string

from modules import utilities
from modules import adventure
#from modules import gofish
from modules.maze import maze
from modules import war
from utilities import checks
from utilities.chess import chess_match
import clients
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
		self.chess_matches = []
		self.war_channel, self.war_players = None, []
		self.gofish_channel, self.gofish_players = None, []
		self.taboo_players = []
		self.maze_started, self.maze_maze = False, None
		self.jeopardy_active, self.jeopardy_question_active, self.jeopardy_board, self.jeopardy_answer, self.jeopardy_answered, self.jeopardy_scores, self.jeopardy_board_output, self.jeopardy_max_width = False, False, [], None, None, {}, None, None
		self.trivia_active, self.trivia_countdown, self.bet_countdown = False, None, None
		self.blackjack_ranks = copy.deepcopy(pydealer.const.DEFAULT_RANKS)
		self.blackjack_ranks["values"].update({"Ace": 0, "King": 9, "Queen": 9, "Jack": 9})
		for value in self.blackjack_ranks["values"]:
			self.blackjack_ranks["values"][value] += 1
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
		dealer_string = self.cards_to_string(dealer.cards)
		hand_string = self.cards_to_string(hand.cards)
		dealer_total = sum([self.blackjack_ranks["values"][card.value] for card in dealer.cards])
		hand_total = sum([self.blackjack_ranks["values"][card.value] for card in hand.cards])
		await self.bot.embed_say("Dealer: {} ({})\n{}: {} ({})".format(dealer_string, dealer_total, ctx.message.author.display_name, hand_string, hand_total))
		await self.bot.embed_reply("Hit or Stay?")
		while True:
			action = await self.bot.wait_for_message(author = ctx.message.author, check = lambda msg: msg.content.lower() in ["hit", "stay"])
			if action.content.lower() == "hit":
				hand.add(deck.deal())
				hand_string = self.cards_to_string(hand.cards)
				hand_total = sum([self.blackjack_ranks["values"][card.value] for card in hand.cards])
				await self.bot.embed_say("Dealer: {} ({})\n{}: {} ({})\n".format(dealer_string, dealer_total, ctx.message.author.display_name, hand_string, hand_total))
				if hand_total > 21:
					await self.bot.embed_reply(":boom: You have busted. You lost :(")
					return
				else:
					await self.bot.embed_reply("Hit or Stay?")
			else:
				if dealer_total > 21:
					await self.bot.embed_reply("The dealer busted. You win!")
					return
				elif dealer_total > hand_total:
					await self.bot.embed_reply("The dealer beat you. You lost :(")
					return
				while True:
					dealer.add(deck.deal())
					dealer_string = self.cards_to_string(dealer.cards)
					dealer_total = sum([self.blackjack_ranks["values"][card.value] for card in dealer.cards])
					await self.bot.embed_say("Dealer: {} ({})\n{}: {} ({})\n".format(dealer_string, dealer_total, ctx.message.author.display_name, hand_string, hand_total))
					if dealer_total > 21:
						await self.bot.embed_reply("The dealer busted. You win!")
						return
					elif dealer_total > hand_total:
						await self.bot.embed_reply("The dealer beat you. You lost :(")
						return
					await asyncio.sleep(5)
	
	@commands.group(pass_context = True, invoke_without_command = True)
	@checks.not_forbidden()
	async def chess(self, ctx):
		'''
		Play chess
		Supports standard algebraic and UCI notation
		Example:
		 !chess play you
		 white
		 e2e4
		'''
		await self.bot.embed_reply("See {}help chess".format(ctx.prefix))
		
		'''
		else:
			try:
				self._chess_board.push_san(move)
			except ValueError:
				try:
					self._chess_board.push_uci(move)
				except ValueError:
					await self.bot.embed_reply(":no_entry: Invalid move")
					return
			await self._update_chess_board_embed()
		'''
	
	@chess.command(name = "play", aliases = ["start"], pass_context = True)
	@checks.not_forbidden()
	async def chess_play(self, ctx, *, opponent : str = ""):
		'''
		Challenge someone to a match
		You can play me as well
		'''
		# check if already playing a match in this channel
		if self.get_chess_match(ctx.message.channel, ctx.message.author):
			await self.bot.embed_reply(":no_entry: You're already playing a chess match here")
			return
		# prompt for opponent
		if not opponent:
			await self.bot.embed_reply("Who would you like to play?")
			message = await self.bot.wait_for_message(author = ctx.message.author, channel = ctx.message.channel)
			opponent = message.content
		color = None
		if opponent.lower() in ("harmonbot", "you"):
			opponent = self.bot.user
		elif opponent.lower() in ("myself", "me"):
			opponent = ctx.message.author
			color = 'w'
		else:
			opponent = await utilities.get_user(ctx, opponent)
			if not opponent:
				await self.bot.embed_reply(":no_entry: Opponent not found")
				return
		# check if opponent already playing a match in this channel
		if opponent != self.bot.user and self.get_chess_match(ctx.message.channel, opponent):
			await self.bot.embed_reply(":no_entry: Your chosen opponent is playing a chess match here")
			return
		# prompt for color
		if opponent == ctx.message.author:
			color = 'w'
		if not color:
			await self.bot.embed_reply("Would you like to play white, black, or random?")
			message = await self.bot.wait_for_message(author = ctx.message.author, channel = ctx.message.channel, check = lambda msg: msg.content.lower() in ("white", "black", "random", 'w', 'b', 'r'))
			color = message.content.lower()
		if color in ("random", 'r'):
			color = random.choice(('w', 'b'))
		if color in ("white", 'w'):
			white_player = ctx.message.author
			black_player = opponent
		elif color in ("black", 'b'):
			white_player = opponent
			black_player = ctx.message.author
		# prompt opponent
		if opponent != self.bot.user and opponent != ctx.message.author:
			await self.bot.say("{}: {} has challenged you to a chess match\nWould you like to accept? yes/no".format(opponent.mention, ctx.message.author))
			message = await self.bot.wait_for_message(author = opponent, channel = ctx.message.channel, check = lambda msg: msg.content.lower() in ("yes", "no", 'y', 'n'), timeout = 300)
			if not message or message.content.lower() in ("no", 'n'):
				await self.bot.say("{}: {} has declined your challenge".format(ctx.message.author.mention, opponent))
				return
		match = chess_match()
		match.initialize(self.bot, ctx.message.channel, white_player, black_player)
		self.chess_matches.append(match)
	
	def get_chess_match(self, text_channel, player):
		return discord.utils.find(lambda cb: cb.text_channel == text_channel and (cb.white_player == player or cb.black_player == player), self.chess_matches)
	
	#dm
	#check mate, etc.
	
	@chess.group(name = "board", aliases = ["match"], pass_context = True, invoke_without_command = True)
	async def chess_board(self, ctx):
		'''Current match/board'''
		match = self.get_chess_match(ctx.message.channel, ctx.message.author)
		if not match:
			await self.bot.embed_reply(":no_entry: Chess match not found")
			return
		await match.new_match_embed()
	
	@chess_board.command(name = "text", pass_context = True)
	async def chess_board_text(self, ctx):
		'''Text version of the current board'''
		match = self.get_chess_match(ctx.message.channel, ctx.message.author)
		if not match:
			await self.bot.embed_reply(":no_entry: Chess match not found")
			return
		await self.bot.reply(clients.code_block.format(match))
	
	@chess.command(name = "fen", pass_context = True)
	async def chess_fen(self, ctx):
		'''FEN of the current board'''
		match = self.get_chess_match(ctx.message.channel, ctx.message.author)
		if not match:
			await self.bot.embed_reply(":no_entry: Chess match not found")
			return
		await self.bot.embed_reply(match.fen())
	
	@chess.command(name = "pgn", pass_context = True, hidden = True)
	async def chess_pgn(self, ctx):
		'''PGN of the current game'''
		match = self.get_chess_match(ctx.message.channel, ctx.message.author)
		if not match:
			await self.bot.embed_reply(":no_entry: Chess match not found")
			return
		await self.bot.embed_reply(str(chess.pgn.Game.from_board(match)))
	
	@chess.command(name = "turn", pass_context = True, hidden = True)
	async def chess_turn(self, ctx):
		'''Who's turn it is to move'''
		match = self.get_chess_match(ctx.message.channel, ctx.message.author)
		if not match:
			await self.bot.embed_reply(":no_entry: Chess match not found")
			return
		if match.turn:
			await self.bot.embed_reply("It's white's turn to move")
		else:
			await self.bot.embed_reply("It's black's turn to move")
	
	"""
	@chess.command(name = "reset", pass_context = True)
	async def chess_reset(self, ctx):
		'''Reset the board'''
		self._chess_board.reset()
		await self.bot.embed_reply("The board has been reset")
	"""
	
	"""
	@chess.command(name = "undo", pass_context = True)
	async def chess_undo(self, ctx):
		'''Undo the previous move'''
		try:
			self._chess_board.pop()
			await self._display_chess_board(ctx, message = "The previous move was undone")
		except IndexError:
			await self.bot.embed_reply(":no_entry: There are no more moves to undo")
	"""
	
	@chess.command(name = "previous", aliases = ["last"], pass_context = True, hidden = True)
	async def chess_previous(self, ctx):
		'''Previous move'''
		match = self.get_chess_match(ctx.message.channel, ctx.message.author)
		if not match:
			await self.bot.embed_reply(":no_entry: Chess match not found")
			return
		try:
			await self.bot.embed_reply(str(match.peek()))
		except IndexError:
			await self.bot.embed_reply(":no_entry: There was no previous move")
	
	"""
	@chess.command(name = "(╯°□°）╯︵", pass_context = True, hidden = True)
	async def chess_flip(self, ctx):
		'''Flip the table over'''
		self._chess_board.clear()
		await self.bot.say(ctx.message.author.name + " flipped the table over in anger!")
	"""
	
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
	
	@commands.group(pass_context = True, invoke_without_command = True)
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
	
	@commands.group(pass_context = True, invoke_without_command = True)
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
		'''
		Trivia game
		Answers prepended with ! or > are ignored
		'''
		if not self.trivia_active:
			bet, bets = options and options[0] == "bet", {}
			self.trivia_active, responses = True, {}
			data = {}
			while not data.get("question"):
				async with aiohttp_session.get("http://jservice.io/api/random") as resp:
					data = (await resp.json())[0]
			if bet:
				self.bet_countdown = int(wait_time)
				embed = discord.Embed(title = string.capwords(data["category"]["title"]), color = clients.bot_color)
				embed.set_footer(text = "You have {} seconds left to bet".format(self.bet_countdown))
				bet_message, embed = await self.bot.say(embed = embed)
				bet_countdown_task = self.bot.loop.create_task(self._bet_countdown(bet_message, embed))
				while self.bet_countdown:
					message = await self.bot.wait_for_message(timeout = self.bet_countdown, channel = ctx.message.channel, check = lambda m: m.content.isdigit())
					if message:
						with open("data/trivia_points.json", 'r') as trivia_file:
							score = json.load(trivia_file)
						if int(message.content) <= score[message.author.id][2]:
							bets[message.author] = int(message.content)
							await self.bot.embed_say("{} has bet ${}".format(message.author.display_name, int(message.content)))
							await self.bot.delete_message(message)
						else:
							await self.bot.embed_reply("You don't have that much money to bet!")
				while not bet_countdown_task.done():
					await asyncio.sleep(0.1)
				embed.set_footer(text = "Betting is over")
				await self.bot.edit_message(bet_message, embed = embed)
			self.trivia_countdown = int(wait_time)
			embed = discord.Embed(color = clients.bot_color, title = string.capwords(data["category"]["title"]), description = data["question"])
			embed.set_footer(text = "You have {} seconds left to answer".format(self.trivia_countdown))
			answer_message, embed = await self.bot.say(embed = embed)
			countdown_task = self.bot.loop.create_task(self._trivia_countdown(answer_message, embed))
			while self.trivia_countdown:
				message = await self.bot.wait_for_message(timeout = self.trivia_countdown, channel = ctx.message.channel)
				if message and not message.content.startswith(('!', '>')):
					responses[message.author] = message.content
			while not countdown_task.done():
				await asyncio.sleep(0.1)
			embed.set_footer(text = "Time's up!")
			await self.bot.edit_message(answer_message, embed = embed)
			correct_players = []
			incorrect_players = []
			matches = re.search("\((.+)\) (.+)", data["answer"].lower())
			for player, response in responses.items():
				if data["answer"].lower() in [s + response.lower() for s in ["", "a ", "an ", "the "]] \
				or response.lower() == BeautifulSoup(html.unescape(data["answer"]), "html.parser").get_text().lower() \
				or response.lower().replace('-', ' ') == data["answer"].lower().replace('-', ' ') \
				or response.lower().replace('(', "").replace(')', "") == data["answer"].lower().replace('(', "").replace(')', "") \
				or (matches and (response.lower() == matches.group(0) or response.lower() == matches.group(1))) \
				or response.lower().strip('"') == data["answer"].lower().strip('"'):
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
						score[trivia_player.id][2] += bets[trivia_player]
						trivia_bets_output += trivia_player.name + " won $" + utilities.add_commas(bets[trivia_player]) + " and now has $" + utilities.add_commas(score[trivia_player.id][2]) + ". "
					else:
						score[trivia_player.id][2] -= bets[trivia_player]
						trivia_bets_output += trivia_player.name + " lost $" + utilities.add_commas(bets[trivia_player]) + " and now has $" + utilities.add_commas(score[trivia_player.id][2]) + ". "
				trivia_bets_output = trivia_bets_output[:-1]
			with open("data/trivia_points.json", 'w') as trivia_file:
				json.dump(score, trivia_file, indent = 4)
			embed = discord.Embed(description = "The answer was `{}`".format(BeautifulSoup(html.unescape(data["answer"]), "html.parser").get_text()), color = clients.bot_color)
			embed.set_footer(text = correct_players_output)
			await self.bot.say(embed = embed)
			if bet and trivia_bets_output:
				await self.bot.embed_say(trivia_bets_output)
			self.trivia_active = False
		else:
			await self.bot.embed_reply("There is already an ongoing game of trivia. Other options: score money")
	
	async def _bet_countdown(self, bet_message, embed):
		while self.bet_countdown:
			await asyncio.sleep(1)
			self.bet_countdown -= 1
			embed.set_footer(text = "You have {} seconds left to bet".format(self.bet_countdown))
			await self.bot.edit_message(bet_message, embed = embed)
	
	async def _trivia_countdown(self, answer_message, embed):
		while self.trivia_countdown:
			await asyncio.sleep(1)
			self.trivia_countdown -= 1
			embed.set_footer(text = "You have {} seconds left to answer".format(self.trivia_countdown))
			await self.bot.edit_message(answer_message, embed = embed)
	
	# url = "http://api.futuretraxex.com/v1/getRandomQuestion
	# await self.bot.say(BeautifulSoup(html.unescape(data["q_text"]), "html.parser").get_text() + "\n1. " + data["q_options_1"] + "\n2. " + data["q_options_2"] + "\n3. " + data["q_options_3"] + "\n4. " + data["q_options_4"])
	# if answer == data["q_correct_option"]:
	# await self.bot.say("The answer was " + str(data["q_correct_option"]) + ". " + data["q_options_" + str(data["q_correct_option"])] + "\n" + correct_players_output)
	
	@trivia.command(name = "score", aliases = ["points"], pass_context = True)
	async def trivia_score(self, ctx):
		with open("data/trivia_points.json", 'r') as trivia_file:
			score = json.load(trivia_file)
		correct = score[ctx.message.author.id][0]
		incorrect = score[ctx.message.author.id][1]
		correct_percentage = round(float(correct) / (float(correct) + float(incorrect)) * 100, 2)
		await self.bot.embed_reply("You have answered {}/{} ({}%) correctly.".format(str(correct), str(correct + incorrect), str(correct_percentage)))
	
	@trivia.command(name = "money", aliases = ["cash"], pass_context = True)
	async def trivia_money(self, ctx):
		with open("data/trivia_points.json", 'r') as trivia_file:
			score = json.load(trivia_file)
		cash = score[ctx.message.author.id][2]
		await self.bot.embed_reply("You have $" + utilities.add_commas(cash))
	
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
	
	# Utility Functions
	
	def cards_to_string(self, cards):
		return "".join([":{}: {} ".format(card.suit.lower(), card.value) for card in cards])

