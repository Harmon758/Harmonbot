
import discord
from discord.ext import commands

import asyncio
import random
import re
import timeit
from typing import Optional

from bs4 import BeautifulSoup

# from modules import war
from units import games
from utilities import checks


async def setup(bot):
	await bot.add_cog(Games(bot))

class Games(commands.Cog):
	
	"""
	Also see Adventure, Blackjack, Chess, Fish, Maze, Poker, Slots, and Trivia categories
	"""
	
	# TODO: harmonopoly (alias: hrmp)
	# Harmonopoly is a game based on The Centipede Game where every player
	# chooses a number.
	# The player with the lowest number that is not surpassed within +2 of
	# another number that is chosen, wins. The winner gets points equal to the
	# number that they chose.
	# Examples: {1,2 Winner(W): 2} {1,3 W: 3} {1,4 W: 1} {1,3,5 W: 5}
	# {1,3,5,7,10 W: 7}
	
	# TODO: Taboo
	
	def __init__(self, bot):
		self.bot = bot
		self.war_channel, self.war_players = None, []
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
	
	@commands.hybrid_command(
		name = "8-ball", aliases = ["8ball", "eightball", '\N{BILLIARDS}']
	)
	@checks.not_forbidden()
	async def eightball(
		self, ctx, *,
		question: Optional[str] = ""  # noqa: UP007 (non-pep604-annotation)
	):
		"""
		Ask 8-ball a yes or no question
		
		Also triggers on \N{BILLIARDS} without prefix
		
		Parameters
		----------
		question
			Yes or no question to ask 8-ball
		"""
		await ctx.defer()
		await ctx.embed_reply(
			f"{ctx.author.mention}: {question}\n"
			f"\N{BILLIARDS} {games.eightball()}"
		)
	
	@commands.group(case_insensitive = True, invoke_without_command = True)
	@checks.not_forbidden()
	async def guess(
		self, ctx,
		max_value: Optional[int] = 10,  # noqa: UP007 (non-pep604-annotation)
		tries: Optional[int] = 1  # noqa: UP007 (non-pep604-annotation)
	):
		'''Guessing game'''
		correct_number = random.randint(1, max_value)
		await ctx.embed_reply(f"Guess a number between 1 to {max_value}")
		while tries != 0:
			try:
				guess = await self.bot.wait_for(
					"message",
					timeout = 15.0,
					check = (
						lambda m:
							m.author == ctx.author and
							m.content.isdigit() and
							m.content != '0'
					)
				)
			except asyncio.TimeoutError:
				await ctx.embed_reply(
					f"Sorry, you took too long\nIt was {correct_number}"
				)
				return
			if int(guess.content) == correct_number:
				await ctx.embed_reply("You are right!")
				return
			elif tries != 1 and int(guess.content) > correct_number:
				await ctx.embed_reply("It's less than " + guess.content)
				tries -= 1
			elif tries != 1 and int(guess.content) < correct_number:
				await ctx.embed_reply("It's greater than " + guess.content)
				tries -= 1
			else:
				await ctx.embed_reply(
					f"Sorry, it was actually {correct_number}"
				)
				return
	
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
	
	@commands.command()
	@checks.not_forbidden()
	async def simon(self, ctx):
		'''Based on the electronic memory game'''
		circle_emojis = (
			"\N{LARGE BLUE CIRCLE}", "\N{LARGE GREEN CIRCLE}",
			"\N{LARGE RED CIRCLE}", "\N{LARGE YELLOW CIRCLE}"
		)
		message = await ctx.embed_reply("Get ready!")
		embed = message.embeds[0]
		sequence = []
		for circle_emoji in circle_emojis:
			await message.add_reaction(circle_emoji)
		while not embed.description.startswith("Game over."):
			await asyncio.sleep(1)
			sequence.append(random.choice(circle_emojis))
			for circle_emoji in sequence:
				display = ["\N{MEDIUM BLACK CIRCLE}"] * 4
				embed.description = (
					"Playing the sequence:\n" + ' '.join(display)
				)
				await message.edit(embed = embed)
				await asyncio.sleep(1)
				display[circle_emojis.index(circle_emoji)] = circle_emoji
				embed.description = (
					"Playing the sequence:\n" + ' '.join(display)
				)
				await message.edit(embed = embed)
				await asyncio.sleep(1)
			embed.description = "Playback the sequence:"
			await message.edit(embed = embed)
			for correct_emoji in sequence:
				try:
					payload = await ctx.bot.wait_for_raw_reaction_add_or_remove(
						emoji = circle_emojis, message = message,
						user = ctx.author, timeout = 5
					)
				except asyncio.TimeoutError:
					embed.description = (
						f"Game over. You timed out on a sequence of length {len(sequence)}."
					)
					break
				if payload.emoji.name != correct_emoji:
					embed.description = (
						f"Game over. You failed on a sequence of length {len(sequence)}."
					)
					break
			else:
				embed.description = (
					f"You completed the sequence! Get ready for a sequence of length {len(sequence) + 1}."
				)
			await message.edit(embed = embed)
		await message.clear_reactions()
	
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

