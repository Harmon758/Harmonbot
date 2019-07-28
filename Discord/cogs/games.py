
import discord
from discord.ext import commands

import asyncio
import copy
import json
import os
import random
import re
import sys
import timeit
import typing

from bs4 import BeautifulSoup
import pydealer

import clients
from modules import adventure
# from modules import gofish
from modules import maze
# from modules import war
from utilities import checks

sys.path.insert(0, "..")
from units import games
sys.path.pop(0)

def setup(bot):
	bot.add_cog(Games(bot))

class Games(commands.Cog):
	
	'''
	Also see Chess, Poker, and Trivia categories
	'''
	
	def __init__(self, bot):
		self.bot = bot
		self.war_channel, self.war_players = None, []
		self.gofish_channel, self.gofish_players = None, []
		self.taboo_players = []
		self.mazes = {}
		self.blackjack_ranks = copy.deepcopy(pydealer.const.DEFAULT_RANKS)
		self.blackjack_ranks["values"].update({"Ace": 0, "King": 9, "Queen": 9, "Jack": 9})
		for value in self.blackjack_ranks["values"]:
			self.blackjack_ranks["values"][value] += 1
		#check default values
		
		self.adventure_players = {}
		
		# Necessary for maze generation
		sys.setrecursionlimit(5000)
	
	# Adventure
	
	@commands.group(aliases = ["rpg"], invoke_without_command = True, case_insensitive = True, hidden = True)
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
	
	@adventure.group(name = "stats", aliases = ["stat", "levels", "level", "lvls", "lvl"], invoke_without_command = True, case_insensitive = True)
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
	
	@adventure.group(name = "forage", aliases = ["gather"], invoke_without_command = True, case_insensitive = True)
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
	
	@adventure.group(name = "chop", aliases = ["woodcutting", "wc"], invoke_without_command = True, case_insensitive = True)
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
		async with self.bot.aiohttp_session.get(url, params = params) as resp:
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
	
	@commands.group(case_insensitive = True, hidden = True)
	@checks.not_forbidden()
	async def gofish(self, ctx):
		'''WIP'''
		return
	
	@gofish.command(case_insensitive = True, hidden = True, name = "start")
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
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def guess(self, ctx, max_value : typing.Optional[int], tries : typing.Optional[int]):
		'''Guessing game'''
		if not max_value:
			await ctx.embed_reply("What range of numbers would you like to guess to? 1 to _")
			try:
				max_value = await self.bot.wait_for("message", timeout = clients.wait_time, check = lambda m: m.author == ctx.author and m.content.isdigit() and m.content != '0')
			except asyncio.TimeoutError:
				max_value = 10
			else:
				max_value = int(max_value.content)
		if not tries:
			await ctx.embed_reply("How many tries would you like?")
			try:
				tries = await self.bot.wait_for("message", timeout = clients.wait_time, check = lambda m: m.author == ctx.author and m.content.isdigit() and m.content != '0')
			except asyncio.TimeoutError:
				tries = 1
			else:
				tries = int(tries.content)
		answer = random.randint(1, max_value)
		await ctx.embed_reply(f"Guess a number between 1 to {max_value}")
		while tries != 0:
			try:
				guess = await self.bot.wait_for("message", timeout = clients.wait_time, check = lambda m: m.author == ctx.author and m.content.isdigit() and m.content != '0')
			except asyncio.TimeoutError:
				return await ctx.embed_reply(f"Sorry, you took too long\nIt was {answer}")
			if int(guess.content) == answer:
				return await ctx.embed_reply("You are right!")
			elif tries != 1 and int(guess.content) > answer:
				await ctx.embed_reply("It's less than " + guess.content)
				tries -= 1
			elif tries != 1 and int(guess.content) < answer:
				await ctx.embed_reply("It's greater than " + guess.content)
				tries -= 1
			else:
				return await ctx.embed_reply(f"Sorry, it was actually {answer}")
	
	@commands.group(aliases = ["hrmp"], case_insensitive = True, hidden = True)
	@checks.not_forbidden()
	async def harmonopoly(self, ctx):
		'''
		WIP
		Harmonopoly is a game based on The Centipede Game where every player chooses a number.
		The player with the lowest number that is not surpassed within +2 of another number that is chosen, wins. The winner gets points equal to the number that they chose.
		Examples: {1,2 Winner(W): 2} {1,3 W: 3} {1,4 W: 1} {1,3,5 W: 5} {1,3,5,7,10 W: 7}
		'''
		pass
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def maze(self, ctx):
		'''
		Maze game
		[w, a, s, d] to move
		Also see mazer
		'''
		await ctx.send_help(ctx.command)
	
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
		maze_message = await ctx.embed_reply(ctx.bot.CODE_BLOCK.format(maze_instance.print_visible()))
		'''
		maze_print = ""
		for r in maze_instance.test_print():
			row_print = ""
			for cell in r:
				row_print += cell + ' '
			maze_print += row_print + "\n"
		await ctx.reply(ctx.bot.CODE_BLOCK.format(maze_print))
		'''
		# await ctx.reply(ctx.bot.CODE_BLOCK.format(repr(maze_instance)))
		convert_move = {'w' : 'n', 'a' : 'w', 's' : 's', 'd' : 'e'}
		while not maze_instance.reached_end():
			move = await self.bot.wait_for("message", check = lambda message: message.content.lower() in ['w', 'a', 's', 'd'] and message.channel == ctx.channel) # author = ctx.author
			moved = maze_instance.move(convert_move[move.content.lower()])
			response = ctx.bot.CODE_BLOCK.format(maze_instance.print_visible())
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
			await ctx.embed_reply(ctx.bot.CODE_BLOCK.format(self.mazes[ctx.channel.id].print_visible()))
		else:
			await ctx.embed_reply(":no_entry: There's no maze game currently going on")
	
	# add maze print, position?
	
	@commands.command(aliases = ["rtg", "reactiontime", "reactiontimegame", "reaction_time_game"])
	@checks.not_forbidden()
	async def reaction_time(self, ctx):
		'''Reaction time game'''
		# TODO: Use embeds
		# TODO: Randomly add reactions
		response = await ctx.send("Please choose 10 reactions")
		while len(response.reactions) < 10:
			await self.bot.wait_for("reaction_add", check = lambda r, u: r.message.id == response.id)
			response = await ctx.channel.fetch_message(response.id)
		reactions = response.reactions
		reaction = random.choice(reactions)
		await response.edit(content = "Please wait..")
		for _reaction in reactions:
			try:
				await response.add_reaction(_reaction.emoji)
				# Unable to add custom emoji?
			except discord.HTTPException:
				await response.edit(content = ":no_entry: Error: Please don't deselect your reactions before I've selected them")
				return
		for countdown in range(10, 0, -1):
			await response.edit(content = "First to select the reaction _ wins.\nMake sure to have all the reactions deselected.\nGet ready! {}".format(countdown))
			await asyncio.sleep(1)
		await response.edit(content = "First to select the reaction {} wins. Go!".format(reaction.emoji))
		start_time = timeit.default_timer()
		reaction, winner = await self.bot.wait_for("reaction_add", check = lambda r, u: r.message.id == response.id and r.emoji == reaction.emoji)
		# TODO: Support reaction remove
		elapsed = timeit.default_timer() - start_time
		await response.edit(content = "{} was the first to select {} and won with a time of {:.5} seconds!".format(winner.display_name, reaction.emoji, elapsed))
	
	@commands.command(aliases = ["rockpaperscissors", "rock-paper-scissors", "rock_paper_scissors"])
	@checks.not_forbidden()
	async def rps(self, ctx, object : str):
		'''Rock paper scissors'''
		if object.lower() not in ('r', 'p', 's', "rock", "paper", "scissors"):
			return await ctx.embed_reply(":no_entry: That's not a valid object")
		value = random.choice(("rock", "paper", "scissors"))
		short_shape = object[0].lower()
		resolution = {'r': {'s': "crushes"}, 'p': {'r': "covers"}, 's': {'p': "cuts"}}
		emotes = {'r': f"\N{RAISED FIST}{ctx.bot.emoji_skin_tone}", 'p': f"\N{RAISED HAND}{ctx.bot.emoji_skin_tone}", 
					's': f"\N{VICTORY HAND}{ctx.bot.emoji_skin_tone}"}
		if value[0] == short_shape:
			await ctx.embed_reply(f"I chose `{value}`\nIt's a draw :confused:")
		elif short_shape in resolution[value[0]]:
			await ctx.embed_reply(f"I chose `{value}`\n"
									f"{emotes[value[0]]} {resolution[value[0]][short_shape]} {emotes[short_shape]}\n"
									"You lose :slight_frown:")
		else:
			await ctx.embed_reply(f"I chose `{value}`\n"
									f"{emotes[short_shape]} {resolution[short_shape][value[0]]} {emotes[value[0]]}\n"
									"You win! :tada:")
	
	@commands.command(aliases = ["rockpaperscissorslizardspock", "rock-paper-scissors-lizard-spock"])
	@checks.not_forbidden()
	async def rpsls(self, ctx, object : str):
		'''
		RPS lizard Spock
		https://upload.wikimedia.org/wikipedia/commons/f/fe/Rock_Paper_Scissors_Lizard_Spock_en.svg
		'''
		if object.lower() not in ('r', 'p', 's', 'l', "rock", "paper", "scissors", "lizard", "spock"):
			return await ctx.embed_reply(":no_entry: That's not a valid object")
		value = random.choice(("rock", "paper", "scissors", "lizard", "Spock"))
		if object[0] == 'S' and object.lower() != "scissors" or object.lower() == "spock":
			short_shape = 'S'
		else:
			short_shape = object[0].lower()
		resolution = {'r': {'s': "crushes", 'l': "crushes"}, 'p': {'r': "covers", 'S': "disproves"}, 
						's': {'p': "cuts", 'l': "decapitates"}, 'l': {'p': "eats", 'S': "poisons"}, 
						'S': {'r': "vaporizes", 's': "smashes"}}
		emotes = {'r': f"\N{RAISED FIST}{ctx.bot.emoji_skin_tone}", 'p': f"\N{RAISED HAND}{ctx.bot.emoji_skin_tone}", 
					's': f"\N{VICTORY HAND}{ctx.bot.emoji_skin_tone}", 'l': ":lizard:", 
					'S': f"\N{RAISED HAND WITH PART BETWEEN MIDDLE AND RING FINGERS}{ctx.bot.emoji_skin_tone}"}
		if value[0] == short_shape:
			await ctx.embed_reply(f"I chose `{value}`\nIt's a draw :confused:")
		elif short_shape in resolution[value[0]]:
			await ctx.embed_reply(f"I chose `{value}`\n"
									f"{emotes[value[0]]} {resolution[value[0]][short_shape]} {emotes[short_shape]}\n"
									"You lose :slight_frown:")
		else:
			await ctx.embed_reply(f"I chose `{value}`\n"
									f"{emotes[short_shape]} {resolution[short_shape][value[0]]} {emotes[value[0]]}\n"
									"You win! :tada:")
	
	@commands.command(aliases = ["rockpaperscissorslizardspockspidermanbatmanwizardglock", 
									"rock-paper-scissors-lizard-spock-spiderman-batman-wizard-glock"])
	@checks.not_forbidden()
	async def rpslssbwg(self, ctx, object : str):
		'''
		RPSLS Spider-Man Batman wizard Glock
		http://i.imgur.com/m9C2UTP.jpg
		'''
		object = object.lower().replace('-', "")
		if object not in ("rock", "paper", "scissors", "lizard", "spock", "spiderman", "batman", "wizard", "glock"):
			return await ctx.embed_reply(":no_entry: That's not a valid object")
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
		emotes = {"rock": f"\N{RAISED FIST}{ctx.bot.emoji_skin_tone}", "paper": f"\N{RAISED HAND}{ctx.bot.emoji_skin_tone}", 
					"scissors": f"\N{VICTORY HAND}{ctx.bot.emoji_skin_tone}", "lizard": ":lizard:", 
					"spock": f"\N{RAISED HAND WITH PART BETWEEN MIDDLE AND RING FINGERS}{ctx.bot.emoji_skin_tone}", 
					"spiderman": ":spider:", "batman": ":bat:", "wizard": ":tophat:", "glock": ":gun:"}
		standard_value = value.lower().replace('-', "")
		if standard_value == object:
			await ctx.embed_reply(f"I chose `{value}`\n"
									"It's a draw :confused:")
		elif object in resolution[standard_value]:
			await ctx.embed_reply(f"I chose `{value}`\n"
									f"{emotes[standard_value]} {resolution[standard_value][object]} {emotes[object]}\n"
									"You lose :slight_frown:")
		else:
			await ctx.embed_reply(f"I chose `{value}`\n"
									f"{emotes[object]} {resolution[object][standard_value]} {emotes[standard_value]}\n"
									"You win! :tada:")
	
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
		emotes = {"dynamite": ":boom:", "tornado": ":cloud_tornado:", "quicksand": "quicksand", 
					"pit": ":black_circle:", "chain": ":chains:", "gun": ":gun:", "law": ":scales:", "whip": "whip", 
					"sword": ":crossed_swords:", "rock": f"\N{RAISED FIST}{ctx.bot.emoji_skin_tone}", "death": ":skull:", 
					"wall": "wall", "sun": ":sunny:", "camera": ":camera:", "fire": ":fire:", "chainsaw": "chainsaw", 
					"school": ":school:", "scissors": ":scissors:", "poison": "poison", "cage": "cage", "axe": "axe", 
					"peace": ":peace:", "computer": ":computer:", "castle": ":european_castle:", "snake": ":snake:", 
					"blood": "blood", "porcupine": "porcupine", "vulture": "vulture", "monkey": ":monkey:", "king": "king", 
					"queen": "queen", "prince": "prince", "princess": "princess", "police": ":police_car:", 
					"woman": f"\N{WOMAN}{ctx.bot.emoji_skin_tone}", "baby": f"\N{BABY}{ctx.bot.emoji_skin_tone}", 
					"man": f"\N{MAN}{ctx.bot.emoji_skin_tone}", "home": ":homes:", "train": ":train:", "car": ":red_car:", 
					"noise": "noise", "bicycle": f"\N{BICYCLIST}{ctx.bot.emoji_skin_tone}", "tree": ":evergreen_tree:", 
					"turnip": "turnip", "duck": ":duck:", "wolf": ":wolf:", "cat": ":cat:", "bird": ":bird:", 
					"fish": ":fish:", "spider": ":spider:", "cockroach": "cockroach", "brain": "brain", 
					"community": "community", "cross": ":cross:", "money": ":moneybag:", "vampire": "vampire", 
					"sponge": "sponge", "church": ":church:", "butter": "butter", "book": ":book:", 
					"paper": f"\N{RAISED HAND}{ctx.bot.emoji_skin_tone}", "cloud": ":cloud:", "airplane": ":airplane:", 
					"moon": ":full_moon:", "grass": "grass", "film": ":film_frames:", "toilet": ":toilet:", "air": "air", 
					"planet": "planet", "guitar": ":guitar:", "bowl": "bowl", "cup": "cup", "beer": ":beer:", 
					"rain": ":cloud_rain:", "water": ":potable_water:", "tv": ":tv:", "rainbow": ":rainbow:", "ufo": "ufo", 
					"alien": ":alien:", "prayer": f"\N{PERSON WITH FOLDED HANDS}{ctx.bot.emoji_skin_tone}", 
					"mountain": ":mountain:", "satan": "satan", "dragon": ":dragon:", "diamond": "diamond", 
					"platinum": "platinum", "gold": "gold", "devil": "devil", "fence": "fence", "game": ":video_game:", 
					"math": "math", "robot": ":robot:", "heart": ":heart:", "electricity": ":zap:", 
					"lightning": ":cloud_lightning:", "medusa": "medusa", "power": ":electric_plug:", "laser": "laser", 
					"nuke": ":bomb:", "sky": "sky", "tank": "tank", "helicopter": ":helicopter:"}
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
			return await ctx.embed_reply(":no_entry: That's not a valid object")
		standard_value = value.lower().replace('.', "").replace("video game", "game")
		if standard_value == object:
			await ctx.embed_reply(f"I chose `{value}`\n"
									"It's a draw :confused:")
		elif object in resolution[standard_value]:
			await ctx.embed_reply(f"I chose `{value}`\n"
									f"{emotes[standard_value]} {resolution[standard_value][object]} {emotes[object]}\n"
									"You lose :slight_frown:")
		elif standard_value in resolution[object]:
			await ctx.embed_reply(f"I chose `{value}`\n"
									f"{emotes[object]} {resolution[object][standard_value]} {emotes[standard_value]}\n"
									"You win! :tada:")
	
	async def generate_erps_dict(self):
		async with self.bot.aiohttp_session.get("http://www.umop.com/rps101/alloutcomes.htm") as resp:
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
	
	@commands.group(case_insensitive = True, hidden = True)
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
	
	@commands.group(case_insensitive = True)
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

