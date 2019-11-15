
import discord
from discord.ext import commands

import collections
import copy
import inspect
import random

from modules import maze
from modules import utilities
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

class Reactions(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.reaction_messages = {}
		self.mazes = {}
		self.numbers = {'\N{KEYCAP TEN}': 10}
		for number in range(9):
			self.numbers[chr(ord('\u0031') + number) + '\N{COMBINING ENCLOSING KEYCAP}'] = number + 1 # '\u0031' - 1
		self.arrows = collections.OrderedDict([('\N{LEFTWARDS BLACK ARROW}', 'W'), ('\N{UPWARDS BLACK ARROW}', 'N'), ('\N{DOWNWARDS BLACK ARROW}', 'S'), ('\N{BLACK RIGHTWARDS ARROW}', 'E')]) # tuple?
		self.controls = collections.OrderedDict([('\N{BLACK RIGHT-POINTING TRIANGLE WITH DOUBLE VERTICAL BAR}', "pause_resume"), ('\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}', "skip"), ('\N{CLOCKWISE RIGHTWARDS AND LEFTWARDS OPEN CIRCLE ARROWS WITH CIRCLED ONE OVERLAY}', "replay"), ('\N{TWISTED RIGHTWARDS ARROWS}', "shuffle"), ('\N{RADIO}', "radio"), ('\N{SPEAKER WITH ONE SOUND WAVE}', "volume_down"), ('\N{SPEAKER WITH THREE SOUND WAVES}', "volume_up")])
		self.reaction_commands = ((self.guessr, "Games.guess"), (self.newsr, "Resources.news"), (self.mazer, "Games.maze"), (self.playingr, "Audio.playing"))
		for command, parent_name in self.reaction_commands:
			utilities.add_as_subcommand(self, command, parent_name, "reactions", aliases = ["reaction", 'r'])
	
	def cog_unload(self):
		for command, parent_name in self.reaction_commands:
			utilities.remove_as_subcommand(self, parent_name, "reactions")
	
	@commands.command(aliases = ["guessreactions", "guessreaction"])
	@checks.not_forbidden()
	async def guessr(self, ctx):
		'''
		Guessing game
		With reactions
		'''
		guess_message = await ctx.embed_reply("Guess a number between 1 to 10")
		embed = guess_message.embeds[0]
		answer = random.randint(1, 10)
		for number_emote in sorted(self.numbers.keys()):
			await guess_message.add_reaction(number_emote)
		self.reaction_messages[guess_message.id] = lambda reaction, user: self.guessr_processr(ctx.author, answer, embed, reaction, user)
	
	async def guessr_processr(self, player, answer, embed, reaction, user):
		if user == player and reaction.emoji in self.numbers:
			if self.numbers[reaction.emoji] == answer:
				embed.description = "{}: It was {}!".format(player.display_name, self.numbers[reaction.emoji])
				await reaction.message.edit(embed = embed)
				del self.reaction_messages[reaction.message.id]
			else:
				embed.description = "{}: Guess a number between 1 to 10. No, it's not {}".format(player.display_name, self.numbers[reaction.emoji])
				await reaction.message.edit(embed = embed)
	
	@commands.command(invoke_without_command = True)
	@checks.not_forbidden()
	async def newsr(self, ctx, source : str):
		'''
		News
		With Reactions
		Powered by NewsAPI.org
		'''
		async with ctx.bot.aiohttp_session.get("https://newsapi.org/v1/articles?source={}&apiKey={}".format(source, ctx.bot.NEWSAPI_ORG_API_KEY)) as resp:
			data = await resp.json()
		if data["status"] != "ok":
			await ctx.embed_reply(":no_entry: Error: {}".format(data["message"]))
			return
		response = await ctx.reply("React with a number from 1 to 10 to view each news article")
		numbers = {'\N{KEYCAP TEN}': 10}
		for number in range(9):
			numbers[chr(ord('\u0031') + number) + '\N{COMBINING ENCLOSING KEYCAP}'] = number + 1 # '\u0031' - 1
		for number_emote in sorted(numbers.keys()):
			await response.add_reaction(number_emote)
		while True:
			reaction, user = await self.bot.wait_for_reaction_add_or_remove(message = response, user = ctx.author, emoji = numbers.keys())
			number = numbers[reaction.emoji]
			article = data["articles"][number - 1]
			output = "Article {}:".format(number)
			output += "\n**{}**".format(article["title"])
			if article.get("publishedAt"):
				output += " ({})".format(article.get("publishedAt").replace('T', " ").replace('Z', ""))
			# output += "\n{}".format(article["description"])
			# output += "\n<{}>".format(article["url"])
			output += "\n{}".format(article["url"])
			output += "\nSelect a different number for another article"
			await response.edit(content = "{}: {}".format(ctx.author.display_name, output))
	
	# TODO: urband
	# TODO: rtg
	
	@commands.command()
	@checks.not_forbidden()
	async def mazer(self, ctx, width : int = 5, height : int = 5, random_start : bool = False, random_end : bool = False):
		'''
		Maze game
		With reactions
		width: 2 - 100
		height: 2 - 100
		React with an arrow key to move
		'''
		maze_instance = maze.Maze(width, height, random_start = random_start, random_end = random_end)
		maze_message = await ctx.embed_reply(ctx.bot.CODE_BLOCK.format(maze_instance.print_visible()), footer_text = "Your current position: {}, {}".format(maze_instance.column + 1, maze_instance.row + 1))
		self.mazes[maze_message.id] = maze_instance
		for emote in tuple(self.arrows.keys()) + ("\N{PRINTER}",):
			await maze_message.add_reaction(emote)
		self.reaction_messages[maze_message.id] = lambda reaction, user: self.mazer_processr(ctx.author, reaction, user)
	
	async def mazer_processr(self, player, reaction, user):
		if user == player and reaction.emoji in tuple(self.arrows.keys()) + ("\N{PRINTER}",):
			maze_instance = self.mazes[reaction.message.id]
			if reaction.emoji == "\N{PRINTER}":
				with open(self.bot.data_path + "/temp/maze.txt", 'w') as maze_file:
					maze_file.write('\n'.join(maze_instance.visible))
				await reaction.message.channel.send(content = "{}:\nYour maze is attached".format(player.display_name), file = discord.File(self.bot.data_path + "/temp/maze.txt"))
				return
			embed = discord.Embed(color = self.bot.bot_color)
			embed.set_author(name = player.display_name, icon_url = player.avatar_url)
			moved = maze_instance.move(self.arrows[reaction.emoji].lower())
			embed.set_footer(text = "Your current position: {}, {}".format(maze_instance.column + 1, maze_instance.row + 1))
			if moved:
				if maze_instance.reached_end():
					embed.description = "{}\nCongratulations! You reached the end of the maze in {} moves".format(self.bot.CODE_BLOCK.format(maze_instance.print_visible()), maze_instance.move_counter)
					del self.reaction_messages[reaction.message.id]
				else:
					embed.description = "{}".format(self.bot.CODE_BLOCK.format(maze_instance.print_visible()))
			else:
				embed.description = "{}\n:no_entry: You can't go that way".format(self.bot.CODE_BLOCK.format(maze_instance.print_visible()))
			await reaction.message.edit(embed = embed)
	
	@commands.command(aliases = ["player"])
	@commands.guild_only()
	@checks.not_forbidden()
	async def playingr(self, ctx):
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
		self.reaction_messages[player_message.id] = lambda reaction, user: self.playingr_processr(ctx, reaction, user)
	
	# TODO: Queue?, Empty?, Settext?, Other?
	# TODO: Resend player?
	
	async def playingr_processr(self, ctx, reaction, user):
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

