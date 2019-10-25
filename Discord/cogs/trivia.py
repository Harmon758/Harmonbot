
import discord
from discord.ext import commands

import asyncio
import datetime
import html
import random
import re
import string
import unicodedata

import aiohttp
from bs4 import BeautifulSoup
import dateutil.parser
from pyparsing import Forward, Group, printables, OneOrMore, Suppress, Word, ZeroOrMore

from utilities import checks
from utilities.context import Context

def setup(bot):
	bot.add_cog(Trivia(bot))

class Trivia(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.wait_time = 15
		self.active_trivia = {}
		self.active_jeopardy = {}
		
		# Add jeopardy as trivia subcommand
		self.bot.add_command(self.jeopardy)
		self.trivia.add_command(self.jeopardy)
		
		self.bot.loop.create_task(self.initialize_database())
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden_predicate(ctx)
	
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
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	async def trivia(self, ctx):
		'''
		Trivia game
		Only your last answer is accepted
		Answers prepended with ! or > are ignored
		Questions are taken from Jeopardy!
		'''
		if ctx.guild.id in self.active_trivia:
			channel_id = self.active_trivia[ctx.guild.id]["channel_id"]
			if ctx.channel.id == channel_id:
				return await ctx.embed_reply(f"There is already an ongoing game of trivia here")
			else:
				channel = ctx.guild.get_channel(channel_id)
				return await ctx.embed_reply(f"There is already an ongoing game of trivia in {channel.mention}")
		self.active_trivia[ctx.guild.id] = {"channel_id": ctx.channel.id, "question_countdown": 0, "responses": {}}
		try:
			await self.trivia_round(ctx)
		finally:
			del self.active_trivia[ctx.guild.id]
	
	@trivia.command(name = "bet")
	async def trivia_bet(self, ctx):
		'''
		Trivia with betting
		The category is shown first during the betting phase
		Enter any amount under or equal to the money you have to bet
		Currently, you start with $100,000
		'''
		if ctx.guild.id in self.active_trivia:
			channel = ctx.guild.get_channel(self.active_trivia[ctx.guild.id]["channel_id"])
			return await ctx.embed_reply(f"There is already an ongoing game of trivia in {channel.mention}")
		self.active_trivia[ctx.guild.id] = {"channel_id": ctx.channel.id, "question_countdown": 0, "responses": {}, 
											"bet_countdown": 0, "bets": {}}
		try:
			await self.trivia_round(ctx, bet = True)
		finally:
			del self.active_trivia[ctx.guild.id]
	
	async def trivia_round(self, ctx, bet = False, response = None):
		try:
			async with ctx.bot.aiohttp_session.get("http://jservice.io/api/random") as resp:
				data = (await resp.json())[0]
		except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
			return await ctx.embed_reply(":no_entry: Error: Error connecting to API")
		if not data.get("question") or not data.get("category") or data["question"] == '=':
			if response:
				embed = response.embeds[0]
				embed.description += "\n:no_entry: Error: API response missing question/category"
				return await response.edit(embed = embed)
			else:
				response = await ctx.embed_reply(":no_entry: Error: API response missing question/category\nRetrying...")
				return await self.trivia_round(ctx, bet, response)
		# Add message about making POST request to API/invalid with id?
		# Include site page to send ^?
		if bet:
			self.active_trivia[ctx.guild.id]["bet_countdown"] = self.wait_time
			bet_message = await ctx.embed_reply(author_name = None, title = string.capwords(data["category"]["title"]), 
												footer_text = f"You have {self.active_trivia[ctx.guild.id]['bet_countdown']} seconds left to bet")
			embed = bet_message.embeds[0]
			while self.active_trivia[bet_message.guild.id]["bet_countdown"]:
				await asyncio.sleep(1)
				self.active_trivia[bet_message.guild.id]["bet_countdown"] -= 1
				embed.set_footer(text = f"You have {self.active_trivia[bet_message.guild.id]['bet_countdown']} seconds left to bet")
				await bet_message.edit(embed = embed)
			embed.set_footer(text = "Betting is over")
			await bet_message.edit(embed = embed)
		self.active_trivia[ctx.guild.id]["question_countdown"] = self.wait_time
		question_message = await ctx.embed_reply(data["question"], author_name = None, 
													title = string.capwords(data["category"]["title"]), 
													footer_text = f"You have {self.wait_time} seconds left to answer | Air Date", 
													timestamp = dateutil.parser.parse(data["airdate"]))
		embed = question_message.embeds[0]
		while self.active_trivia[question_message.guild.id]["question_countdown"]:
			await asyncio.sleep(1)
			self.active_trivia[question_message.guild.id]["question_countdown"] -= 1
			embed.set_footer(text = f"You have {self.active_trivia[question_message.guild.id]['question_countdown']} seconds left to answer | Air Date")
			try:
				await question_message.edit(embed = embed)
			except (aiohttp.ClientConnectionError, discord.NotFound):
				continue
		embed.set_footer(text = "Time's up! | Air Date")
		try:
			await question_message.edit(embed = embed)
		except discord.NotFound:
			pass
		correct_players = []
		incorrect_players = []
		for player, response in self.active_trivia[ctx.guild.id]["responses"].items():
			if self.check_answer(data["answer"], response):
				correct_players.append(player)
			else:
				incorrect_players.append(player)
		if correct_players:
			correct_players_output = ctx.bot.inflect_engine.join([player.display_name for player in correct_players])
			correct_players_output += f" {ctx.bot.inflect_engine.plural('was', len(correct_players))} right!"
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
		await ctx.embed_reply(f"The answer was `{answer}`", 
								footer_text = correct_players_output, 
								author_name = None, in_response_to = False)
		if bet and self.active_trivia[ctx.guild.id]["bets"]:
			bets_output = []
			for player, player_bet in self.active_trivia[ctx.guild.id]["bets"].items():
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
			await ctx.embed_reply('\n'.join(bets_output), author_name = None)
	
	@commands.Cog.listener("on_message")
	async def trivia_on_message(self, message):
		if not message.guild or message.guild.id not in self.active_trivia:
			return
		if message.channel.id != self.active_trivia[message.guild.id]["channel_id"]:
			return
		if self.active_trivia[message.guild.id].get("bet_countdown") and message.content.isdigit():
			ctx = await self.bot.get_context(message, cls = Context)
			money = await self.bot.db.fetchval("SELECT money FROM trivia.users WHERE user_id = $1", message.author.id)
			if not money:
				money = await self.bot.db.fetchval(
					"""
					INSERT INTO trivia.users (user_id, correct, incorrect, money)
					VALUES ($1, 0, 0, 100000)
					RETURNING money
					""", 
					message.author.id
				)
			if int(message.content) <= money:
				self.active_trivia[message.guild.id]["bets"][message.author] = int(message.content)
				await ctx.embed_reply(f"has bet ${message.content}")
			else:
				await ctx.embed_reply("You don't have that much money to bet!")
		elif self.active_trivia[message.guild.id]["question_countdown"] and not message.content.startswith(('!', '>')):
			self.active_trivia[message.guild.id]["responses"][message.author] = message.content
	
	@trivia.command(name = "money", aliases = ["cash"])
	async def trivia_money(self, ctx):
		'''Trivia money'''
		money = await ctx.bot.db.fetchval("SELECT money FROM trivia.users WHERE user_id = $1", ctx.author.id)
		if not money:
			return await ctx.embed_reply("You have not played any trivia yet")
		await ctx.embed_reply(f"You have ${money:,}")
	
	@trivia.command(name = "score", aliases = ["points", "rank", "level"])
	async def trivia_score(self, ctx):
		'''Trivia score'''
		record = await ctx.bot.db.fetchrow("SELECT correct, incorrect FROM trivia.users WHERE user_id = $1", ctx.author.id)
		if not record:
			return await ctx.embed_reply("You have not played any trivia yet")
		total = record["correct"] + record["incorrect"]
		correct_percentage = record["correct"] / total * 100
		await ctx.embed_reply(f"You have answered {record['correct']}/{total} ({correct_percentage:.2f}%) correctly.")
	
	@trivia.command(name = "scores", aliases = ["scoreboard", "top", "ranks", "levels"])
	async def trivia_scores(self, ctx, number: int = 10):
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
						user = await ctx.bot.fetch_user(record["user_id"])
					total = record["correct"] + record["incorrect"]
					correct_percentage = record["correct"] / total * 100
					fields.append((str(user), f"{record['correct']}/{total} correct ({correct_percentage:.2f}%)"))
		await ctx.embed_reply(title = f"Trivia Top {number}", fields = fields)
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	async def jeopardy(self, ctx):
		'''
		Trivia with categories
		[row number] [value] to pick the question
		Based on Jeopardy!
		'''
		# TODO: Daily Double?
		if ctx.guild.id in self.active_jeopardy:
			channel_id = self.active_jeopardy[ctx.guild.id]["channel_id"]
			if ctx.channel.id == channel_id:
				return await ctx.embed_reply(f"There is already an ongoing game of jeopardy here")
			else:
				channel = ctx.guild.get_channel(channel_id)
				return await ctx.embed_reply(f"There is already an ongoing game of jeopardy in {channel.mention}")
		self.active_jeopardy[ctx.guild.id] = {"channel_id": ctx.channel.id, "question_countdown": 0, 
												"answer": None, "answerer": None}
		message = await ctx.embed_reply("Generating board..", title = "Jeopardy!", author_name = None)
		board = {}
		values = [200, 400, 600, 800, 1000]
		while len(board) < 6:
			url = "http://jservice.io/api/random"
			params = {"count": 6 - len(board)}
			async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			for random_clue in data:
				category_id = random_clue["category_id"]
				if category_id in board:
					continue
				url = "http://jservice.io/api/category"
				params = {"id": category_id}
				async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
					data = await resp.json()
				# The first round originally ranged from $100 to $500
				# and was doubled to $200 to $1,000 on November 26, 2001
				# https://en.wikipedia.org/wiki/Jeopardy!
				# http://www.j-archive.com/showgame.php?game_id=1062
				# jService uses noon UTC for airdates
				# jService doesn't include Double Jeopardy! clues
				transition_date = datetime.datetime(2001, 11, 26, 12, tzinfo = datetime.timezone.utc)
				clues = {value: [] for value in values}
				for clue in data["clues"]:
					if not clue["question"] or not clue["value"]:
						continue
					if dateutil.parser.parse(clue["airdate"]) < transition_date:
						clues[clue["value"] * 2].append(clue)
					else:
						clues[clue["value"]].append(clue)
				if not all(clues.values()):
					continue
				clues = [random.choice(clues[value]) for value in values]
				board[category_id] = {"title": string.capwords(random_clue["category"]["title"]), 
										"clues": clues}
		for category_id, category_info in board.items():
			category_title = category_info["title"]
			category_title_line_character_limit = ctx.bot.EMBED_DESCRIPTION_CODE_BLOCK_ROW_CHARACTER_LIMIT - 25
			# len("#) " + "  200 400 600 800 1000") = 25
			if len(category_title) > category_title_line_character_limit:
				split_index = category_title.rfind(' ', 0, category_title_line_character_limit)
				board[category_id]["title"] = category_title[:split_index] + '\n' + category_title[split_index + 1:]
		max_width = max(len(section) for category in board.values() for section in category["title"].split('\n'))
		board_lines = []
		for number, category_title in enumerate(category["title"] for category in board.values()):
			try:
				split_index = category_title.index('\n')
				board_lines.append(f"{number + 1}) {category_title[:split_index]}\n"
									f"   {category_title[split_index + 1:].ljust(max_width)}  200 400 600 800 1000")
			except ValueError:
				board_lines.append(f"{number + 1}) {category_title.ljust(max_width)}  200 400 600 800 1000")
		embed = message.embeds[0]
		embed.description = ctx.bot.CODE_BLOCK.format('\n'.join(board_lines))
		await message.edit(embed = embed)
		scores = {}
		
		def choice_check(message):
			if message.channel.id != ctx.channel.id:
				return False
			parts = message.content.split()
			if len(parts) < 2:
				return False
			return parts[0].isdecimal() and parts[1].isdecimal()
		
		while any(clue for category in board.values() for clue in category["clues"]):
			message = await ctx.bot.wait_for("message", check = choice_check)
			# TODO: Timeout?
			# TODO: Enforce last person to answer correctly chooses?
			ctx = await ctx.bot.get_context(message)
			message_parts = message.content.split()
			row_number = int(message_parts[0])
			value = int(message_parts[1])
			if row_number < 1 or row_number > 6:
				await ctx.embed_reply(":no_entry: That's not a valid row number")
				continue
			if value not in values:
				await ctx.embed_reply(":no_entry: That's not a valid value")
				continue
			value_index = values.index(value)
			category_id = list(board.keys())[row_number - 1]
			clue = board[category_id]["clues"][value_index]
			if not clue:  # Use := in Python 3.8
				await ctx.embed_reply(":no_entry: That question has already been chosen")
				continue
			self.active_jeopardy[ctx.guild.id]["answerer"] = None
			self.active_jeopardy[ctx.guild.id]["answer"] = clue["answer"]
			self.active_jeopardy[ctx.guild.id]["question_countdown"] = self.wait_time
			message = await ctx.embed_reply(clue["question"], title = board[category_id]["title"], author_name = None, 
											footer_text = f"You have {self.wait_time} seconds left to answer | Air Date", 
											timestamp = dateutil.parser.parse(clue["airdate"]))
			embed = message.embeds[0]
			while self.active_jeopardy[ctx.guild.id]["question_countdown"]:
				await asyncio.sleep(1)
				self.active_jeopardy[ctx.guild.id]["question_countdown"] -= 1
				embed.set_footer(text = f"You have {self.active_jeopardy[ctx.guild.id]['question_countdown']} seconds left to answer | Air Date")
				await message.edit(embed = embed)
				if self.active_jeopardy[ctx.guild.id]["answerer"]:
					break
			embed.set_footer(text = "Time's up! | Air Date")
			await message.edit(embed = embed)
			answer = BeautifulSoup(html.unescape(self.active_jeopardy[ctx.guild.id]["answer"]), 
									"html.parser").get_text().replace("\\'", "'")
			response = f"The answer was `{answer}`\n"
			answerer = self.active_jeopardy[ctx.guild.id]["answerer"]
			if answerer:  # Use := in Python 3.8
				scores[answerer] = scores.get(answerer, 0) + int(value)
				response += f"{answerer.mention} was right! They now have ${scores[answerer]}\n"
			else:
				response += "Nobody got it right\n"
			response += ", ".join(f"{player.mention}: ${score}" for player, score in scores.items()) + '\n'
			board[category_id]["clues"][value_index] = None
			board_lines[row_number - 1] = (len(str(value)) * ' ').join(board_lines[row_number - 1].rsplit(str(value), 1))
			response += ctx.bot.CODE_BLOCK.format('\n'.join(board_lines))
			await ctx.embed_send(response)
		highest_score = max(scores.values())
		winners = [answerer.mention for answerer, score in scores.items() if score == highest_score]
		await ctx.embed_send(f"{ctx.bot.inflect_engine.join(winners)} {ctx.bot.inflect_engine.plural('is', len(winners))} "
								f"the {ctx.bot.inflect_engine.plural('winner', len(winners))} with ${highest_score}!", 
								title = "Jeopardy!")
		del self.active_jeopardy[ctx.guild.id]
	
	@commands.Cog.listener("on_message")
	async def jeopardy_on_message(self, message):
		if not message.guild or message.guild.id not in self.active_jeopardy:
			return
		if message.channel.id != self.active_jeopardy[message.guild.id]["channel_id"]:
			return
		if (self.active_jeopardy[message.guild.id]["question_countdown"] and 
			self.check_answer(self.active_jeopardy[message.guild.id]["answer"], message.content) and 
			not self.active_jeopardy[message.guild.id]["answerer"]):
				self.active_jeopardy[message.guild.id]["answerer"] = message.author
	
	# TODO: jeopardy stats
	
	def check_answer(self, answer, response):
		# Unescape HTML entities in answer and extract text between HTML tags
		answer = BeautifulSoup(html.unescape(answer), "html.parser").get_text()
		# Replace in answer: \' -> '
		# Replace: & -> and
		answer = answer.replace("\\'", "'").replace('&', "and")
		response = response.replace('&', "and")
		# Remove exclamation marks, periods, and quotation marks
		for character in '!."':
			if character in answer:
				answer = answer.replace(character, "")
			if character in response:
				response = response.replace(character, "")
		# Remove diacritics
		answer = "".join(character for character in unicodedata.normalize("NFD", answer) 
							if not unicodedata.combining(character))
		response = "".join(character for character in unicodedata.normalize("NFD", response) 
							if not unicodedata.combining(character))
		# Remove extra whitespace
		# Make lowercase
		answer = ' '.join(answer.split()).lower()
		response = ' '.join(response.split()).lower()
		# Remove article prefixes
		answer = self.remove_article_prefix(answer)
		response = self.remove_article_prefix(response)
		# Return False if empty response
		if not response:
			return False
		# Get items in lists
		answer_items = [item.strip() for item in answer.split(',')]
		answer_items[-1:] = [item.strip() for item in answer_items[-1].split("and") if item]
		response_items = [item.strip() for item in response.split(',')]
		response_items[-1:] = [item.strip() for item in response_items[-1].split("and") if item]
		# Return False if only "and"
		if not response_items:
			return False
		# Remove article prefixes
		for index, item in enumerate(answer_items):
			answer_items[index] = self.remove_article_prefix(item)
		for index, item in enumerate(response_items):
			response_items[index] = self.remove_article_prefix(item)
		# Check equivalence
		if set(answer_items) == set(response_items):
			return True
		# Check plurality
		if response == self.bot.inflect_engine.plural(answer):
			return True
		# Check XX and YY ZZ
		last = answer_items[-1].split()
		if len(last) > 1:
			suffix = last[-1]
			if set([f"{item} {suffix}" for item in answer_items[:-1]] + [answer_items[-1]]) == set(response_items):
				return True
		last = response_items[-1].split()
		if len(last) > 1:
			suffix = last[-1]
			if set(answer_items) == set([f"{item} {suffix}" for item in response_items[:-1]] + [response_items[-1]]):
				return True
		# Remove commas
		if ',' in answer:
			answer = answer.replace(',', "")
		if ',' in response:
			response = response.replace(',', "")
		# Check for list separated by /
		if set(item.strip() for item in answer.split('/')) == set(item.strip() for item in response.split('/')):
			return True
		# Check removal of/replacement of - with space
		if answer.replace('-', ' ') == response.replace('-', ' '):
			return True
		if answer.replace('-', "") == response.replace('-', ""):
			return True
		# Check removal of parentheses
		if response == self.remove_article_prefix(answer.replace('(', "").replace(')', "")):
			return True
		# Check XX or YY
		if response in answer.split(" or "):
			return True
		# Check XX/YY
		if response in answer.split('/'):
			return True
		# Check XX/YY ZZ
		answer_words = answer.split()
		answers = answer_words[0].split('/')
		for answer_word in answer_words[1:]:
			if '/' in answer_word:
				answers = [f"{permutation} {word}" for permutation in answers for word in answer_word.split('/')]
			else:
				answers = [f"{permutation} {answer_word}" for permutation in answers]
		if response in answers:
			return True
		# Check numbers to words conversion
		response_words = response.split()
		for words in (answer_words, response_words):
			for index, word in enumerate(words):
				if word[0].isdigit():
					words[index] = self.bot.inflect_engine.number_to_words(word)
		if ' '.join(answer_words) == ' '.join(response_words):
			return True
		# Handle optional parentheses
		word = Word(printables, excludeChars = "()")
		token = Forward()
		token << ( word | Group(Suppress('(') + OneOrMore(token) + Suppress(')')) )
		expression = ZeroOrMore(token)
		parsed = expression.parseString(answer).asList()
		def add_accepted(accepted, item, initial_length = 0):
			if isinstance(item, list):
				accepted = add_optional_accepted(accepted, item)
			else:
				for accepted_index, accepted_item in enumerate(accepted[initial_length:]):
					accepted[initial_length + accepted_index] = f"{accepted_item} {item}".lstrip()
			return accepted
		def add_optional_accepted(accepted, optional):
			initial_length = len(accepted)
			if isinstance(optional[0], list):
				accepted = add_optional_accepted(accepted, optional[0])
			else:
				for accepted_item in accepted.copy():
					accepted.append(f"{accepted_item} {optional[0]}".lstrip())
			for item in optional[1:]:
				add_accepted(accepted, item, initial_length = initial_length)
			return accepted
		accepted = [""]
		for item in parsed:
			accepted = add_accepted(accepted, item)
		for item in parsed:
			if isinstance(item, list):
				accepted.extend(add_optional_accepted([""], item)[1:])
		for item in accepted:
			if item.startswith("or "):
				accepted.append(item[3:])
				accepted.append(self.remove_article_prefix(item[3:]))
			if item.endswith(" accepted"):
				accepted.append(item[:-9])
				accepted.append(self.remove_article_prefix(item[:-9]))
		if response in accepted:
			return True
		# Check XX YY (or ZZ accepted)
		matches = re.search(r"(.+?)\s?\((?:or )?(?:a |an |the )?(.+?)(?: accepted)?\)", answer)
		if matches and response == f"{matches.group(1).rsplit(' ', 1)[0]} {matches.group(2)}":
			return True
		# Check abbreviations
		for abbreviation, word in (("mt", "mount"), ("st", "saint")):
			if (re.sub(fr"(^|\W)({abbreviation})($|\W)", fr"\1{word}\3", answer) == 
				re.sub(fr"(^|\W)({abbreviation})($|\W)", fr"\1{word}\3", response)):
				return True
		return False
	
	def remove_article_prefix(self, string):
		for article in ("a ", "an ", "the "):
			if string.startswith(article):
				return string[len(article):]
		return string

