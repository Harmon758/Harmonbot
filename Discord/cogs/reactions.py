
import discord
from discord.ext import commands, menus

import collections
import copy
import io
import random

from modules.maze import Maze
from utilities import checks
from utilities import errors

def setup(bot):
	bot.add_cog(Reactions(bot))
	
	async def process_reactions(reaction, user):
		if user == bot.user:
			return
		await bot.cogs["Reactions"].reaction_messages[reaction.message.id](reaction, user)
		await bot.db.execute(
			"""
			UPDATE meta.stats
			SET reaction_responses = reaction_responses + 1
			WHERE timestamp = $1
			""", 
			bot.online_time
		)
		# Count fixed to stop counting own reactions on 2019-10-25
	
	@bot.event
	async def on_reaction_add(reaction, user):
		if "Reactions" in bot.cogs and reaction.message.id in bot.cogs["Reactions"].reaction_messages:
			await process_reactions(reaction, user)

	@bot.event
	async def on_reaction_remove(reaction, user):
		if "Reactions" in bot.cogs and reaction.message.id in bot.cogs["Reactions"].reaction_messages:
			await process_reactions(reaction, user)

async def increment_menu_reaction_count(bot):
	await bot.db.execute(
		"""
		UPDATE meta.stats
		SET menu_reactions = menu_reactions + 1
		WHERE timestamp = $1
		""", 
		bot.online_time
	)

class GuessMenu(menus.Menu):
	
	def __init__(self):
		super().__init__(timeout = None, check_embeds = True)
		self.numbers = {str(number) + '\N{COMBINING ENCLOSING KEYCAP}': number for number in range(1, 10)}
		self.numbers['\N{KEYCAP TEN}'] = 10
		for emoji, number in self.numbers.items():
			self.add_button(menus.Button(emoji, self.process_reaction, position = number))
	
	# TODO: Track number of tries
	
	async def send_initial_message(self, ctx, channel):
		self.answer = random.randint(1, 10)
		return await ctx.embed_reply(f"{ctx.author.mention}: Guess a number between 1 to 10")
	
	async def process_reaction(self, payload):
		embed = self.message.embeds[0]
		if (number := self.numbers[str(payload.emoji)]) == self.answer:
			embed.description = f"{self.ctx.author.mention}: It was {number}!"
			self.stop()
		else:
			embed.description = (f"{self.ctx.author.mention}: Guess a number between 1 to 10\n"
									f"No, it's not {number}")
		await self.message.edit(embed = embed)
		await increment_menu_reaction_count(self.bot)

class MazeMenu(menus.Menu):
	
	def __init__(self, width, height, random_start, random_end):
		super().__init__(timeout = None, clear_reactions_after = True, check_embeds = True)
		self.maze = Maze(width, height, random_start, random_end)
		self.arrows = {'\N{LEFTWARDS BLACK ARROW}': 'w', '\N{UPWARDS BLACK ARROW}': 'n', '\N{DOWNWARDS BLACK ARROW}': 's', '\N{BLACK RIGHTWARDS ARROW}': 'e'}
		for number, emoji in enumerate(self.arrows.keys(), start = 1):
			self.add_button(menus.Button(emoji, self.on_direction, position = number))
	
	async def send_initial_message(self, ctx, channel):
		return await ctx.embed_reply(ctx.bot.CODE_BLOCK.format(self.maze.print_visible()), 
										footer_text = f"Your current position: {self.maze.column + 1}, {self.maze.row + 1}")
	
	async def on_direction(self, payload):
		embed = self.message.embeds[0]
		if not self.maze.move(self.arrows[str(payload.emoji)]):
			embed.description = (self.bot.CODE_BLOCK.format(self.maze.print_visible())
									+ "\n:no_entry: You can't go that way")
		elif self.maze.reached_end():
			embed.description = (self.bot.CODE_BLOCK.format(self.maze.print_visible())
									+ f"\nCongratulations! You reached the end of the maze in {self.maze.move_counter} moves")
			self.stop()
		else:
			embed.description = self.bot.CODE_BLOCK.format(self.maze.print_visible())
		embed.set_footer(text = f"Your current position: {self.maze.column + 1}, {self.maze.row + 1}")
		await self.message.edit(embed = embed)
		await increment_menu_reaction_count(self.bot)
	
	@menus.button("\N{PRINTER}", position = 5, lock = False)
	async def on_printer(self, payload):
		await self.message.channel.send(content = f"{self.ctx.author.display_name}:\n"
													"Your maze is attached", 
										file = discord.File(io.BytesIO(('\n'.join(self.maze.visible)).encode()), 
															filename = "maze.txt"))
		await increment_menu_reaction_count(self.bot)

class NewsSource(menus.ListPageSource):
	
	def __init__(self, articles):
		super().__init__(articles, per_page = 1)
	
	async def format_page(self, menu, article):
		output = f"Article {menu.current_page + 1}:"
		output += f"\n**{article['title']}**"
		if article.get("publishedAt"):
			output += f" ({article.get('publishedAt').replace('T', ' ').replace('Z', '')})"
		# output += f"\n{article['description']}"
		# output += f"\n<{article['url']}>"
		output += f"\n{article['url']}"
		return f"{menu.ctx.author.display_name}: {output}"

class Reactions(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.reaction_messages = {}
		self.controls = collections.OrderedDict([('\N{BLACK RIGHT-POINTING TRIANGLE WITH DOUBLE VERTICAL BAR}', "pause_resume"), ('\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}', "skip"), ('\N{CLOCKWISE RIGHTWARDS AND LEFTWARDS OPEN CIRCLE ARROWS WITH CIRCLED ONE OVERLAY}', "replay"), ('\N{TWISTED RIGHTWARDS ARROWS}', "shuffle"), ('\N{RADIO}', "radio"), ('\N{SPEAKER WITH ONE SOUND WAVE}', "volume_down"), ('\N{SPEAKER WITH THREE SOUND WAVES}', "volume_up")])
		self.reaction_commands = (
			(self.guess, "Games", "guess", [], [checks.not_forbidden().predicate]), 
			(self.maze, "Games", "maze", [], [checks.not_forbidden().predicate]), 
			(self.news, "Resources", "news", [], [checks.not_forbidden().predicate]), 
			(self.playing, "Audio", "playing", ["player"], [checks.not_forbidden().predicate, commands.guild_only().predicate])
		)
		for command, cog_name, parent_name, aliases, command_checks in self.reaction_commands:
			self.reactions.add_command(commands.Command(command, aliases = aliases, checks = command_checks))
			if (cog := self.bot.get_cog(cog_name)) and (parent := getattr(cog, parent_name)):
				parent.add_command(commands.Command(command, name = "reactions", aliases = ["reaction", 'r', "menus", "menu", 'm'], checks = command_checks))
	
	def cog_unload(self):
		for command, cog_name, parent_name, *_ in self.reaction_commands:
			if (cog := self.bot.get_cog(cog_name)) and (parent := getattr(cog, parent_name)):
				parent.remove_command("reactions")
	
	@commands.group(aliases = ["reaction", "menus", "menu"], invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def reactions(self, ctx):
		'''Reactions versions of commands'''
		await ctx.send_help(ctx.command)
	
	# TODO: rtg
	# TODO: urband
	
	async def guess(self, ctx):
		'''
		Guessing game
		With reactions
		'''
		await GuessMenu().start(ctx)
	
	async def maze(self, ctx, width: int = 5, height: int = 5, random_start: bool = False, random_end: bool = False):
		'''
		Maze game
		With reactions
		width: 2 - 100
		height: 2 - 100
		React with an arrow key to move
		'''
		await MazeMenu(width, height, random_start, random_end).start(ctx)
	
	async def news(self, ctx, source: str):
		'''
		News
		With Reactions
		Powered by NewsAPI.org
		'''
		url = "https://newsapi.org/v2/top-headlines"
		params = {"sources": source, "apiKey": ctx.bot.NEWSAPI_ORG_API_KEY}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if data["status"] != "ok":
			return await ctx.embed_reply(f":no_entry: Error: {data['message']}")
		if not data["totalResults"]:
			return await ctx.embed_reply(f":no_entry: Error: No news articles found for that source")
		await menus.MenuPages(NewsSource(data["articles"]), timeout = None, clear_reactions_after = True).start(ctx)
	
	async def playing(self, ctx):
		'''Audio player'''
		try:
			embed = self.bot.cogs["Audio"].players[ctx.guild.id].current_embed()
		except errors.AudioNotPlaying:
			player_message = await ctx.embed_reply(":speaker: There is no song currently playing")
		else:
			embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url)
			player_message, embed = await self.bot.say(embed = embed)
		await self.bot.attempt_delete_message(ctx.message)
		for control_emote in self.controls.keys():
			await player_message.add_reaction(control_emote)
		self.reaction_messages[player_message.id] = lambda reaction, user: self.playing_reactions_processor(ctx, reaction, user)
	
	# TODO: Queue?, Empty?, Settext?, Other?
	# TODO: Resend player?
	
	async def playing_reactions_processor(self, ctx, reaction, user):
		if reaction.emoji in self.controls:
			if self.controls[reaction.emoji] == "pause_resume":
				permitted = await ctx.get_permission("pause", id = user.id)
				if permitted or user == ctx.guild.owner or user.id == self.bot.owner_id:
					embed = discord.Embed(color = ctx.bot.bot_color).set_author(name = user.display_name, icon_url = user.avatar_url)
					try:
						self.bot.cogs["Audio"].players[ctx.guild.id].pause()
					except errors.AudioNotPlaying:
						embed.description = ":no_entry: There is no song to pause"
					except errors.AudioAlreadyDone:
						self.bot.cogs["Audio"].players[ctx.guild.id].resume()
						embed.description = ":play_pause: Resumed song"
					else:
						embed.description = ":pause_button: Paused song"
					await self.bot.send_message(ctx.channel, embed = embed)
					await self.bot.attempt_delete_message(ctx.message)
			elif self.controls[reaction.emoji] in ("skip", "replay", "shuffle", "radio"):
				permitted = await ctx.get_permission(self.controls[reaction.emoji], id = user.id)
				if permitted or user.id in (ctx.guild.owner.id, self.bot.owner_id):
					message = copy.copy(ctx.message)
					message.content = "{}{}".format(ctx.prefix, self.controls[reaction.emoji])
					await self.bot.process_commands(message)
					# Timestamp for radio
			elif self.controls[reaction.emoji] in ("volume_down", "volume_up"):
				permitted = await ctx.get_permission("volume", id = user.id)
				if permitted or user.id in (ctx.guild.owner, self.bot.owner_id):
					try:
						current_volume = self.bot.cogs["Audio"].players[ctx.guild.id].get_volume()
					except errors.AudioNotPlaying:
						await ctx.embed_reply(":no_entry: Couldn't change volume\nThere's nothing playing right now")
					if self.controls[reaction.emoji] == "volume_down": set_volume = current_volume - 10
					elif self.controls[reaction.emoji] == "volume_up": set_volume = current_volume + 10
					message = copy.copy(ctx.message)
					message.content = "{}volume {}".format(ctx.prefix, set_volume)
					await self.bot.process_commands(message)

