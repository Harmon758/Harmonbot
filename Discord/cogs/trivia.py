
from discord.ext import commands

import asyncio
import html
import re
import string

import aiohttp
from bs4 import BeautifulSoup

import clients
from utilities import checks

def setup(bot):
	bot.add_cog(Trivia(bot))

class Trivia:
	
	def __init__(self, bot):
		self.bot = bot
		self.active = {}
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
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def trivia(self, ctx):
		'''
		Trivia game
		Only your last answer is accepted
		Answers prepended with ! or > are ignored
		'''
		if ctx.guild.id in self.active:
			channel = ctx.guild.get_channel(self.active[ctx.guild.id]["channel"])
			return await ctx.embed_reply(f"There is already an ongoing game of trivia in {channel.mention}")
		self.active[ctx.guild.id] = {"channel": ctx.channel.id, "question_countdown": 0}
		await self.trivia_round(ctx)
		del self.active[ctx.guild.id]
	
	@trivia.command(name = "bet")
	@checks.not_forbidden()
	async def trivia_bet(self, ctx):
		'''
		Trivia with betting
		The category is shown first during the betting phase
		Enter any amount under or equal to the money you have to bet
		Currently, you start with $100,000
		'''
		if ctx.guild.id in self.active:
			channel = ctx.guild.get_channel(self.active[ctx.guild.id]["channel"])
			return await ctx.embed_reply(f"There is already an ongoing game of trivia in {channel.mention}")
		self.active[ctx.guild.id] = {"channel": ctx.channel.id, "bet_countdown": 0, "question_countdown": 0}
		await self.trivia_round(ctx, bet = True)
		del self.active[ctx.guild.id]
	
	async def trivia_round(self, ctx, bet = False):
		try:
			async with clients.aiohttp_session.get("http://jservice.io/api/random") as resp:
				data = (await resp.json())[0]
		except aiohttp.ClientConnectionError as e:
			return await ctx.embed_reply(":no_entry: Error: Error connecting to API")
		if not data.get("question"):
			return await ctx.embed_reply(":no_entry: Error: API response missing question")
		if not data.get("category"):
			return await ctx.embed_reply(":no_entry: Error: API response missing category")
		# Add message about making POST request to API/invalid with id?
		# Include site page to send ^?
		if bet:
			bets = {}
			self.active[ctx.guild.id]["bet_countdown"] = int(clients.wait_time)
			bet_message = await ctx.embed_say(None, title = string.capwords(data["category"]["title"]), 
												footer_text = f"You have {self.active[ctx.guild.id]['bet_countdown']} seconds left to bet")
			bet_countdown_task = ctx.bot.loop.create_task(self._bet_countdown(bet_message))
			while self.active[ctx.guild.id]["bet_countdown"]:
				try:
					message = await ctx.bot.wait_for("message", timeout = self.active[ctx.guild.id]["bet_countdown"], 
														check = lambda m: m.channel == ctx.channel and m.content.isdigit())
				except asyncio.TimeoutError:
					pass
				else:
					bet_ctx = await ctx.bot.get_context(message, cls = clients.Context)
					money = await ctx.bot.db.fetchval("SELECT money FROM trivia.users WHERE user_id = $1", message.author.id)
					if not money:
						money = await ctx.bot.db.fetchval(
							"""
							INSERT INTO trivia.users (user_id, correct, incorrect, money)
							VALUES ($1, 0, 0, 100000)
							RETURNING money
							""", 
							message.author.id
						)
					if int(message.content) <= money:
						bets[message.author] = int(message.content)
						await bet_ctx.embed_reply(f"Has bet ${message.content}")
					else:
						await bet_ctx.embed_reply("You don't have that much money to bet!")
			while not bet_countdown_task.done():
				await asyncio.sleep(0.1)
			embed = bet_message.embeds[0]
			embed.set_footer(text = "Betting is over")
			await bet_message.edit(embed = embed)
		responses = {}
		self.active[ctx.guild.id]["question_countdown"] = int(clients.wait_time)
		answer_message = await ctx.embed_say(data["question"], title = string.capwords(data["category"]["title"]), 
												footer_text = f"You have {self.active[ctx.guild.id]['question_countdown']} seconds left to answer")
		countdown_task = ctx.bot.loop.create_task(self._trivia_countdown(answer_message))
		while self.active[ctx.guild.id]["question_countdown"]:
			try:
				message = await ctx.bot.wait_for("message", timeout = self.active[ctx.guild.id]["question_countdown"], 
													check = lambda m: m.channel == ctx.channel)
			except asyncio.TimeoutError:
				pass
			else:
				if not message.content.startswith(('!', '>')):
					responses[message.author] = message.content
		while not countdown_task.done():
			await asyncio.sleep(0.1)
		embed = answer_message.embeds[0]
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
		if correct_players:
			correct_players_output = clients.inflect_engine.join([player.display_name for player in correct_players])
			correct_players_output += f" {clients.inflect_engine.plural('was', len(correct_players))} right!"
		else:
			correct_players_output = "Nobody got it right!"
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
		answer = BeautifulSoup(html.unescape(data["answer"]), "html.parser").get_text().replace("\\'", "'")
		await ctx.embed_say(f"The answer was `{answer}`", footer_text = correct_players_output)
		if bet and bets:
			bets_output = []
			for player, player_bet in bets.items():
				if player in correct_players:
					difference = player_bet
					action_text = "won"
				else:
					difference = -player_bet
					action_text = "lost"
				money = await ctx.bot.db.fetchval(
					"""
					UPDATE trivia.users
					SET money = money + $2
					WHERE user_id = $1
					RETURNING money
					""", 
					player.id, difference
				)
				bets_output.append(f"{player.mention} {action_text} ${player_bet:,} and now has ${money:,}.")
			await ctx.embed_say('\n'.join(bets_output))
	
	async def _bet_countdown(self, bet_message):
		embed = bet_message.embeds[0]
		while self.active[bet_message.guild.id]["bet_countdown"]:
			await asyncio.sleep(1)
			self.active[bet_message.guild.id]["bet_countdown"] -= 1
			embed.set_footer(text = f"You have {self.active[bet_message.guild.id]['bet_countdown']} seconds left to bet")
			await bet_message.edit(embed = embed)
	
	async def _trivia_countdown(self, answer_message):
		embed = answer_message.embeds[0]
		while self.active[answer_message.guild.id]["question_countdown"]:
			await asyncio.sleep(1)
			self.active[answer_message.guild.id]["question_countdown"] -= 1
			embed.set_footer(text = f"You have {self.active[answer_message.guild.id]['question_countdown']} seconds left to answer")
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
		if not money:
			return await ctx.embed_reply("You have not played any trivia yet")
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

