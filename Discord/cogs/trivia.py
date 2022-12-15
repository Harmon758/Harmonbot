
import discord
from discord.ext import commands

import asyncio
import datetime
import html
import random
import sys

import aiohttp
from bs4 import BeautifulSoup
import dateutil.parser

from utilities import checks

sys.path.insert(0, "..")
from units.trivia import capwords, check_answer
sys.path.pop(0)

async def setup(bot):
	await bot.add_cog(Trivia(bot))

class Trivia(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.wait_time = 15
		self.active_trivia = {}
		self.active_jeopardy = {}
		
		self.jeopardy_matches = {}
		
		# Add jeopardy as trivia subcommand
		self.bot.add_command(self.jeopardy)
		self.trivia.add_command(self.jeopardy)
	
	async def cog_load(self):
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
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	max_concurrency = commands.MaxConcurrency(1, per = commands.BucketType.guild, wait = False)
	
	async def cog_command_error(self, ctx, error):
		if isinstance(error, commands.MaxConcurrencyReached):
			if ctx.guild.id in self.active_trivia:
				game = "trivia"
			elif ctx.guild.id in self.active_jeopardy:
				game = "jeopardy"
			else:
				raise RuntimeError("Trivia max concurrency reached, but neither active trivia nor jeopardy found.")
			channel_id = getattr(self, f"active_{game}")[ctx.guild.id]["channel_id"]
			if ctx.channel.id == channel_id:
				return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: There is already an ongoing game of {game} here")
			else:
				channel = ctx.guild.get_channel_or_thread(channel_id)
				return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: There is already an ongoing game of {game} in {channel.mention}")
	
	@commands.group(max_concurrency = max_concurrency, invoke_without_command = True, case_insensitive = True)
	async def trivia(self, ctx):
		"""
		Trivia game
		Only your last answer is accepted
		Answers prepended with ! or > are ignored
		Questions are taken from Jeopardy!
		"""
		self.active_trivia[ctx.guild.id] = {"channel_id": ctx.channel.id, "question_countdown": 0, "responses": {}}
		try:
			await self.trivia_round(ctx)
		finally:
			del self.active_trivia[ctx.guild.id]
	
	@trivia.command(name = "bet", max_concurrency = max_concurrency)
	async def trivia_bet(self, ctx):
		'''
		Trivia with betting
		The category is shown first during the betting phase
		Enter any amount under or equal to the money you have to bet
		Currently, you start with $100,000
		'''
		self.active_trivia[ctx.guild.id] = {"channel_id": ctx.channel.id, "question_countdown": 0, "responses": {}, 
											"bet_countdown": 0, "bets": {}}
		try:
			await self.trivia_round(ctx, bet = True)
		finally:
			del self.active_trivia[ctx.guild.id]
	
	async def trivia_round(self, ctx, bet = False, response = None):
		try:
			async with ctx.bot.aiohttp_session.get(
				"http://jservice.io/api/random"
			) as resp:
				if resp.status in (500, 503):
					await ctx.embed_reply(
						f"{ctx.bot.error_emoji} Error: Error connecting to API"
					)
					return
				data = (await resp.json())[0]
		except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
			await ctx.embed_reply(
				f"{ctx.bot.error_emoji} Error: Error connecting to API"
			)
			return
		
		if not data.get("question") or not data.get("category") or data["question"] == '=' or not data.get("answer"):
			if response:
				embed = response.embeds[0]
				embed.description += f"\n{ctx.bot.error_emoji} Error: API response missing question/category/answer"
				await response.edit(embed = embed)
				return
			else:
				response = await ctx.embed_reply(
					f"{ctx.bot.error_emoji} Error: API response missing question/category/answer\nRetrying..."
				)
				await self.trivia_round(ctx, bet, response)
				return
		# Add message about making POST request to API/invalid with id?
		# Include site page to send ^?
		if bet:
			self.active_trivia[ctx.guild.id]["bet_countdown"] = self.wait_time
			bet_message = await ctx.embed_reply(
				author_name = None,
				title = capwords(data["category"]["title"]),
				footer_text = f"You have {self.active_trivia[ctx.guild.id]['bet_countdown']} seconds left to bet"
			)
			embed = bet_message.embeds[0]
			while self.active_trivia[bet_message.guild.id]["bet_countdown"]:
				await asyncio.sleep(1)
				self.active_trivia[bet_message.guild.id]["bet_countdown"] -= 1
				embed.description = '\n'.join(
					f"{player.mention} has bet ${bet}"
					for player, bet in self.active_trivia[bet_message.guild.id]["bets"].items()
				)
				embed.set_footer(
					text = f"You have {self.active_trivia[bet_message.guild.id]['bet_countdown']} seconds left to bet"
				)
				await bet_message.edit(embed = embed)
			embed.set_footer(text = "Betting is over")
			await bet_message.edit(embed = embed)
		
		self.active_trivia[ctx.guild.id]["question_countdown"] = self.wait_time
		question_message = await ctx.embed_reply(
			author_name = None,
			title = capwords(data["category"]["title"]),
			description = data["question"],
			footer_text = f"You have {self.wait_time} seconds left to answer | Air Date",
			timestamp = dateutil.parser.parse(data["airdate"])
		)
		embed = question_message.embeds[0]
		
		while self.active_trivia[question_message.guild.id]["question_countdown"]:
			await asyncio.sleep(1)
			self.active_trivia[question_message.guild.id]["question_countdown"] -= 1
			embed.set_footer(
				text = f"You have {self.active_trivia[question_message.guild.id]['question_countdown']} seconds left to answer | Air Date"
			)
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
			if check_answer(
				data["answer"], response,
				inflect_engine = self.bot.inflect_engine
			):
				correct_players.append(player)
			else:
				incorrect_players.append(player)
		if correct_players:
			correct_players_output = ctx.bot.inflect_engine.join(
				[player.display_name for player in correct_players]
			)
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
			if points_cog := ctx.bot.get_cog("Points"):
				await points_cog.add(user = correct_player, points = 10)
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
		
		answer = BeautifulSoup(
			html.unescape(data["answer"]), "html.parser"
		).get_text().replace("\\'", "'")
		await ctx.embed_reply(
			author_name = None,
			footer_text = correct_players_output,
			description = f"The answer was `{answer}`",
			in_response_to = False
		)
		
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
				bets_output.append(
					f"{player.mention} {action_text} ${player_bet:,} and now has ${money:,}"
				)
			await ctx.embed_reply('\n'.join(bets_output), author_name = None)
	
	@commands.Cog.listener("on_message")
	async def trivia_on_message(self, message):
		if not message.guild or message.guild.id not in self.active_trivia:
			return
		if message.channel.id != self.active_trivia[message.guild.id]["channel_id"]:
			return
		if self.active_trivia[message.guild.id].get("bet_countdown") and message.content.isdigit():
			ctx = await self.bot.get_context(message)
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
				await self.bot.attempt_delete_message(message)
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
	
	@commands.group(max_concurrency = max_concurrency, invoke_without_command = True, case_insensitive = True)
	async def jeopardy(self, ctx):
		'''
		Trivia with categories
		[row number] [value] to pick the question
		Based on Jeopardy!
		'''
		# TODO: Daily Double?
		self.active_jeopardy[ctx.guild.id] = {"channel_id": ctx.channel.id, "question_countdown": 0, 
												"answer": None, "answerer": None}
		message = await ctx.embed_reply("Generating board..", title = "Jeopardy!", author_name = None)
		board = {}
		values = [200, 400, 600, 800, 1000]
		while len(board) < 6:
			url = "http://jservice.io/api/random"
			params = {"count": 6 - len(board)}
			async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
				if resp.status in (500, 503):
					embed = message.embeds[0]
					embed.description = f"{ctx.bot.error_emoji} Error: Error connecting to API"
					await message.edit(embed = embed)
					return
				data = await resp.json()
			for random_clue in data:
				category_id = random_clue["category_id"]
				if category_id is None or category_id in board:
					continue
				url = "http://jservice.io/api/category"
				params = {"id": category_id}
				async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
					if resp.status == 404:
						continue
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
				board[category_id] = {"title": capwords(random_clue["category"]["title"]), 
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
				await ctx.embed_reply(f"{ctx.bot.error_emoji} That's not a valid row number")
				continue
			if value not in values:
				await ctx.embed_reply(f"{ctx.bot.error_emoji} That's not a valid value")
				continue
			value_index = values.index(value)
			category_id = list(board.keys())[row_number - 1]
			if not (clue := board[category_id]["clues"][value_index]):
				await ctx.embed_reply(f"{ctx.bot.error_emoji} That question has already been chosen")
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
				await ctx.bot.attempt_edit_message(message, embed = embed)
				if self.active_jeopardy[ctx.guild.id]["answerer"]:
					break
			embed.set_footer(text = "Time's up! | Air Date")
			await message.edit(embed = embed)
			answer = BeautifulSoup(html.unescape(self.active_jeopardy[ctx.guild.id]["answer"]), 
									"html.parser").get_text().replace("\\'", "'")
			response = f"The answer was `{answer}`\n"
			if answerer := self.active_jeopardy[ctx.guild.id]["answerer"]:
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
		if message.author.id == self.bot.user.id:
			return
		if not self.active_jeopardy[message.guild.id]["question_countdown"]:
			return
		if self.active_jeopardy[message.guild.id]["answerer"]:
			return
		if check_answer(self.active_jeopardy[message.guild.id]["answer"], message.content, inflect_engine = self.bot.inflect_engine):
			self.active_jeopardy[message.guild.id]["answerer"] = message.author
	
	@jeopardy.command()
	async def buzzer(self, ctx):
		if match := self.jeopardy_matches.get(ctx.channel.id):
			await ctx.embed_reply(
				f"[There's already a Jeopardy match in progress here]({match.message.jump_url})"
			)
			return
		
		self.jeopardy_matches[ctx.channel.id] = JeopardyMatch()
		await self.jeopardy_matches[ctx.channel.id].start(ctx)
		await self.jeopardy_matches[ctx.channel.id].ended.wait()
		del self.jeopardy_matches[ctx.channel.id]
	
	# TODO: jeopardy stats


class JeopardyMatch:
	
	VALUES = (200, 400, 600, 800, 1000)
	
	def __init__(self):
		self.board = []
		self.board_lines = []
		self.scores = {}
		
		self.ended = asyncio.Event()
	
	async def start(self, ctx):
		self.bot = ctx.bot
		self.ctx = ctx
		self.message = await ctx.embed_reply(
			author_name = None, 
			title = "Jeopardy!", 
			description = "Generating board..", 
			footer_text = None
		)
		self.turn = ctx.author  # who's turn it is
		
		await self.generate_board()
		
		embed = self.message.embeds[0]
		embed.description = ctx.bot.CODE_BLOCK.format('\n'.join(self.board_lines))
		embed.description += f"\nIt's {self.turn.mention}'s turn"
		await self.message.edit(embed = embed, view = JeopardySelectionView(self))
	
	async def answer(self, player):
		self.answered.append(player)
		self.answerer = player
		
		answer_prompt_message = await self.ctx.embed_send(
			title = "Jeopardy!", 
			title_url = self.message.jump_url, 
			description = (
				f"{player.mention} hit the buzzer\n"
				f"{player.mention}: What's your answer?"
			), 
			footer_text = "You have 15 seconds to answer"
		)
		
		try:
			message = await self.bot.wait_for("message", check = self.answer_check, timeout = 15)
		except asyncio.TimeoutError:
			self.scores[player] = self.scores.get(player, 0) - int(self.value)
			await self.ctx.embed_send(
				title = "Jeopardy!", 
				title_url = answer_prompt_message.jump_url, 
				description = (
					f"{player.mention} ran out of time and lost `{self.value}`\n"
					f"{player.mention} now has `{self.scores[player]}`"
				)
			)
			self.message = await self.ctx.send(
				embed = self.message.embeds[0], 
				view = JeopardyBuzzerView(self)
			)
			return
		
		if check_answer(self.correct_answer, message.content, inflect_engine = self.bot.inflect_engine):
			# Correct answer
			answer = BeautifulSoup(html.unescape(self.correct_answer), "html.parser").get_text().replace("\\'", "'")
			self.scores[player] = self.scores.get(player, 0) + int(self.value)
			
			response = (
				f"The answer was `{answer}`\n"
				f"{player.mention} was correct and won `{self.value}`\n\n"
			)
			if scores := ", ".join(f"{player.mention}: `{score}`" for player, score in self.scores.items()):
				response += scores + '\n'
			
			self.board[self.category_number - 1]["clues"][self.value] = None
			self.board_lines[self.category_number - 1] = (len(str(self.value)) * ' ').join(self.board_lines[self.category_number - 1].rsplit(str(self.value), 1))
			response += self.bot.CODE_BLOCK.format('\n'.join(self.board_lines))
			
			if clues_left := any(clue for category in self.board for clue in category["clues"].values()):
				self.turn = player
				response += f"\nIt's {self.turn.mention}'s turn"
				view = JeopardySelectionView(self)
			else:
				view = None
			
			self.message = await self.ctx.embed_send(
				title = "Jeopardy!", 
				title_url = answer_prompt_message.jump_url, 
				description = response, 
				view = view
			)
			
			if not clues_left:
				await self.send_winner()
				self.ended.set()
		else:
			# Incorrect answer
			self.scores[player] = self.scores.get(player, 0) - int(self.value)
			await self.ctx.embed_send(
				title = "Jeopardy!", 
				title_url = answer_prompt_message.jump_url, 
				description = (
					f"{player.mention} was incorrect and lost `{self.value}`\n"
					f"{player.mention} now has `{self.scores[player]}`"
				)
			)
			self.message = await self.ctx.send(
				embed = self.message.embeds[0], 
				view = JeopardyBuzzerView(self)
			)
	
	def answer_check(self, message):
		if message.channel != self.ctx.channel:
			return False
		
		return message.author == self.answerer
	
	async def select(self, category_number, value):
		self.category_number = category_number
		self.value = value
		
		clue = self.board[category_number - 1]["clues"][self.value]
		
		self.correct_answer = clue["answer"]
		self.answered = []
		
		self.message = await self.ctx.embed_send(
			title = f"{self.board[category_number - 1]['title']}\n(for {value})", 
			title_url = self.message.jump_url, 
			description = clue["question"], 
			footer_text = f"You have 15 seconds to hit the buzzer | Air Date",  # TODO: Dynamic wait time
			timestamp = dateutil.parser.parse(clue["airdate"]), 
			view = JeopardyBuzzerView(self)
		)
	
	async def timeout(self):
		embed = self.message.embeds[0]
		embed.set_footer(text = "Time's up! | Air Date")
		await self.message.edit(embed = embed)
		
		answer = BeautifulSoup(html.unescape(self.correct_answer), "html.parser").get_text().replace("\\'", "'")
		response = (
			f"The answer was `{answer}`\n"
			"Nobody got it right\n\n"
		)
		if scores := ", ".join(f"{player.mention}: `{score}`" for player, score in self.scores.items()):
			response += scores + '\n'
		
		self.board[self.category_number - 1]["clues"][self.value] = None
		self.board_lines[self.category_number - 1] = (len(str(self.value)) * ' ').join(self.board_lines[self.category_number - 1].rsplit(str(self.value), 1))
		response += self.bot.CODE_BLOCK.format('\n'.join(self.board_lines))
		
		if clues_left := any(clue for category in self.board for clue in category["clues"].values()):
			response += f"\nIt's {self.turn.mention}'s turn"
			view = JeopardySelectionView(self)
		else:
			view = None
		
		self.message = await self.ctx.embed_send(
			title = "Jeopardy!", 
			title_url = self.message.jump_url, 
			description = response, 
			view = view
		)
		
		if not clues_left:
			await self.send_winner()
			self.ended.set()
	
	async def generate_board(self):
		while len(self.board) < 6:
			url = "http://jservice.io/api/random"
			params = {"count": 6 - len(self.board)}
			async with self.bot.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			
			for random_clue in data:
				category_id = random_clue["category_id"]
				
				if category_id is None or category_id in self.board:
					continue
				
				url = "http://jservice.io/api/category"
				params = {"id": category_id}
				async with self.bot.aiohttp_session.get(url, params = params) as resp:
					if resp.status == 404:
						continue
					data = await resp.json()
				
				# The first round originally ranged from $100 to $500
				# and was doubled to $200 to $1,000 on November 26, 2001
				# https://en.wikipedia.org/wiki/Jeopardy!
				# http://www.j-archive.com/showgame.php?game_id=1062
				# jService uses noon UTC for airdates
				# jService doesn't include Double Jeopardy! clues
				transition_date = datetime.datetime(2001, 11, 26, 12, tzinfo = datetime.timezone.utc)
				clues = {value: [] for value in self.VALUES}
				for clue in data["clues"]:
					if not clue["question"] or not clue["value"]:
						continue
					if dateutil.parser.parse(clue["airdate"]) < transition_date:
						clues[clue["value"] * 2].append(clue)
					else:
						clues[clue["value"]].append(clue)
				if not all(clues.values()):
					continue
				
				self.board.append({
					"title": capwords(random_clue["category"]["title"]), 
					"clues": {
						value: random.choice(clues[value])
						for value in self.VALUES
					}
				})
		
		category_title_line_character_limit = self.bot.EDCBRCL - 25
		# EDCBRCL = Embed Description Code Block Row Character Limit
		# len("#) " + "  200 400 600 800 1000") = 25
		for category in self.board:
			category_title = category["formatted_title"] = category["title"]
			if len(category_title) > category_title_line_character_limit:
				split_index = category_title.rfind(' ', 0, category_title_line_character_limit)
				category["formatted_title"] = category_title[:split_index] + '\n' + category_title[split_index + 1:]
		
		max_width = max(len(section) for category in self.board for section in category["formatted_title"].split('\n'))
		for number, category_title in enumerate(category["formatted_title"] for category in self.board):
			try:
				split_index = category_title.index('\n')
				self.board_lines.append(
					f"{number + 1}) {category_title[:split_index]}\n"
					f"   {category_title[split_index + 1:].ljust(max_width)}  200 400 600 800 1000"
				)
			except ValueError:
				self.board_lines.append(
					f"{number + 1}) {category_title.ljust(max_width)}  200 400 600 800 1000"
				)
	
	async def send_winner(self):
		highest_score = max(self.scores.values())
		winners = [answerer.mention for answerer, score in self.scores.items() if score == highest_score]
		await self.ctx.embed_send(
			title = "Jeopardy!", 
			title_url = self.message.jump_url, 
			description = (
				f"{self.bot.inflect_engine.join(winners)} {self.bot.inflect_engine.plural('is', len(winners))} "
				f"the {self.bot.inflect_engine.plural('winner', len(winners))} with `{highest_score}`!"
			)
		)


class JeopardySelectionView(discord.ui.View):
	
	def __init__(self, match):
		super().__init__(timeout = None)
		# TODO: Timeout?
		
		self.match = match
		
		for number, category in enumerate(self.match.board, start = 1):
			if any(category["clues"].values()):
				self.category.add_option(label = number, description = category["title"])
				# TODO: Handle description longer than 50 characters?
		
		for value in self.match.VALUES:
			self.add_item(JeopardyValueButton(value))
	
	@discord.ui.select(placeholder = "Select a category")
	async def category(self, interaction, select):
		for item in self.children:
			if isinstance(item, discord.ui.Button):
				item.disabled = not self.match.board[int(select.values[0]) - 1]["clues"][int(item.label)]
		
		select.placeholder = select.values[0]
		
		await interaction.response.edit_message(view = self)


class JeopardyValueButton(discord.ui.Button):
	
	def __init__(self, label):
		super().__init__(style = discord.ButtonStyle.blurple, label = label)
	
	async def callback(self, interaction):
		if interaction.user != self.view.match.turn:
			await interaction.response.send_message(
				"It's not your turn", ephemeral = True
			)
			return
		
		if not self.view.category.values:
			await interaction.response.send_message(
				"Select a category first", ephemeral = True
			)
			return
		
		category_number = int(self.view.category.values[0])
		value = int(self.label)
		
		if not self.view.match.board[category_number - 1]["clues"][value]:
			await interaction.response.send_message(
				"That question has already been chosen", ephemeral = True
			)
			return
		
		embed = interaction.message.embeds[0]
		embed.description += f"\n{interaction.user.mention} chose {self.view.match.board[category_number - 1]['title']} for `{value}`"
		await interaction.response.edit_message(embed = embed, view = None)
		
		await self.view.match.select(category_number, value)


class JeopardyBuzzerView(discord.ui.View):
	
	def __init__(self, match):
		super().__init__(timeout = 15)
		
		self.match = match
		
		self.hit = False
	
	@discord.ui.button(style = discord.ButtonStyle.red, label = "Buzzer")
	async def buzzer(self, interaction, button):
		if self.hit:
			return
		self.hit = True
		
		if interaction.user in self.match.answered:
			await interaction.response.send_message(
				"You already hit the buzzer", ephemeral = True
			)
			return
		
		await interaction.response.edit_message(view = None)
		self.stop()
		
		await self.match.answer(interaction.user)
	
	async def on_timeout(self):
		await self.match.message.edit(view = None)
		self.stop()
		
		await self.match.timeout()

