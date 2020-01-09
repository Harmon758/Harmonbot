
import discord
from discord.ext import commands, menus

import io
import random

import dateutil.parser

from modules.maze import Maze
from utilities import checks

def setup(bot):
	bot.add_cog(Reactions(bot))

# meta.stats reaction_responses column:
#  Fixed to stop counting own reactions on 2019-10-25
#  Deprecated on 2020-01-04 in favor of menu_reactions

class CustomMenu(menus.Menu):
	
	async def update(self, payload):
		await super().update(payload)
		await self.bot.increment_menu_reactions_count()

class GuessMenu(CustomMenu):
	
	def __init__(self):
		super().__init__(timeout = None, check_embeds = True)
		self.numbers = {str(number) + '\N{COMBINING ENCLOSING KEYCAP}': number for number in range(1, 10)}
		self.numbers['\N{KEYCAP TEN}'] = 10
		for emoji, number in self.numbers.items():
			self.add_button(menus.Button(emoji, self.on_number, position = number))
	
	# TODO: Track number of tries
	
	async def send_initial_message(self, ctx, channel):
		self.answer = random.randint(1, 10)
		return await ctx.embed_reply(f"{ctx.author.mention}: Guess a number between 1 to 10")
	
	async def on_number(self, payload):
		embed = self.message.embeds[0]
		if (number := self.numbers[str(payload.emoji)]) == self.answer:
			embed.description = f"{self.ctx.author.mention}: It was {number}!"
			self.stop()
		else:
			embed.description = (f"{self.ctx.author.mention}: Guess a number between 1 to 10\n"
									f"No, it's not {number}")
		await self.message.edit(embed = embed)

class MazeMenu(CustomMenu):
	
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
	
	@menus.button("\N{PRINTER}", position = 5, lock = False)
	async def on_printer(self, payload):
		await self.message.channel.send(content = f"{self.ctx.author.display_name}:\n"
													"Your maze is attached", 
										file = discord.File(io.BytesIO(('\n'.join(self.maze.visible)).encode()), 
															filename = "maze.txt"))

class NewsSource(menus.ListPageSource):
	
	def __init__(self, articles):
		self.articles = articles
		super().__init__(articles, per_page = 1)
	
	async def format_page(self, menu, article):
		embed = discord.Embed(title = article["title"], url = article["url"], 
								description = article["description"], color = menu.bot.bot_color)
		embed.set_author(name = menu.ctx.author.display_name, icon_url = menu.ctx.author.avatar_url)
		embed.set_image(url = article["urlToImage"])
		embed.set_footer(text = f"{article['source']['name']} (Article {menu.current_page + 1} of {len(self.articles)})")
		if timestamp := article.get("publishedAt"):
			embed.timestamp = dateutil.parser.parse(timestamp)
		return {"content": f"In response to: `{menu.ctx.message.clean_content}`", "embed": embed}

class NewsMenu(CustomMenu, menus.MenuPages):
	
	def __init__(self, articles):
		super().__init__(NewsSource(articles), timeout = None, clear_reactions_after = True, check_embeds = True)
	
	async def send_initial_message(self, ctx, channel):
		message = await super().send_initial_message(ctx, channel)
		await ctx.bot.attempt_delete_message(ctx.message)
		return message

class PlayingMenu(CustomMenu):
	
	def __init__(self):
		super().__init__(timeout = None, check_embeds = True)
		self.direct_actions = {'\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}': "skip", 
								'\N{CLOCKWISE RIGHTWARDS AND LEFTWARDS OPEN CIRCLE ARROWS WITH CIRCLED ONE OVERLAY}': "replay", 
								'\N{TWISTED RIGHTWARDS ARROWS}': "shuffle", '\N{RADIO}': "radio"}
		for number, emoji in enumerate(self.direct_actions.keys(), start = 2):
			self.add_button(menus.Button(emoji, self.on_direct_action_reaction, position = number, lock = False))
	
	async def send_initial_message(self, ctx, channel):
		return await ctx.invoke(ctx.bot.cogs["Audio"].playing)
	
	# TODO: Queue?, Empty?, Settext?, Join?, Leave?, Other?
	# TODO: Resend player?
	# TODO: player command: Timestamp for radio?
	# TODO: Fix embed replying to user who invoked command rather than clicked button
	
	def reaction_check(self, payload):
		if payload.message_id != self.message.id:
			return False
		if payload.user_id == self.bot.user.id:
			return False
		return str(payload.emoji) in self.buttons
	
	async def is_permitted(self, command, user_id):
		while ((permitted := await self.ctx.get_permission(command.name, id = user_id)) is None
				and command.parent is not None):
			command = command.parent
		return permitted or user_id in (self.ctx.guild.owner.id, self.bot.owner_id)
	
	@menus.button('\N{BLACK RIGHT-POINTING TRIANGLE WITH DOUBLE VERTICAL BAR}', position = 1)
	async def on_pause_or_resume(self, payload):
		if self.ctx.guild.voice_client.is_playing():
			command = self.ctx.bot.cogs["Audio"].pause
		else:
			command = self.ctx.bot.cogs["Audio"].resume
		if await self.is_permitted(command, payload.user_id):
			await self.ctx.invoke(command)
	
	async def on_direct_action_reaction(self, payload):
		command = getattr(self.ctx.bot.cogs["Audio"], self.direct_actions[str(payload.emoji)])
		if await self.is_permitted(command, payload.user_id):
			await self.ctx.invoke(command)
	
	@menus.button('\N{SPEAKER WITH ONE SOUND WAVE}', position = 6)
	async def on_volume_down(self, payload):
		await self.change_volume(payload.user_id, -10)
	
	@menus.button('\N{SPEAKER WITH THREE SOUND WAVES}', position = 7)
	async def on_volume_up(self, payload):
		await self.change_volume(payload.user_id, 10)
	
	async def change_volume(self, user_id, volume_change):
		command = self.ctx.bot.cogs["Audio"].volume
		if await self.is_permitted(command, user_id):
			# TODO: Just invoke without checking?
			if self.ctx.guild.voice_client.is_playing():
				await self.ctx.invoke(command, volume_setting = self.ctx.guild.voice_client.source.volume + volume_change)
			else:
				await self.ctx.embed_reply(f":no_entry: Couldn't {'increase' if volume_change > 0 else 'decrease'} volume\n"
											"There's nothing playing right now")

class Reactions(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.reaction_commands = (
			(self.guess, "Games", "guess", [], [checks.not_forbidden().predicate]), 
			(self.maze, "Games", "maze", [], [checks.not_forbidden().predicate]), 
			(self.news, "Resources", "news", [], [checks.not_forbidden().predicate]), 
			(self.playing, "Audio", "playing", ["player"], [checks.not_forbidden().predicate, commands.guild_only().predicate])
		)
		for command, cog_name, parent_name, aliases, command_checks in self.reaction_commands:
			self.reactions.add_command(commands.Command(command, aliases = aliases, checks = command_checks))
			if (cog := self.bot.get_cog(cog_name)) and (parent := getattr(cog, parent_name)):
				parent.add_command(commands.Command(command, 
													name = "reactions", aliases = ["reaction", 'r', "menus", "menu", 'm'], 
													checks = command_checks))
	
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
		await NewsMenu(data["articles"]).start(ctx)
	
	async def playing(self, ctx):
		'''Audio player'''
		await PlayingMenu().start(ctx)

