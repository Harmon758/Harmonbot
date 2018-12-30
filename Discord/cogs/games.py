
import discord
from discord.ext import commands

import asyncio
import copy
import html
import json
import os
import random
import re
import string
import sys
import timeit

import aiohttp
from bs4 import BeautifulSoup
# import chess
import chess.pgn
# import deuces
import pydealer

import clients
from modules import adventure
from modules.chess import chess_match
# from modules import gofish
from modules import maze
from modules import utilities
# from modules import war
from utilities import checks

sys.path.insert(0, "..")
from units import games
sys.path.pop(0)

def setup(bot):
	bot.add_cog(Games(bot))

class Games:
	
	def __init__(self, bot):
		self.bot = bot
		self.chess_matches = []
		self.war_channel, self.war_players = None, []
		self.gofish_channel, self.gofish_players = None, []
		self.taboo_players = []
		self.mazes = {}
		self.jeopardy_active, self.jeopardy_question_active, self.jeopardy_board, self.jeopardy_answer, self.jeopardy_answered, self.jeopardy_scores, self.jeopardy_board_output, self.jeopardy_max_width = False, False, [], None, None, {}, None, None
		self.trivia_active, self.trivia_countdown, self.bet_countdown = False, None, None
		self.blackjack_ranks = copy.deepcopy(pydealer.const.DEFAULT_RANKS)
		self.blackjack_ranks["values"].update({"Ace": 0, "King": 9, "Queen": 9, "Jack": 9})
		for value in self.blackjack_ranks["values"]:
			self.blackjack_ranks["values"][value] += 1
		self.poker_status, self.poker_players, self.poker_deck, self.poker_hands, self.poker_turn, self.poker_bets, self.poker_current_bet, self.poker_pot, self.poker_community_cards, self.poker_folded = None, [], None, {}, None, {}, None, None, None, []
		#check default values
		
		self.adventure_players = {}
		
		# Necessary for maze generation
		sys.setrecursionlimit(5000)
		
		self.bot.loop.create_task(self.initialize_database())
	
	async def initialize_database(self):
		await self.bot.connect_to_database()
		await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS trivia")
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS trivia.users (
				user_id		BIGINT PRIMARY KEY, 
				correct		INT,
				incorrect	INT,
				money		INT
			)
			"""
		)
	
	# Adventure
	
	@commands.group(aliases = ["rpg"], invoke_without_command = True, hidden = True)
	@checks.not_forbidden()
	async def adventure(self, ctx):
		'''WIP'''
		pass
	
	def get_adventure_player(self, user_id):
		player = self.adventure_players.get(user_id)
		if not player:
			player = adventure.AdventurePlayer(user_id)
			self.adventure_players[user_id] = player
		return player
	
	@adventure.group(name = "stats", aliases = ["stat", "levels", "level", "lvls", "lvl"], invoke_without_command = True)
	@checks.not_forbidden()
	async def adventure_stats(self, ctx):
		'''Stats'''
		player = self.get_adventure_player(ctx.author.id)
		await ctx.embed_reply("\n:fishing_pole_and_fish: Fishing xp: {} (Level {})"
		"\n:herb: Foraging xp: {} (Level {})"
		"\n:pick: Mining xp: {} (Level {})"
		"\n:evergreen_tree: Woodcutting xp: {} (Level {})".format(player.fishing_xp, player.fishing_lvl, player.foraging_xp, player.foraging_lvl, player.mining_xp, player.mining_lvl, player.woodcutting_xp, player.woodcutting_lvl))
		# time started/played
	
	@adventure_stats.command(name = "woodcutting", aliases = ["wc"])
	@checks.not_forbidden()
	async def stats_woodcutting(self, ctx):
		'''Woodcutting stats'''
		player = self.get_adventure_player(ctx.author.id)
		woodcutting_xp = player.woodcutting_xp
		await ctx.embed_reply("\n:evergreen_tree: Woodcutting xp: {}\n{}\n{} xp to next level".format(woodcutting_xp, self.level_bar(woodcutting_xp), adventure.xp_left_to_next_lvl(woodcutting_xp)))
	
	@adventure_stats.command(name = "foraging", aliases = ["forage", "gather", "gathering"])
	@checks.not_forbidden()
	async def stats_foraging(self, ctx):
		'''Foraging stats'''
		player = self.get_adventure_player(ctx.author.id)
		foraging_xp = player.foraging_xp
		await ctx.embed_reply("\n:herb: Foraging xp: {}\n{}\n{} xp to next level".format(foraging_xp, self.level_bar(foraging_xp), adventure.xp_left_to_next_lvl(foraging_xp)))
	
	def level_bar(self, xp):
		lvl = adventure.xp_to_lvl(xp)
		previous_xp = adventure.lvl_to_xp(lvl)
		next_xp = adventure.lvl_to_xp(lvl + 1)
		difference = next_xp - previous_xp
		shaded = int((xp - previous_xp) / difference * 10)
		bar = chr(9632) * shaded + chr(9633) * (10 - shaded)
		return "Level {0} ({3} xp) [{2}] Level {1} ({4} xp)".format(lvl, lvl + 1, bar, previous_xp, next_xp)
	
	@adventure.command(name = "inventory")
	@checks.not_forbidden()
	async def adventure_inventory(self, ctx, *, item : str = ""):
		'''Inventory'''
		player = self.get_adventure_player(ctx.author.id)
		inventory = player.inventory
		if item in inventory:
			await ctx.embed_reply("{}: {}".format(item, inventory[item]))
		else:
			await ctx.embed_reply(", ".join(["{}: {}".format(item, amount) for item, amount in sorted(inventory.items())]))
	
	@adventure.command(name = "examine")
	@checks.not_forbidden()
	async def adventure_examine(self, ctx, *, item : str):
		'''Examine items'''
		player = self.get_adventure_player(ctx.author.id)
		inventory = player.inventory
		if item in inventory:
			if item in adventure.examine_messages:
				await ctx.embed_reply("{}".format(adventure.examine_messages[item]))
			else:
				await ctx.embed_reply("{}".format(item))
		else:
			await ctx.embed_reply(":no_entry: You don't have that item")
	
	@adventure.group(name = "forage", aliases = ["gather"], invoke_without_command = True)
	@checks.not_forbidden()
	async def adventure_forage(self, ctx, *, item : str = ""):
		'''Foraging'''
		player = self.get_adventure_player(ctx.author.id)
		started = player.start_foraging(item)
		if started == "foraging":
			stopped = player.stop_foraging()
			output = "\n:herb: You were foraging {0[0]} for {0[1]:.2f} min. and received {0[2]} {0[0]} and xp. While you were foraging, you also found {0[3]} {1}".format(stopped, adventure.forageables[stopped[0]][0])
			if stopped[4]:
				output += " and {0[4]} {1}!".format(stopped, adventure.forageables[stopped[0]][1])
			await ctx.embed_reply(output)
			if item:
				started = player.start_foraging(item)
			else:
				return
		if started is True:
			await ctx.embed_reply("\n:herb: You have started foraging for {}".format(item))
			# active?
		elif started is False:
			await ctx.embed_reply(":no_entry: That item type doesn't exist")
		else:
			await ctx.embed_reply(":no_entry: You're currently {}! You can't start/stop foraging right now".format(started))
	
	@adventure_forage.command(name = "start", aliases = ["on"])
	@checks.not_forbidden()
	async def forage_start(self, ctx, *, item : str):
		'''Start foraging'''
		player = self.get_adventure_player(ctx.author.id)
		started = player.start_foraging(item)
		if started is True:
			await ctx.embed_reply("\n:herb: You have started foraging for {}".format(item))
			# active?
		elif started is False:
			await ctx.embed_reply(":no_entry: That item type doesn't exist")
		else:
			await ctx.embed_reply(":no_entry: You're currently {}! You can't start foraging right now".format(started))
	
	@adventure_forage.command(name = "stop", aliases = ["off"])
	@checks.not_forbidden()
	async def forage_stop(self, ctx):
		'''Stop foraging'''
		player = self.get_adventure_player(ctx.author.id)
		stopped = player.stop_foraging()
		if stopped[0]:
			output = "\n:herb: You were foraging {0[0]} for {0[1]:.2f} min. and received {0[2]} {0[0]} and xp. While you were foraging, you also found {0[3]} {1}".format(stopped, adventure.forageables[stopped[0]][0])
			if stopped[4]:
				output += " and {0[4]} {1}!".format(stopped, adventure.forageables[stopped[0]][1])
			await ctx.embed_reply(output)
		elif stopped[1]:
			await ctx.embed_reply(":no_entry: You're currently {}! You aren't foraging right now")
		else:
			await ctx.embed_reply(":no_entry: You aren't foraging")
	
	@adventure_forage.command(name = "items", aliases = ["item", "type", "types"])
	@checks.not_forbidden()
	async def forage_items(self, ctx):
		'''Forageable items'''
		await ctx.embed_reply(", ".join(adventure.forageables.keys()))
	
	@adventure.command(name = "create", aliases = ["make", "craft"])
	@checks.not_forbidden()
	async def adventure_create(self, ctx, *items : str):
		'''
		Create item
		items: items to use to attempt to create something else
		Use quotes for spaces in item names
		'''
		player = self.get_adventure_player(ctx.author.id)
		created = player.create_item(items)
		if created is None:
			await ctx.embed_reply("You don't have those items")
		elif created is False:
			await ctx.embed_reply("You were unable to create anything with those items")
		else:
			await ctx.embed_reply("You have created {}".format(created))
	
	@adventure.group(name = "chop", aliases = ["woodcutting", "wc"], invoke_without_command = True)
	@checks.not_forbidden()
	async def adventure_woodcutting(self, ctx, *, wood_type : str = ""):
		'''Woodcutting'''
		player = self.get_adventure_player(ctx.author.id)
		started = player.start_woodcutting(wood_type)
		if started == "woodcutting":
			stopped = player.stop_woodcutting()
			await ctx.embed_reply("\n:evergreen_tree: You were chopping {0[0]} for {0[1]:.2f} min. and received {0[2]} {0[0]} and {0[3]} xp".format(stopped))
			if wood_type:
				started = player.start_woodcutting(wood_type)
			else:
				return
		if started is True:
			await ctx.embed_reply("\n:evergreen_tree: You have started chopping {} trees".format(wood_type))
			await self.woodcutting_active(ctx, wood_type)
		elif started is False:
			await ctx.embed_reply(":no_entry: That wood type doesn't exist")
		else:
			await ctx.embed_reply(":no_entry: You're currently {}! You can't start/stop woodcutting right now".format(started))
	
	@adventure_woodcutting.command(name = "start", aliases = ["on"])
	@checks.not_forbidden()
	async def woodcutting_start(self, ctx, *, wood_type : str):
		'''Start chopping wood'''
		player = self.get_adventure_player(ctx.author.id)
		started = player.start_woodcutting(wood_type)
		if started is True:
			await ctx.embed_reply("\n:evergreen_tree: You have started chopping {} trees".format(wood_type))
			await self.woodcutting_active(ctx, wood_type)
		elif started is False:
			await ctx.embed_reply(":no_entry: That wood type doesn't exist")
		else:
			await ctx.embed_reply(":no_entry: You're currently {}! You can't start woodcutting right now".format(started))
	
	async def woodcutting_active(self, ctx, wood_type):
		player = self.get_adventure_player(ctx.author.id)
		ask_message = await ctx.embed_reply("\n:grey_question: Would you like to chop {} trees actively? Yes/No".format(wood_type))
		message = await self.bot.wait_for_message(timeout = 60, author = ctx.author, check = lambda m: m.content.lower() in ('y', "yes", 'n', "no"))
		await self.bot.delete_message(ask_message)
		if not message or message.content.lower() in ('n', "no"):
			if message:
				await self.bot.delete_message(message)
			return
		rate = player.wood_rate(wood_type) * player.woodcutting_rate
		if rate == 0:
			await ctx.embed_reply(":no_entry: You can't chop this wood yet")
			return
		time = int(60 / rate)
		chopped_message = None
		while message:
			chopping = await ctx.embed_reply("\n:evergreen_tree: Chopping.. (this could take up to {} sec.)".format(time))
			await asyncio.sleep(random.randint(1, time))
			await self.bot.delete_message(message)
			await self.bot.delete_message(chopping)
			prompt = random.choice(["chop", "whack", "swing", "cut"])
			prompt_message = await ctx.embed_reply('Reply with "{}" in the next 10 sec. to continue'.format(prompt))
			message = await self.bot.wait_for_message(timeout = 10, author = ctx.author, content = prompt)
			if message:
				chopped = player.chop_once(wood_type)
				if chopped_message:
					await self.bot.delete_message(chopped_message)
				chopped_message = await ctx.embed_reply("\n:evergreen_tree: You chopped a {0} tree. You now have {1[0]} {0} and {1[1]} woodcutting xp".format(wood_type, chopped))
			else:
				await ctx.embed_reply("\n:stop_sign: You have stopped actively chopping {}".format(wood_type))
			await self.bot.delete_message(prompt_message)
	
	@adventure_woodcutting.command(name = "stop", aliases = ["off"])
	@checks.not_forbidden()
	async def woodcutting_stop(self, ctx):
		'''Stop chopping wood'''
		player = self.get_adventure_player(ctx.author.id)
		stopped = player.stop_woodcutting()
		if stopped[0]:
			await ctx.embed_reply("\n:evergreen_tree: You were chopping {0[0]} for {0[1]:.2f} min. and received {0[2]} {0[0]} and {0[3]} xp".format(stopped))
		elif stopped[1]:
			await ctx.embed_reply(":no_entry: You're currently {}! You aren't woodcutting right now")
		else:
			await ctx.embed_reply(":no_entry: You aren't woodcutting")
	
	@adventure_woodcutting.command(name = "types", aliases = ["type", "item", "items"])
	@checks.not_forbidden()
	async def woodcutting_types(self, ctx):
		'''Types of wood'''
		await ctx.embed_reply(", ".join(adventure.wood_types))
	
	@adventure_woodcutting.command(name = "rate", aliases = ["rates"])
	@checks.not_forbidden()
	async def woodcutting_rate(self, ctx, *, wood_type : str):
		'''Rate of chopping certain wood'''
		player = self.get_adventure_player(ctx.author.id)
		if wood_type in adventure.wood_types:
			await ctx.embed_reply("You will get {:.2f} {}/min. at your current level".format(player.wood_rate(wood_type) * player.woodcutting_rate, wood_type))
		else:
			await ctx.embed_reply(":no_entry: That wood type doesn't exist")
	
	# Not Adventure
	
	@commands.command()
	@checks.not_forbidden()
	async def blackjack(self, ctx):
		'''
		Play a game of blackjack
		Manage Messages permission required for message cleanup
		'''
		# TODO: S17
		deck = pydealer.Deck()
		deck.shuffle()
		dealer = deck.deal(2)
		player = deck.deal(2)
		dealer_string = ":grey_question: :{}: {}".format(dealer.cards[1].suit.lower(), dealer.cards[1].value)
		player_string = self.cards_to_string(player.cards)
		dealer_total = self.blackjack_total(dealer.cards)
		player_total = self.blackjack_total(player.cards)
		response = await ctx.embed_reply("Dealer: {} (?)\n{}: {} ({})\n".format(dealer_string, ctx.author.display_name, player_string, player_total), title = "Blackjack", footer_text = "Hit or Stay?")
		embed = response.embeds[0]
		while True:
			action = await self.bot.wait_for("message", check = lambda m: m.author == ctx.author and m.content.lower().strip('!') in ("hit", "stay"))
			await self.bot.attempt_delete_message(action)
			if action.content.lower().strip('!') == "hit":
				player.add(deck.deal())
				player_string = self.cards_to_string(player.cards)
				player_total = self.blackjack_total(player.cards)
				embed.description = "Dealer: {} (?)\n{}: {} ({})\n".format(dealer_string, ctx.author.display_name, player_string, player_total)
				await response.edit(embed = embed)
				if player_total > 21:
					embed.description += ":boom: You have busted"
					embed.set_footer(text = "You lost :(")
					break
			else:
				dealer_string = self.cards_to_string(dealer.cards)
				embed.description = "Dealer: {} ({})\n{}: {} ({})\n".format(dealer_string, dealer_total, ctx.author.display_name, player_string, player_total)
				if dealer_total > 21:
					embed.description += ":boom: The dealer busted"
					embed.set_footer(text = "You win!")
					break
				elif dealer_total > player_total:
					embed.description += "The dealer beat you"
					embed.set_footer(text = "You lost :(")
					break
				embed.set_footer(text = "Dealer's turn..")
				await response.edit(embed = embed)
				while True:
					await asyncio.sleep(5)
					dealer.add(deck.deal())
					dealer_string = self.cards_to_string(dealer.cards)
					dealer_total = self.blackjack_total(dealer.cards)
					embed.description = "Dealer: {} ({})\n{}: {} ({})\n".format(dealer_string, dealer_total, ctx.author.display_name, player_string, player_total)
					await response.edit(embed = embed)
					if dealer_total > 21:
						embed.description += ":boom: The dealer busted"
						embed.set_footer(text = "You win!")
						break
					elif dealer_total > player_total:
						embed.description += "The dealer beat you"
						embed.set_footer(text = "You lost :(")
						break
					elif dealer_total == player_total == 21:
						embed.set_footer(text = "It's a push (tie)")
						break
				break
		await response.edit(embed = embed)
	
	def blackjack_total(self, cards):
		total = sum(self.blackjack_ranks["values"][card.value] for card in cards)
		if pydealer.tools.find_card(cards, term = "Ace", limit = 1) and total <= 11: total += 10
		return total
	
	@commands.group(invoke_without_command = True)
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
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
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
	
	@chess.command(name = "play", aliases = ["start"])
	@checks.not_forbidden()
	async def chess_play(self, ctx, *, opponent : str = ""):
		'''
		Challenge someone to a match
		You can play me as well
		'''
		# check if already playing a match in this channel
		if self.get_chess_match(ctx.channel, ctx.author):
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
		if opponent != self.bot.user and self.get_chess_match(ctx.channel, opponent):
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
		match = chess_match()
		match.initialize(self.bot, ctx.channel, white_player, black_player)
		self.chess_matches.append(match)
	
	def get_chess_match(self, text_channel, player):
		return discord.utils.find(lambda cb: cb.text_channel == text_channel and (cb.white_player == player or cb.black_player == player), self.chess_matches)
	
	#dm
	#check mate, etc.
	
	@chess.group(name = "board", aliases = ["match"], invoke_without_command = True)
	async def chess_board(self, ctx):
		'''Current match/board'''
		match = self.get_chess_match(ctx.channel, ctx.author)
		if not match:
			await ctx.embed_reply(":no_entry: Chess match not found")
			return
		await match.new_match_embed()
	
	@chess_board.command(name = "text")
	async def chess_board_text(self, ctx):
		'''Text version of the current board'''
		match = self.get_chess_match(ctx.channel, ctx.author)
		if not match:
			await ctx.embed_reply(":no_entry: Chess match not found")
			return
		await ctx.reply(clients.code_block.format(match))
	
	@chess.command(name = "fen")
	async def chess_fen(self, ctx):
		'''FEN of the current board'''
		match = self.get_chess_match(ctx.channel, ctx.author)
		if not match:
			await ctx.embed_reply(":no_entry: Chess match not found")
			return
		await ctx.embed_reply(match.fen())
	
	@chess.command(name = "pgn", hidden = True)
	async def chess_pgn(self, ctx):
		'''PGN of the current game'''
		match = self.get_chess_match(ctx.channel, ctx.author)
		if not match:
			await ctx.embed_reply(":no_entry: Chess match not found")
			return
		await ctx.embed_reply(chess.pgn.Game.from_board(match))
	
	@chess.command(name = "turn", hidden = True)
	async def chess_turn(self, ctx):
		'''Who's turn it is to move'''
		match = self.get_chess_match(ctx.channel, ctx.author)
		if not match:
			await ctx.embed_reply(":no_entry: Chess match not found")
			return
		if match.turn:
			await ctx.embed_reply("It's white's turn to move")
		else:
			await ctx.embed_reply("It's black's turn to move")
	
	"""
	@chess.command(name = "reset")
	async def chess_reset(self, ctx):
		'''Reset the board'''
		self._chess_board.reset()
		await ctx.embed_reply("The board has been reset")
	"""
	
	"""
	@chess.command(name = "undo")
	async def chess_undo(self, ctx):
		'''Undo the previous move'''
		try:
			self._chess_board.pop()
			await self._display_chess_board(ctx, message = "The previous move was undone")
		except IndexError:
			await ctx.embed_reply(":no_entry: There are no more moves to undo")
	"""
	
	@chess.command(name = "previous", aliases = ["last"], hidden = True)
	async def chess_previous(self, ctx):
		'''Previous move'''
		match = self.get_chess_match(ctx.channel, ctx.author)
		if not match:
			await ctx.embed_reply(":no_entry: Chess match not found")
			return
		try:
			await ctx.embed_reply(match.peek())
		except IndexError:
			await ctx.embed_reply(":no_entry: There was no previous move")
	
	"""
	@chess.command(name = "(╯°□°）╯︵", hidden = True)
	async def chess_flip(self, ctx):
		'''Flip the table over'''
		self._chess_board.clear()
		await ctx.say(ctx.author.name + " flipped the table over in anger!")
	"""
	
	@commands.command(aliases = ["talk", "ask"])
	@checks.not_forbidden()
	async def cleverbot(self, ctx, *, message : str):
		'''
		Talk to Cleverbot
		Uses [Cleverbot](http://www.cleverbot.com/)'s [API](https://www.cleverbot.com/api/)
		'''
		response = await self.cleverbot_get_reply(message)
		await ctx.embed_reply(response)
	
	async def cleverbot_get_reply(self, message):
		# TODO: Rename to get_cleverbot_reply
		# TODO: Include user-specific conversation state
		# TODO: Move to utilities?
		url = "https://www.cleverbot.com/getreply"
		params = {"key": self.bot.CLEVERBOT_API_KEY, "input": message}
		async with clients.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		return data["output"]
	
	@commands.command(name = "8ball", aliases = ["eightball", '\N{BILLIARDS}'])
	@checks.not_forbidden()
	async def eightball(self, ctx):
		'''
		Ask 8ball a yes or no question
		Also triggers on \N{BILLIARDS} without prefix
		'''
		await ctx.embed_reply(f"\N{BILLIARDS} {games.eightball()}")
	
	@commands.group(hidden = True)
	@checks.not_forbidden()
	async def gofish(self, ctx):
		'''WIP'''
		return
	
	@gofish.command(hidden = True, name = "start")
	@commands.guild_only()
	@commands.is_owner()
	async def gofish_start(self, ctx, *players : str):
		'''WIP'''
		self.gofish_channel = ctx.channel
		if ctx.guild:
			for member in ctx.guild.members:
				if member.name in players:
					self.gofish_players.append(member)
					break
		else:
			await ctx.embed_reply(":no_entry: Please use that command in a server")
			pass
		gofish.start(len(players))
		gofish_players_string = ""
		for player in self.gofish_players:
			gofish_players_string += player.name + " and "
		await ctx.embed_reply("{} has started a game of Go Fish between {}!".format(message.author.display_name, gofish_players_string[:-5]))
	
	@gofish.command(hidden = True, name = "hand")
	@commands.is_owner()
	async def gofish_hand(self, ctx):
		'''WIP'''
		if ctx.author in gofish_players:
			await ctx.whisper("Your hand: " + gofish.hand(gofish_players.index(ctx.author) + 1))
	
	@gofish.command(hidden = True, name = "ask")
	@commands.is_owner()
	async def gofish_ask(self, ctx):
		'''WIP'''
		if ctx.author in gofish_players:
			pass
	
	@commands.group(invoke_without_command = True)
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
			await ctx.embed_reply("What range of numbers would you like to guess to? 1 to _")
			try:
				max_value = await self.bot.wait_for("message", timeout = clients.wait_time, check = lambda m: m.author == ctx.author and utilities.message_is_digit_gtz(m))
			except asyncio.TimeoutError:
				max_value = 10
			else:
				max_value = int(max_value.content)
		answer = random.randint(1, max_value)
		if not tries:
			await ctx.embed_reply("How many tries would you like?")
			try:
				tries = await self.bot.wait_for("message", timeout = clients.wait_time, check = lambda m: m.author == ctx.author and utilities.message_is_digit_gtz(m))
			except asyncio.TimeoutError:
				tries = 1
			else:
				tries = int(tries.content)
		await ctx.embed_reply("Guess a number between 1 to {}".format(max_value))
		while tries != 0:
			try:
				guess = await self.bot.wait_for("message", timeout = clients.wait_time, check = lambda m: m.author == ctx.author and utilities.message_is_digit_gtz(m))
			except asyncio.TimeoutError:
				await ctx.embed_reply("Sorry, you took too long\nIt was {}".format(answer))
				return
			if int(guess.content) == answer:
				await ctx.embed_reply("You are right!")
				return
			elif tries != 1 and int(guess.content) > answer:
				await ctx.embed_reply("It's less than " + guess.content)
				tries -= 1
			elif tries != 1 and int(guess.content) < answer:
				await ctx.embed_reply("It's greater than " + guess.content)
				tries -= 1
			else:
				await ctx.embed_reply("Sorry, it was actually {}".format(answer))
				return
	
	@commands.group(aliases = ["hrmp"], hidden = True)
	@checks.not_forbidden()
	async def harmonopoly(self, ctx):
		'''
		WIP
		Harmonopoly is a game based on The Centipede Game where every player chooses a number.
		The player with the lowest number that is not surpassed within +2 of another number that is chosen, wins. The winner gets points equal to the number that they chose.
		Examples: {1,2 Winner(W): 2} {1,3 W: 3} {1,4 W: 1} {1,3,5 W: 5} {1,3,5,7,10 W: 7}
		'''
		pass
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def jeopardy(self, ctx, row_number : int, value : int):
		'''
		Trivia with categories
		jeopardy [row number] [value] to pick the question
		Based on Jeopardy
		'''
		if not self.jeopardy_active:
			await ctx.embed_reply(":no_entry: There's not a jeopardy game currently in progress")
			return
		if self.jeopardy_question_active:
			await ctx.embed_reply(":no_entry: There's already a jeopardy question in play")
			return
		if row_number < 1 or row_number > 6:
			await ctx.embed_reply(":no_entry: That's not a valid row number")
			return
		if value not in [200, 400, 600, 800, 1000]:
			await ctx.embed_reply(":no_entry: That's not a valid value")
			return
		value_index = ["200", "400", "600", "800", "1000"].index(str(value))
		if not self.jeopardy_board[row_number - 1][value_index + 1]:
			self.jeopardy_question_active = True
			self.jeopardy_answered = None
			url = "http://jservice.io/api/category?id=" + str(self.jeopardy_board[row_number - 1][0])
			async with clients.aiohttp_session.get(url) as resp:
				data = await resp.json()
			self.jeopardy_answer = data["clues"][value_index]["answer"]
			await ctx.embed_say("Category: " + string.capwords(data["title"]) + "\n" + data["clues"][value_index]["question"])
			counter = int(clients.wait_time)
			answer_message, embed = await ctx.say("You have {} seconds left to answer".format(str(counter)))
			self.bot.loop.create_task(self.jeopardy_wait_for_answer())
			while counter:
				await asyncio.sleep(1)
				counter -= 1
				await answer_message.edit("You have {} seconds left to answer".format(counter))
				if self.jeopardy_answered:
					break
			await answer_message.edit("Time's up!")
			if self.jeopardy_answered:
				if self.jeopardy_answered in self.jeopardy_scores:
					self.jeopardy_scores[self.jeopardy_answered] += int(value)
				else:
					self.jeopardy_scores[self.jeopardy_answered] = int(value)
				answered_message = "{} was right! They now have ${}.".format(self.jeopardy_answered.name, str(self.jeopardy_scores[self.jeopardy_answered]))
			else:
				answered_message = "Nobody got it right"
			score_output = ""
			for player, score in self.jeopardy_scores.items():
				score_output += "{}: ${}, ".format(player.name, str(score))
			score_output = score_output[:-2]
			self.jeopardy_board[row_number - 1][value_index + 1] = True
			clue_delete_cursor = (self.jeopardy_max_width + 2) * row_number + 1 * (row_number - 1) + 20 * (row_number - 1) + 4 * value_index
			if value_index == 4:
				self.jeopardy_board_output = self.jeopardy_board_output[:clue_delete_cursor] + "    " + self.jeopardy_board_output[clue_delete_cursor + 4:]
			else:
				self.jeopardy_board_output = self.jeopardy_board_output[:clue_delete_cursor] + "   " + self.jeopardy_board_output[clue_delete_cursor + 3:]
			await ctx.embed_say("The answer was " + BeautifulSoup(html.unescape(self.jeopardy_answer), "html.parser").get_text() + "\n" + answered_message + "\n" + score_output + "\n```" + self.jeopardy_board_output + "```")
			self.jeopardy_question_active = False
	
	async def jeopardy_wait_for_answer(self):
		if self.jeopardy_question_active:
			try:
				message = await self.bot.wait_for("message", timeout = clients.wait_time, check = lambda m: self.jeopardy_answer.lower() in [s + m.content.lower() for s in ["", "a ", "an ", "the "]] or m.content.lower() == BeautifulSoup(html.unescape(self.jeopardy_answer.lower()), "html.parser").get_text().lower())
			except asyncio.TimeoutError:
				return
			if not message.content.startswith('>'):
				self.jeopardy_answered = message.author
	
	#jeopardy stats
	
	@jeopardy.command(name = "start")
	async def jeopardy_start(self, ctx):
		if self.jeopardy_active:
			await ctx.embed_reply(":no_entry: There's already a jeopardy game in progress")
			return
		self.jeopardy_active = True
		categories = []
		category_titles = []
		self.jeopardy_board_output = ""
		url = "http://jservice.io/api/random"
		for i in range(6):
			async with clients.aiohttp_session.get(url) as resp:
				data = await resp.json()
			categories.append(data[0]["category_id"])
		for category in categories:
			url = "http://jservice.io/api/category?id=" + str(category)
			async with clients.aiohttp_session.get(url) as resp:
				data = await resp.json()
			category_titles.append(string.capwords(data["title"]))
			self.jeopardy_board.append([category, False, False, False, False, False])
		self.jeopardy_max_width = max(len(category_title) for category_title in category_titles)
		for category_title in category_titles:
			self.jeopardy_board_output += category_title.ljust(self.jeopardy_max_width) + "  200 400 600 800 1000\n"
		await ctx.embed_say(clients.code_block.format(self.jeopardy_board_output))
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def maze(self, ctx):
		'''
		Maze game
		[w, a, s, d] to move
		Also see mazer
		'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	@maze.command(name = "start", aliases = ["begin"])
	@checks.not_forbidden()
	async def maze_start(self, ctx, width : int = 5, height : int = 5, random_start : bool = False, random_end : bool = False):
		'''
		Start a maze game
		width: 2 - 100
		height: 2 - 100
		'''
		if ctx.channel.id in self.mazes:
			await ctx.embed_reply(":no_entry: There's already a maze game going on")
			return
		self.mazes[ctx.channel.id] = maze.Maze(width, height, random_start = random_start, random_end = random_end)
		maze_instance = self.mazes[ctx.channel.id]
		maze_message = await ctx.embed_reply(clients.code_block.format(maze_instance.print_visible()))
		'''
		maze_print = ""
		for r in maze_instance.test_print():
			row_print = ""
			for cell in r:
				row_print += cell + ' '
			maze_print += row_print + "\n"
		await ctx.reply(clients.code_block.format(maze_print))
		'''
		# await ctx.reply(clients.code_block.format(repr(maze_instance)))
		convert_move = {'w' : 'n', 'a' : 'w', 's' : 's', 'd' : 'e'}
		while not maze_instance.reached_end():
			move = await self.bot.wait_for("message", check = lambda message: message.content.lower() in ['w', 'a', 's', 'd'] and message.channel == ctx.channel) # author = ctx.author
			moved = maze_instance.move(convert_move[move.content.lower()])
			response = clients.code_block.format(maze_instance.print_visible())
			if not moved:
				response += "\n:no_entry: You can't go that way"
			new_maze_message = await ctx.embed_reply(response)
			await self.bot.attempt_delete_message(move)
			await self.bot.attempt_delete_message(maze_message)
			maze_message = new_maze_message
		await ctx.embed_reply("Congratulations! You reached the end of the maze in {} moves".format(maze_instance.move_counter))
		del self.mazes[ctx.channel.id]
	
	@maze.command(name = "current")
	@checks.not_forbidden()
	async def maze_current(self, ctx):
		'''Current maze game'''
		if ctx.channel.id in self.mazes:
			await ctx.embed_reply(clients.code_block.format(self.mazes[ctx.channel.id].print_visible()))
		else:
			await ctx.embed_reply(":no_entry: There's no maze game currently going on")
	
	# add maze print, position?
	
	@commands.group()
	@checks.not_forbidden()
	async def poker(self, ctx):
		'''WIP'''
		...
	
	@poker.command(name = "start")
	async def poker_start(self, ctx):
		if self.poker_status not in (None, "started"):
			await ctx.embed_reply("There's already a round of poker in progress")
		elif self.poker_status is None:
			self.poker_status = "started"
			self.poker_players = []
			self.poker_hands = {}
			# reset other
			self.poker_deck = pydealer.Deck()
			self.poker_deck.shuffle()
			self.poker_pot = 0
			await ctx.embed_say("{0} has started a round of poker\n`{1}poker join` to join\n`{1}poker start` again to start".format(ctx.author.display_name, ctx.prefix))
		else:
			self.poker_status = "pre-flop"
			await ctx.embed_say("The poker round has started\nPlayers: {}".format(" ".join([player.mention for player in self.poker_players])))
			for player in self.poker_players:
				cards_string = self.cards_to_string(self.poker_hands[player.id].cards)
				await self.bot.send_embed(player, "Your poker hand: {}".format(cards_string))
			await self.poker_betting()
			while self.poker_status:
				await asyncio.sleep(1)
			await ctx.embed_say("The pot: {}".format(self.poker_pot))
			self.poker_community_cards = self.poker_deck.deal(3)
			await ctx.embed_say("The flop: {}".format(self.cards_to_string(self.poker_community_cards)))
			await self.poker_betting()
			while self.poker_status:
				await asyncio.sleep(1)
			await ctx.embed_say("The pot: {}".format(self.poker_pot))
			self.poker_community_cards.add(self.poker_deck.deal(1))
			await ctx.embed_say("The turn: {}".format(self.cards_to_string(self.poker_community_cards)))
			await self.poker_betting()
			while self.poker_status:
				await asyncio.sleep(1)
			await ctx.embed_say("The pot: {}".format(self.poker_pot))
			self.poker_community_cards.add(self.poker_deck.deal(1))
			await ctx.embed_say("The river: {}".format(self.cards_to_string(self.poker_community_cards)))
			await self.poker_betting()
			while self.poker_status:
				await asyncio.sleep(1)
			await ctx.embed_say("The pot: {}".format(self.poker_pot))
			
			evaluator = deuces.Evaluator()
			board = []
			for card in self.poker_community_cards.cards:
				abbreviation = pydealer.card.card_abbrev(card.value[0] if card.value != "10" else 'T', card.suit[0].lower())
				board.append(deuces.Card.new(abbreviation))
			best_hand_value = 7462
			best_player = None
			for player, hand in self.poker_hands.items():
				hand_stack = []
				for card in hand:
					abbreviation = pydealer.card.card_abbrev(card.value[0] if card.value != "10" else 'T', card.suit[0].lower())
					hand_stack.append(deuces.Card.new(abbreviation))
				value = evaluator.evaluate(board, hand_stack)
				if value < best_hand_value:
					best_hand_value = value
					best_player = player
			player = await self.bot.get_user_info(player)
			type = evaluator.class_to_string(evaluator.get_rank_class(best_hand_value))
			await ctx.embed_say("{} is the winner with a {}".format(player.mention, type))
	
	@poker.command(name = "join")
	async def poker_join(self, ctx):
		if self.poker_status == "started":
			self.poker_players.append(ctx.author)
			self.poker_hands[ctx.author.id] = self.poker_deck.deal(2)
			await ctx.embed_say("{} has joined the poker match".format(ctx.author.display_name))
		elif self.poker_status is None:
			await ctx.embed_reply("There's not currently a round of poker going on\nUse `{}poker start` to start one".format(ctx.prefix))
		else:
			await ctx.embed_reply(":no_entry: The current round of poker already started")
	
	@poker.command(name = "raise")
	async def poker_raise(self, ctx, points : int):
		if self.poker_turn and self.poker_turn.id == ctx.author.id:
			if points > self.poker_current_bet:
				self.poker_bets[self.poker_turn.id] = points
				self.poker_current_bet = points
				await ctx.embed_reply("{} has raised to {}".format(ctx.author.display_name, points))
				self.poker_turn = None
			elif points == self.poker_current_bet:
				self.poker_bets[self.poker_turn.id] = points
				await ctx.embed_say("{} has called".format(ctx.author.display_name))
				self.poker_turn = None
			else:
				await ctx.embed_reply("The current bet is more than that")
		else:
			await ctx.embed_reply(":no_entry: You can't do that right now")
	
	@poker.command(name = "call")
	async def poker_call(self, ctx):
		if self.poker_turn and self.poker_turn.id == ctx.author.id:
			if self.poker_current_bet == 0 or (self.poker_turn.id in self.poker_bets and self.poker_bets[self.poker_turn.id] == self.poker_current_bet):
				await ctx.embed_reply("You can't call\nYou have checked instead")
				await ctx.embed_say("{} has checked".format(ctx.author.display_name))
			else:
				self.poker_bets[self.poker_turn.id] = self.poker_current_bet
				await ctx.embed_say("{} has called".format(ctx.author.display_name))
			self.poker_turn = None
		else:
			await ctx.embed_reply(":no_entry: You can't do that right now")
	
	@poker.command(name = "check")
	async def poker_check(self, ctx):
		if self.poker_turn and self.poker_turn.id == ctx.author.id:
			if self.poker_current_bet != 0 and (self.poker_turn.id not in self.poker_bets or self.poker_bets[self.poker_turn.id] < self.poker_current_bet):
				await ctx.embed_reply(":no_entry: You can't check")
			else:
				self.poker_bets[self.poker_turn.id] = self.poker_current_bet
				await ctx.embed_say("{} has checked".format(ctx.author.display_name))
				self.poker_turn = None
		else:
			await ctx.embed_reply(":no_entry: You can't do that right now.")
	
	@poker.command(name = "fold")
	async def poker_fold(self, ctx):
		if self.poker_turn and self.poker_turn.id == ctx.author.id:
			self.poker_bets[self.poker_turn.id] = -1
			self.poker_folded.append(self.poker_turn)
			self.poker_turn = None
		else:
			await ctx.embed_reply(":no_entry: You can't do that right now")
	
	async def poker_betting(self):
		self.poker_status = "betting"
		self.poker_current_bet = 0
		while True:
			for player in self.poker_players:
				self.poker_turn = player
				if player in self.poker_folded:
					continue
				await ctx.embed_say("{}'s turn".format(player.mention))
				while self.poker_turn:
					await asyncio.sleep(1)
			if all([bet == -1 or bet == self.poker_current_bet for bet in self.poker_bets.values()]):
				break
		for bet in self.poker_bets.values():
			if bet != -1:
				self.poker_pot += bet
		self.poker_status = None
	
	@commands.command(aliases = ["rtg", "reactiontime", "reactiontimegame", "reaction_time_game"])
	@checks.not_forbidden()
	async def reaction_time(self, ctx):
		'''Reaction time game'''
		# TODO: Use embeds
		# TODO: Randomly add reactions
		response = await ctx.send("Please choose 10 reactions")
		while len(response.reactions) < 10:
			await self.bot.wait_for_reaction(message = response)
			response = await self.bot.get_message(ctx.channel, response.id)
		reactions = response.reactions
		reaction = random.choice(reactions)
		await response.edit(content = "Please wait..")
		for _reaction in reactions:
			try:
				await self.bot.add_reaction(response, _reaction.emoji)
			except discord.HTTPException:
				await response.edit(content = ":no_entry: Error: Please don't deselect your reactions before I've selected them")
				return
		for countdown in range(10, 0, -1):
			await response.edit(content = "First to select the reaction _ wins.\nMake sure to have all the reactions deselected.\nGet ready! {}".format(countdown))
			await asyncio.sleep(1)
		await response.edit(content = "First to select the reaction {} wins. Go!".format(reaction.emoji))
		start_time = timeit.default_timer()
		winner = await self.bot.wait_for_reaction(message = response, emoji = reaction.emoji)
		elapsed = timeit.default_timer() - start_time
		await response.edit(content = "{} was the first to select {} and won with a time of {:.5} seconds!".format(winner.user.display_name, reaction.emoji, elapsed))
	
	@commands.command(aliases = ["rockpaperscissors", "rock-paper-scissors", "rock_paper_scissors"])
	@checks.not_forbidden()
	async def rps(self, ctx, object : str):
		'''Rock paper scissors'''
		if object.lower() not in ('r', 'p', 's', "rock", "paper", "scissors"):
			await ctx.embed_reply(":no_entry: That's not a valid object")
			return
		value = random.choice(("rock", "paper", "scissors"))
		short_shape = object[0].lower()
		resolution = {'r': {'s': "crushes"}, 'p': {'r': "covers"}, 's': {'p': "cuts"}}
		emotes = {'r': ":fist::skin-tone-2:", 'p': ":raised_hand::skin-tone-2:", 's': ":v::skin-tone-2:"}
		if value[0] == short_shape:
			await ctx.embed_reply("\nI chose `{}`\nIt's a draw :confused:".format(value))
		elif short_shape in resolution[value[0]]:
			await ctx.embed_reply("\nI chose `{}`\n{} {} {}\nYou lose :slight_frown:".format(value, emotes[value[0]], resolution[value[0]][short_shape], emotes[short_shape]))
		else:
			await ctx.embed_reply("\nI chose `{}`\n{} {} {}\nYou win! :tada:".format(value, emotes[short_shape], resolution[short_shape][value[0]], emotes[value[0]]))
	
	@commands.command(aliases = ["rockpaperscissorslizardspock", "rock-paper-scissors-lizard-spock"])
	@checks.not_forbidden()
	async def rpsls(self, ctx, object : str):
		'''
		RPS lizard Spock
		https://upload.wikimedia.org/wikipedia/commons/f/fe/Rock_Paper_Scissors_Lizard_Spock_en.svg
		'''
		if object.lower() not in ('r', 'p', 's', 'l', "rock", "paper", "scissors", "lizard", "spock"):
			await ctx.embed_reply(":no_entry: That's not a valid object")
		else:
			value = random.choice(("rock", "paper", "scissors", "lizard", "Spock"))
			short_shape = 'S' if object[0] == 'S' and object.lower() != "scissors" or object.lower() == "spock" else object[0].lower()
			resolution = {'r': {'s': "crushes", 'l': "crushes"}, 'p': {'r': "covers", 'S': "disproves"}, 's': {'p': "cuts", 'l': "decapitates"}, 'l': {'p': "eats", 'S': "poisons"}, 'S': {'r': "vaporizes", 's': "smashes"}}
			emotes = {'r': ":fist::skin-tone-2:", 'p': ":raised_hand::skin-tone-2:", 's': ":v::skin-tone-2:", 'l': ":lizard:", 'S': ":vulcan::skin-tone-2:"}
			if value[0] == short_shape:
				await ctx.embed_reply("\nI chose `{}`\nIt's a draw :confused:".format(value))
			elif short_shape in resolution[value[0]]:
				await ctx.embed_reply("\nI chose `{}`\n{} {} {}\nYou lose :slight_frown:".format(value, emotes[value[0]], resolution[value[0]][short_shape], emotes[short_shape]))
			else:
				await ctx.embed_reply("\nI chose `{}`\n{} {} {}\nYou win! :tada:".format(value, emotes[short_shape], resolution[short_shape][value[0]], emotes[value[0]]))
	
	@commands.command(aliases = ["rockpaperscissorslizardspockspidermanbatmanwizardglock", "rock-paper-scissors-lizard-spock-spiderman-batman-wizard-glock"])
	@checks.not_forbidden()
	async def rpslssbwg(self, ctx, object : str):
		'''
		RPSLS Spider-Man Batman wizard Glock
		http://i.imgur.com/m9C2UTP.jpg
		'''
		object = object.lower().replace('-', "")
		if object not in ("rock", "paper", "scissors", "lizard", "spock", "spiderman", "batman", "wizard", "glock"):
			await ctx.embed_reply(":no_entry: That's not a valid object")
		else:
			value = random.choice(("rock", "paper", "scissors", "lizard", "Spock", "Spider-Man", "Batman", "wizard", "Glock"))
			resolution = {"rock": {"scissors": "crushes", "lizard": "crushes", "spiderman": "knocks out", "wizard": "interrupts"}, 
			"paper": {"rock": "covers", "spock": "disproves", "batman": "delays", "glock": "jams"}, 
			"scissors": {"paper": "cuts", "lizard": "decapitates", "spiderman": "cuts", "wizard": "cuts"}, 
			"lizard": {"paper": "eats", "spock": "poisons", "batman": "confuses", "glock": "is too small for"}, 
			"spock": {"rock": "vaporizes", "scissors": "smashes", "spiderman": "befuddles", "wizard": "zaps"}, 
			"spiderman": {"paper": "rips", "lizard": "defeats", "wizard": "annoys", "glock": "disarms"}, 
			"batman": {"rock": "explodes", "scissors": "dismantles", "spiderman": "scares", "spock": "hangs"}, 
			"wizard": {"paper": "burns", "lizard": "transforms", "batman": "stuns", "glock": "melts"}, 
			"glock": {"rock": "breaks", "scissors": "dents", "batman": "kills parents of", "spock": "shoots"}}
			emotes = {"rock": ":fist::skin-tone-2:", "paper": ":raised_hand::skin-tone-2:", "scissors": ":v::skin-tone-2:", "lizard": ":lizard:", "spock": ":vulcan::skin-tone-2:", "spiderman": ":spider:", "batman": ":bat:", "wizard": ":tophat:", "glock": ":gun:"}
			standard_value = value.lower().replace('-', "")
			if standard_value == object:
				await ctx.embed_reply("\nI chose `{}`\nIt's a draw :confused:".format(value))
			elif object in resolution[standard_value]:
				await ctx.embed_reply("\nI chose `{}`\n{} {} {}\nYou lose :slight_frown:".format(value, emotes[standard_value], resolution[standard_value][object], emotes[object]))
			else:
				await ctx.embed_reply("\nI chose `{}`\n{} {} {}\nYou win! :tada:".format(value, emotes[object], resolution[object][standard_value], emotes[standard_value]))
	
	@commands.command(aliases = ["cockroachfootnuke", "cockroach-foot-nuke"])
	@checks.not_forbidden()
	async def cfn(self, ctx, object : str):
		'''
		Cockroach foot nuke
		https://www.youtube.com/watch?v=wRi2j8k0vjo
		'''
		if object.lower() not in ('c', 'f', 'n', "cockroach", "foot", "nuke"):
			await ctx.embed_reply(":no_entry: That's not a valid object")
		else:
			value = random.choice(("cockroach", "foot", "nuke"))
			short_shape = object[0].lower()
			resolution = {'c': {'n': "survives"}, 'f': {'c': "squashes"}, 'n': {'f': "blows up"}}
			emotes = {'c': ":bug:", 'f': ":footprints:", 'n': ":bomb:"}
			if value[0] == short_shape:
				await ctx.embed_reply("\nI chose `{}`\nIt's a draw :confused:".format(value))
			elif short_shape in resolution[value[0]]:
				await ctx.embed_reply("\nI chose `{}`\n{} {} {}\nYou lose :slight_frown:".format(value, emotes[value[0]], resolution[value[0]][short_shape], emotes[short_shape]))
			else:
				await ctx.embed_reply("\nI chose `{}`\n{} {} {}\nYou win! :tada:".format(value, emotes[short_shape], resolution[short_shape][value[0]], emotes[value[0]]))
	
	@commands.command(aliases = ["extremerps", "rps-101", "rps101"])
	@checks.not_forbidden()
	async def erps(self, ctx, object : str):
		'''
		Extreme rock paper scissors
		http://www.umop.com/rps101.htm
		http://www.umop.com/rps101/alloutcomes.htm
		http://www.umop.com/rps101/rps101chart.html
		'''
		# Harmonbot option
		object = object.lower().replace('.', "").replace("video game", "game")
		# dynamite: outwits gun
		# tornado: sweeps away -> blows away, fills pit, ruins camera
		emotes = {"dynamite": ":boom:", "tornado": ":cloud_tornado:", "quicksand": "quicksand", "pit": ":black_circle:", "chain": ":chains:", "gun": ":gun:", "law": ":scales:", "whip": "whip", "sword": ":crossed_swords:", "rock": ":fist::skin-tone-2:", "death": ":skull:", "wall": "wall", "sun": ":sunny:", "camera": ":camera:", "fire": ":fire:", "chainsaw": "chainsaw", "school": ":school:", "scissors": ":scissors:", "poison": "poison", "cage": "cage", "axe": "axe", "peace": ":peace:", "computer": ":computer:", "castle": ":european_castle:", "snake": ":snake:", "blood": "blood", "porcupine": "porcupine", "vulture": "vulture", "monkey": ":monkey:", "king": "king", "queen": "queen", "prince": "prince", "princess": "princess", "police": ":police_car:", "woman": ":woman::skin-tone-2:", "baby": ":baby::skin-tone-2:", "man": ":man::skin-tone-2:", "home": ":homes:", "train": ":train:", "car": ":red_car:", "noise": "noise", "bicycle": ":bicyclist::skin-tone-2:", "tree": ":evergreen_tree:", "turnip": "turnip", "duck": ":duck:", "wolf": ":wolf:", "cat": ":cat:", "bird": ":bird:", "fish": ":fish:", "spider": ":spider:", "cockroach": "cockroach", "brain": "brain", "community": "community", "cross": ":cross:", "money": ":moneybag:", "vampire": "vampire", "sponge": "sponge", "church": ":church:", "butter": "butter", "book": ":book:", "paper": ":raised_hand::skin-tone-2:", "cloud": ":cloud:", "airplane": ":airplane:", "moon": ":full_moon:", "grass": "grass", "film": ":film_frames:", "toilet": ":toilet:", "air": "air", "planet": "planet", "guitar": ":guitar:", "bowl": "bowl", "cup": "cup", "beer": ":beer:", "rain": ":cloud_rain:", "water": ":potable_water:", "tv": ":tv:", "rainbow": ":rainbow:", "ufo": "ufo", "alien": ":alien:", "prayer": ":pray::skin-tone-2:", "mountain": ":mountain:", "satan": "satan", "dragon": ":dragon:", "diamond": "diamond", "platinum": "platinum", "gold": "gold", "devil": "devil", "fence": "fence", "game": ":video_game:", "math": "math", "robot": ":robot:", "heart": ":heart:", "electricity": ":zap:", "lightning": ":cloud_lightning:", "medusa": "medusa", "power": ":electric_plug:", "laser": "laser", "nuke": ":bomb:", "sky": "sky", "tank": "tank", "helicopter": ":helicopter:"}
		'''
		for _object in emotes:
			if _object == emotes[_object]:
				print(_object)
		'''
		if not os.path.isfile(clients.data_path + "/erps_dict.json"):
			await self.generate_erps_dict()
		with open(clients.data_path + "/erps_dict.json", 'r') as erps_file:
			resolution = json.load(erps_file)
		value = random.choice(list(emotes.keys()))
		if object not in emotes:
			await ctx.embed_reply(":no_entry: That's not a valid object")
		else:
			standard_value = value.lower().replace('.', "").replace("video game", "game")
			if standard_value == object:
				await ctx.embed_reply("\nI chose `{}`\nIt's a draw :confused:".format(value))
			elif object in resolution[standard_value]:
				await ctx.embed_reply("\nI chose `{}`\n{} {} {}\nYou lose :slight_frown:".format(value, emotes[standard_value], resolution[standard_value][object], emotes[object]))
			elif standard_value in resolution[object]:
				await ctx.embed_reply("\nI chose `{}`\n{} {} {}\nYou win! :tada:".format(value, emotes[object], resolution[object][standard_value], emotes[standard_value]))
	
	async def generate_erps_dict(self):
		async with clients.aiohttp_session.get("http://www.umop.com/rps101/alloutcomes.htm") as resp:
			data = await resp.text()
		raw_text = BeautifulSoup(data).text
		raw_text = re.sub("\n+", '\n', raw_text).strip()
		raw_text = raw_text.lower().replace("video game", "game")
		raw_text = raw_text.split('\n')[:-1]
		objects = {}
		object = raw_text[0].split()[-1]
		object_info = {}
		for line in raw_text[1:]:
			if line[0].isdigit():
				objects[object] = object_info
				object = line.split()[-1]
				object_info = {}
			else:
				object_info[line.split()[-1]] = ' '.join(line.split()[:-1])
		objects[object] = object_info
		with open(clients.data_path + "/erps_dict.json", 'w') as erps_file:
			json.dump(objects, erps_file, indent = 4)
	
	@commands.group(hidden = True)
	@checks.not_forbidden()
	async def taboo(self, ctx):
		'''WIP'''
		return
	
	@taboo.command(hidden = True, name = "start")
	@commands.guild_only()
	async def taboo_start(self, ctx, player : str):
		'''WIP'''
		self.taboo_players.append(ctx.author)
		for member in self.message.guild.members:
			if member.name == player:
				self.taboo_players.append(member)
				break
		await ctx.embed_reply(" has started a game of Taboo with " + taboo_players[1].mention)
		await ctx.whisper("You have started a game of Taboo with " + taboo_players[1].name)
		await self.bot.send_message(taboo_players[1], ctx.author.name + " has started a game of Taboo with you.")
	
	@taboo.command(hidden = True, name = "nextround")
	# @commands.guild_only() ?
	async def taboo_nextround(self, ctx):
		'''WIP'''
		if message.guild:
			pass
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def trivia(self, ctx):
		'''
		Trivia game
		Only your last answer is accepted
		Answers prepended with ! or > are ignored
		'''
		if self.trivia_active:
			return await ctx.embed_reply("There is already an ongoing game of trivia")
		self.trivia_active = True
		await self._trivia(ctx)
		self.trivia_active = False
	
	@trivia.command(name = "bet")
	@checks.not_forbidden()
	async def trivia_bet(self, ctx):
		'''Trivia with betting'''
		if self.trivia_active:
			return await ctx.embed_reply("There is already an ongoing game of trivia")
		self.trivia_active = True
		await self._trivia(ctx, bet = True)
		self.trivia_active = False
	
	async def _trivia(self, ctx, bet = False):
		try:
			async with clients.aiohttp_session.get("http://jservice.io/api/random") as resp:
				data = (await resp.json())[0]
		except aiohttp.ClientConnectionError as e:
			return await ctx.embed_reply(":no_entry: Error: Error connecting to API")
		if not data.get("question"):
			return await ctx.embed_reply(":no_entry: Error: API response missing question")
		if not data.get("category"):
			return await ctx.embed_reply(":no_entry: Error: API response missing category")
		if bet:
			bets = {}
			self.bet_countdown = int(clients.wait_time)
			bet_message = await ctx.embed_say(None, title = string.capwords(data["category"]["title"]), 
												footer_text = f"You have {self.bet_countdown} seconds left to bet")
			embed = bet_message.embeds[0]
			bet_countdown_task = self.bot.loop.create_task(self._bet_countdown(bet_message, embed))
			while self.bet_countdown:
				try:
					message = await self.bot.wait_for("message", timeout = self.bet_countdown, 
														check = lambda m: m.channel == ctx.channel and m.content.isdigit())
				except asyncio.TimeoutError:
					pass
				else:
					bet_ctx = await ctx.bot.get_context(message, cls = clients.Context)
					money = await ctx.bot.db.fetchval("SELECT money FROM trivia.users WHERE user_id = $1", message.author.id)
					# TODO: Check if new player
					if int(message.content) <= money:
						bets[message.author] = int(message.content)
						await bet_ctx.embed_reply(f"Has bet ${message.content}")
					else:
						await bet_ctx.embed_reply("You don't have that much money to bet!")
			while not bet_countdown_task.done():
				await asyncio.sleep(0.1)
			embed.set_footer(text = "Betting is over")
			await bet_message.edit(embed = embed)
		responses = {}
		self.trivia_countdown = int(clients.wait_time)
		answer_message = await ctx.embed_say(data["question"], title = string.capwords(data["category"]["title"]), 
												footer_text = f"You have {self.trivia_countdown} seconds left to answer")
		embed = answer_message.embeds[0]
		countdown_task = self.bot.loop.create_task(self._trivia_countdown(answer_message, embed))
		while self.trivia_countdown:
			try:
				message = await self.bot.wait_for("message", timeout = self.trivia_countdown, 
													check = lambda m: m.channel == ctx.channel)
			except asyncio.TimeoutError:
				pass
			else:
				if not message.content.startswith(('!', '>')):
					responses[message.author] = message.content
		while not countdown_task.done():
			await asyncio.sleep(0.1)
		embed.set_footer(text = "Time's up!")
		await answer_message.edit(embed = embed)
		correct_players = []
		incorrect_players = []
		matches_1 = re.search("\((.+)\) (.+)", data["answer"].lower())
		matches_2 = re.search("(.+) \((.+)\)", data["answer"].lower())
		matches_3 = re.search("(.+)\/(.+)", data["answer"].lower())
		for player, response in responses.items():
			if data["answer"].lower() in [s + response.lower() for s in ["", "a ", "an ", "the "]] \
			or response.lower() == BeautifulSoup(html.unescape(data["answer"]), "html.parser").get_text().lower() \
			or response.lower().replace('-', ' ') == data["answer"].lower().replace('-', ' ') \
			or response.lower() == data["answer"].lower().replace("\\'", "'") \
			or response.lower() == data["answer"].lower().replace('&', "and") \
			or response.lower() == data["answer"].lower().replace('.', "") \
			or response.lower() == data["answer"].lower().replace('!', "") \
			or response.lower().replace('(', "").replace(')', "") == data["answer"].lower().replace('(', "").replace(')', "") \
			or (matches_1 and (response.lower() in (matches_1.group(1), matches_1.group(2)))) \
			or (matches_2 and (response.lower() in (matches_2.group(1), matches_2.group(2)))) \
			or (matches_3 and (response.lower() in (matches_3.group(1), matches_3.group(2)))) \
			or response.lower().strip('"') == data["answer"].lower().strip('"'):
				correct_players.append(player)
			else:
				incorrect_players.append(player)
		if len(correct_players) == 0:
			correct_players_output = "Nobody got it right!"
		else:
			correct_players_output = clients.inflect_engine.join([player.display_name for player in correct_players])
			correct_players_output += f" {clients.inflect_engine.plural('was', len(correct_players))} right!"
		for correct_player in correct_players:
			await ctx.bot.db.execute(
				"""
				INSERT INTO trivia.users (user_id, correct, incorrect, money)
				VALUES ($1, 1, 0, 100000)
				ON CONFLICT (user_id) DO
				UPDATE SET correct = users.correct + 1
				""", 
				correct_player.id
			)
		for incorrect_player in incorrect_players:
			await ctx.bot.db.execute(
				"""
				INSERT INTO trivia.users (user_id, correct, incorrect, money)
				VALUES ($1, 0, 1, 100000)
				ON CONFLICT (user_id) DO
				UPDATE SET incorrect = users.incorrect + 1
				""", 
				incorrect_player.id
			)
		if bet:
			trivia_bets_output = ""
			for trivia_player in bets:
				if trivia_player in correct_players:
					money = await ctx.bot.db.fetchval(
						"""
						UPDATE trivia.users
						SET money = money + $2
						WHERE user_id = $1
						RETURNING money
						""", 
						trivia_player.id, bets[trivia_player]
					)
					trivia_bets_output += f"{trivia_player.display_name} won ${bets[trivia_player]:,} and now has ${money:,}. "
				else:
					money = await ctx.bot.db.fetchval(
						"""
						UPDATE trivia.users
						SET money = money - $2
						WHERE user_id = $1
						RETURNING money
						""", 
						trivia_player.id, bets[trivia_player]
					)
					trivia_bets_output += f"{trivia_player.display_name} lost ${bets[trivia_player]:,} and now has ${money:,}. "
			trivia_bets_output = trivia_bets_output[:-1]
		answer = BeautifulSoup(html.unescape(data["answer"]), "html.parser").get_text().replace("\\'", "'")
		await ctx.embed_say(f"The answer was `{answer}`", footer_text = correct_players_output)
		if bet and trivia_bets_output:
			await ctx.embed_say(trivia_bets_output)
	
	async def _bet_countdown(self, bet_message, embed):
		while self.bet_countdown:
			await asyncio.sleep(1)
			self.bet_countdown -= 1
			embed.set_footer(text = f"You have {self.bet_countdown} seconds left to bet")
			await bet_message.edit(embed = embed)
	
	async def _trivia_countdown(self, answer_message, embed):
		while self.trivia_countdown:
			await asyncio.sleep(1)
			self.trivia_countdown -= 1
			embed.set_footer(text = f"You have {self.trivia_countdown} seconds left to answer")
			await answer_message.edit(embed = embed)
	
	@trivia.command(name = "score", aliases = ["points", "rank", "level"])
	async def trivia_score(self, ctx):
		'''Trivia score'''
		record = await ctx.bot.db.fetchrow("SELECT correct, incorrect FROM trivia.users WHERE user_id = $1", ctx.author.id)
		if not record:
			return await ctx.embed_reply("You have not played any trivia yet")
		total = record["correct"] + record["incorrect"]
		correct_percentage = record["correct"] / total * 100
		await ctx.embed_reply(f"You have answered {record['correct']}/{total} ({correct_percentage:.2f}%) correctly.")
	
	@trivia.command(name = "money", aliases = ["cash"])
	async def trivia_money(self, ctx):
		'''Trivia money'''
		money = await ctx.bot.db.fetchval("SELECT money FROM trivia.users WHERE user_id = $1", ctx.author.id)
		await ctx.embed_reply(f"You have ${money:,}")
	
	@trivia.command(name = "scores", aliases = ["scoreboard", "top", "ranks", "levels"])
	async def trivia_scores(self, ctx, number : int = 10):
		'''Trivia scores'''
		if number > 15:
			number = 15
		fields = []
		async with ctx.bot.database_connection_pool.acquire() as connection:
			async with connection.transaction():
				# Postgres requires non-scrollable cursors to be created
				# and used in a transaction.
				async for record in connection.cursor("SELECT * FROM trivia.users ORDER BY correct DESC LIMIT $1", number):
					# SELECT user_id, correct, incorrect?
					user = ctx.bot.get_user(record["user_id"])
					if not user:
						user = await ctx.bot.get_user_info(record["user_id"])
					total = record["correct"] + record["incorrect"]
					correct_percentage = record["correct"] / total * 100
					fields.append((str(user), f"{record['correct']}/{total} correct ({correct_percentage:.2f}%)"))
		await ctx.embed_reply(title = f"Trivia Top {number}", fields = fields)
	
	@commands.group()
	@checks.not_forbidden()
	async def war(self, ctx):
		'''
		WIP
		Based on the War card game
		'''
		return
	
	@war.command(name = "start")
	@commands.guild_only()
	@commands.is_owner()
	async def war_start(self, ctx, *players : str):
		'''Start a game of War'''
		self.war_players = []
		for member in ctx.guild.members:
			if member.name in players:
				self.war_players.append(member)
				break
		war.start(len(players))
		self.war_channel = ctx.channel
		war_players_string = ""
		for player in self.war_players:
			war_players_string += player.name + " and "
		await ctx.embed_reply("{} has started a game of War between {}!".format(ctx.author.display_name, war_players_string[:-5]))
	
	@war.command(name = "hand")
	@commands.is_owner()
	async def war_hand(self, ctx):
		'''See your current hand'''
		if ctx.author in self.war_players:
			await ctx.whisper("Your hand: " + war.hand(self.war_players.index(ctx.author) + 1))
	
	@war.command(name = "left")
	@commands.is_owner()
	async def war_left(self, ctx):
		'''See how many cards you have left'''
		if ctx.author in self.war_players:
			await ctx.embed_reply("You have {} cards left".format(war.card_count(self.war_players.index(ctx.author) + 1)))
	
	@war.command(name = "play")
	@commands.is_owner()
	async def war_play(self, ctx, *card : str):
		'''Play a card'''
		if ctx.author in self.war_players:
			player_number = self.war_players.index(message.author) + 1
			winner, cardsplayed, tiedplayers = war.play(player_number, ' '.join(card))
			if winner == -1:
				await ctx.embed_reply(":no_entry: You have already chosen your card for this battle")
			elif winner == -3:
				await ctx.embed_reply(":no_entry: You are not in this battle")
			elif winner == -4:
				await ctx.embed_reply(":no_entry: Card not found in your hand")
			else:
				await ctx.embed_reply("You chose the {} of {}".format(cardsplayed[player_number - 1].value, cardsplayed[player_number - 1].suit))
				await ctx.whisper("Your hand: " + war.hand(player_number))
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
		return "".join(":{}: {} ".format(card.suit.lower(), card.value) for card in cards)

