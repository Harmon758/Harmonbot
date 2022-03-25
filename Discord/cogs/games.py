
import discord
from discord.ext import commands

import asyncio
import copy
import random
import re
import sys
import timeit
from typing import Optional

from bs4 import BeautifulSoup
import pydealer

# from modules import war
from utilities import checks

sys.path.insert(0, "..")
from units import games
sys.path.pop(0)

def setup(bot):
	bot.add_cog(Games(bot))

class Games(commands.Cog):
	
	'''
	Also see Adventure, Chess, Fish, Maze, Poker, and Trivia categories
	'''
	
	def __init__(self, bot):
		self.bot = bot
		self.war_channel, self.war_players = None, []
		self.taboo_players = []
		self.blackjack_ranks = copy.deepcopy(pydealer.const.DEFAULT_RANKS)
		self.blackjack_ranks["values"].update({"Ace": 0, "King": 9, "Queen": 9, "Jack": 9})
		for value in self.blackjack_ranks["values"]:
			self.blackjack_ranks["values"][value] += 1
		#check default values

	async def cog_load(self):
		await self.bot.connect_to_database()
		await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS games")
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS games.erps (
				object			TEXT, 
				against			TEXT, 
				action			TEXT, 
				PRIMARY KEY 	(object, against)
			)
			"""
		)
		exists = await self.bot.db.fetchval("SELECT EXISTS (SELECT * from games.erps)")
		if not exists:
			url = "http://www.umop.com/rps101/alloutcomes.htm"
			async with self.bot.aiohttp_session.get(url) as resp:
				data = await resp.text()
			raw_text = BeautifulSoup(data, "lxml").text
			raw_text = re.sub("\n+", '\n', raw_text).strip()
			raw_text = raw_text.lower().replace("video game", "game")
			raw_text = raw_text.split('\n')[:-1]
			for line in raw_text:
				words = line.split()
				if words[0].isdecimal() and words[1] == '-':
					object = words[-1]
				else:
					await self.bot.db.execute(
						"""
						INSERT INTO games.erps (object, against, action)
						VALUES ($1, $2, $3)
						ON CONFLICT (object, against) DO
						UPDATE SET action = $3
						""", 
						object, words[-1], ' '.join(words[:-1])
					)
			# TODO: Properly handle object against not at end
	
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
		dealer_string = f":grey_question: :{dealer.cards[1].suit.lower()}: {dealer.cards[1].value}"
		player_string = self.cards_to_string(player.cards)
		dealer_total = self.blackjack_total(dealer.cards)
		player_total = self.blackjack_total(player.cards)
		response = await ctx.embed_reply(f"Dealer: {dealer_string} (?)\n{ctx.author.display_name}: {player_string} ({player_total})\n", title = "Blackjack", footer_text = "Hit or Stay?")
		embed = response.embeds[0]
		while True:
			action = await self.bot.wait_for("message", check = lambda m: m.author == ctx.author and m.content.lower().strip('!') in ("hit", "stay"))
			await self.bot.attempt_delete_message(action)
			if action.content.lower().strip('!') == "hit":
				player.add(deck.deal())
				player_string = self.cards_to_string(player.cards)
				player_total = self.blackjack_total(player.cards)
				embed.description = f"Dealer: {dealer_string} (?)\n{ctx.author.display_name}: {player_string} ({player_total})\n"
				await response.edit(embed = embed)
				if player_total > 21:
					embed.description += ":boom: You have busted"
					embed.set_footer(text = "You lost :(")
					break
			else:
				dealer_string = self.cards_to_string(dealer.cards)
				embed.description = f"Dealer: {dealer_string} ({dealer_total})\n{ctx.author.display_name}: {player_string} ({player_total})\n"
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
				while dealer_total < 21 and dealer_total <= player_total:
					await asyncio.sleep(5)
					dealer.add(deck.deal())
					dealer_string = self.cards_to_string(dealer.cards)
					dealer_total = self.blackjack_total(dealer.cards)
					embed.description = f"Dealer: {dealer_string} ({dealer_total})\n{ctx.author.display_name}: {player_string} ({player_total})\n"
					await response.edit(embed = embed)
				if dealer_total > 21:
					embed.description += ":boom: The dealer busted"
					embed.set_footer(text = "You win!")
				elif dealer_total > player_total:
					embed.description += "The dealer beat you"
					embed.set_footer(text = "You lost :(")
				elif dealer_total == player_total == 21:
					embed.set_footer(text = "It's a push (tie)")
				break
		await response.edit(embed = embed)
	
	def blackjack_total(self, cards):
		total = sum(self.blackjack_ranks["values"][card.value] for card in cards)
		if pydealer.tools.find_card(cards, term = "Ace", limit = 1) and total <= 11: total += 10
		return total
	
	@commands.command(aliases = ["talk", "ask"])
	@checks.not_forbidden()
	async def cleverbot(self, ctx, *, message: str):
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
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def guess(self, ctx, max_value: Optional[int], tries: Optional[int]):
		'''Guessing game'''
		wait_time = 15.0
		if not max_value:
			await ctx.embed_reply("What range of numbers would you like to guess to? 1 to _")
			try:
				max_value = await self.bot.wait_for("message", timeout = wait_time, check = lambda m: m.author == ctx.author and m.content.isdigit() and m.content != '0')
			except asyncio.TimeoutError:
				max_value = 10
			else:
				max_value = int(max_value.content)
		if not tries:
			await ctx.embed_reply("How many tries would you like?")
			try:
				tries = await self.bot.wait_for("message", timeout = wait_time, check = lambda m: m.author == ctx.author and m.content.isdigit() and m.content != '0')
			except asyncio.TimeoutError:
				tries = 1
			else:
				tries = int(tries.content)
		answer = random.randint(1, max_value)
		await ctx.embed_reply(f"Guess a number between 1 to {max_value}")
		while tries != 0:
			try:
				guess = await self.bot.wait_for("message", timeout = wait_time, check = lambda m: m.author == ctx.author and m.content.isdigit() and m.content != '0')
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
	
	@commands.command(aliases = ["rtg", "reactiontime", "reactiontimegame", "reaction_time_game"])
	@checks.not_forbidden()
	async def reaction_time(self, ctx):
		'''Reaction time game'''
		# TODO: Randomly add reactions
		response = await ctx.embed_reply("Please add 10 reactions to this message", author_name = None, attempt_delete = False)
		embed = response.embeds[0]
		while len(response.reactions) < 10:
			await self.bot.wait_for("reaction_add", check = lambda r, u: r.message.id == response.id)
			response = await ctx.channel.fetch_message(response.id)
		reactions = response.reactions
		winning_emoji = random.choice(reactions).emoji
		embed.description = "Please wait.."
		await response.edit(embed = embed)
		for reaction in reactions:
			try:
				await response.add_reaction(reaction.emoji)
				# Unable to add custom emoji?
			except discord.HTTPException:
				embed.description = ":no_entry: Error: Please don't remove your reactions before I've selected them"
				await response.edit(embed = embed)
				return
		for countdown in range(10, 0, -1):
			embed.description = f"First to click the _ reaction wins.\nGet ready! {countdown}"
			await response.edit(embed = embed)
			await asyncio.sleep(1)
		embed.description = f"First to click the {winning_emoji} reaction wins. Go!"
		await response.edit(embed = embed)
		start_time = timeit.default_timer()
		payload = await self.bot.wait_for_raw_reaction_add_or_remove(message = response, emoji = winning_emoji)
		elapsed = timeit.default_timer() - start_time
		winner = await ctx.guild.fetch_member(payload.user_id)
		embed.set_author(name = winner.display_name, icon_url = winner.avatar.url)
		embed.description = f"was the first to click {winning_emoji} and won with a time of {elapsed:.5} seconds!"
		await response.edit(embed = embed)
	
	@commands.command(aliases = ["rockpaperscissors", "rock-paper-scissors", "rock_paper_scissors"], 
						usage = "<object>")
	@checks.not_forbidden()
	async def rps(self, ctx, rps_object: str):
		'''Rock paper scissors'''
		if rps_object.lower() not in ('r', 'p', 's', "rock", "paper", "scissors"):
			raise commands.BadArgument("That's not a valid object")
		value = random.choice(("rock", "paper", "scissors"))
		short_shape = rps_object[0].lower()
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
	
	@commands.command(aliases = ["rockpaperscissorslizardspock", "rock-paper-scissors-lizard-spock"], 
						usage = "<object>")
	@checks.not_forbidden()
	async def rpsls(self, ctx, rpsls_object: str):
		'''
		RPS lizard Spock
		https://upload.wikimedia.org/wikipedia/commons/f/fe/Rock_Paper_Scissors_Lizard_Spock_en.svg
		'''
		if rpsls_object.lower() not in ('r', 'p', 's', 'l', "rock", "paper", "scissors", "lizard", "spock"):
			raise commands.BadArgument("That's not a valid object")
		value = random.choice(("rock", "paper", "scissors", "lizard", "Spock"))
		if rpsls_object[0] == 'S' and rpsls_object.lower() != "scissors" or rpsls_object.lower() == "spock":
			short_shape = 'S'
		else:
			short_shape = rpsls_object[0].lower()
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
									"rock-paper-scissors-lizard-spock-spiderman-batman-wizard-glock"], 
						usage = "<object>")
	@checks.not_forbidden()
	async def rpslssbwg(self, ctx, rpslssbwg_object: str):
		'''
		RPSLS Spider-Man Batman wizard Glock
		http://i.imgur.com/m9C2UTP.jpg
		'''
		rpslssbwg_object = rpslssbwg_object.lower().replace('-', "")
		if rpslssbwg_object not in ("rock", "paper", "scissors", "lizard", "spock", "spiderman", "batman", "wizard", "glock"):
			raise commands.BadArgument("That's not a valid object")
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
		if standard_value == rpslssbwg_object:
			await ctx.embed_reply(f"I chose `{value}`\n"
									"It's a draw :confused:")
		elif rpslssbwg_object in resolution[standard_value]:
			await ctx.embed_reply(f"I chose `{value}`\n"
									f"{emotes[standard_value]} {resolution[standard_value][rpslssbwg_object]} {emotes[rpslssbwg_object]}\n"
									"You lose :slight_frown:")
		else:
			await ctx.embed_reply(f"I chose `{value}`\n"
									f"{emotes[rpslssbwg_object]} {resolution[rpslssbwg_object][standard_value]} {emotes[standard_value]}\n"
									"You win! :tada:")
	
	@commands.command(aliases = ["cockroachfootnuke", "cockroach-foot-nuke"], 
						usage = "<object>")
	@checks.not_forbidden()
	async def cfn(self, ctx, cfn_object: str):
		'''
		Cockroach foot nuke
		https://www.youtube.com/watch?v=wRi2j8k0vjo
		'''
		if cfn_object.lower() not in ('c', 'f', 'n', "cockroach", "foot", "nuke"):
			raise commands.BadArgument("That's not a valid object")
		else:
			value = random.choice(("cockroach", "foot", "nuke"))
			short_shape = cfn_object[0].lower()
			resolution = {'c': {'n': "survives"}, 'f': {'c': "squashes"}, 'n': {'f': "blows up"}}
			emotes = {'c': ":bug:", 'f': ":footprints:", 'n': ":bomb:"}
			if value[0] == short_shape:
				await ctx.embed_reply(f"I chose `{value}`\n"
										"It's a draw :confused:")
			elif short_shape in resolution[value[0]]:
				await ctx.embed_reply(f"I chose `{value}`\n"
										f"{emotes[value[0]]} {resolution[value[0]][short_shape]} {emotes[short_shape]}\n"
										"You lose :slight_frown:")
			else:
				await ctx.embed_reply(f"I chose `{value}`\n"
										f"{emotes[short_shape]} {resolution[short_shape][value[0]]} {emotes[value[0]]}\n"
										"You win! :tada:")
	
	@commands.command(aliases = ["extremerps", "rps-101", "rps101"], 
						usage = "<object>")
	@checks.not_forbidden()
	async def erps(self, ctx, erps_object: str):
		'''
		Extreme rock paper scissors
		http://www.umop.com/rps101.htm
		http://www.umop.com/rps101/alloutcomes.htm
		http://www.umop.com/rps101/rps101chart.html
		'''
		# TODO: Harmonbot option
		erps_object = erps_object.lower().replace('.', "").replace("video game", "game")
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
		for key, emote in emotes.ites():
			if key == emote
				print(key)
		'''
		value = random.choice(list(emotes.keys()))
		if erps_object not in emotes:
			raise commands.BadArgument("That's not a valid object")
		standard_value = value.lower().replace('.', "").replace("video game", "game")
		if standard_value == erps_object:
			return await ctx.embed_reply(f"I chose `{value}`\n"
											"It's a draw :confused:")
		action = await ctx.bot.db.fetchval(
			"""
			SELECT action FROM games.erps
			WHERE object = $1 AND against = $2
			""", 
			standard_value, erps_object
		)
		if action:
			return await ctx.embed_reply(f"I chose `{value}`\n"
											f"{emotes[standard_value]} {action} {emotes[erps_object]}\n"
											"You lose :slight_frown:")
		action = await ctx.bot.db.fetchval(
			"""
			SELECT action FROM games.erps
			WHERE object = $1 AND against = $2
			""", 
			erps_object, standard_value
		)
		if action:
			return await ctx.embed_reply(f"I chose `{value}`\n"
											f"{emotes[erps_object]} {action} {emotes[standard_value]}\n"
											"You win! :tada:")
		return await ctx.embed_reply(":no_entry: Error: I don't know the relationship between "
										f"{emotes[erps_object]} and {emotes[standard_value]}, the object that I chose")
	
	@commands.command()
	@checks.not_forbidden()
	async def simon(self, ctx):
		'''Based on the electronic memory game'''
		emojis = ("\N{LARGE BLUE CIRCLE}", "\N{LARGE GREEN CIRCLE}", "\N{LARGE RED CIRCLE}", "\N{LARGE YELLOW CIRCLE}")
		message = await ctx.embed_reply("Get ready!")
		embed = message.embeds[0]
		sequence = []
		for emoji in emojis:
			await message.add_reaction(emoji)
		while not embed.description.startswith("Game over."):
			await asyncio.sleep(1)
			sequence.append(random.choice(emojis))
			for emoji in sequence:
				display = ["\N{MEDIUM BLACK CIRCLE}"] * 4
				embed.description = "Playing the sequence:\n" + ' '.join(display)
				await message.edit(embed = embed)
				await asyncio.sleep(1)
				display[emojis.index(emoji)] = emoji
				embed.description = "Playing the sequence:\n" + ' '.join(display)
				await message.edit(embed = embed)
				await asyncio.sleep(1)
			embed.description = "Playback the sequence:"
			await message.edit(embed = embed)
			for correct_emoji in sequence:
				try:
					payload = await ctx.bot.wait_for_raw_reaction_add_or_remove(emoji = emojis, message = message, user = ctx.author, timeout = 5)
				except asyncio.TimeoutError:
					embed.description = f"Game over. You timed out on a sequence of length {len(sequence)}."
					break
				if payload.emoji.name != correct_emoji:
					embed.description = f"Game over. You failed on a sequence of length {len(sequence)}."
					break
			else:
				embed.description = f"You completed the sequence! Get ready for a sequence of length {len(sequence) + 1}."
			await message.edit(embed = embed)
		await message.clear_reactions()
	
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

