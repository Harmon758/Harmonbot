
import discord
from discord.ext import commands

import collections
import copy
import inspect
import json
import random

import clients
import credentials
from utilities import checks
from utilities import errors
from modules import maze
from modules import utilities

def setup(bot):
	bot.add_cog(Reactions(bot))

class Reactions:
	
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
	
	def __unload(self):
		for command, parent_name in self.reaction_commands:
			utilities.remove_as_subcommand(self, parent_name, "reactions")
	
	@commands.command(aliases = ["guessreactions", "guessreaction"], pass_context = True)
	@checks.not_forbidden()
	async def guessr(self, ctx):
		'''
		Guessing game
		With reactions
		'''
		guess_message, embed = await self.bot.embed_reply("Guess a number between 1 to 10")
		answer = random.randint(1, 10)
		for number_emote in sorted(self.numbers.keys()):
			await self.bot.add_reaction(guess_message, number_emote)
		self.reaction_messages[guess_message.id] = lambda reaction, user: self.guessr_processr(ctx.message.author, answer, embed, reaction, user)
	
	async def guessr_processr(self, player, answer, embed, reaction, user):
		if user == player and reaction.emoji in self.numbers:
			if self.numbers[reaction.emoji] == answer:
				embed.description = "{}: It was {}!".format(player.display_name, self.numbers[reaction.emoji])
				await self.bot.edit_message(reaction.message, embed = embed)
				del self.reaction_messages[reaction.message.id]
			else:
				embed.description = "{}: Guess a number between 1 to 10. No, it's not {}".format(player.display_name, self.numbers[reaction.emoji])
				await self.bot.edit_message(reaction.message, embed = embed)
	
	@commands.command(pass_context = True, invoke_without_command = True)
	@checks.not_forbidden()
	async def newsr(self, ctx, source : str):
		'''
		News
		With Reactions
		Powered by NewsAPI.org
		'''
		async with clients.aiohttp_session.get("https://newsapi.org/v1/articles?source={}&apiKey={}".format(source, credentials.news_api_key)) as resp:
			data = await resp.json()
		if data["status"] != "ok":
			await self.bot.embed_reply(":no_entry: Error: {}".format(data["message"]))
			return
		response, embed = await self.bot.reply("React with a number from 1 to 10 to view each news article")
		numbers = {'\N{KEYCAP TEN}': 10}
		for number in range(9):
			numbers[chr(ord('\u0031') + number) + '\N{COMBINING ENCLOSING KEYCAP}'] = number + 1 # '\u0031' - 1
		for number_emote in sorted(numbers.keys()):
			await self.bot.add_reaction(response, number_emote)
		while True:
			emoji_response = await self.bot.wait_for_reaction(user = ctx.message.author, message = response, emoji = numbers.keys())
			reaction = emoji_response.reaction
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
			await self.bot.edit_message(response, "{}: {}".format(ctx.message.author.display_name, output))
	
	# TODO: urband
	# TODO: rtg
	
	@commands.command(pass_context = True)
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
		maze_message, embed = await self.bot.embed_reply(clients.code_block.format(maze_instance.print_visible()), footer_text = "Your current position: {}, {}".format(maze_instance.column + 1, maze_instance.row + 1))
		self.mazes[maze_message.id] = maze_instance
		for emote in tuple(self.arrows.keys()) + ("\N{PRINTER}",):
			await self.bot.add_reaction(maze_message, emote)
		self.reaction_messages[maze_message.id] = lambda reaction, user: self.mazer_processr(ctx.message.author, reaction, user)
	
	async def mazer_processr(self, player, reaction, user):
		if user == player and reaction.emoji in tuple(self.arrows.keys()) + ("\N{PRINTER}",):
			maze_instance = self.mazes[reaction.message.id]
			if reaction.emoji == "\N{PRINTER}":
				with open("data/temp/maze.txt", 'w') as maze_file:
					maze_file.write('\n'.join(maze_instance.visible))
				await self.bot.send_file(reaction.message.channel, "data/temp/maze.txt", content = "{}:\nYour maze is attached".format(player.display_name))
				return
			embed = discord.Embed(color = clients.bot_color)
			avatar = player.avatar_url or player.default_avatar_url
			embed.set_author(name = player.display_name, icon_url = avatar)
			moved = maze_instance.move(self.arrows[reaction.emoji].lower())
			embed.set_footer(text = "Your current position: {}, {}".format(maze_instance.column + 1, maze_instance.row + 1))
			if moved:
				if maze_instance.reached_end():
					embed.description = "{}\nCongratulations! You reached the end of the maze in {} moves".format(clients.code_block.format(maze_instance.print_visible()), maze_instance.move_counter)
					del self.reaction_messages[reaction.message.id]
				else:
					embed.description = "{}".format(clients.code_block.format(maze_instance.print_visible()))
			else:
				embed.description = "{}\n:no_entry: You can't go that way".format(clients.code_block.format(maze_instance.print_visible()))
			await self.bot.edit_message(reaction.message, embed = embed)
	
	@commands.command(aliases = ["player"], no_pm = True, pass_context = True)
	@checks.not_forbidden()
	async def playingr(self, ctx):
		'''Audio player'''
		try:
			embed = self.bot.cogs["Audio"].players[ctx.message.server.id].current_embed()
		except errors.AudioNotPlaying:
			player_message, embed = await self.bot.embed_reply(":speaker: There is no song currently playing")
		else:
			embed.set_author(name = ctx.message.author.display_name, icon_url = ctx.message.author.avatar_url or ctx.message.author.default_avatar_url)
			player_message, embed = await self.bot.say(embed = embed)
		await self.bot.attempt_delete_message(ctx.message)
		for control_emote in self.controls.keys():
			await self.bot.add_reaction(player_message, control_emote)
		self.reaction_messages[player_message.id] = lambda reaction, user: self.playingr_processr(ctx, reaction, user)
	
	# TODO: Queue?, Empty?, Settext?, Other?
	# TODO: Resend player?
	
	async def playingr_processr(self, ctx, reaction, user):
		if reaction.emoji in self.controls:
			if self.controls[reaction.emoji] == "pause_resume":
				if utilities.get_permission(ctx, "pause", id = user.id) or user == ctx.message.server.owner or user.id == credentials.myid:
					embed = discord.Embed(color = clients.bot_color).set_author(name = user.display_name, icon_url = user.avatar_url or user.default_avatar_url)
					try:
						self.bot.cogs["Audio"].players[ctx.message.server.id].pause()
					except errors.AudioNotPlaying:
						embed.description = ":no_entry: There is no song to pause"
					except errors.AudioAlreadyDone:
						self.bot.cogs["Audio"].players[ctx.message.server.id].resume()
						embed.description = ":play_pause: Resumed song"
					else:
						embed.description = ":pause_button: Paused song"
					await self.bot.send_message(ctx.message.channel, embed = embed)
					await self.bot.attempt_delete_message(ctx.message)
			elif self.controls[reaction.emoji] in ("skip", "replay", "shuffle", "radio"):
				if utilities.get_permission(ctx, self.controls[reaction.emoji], id = user.id) or user.id in (ctx.message.server.owner.id, credentials.myid):
					message = copy.copy(ctx.message)
					message.content = "{}{}".format(ctx.prefix, self.controls[reaction.emoji])
					await self.bot.process_commands(message)
					# Timestamp for radio
			elif self.controls[reaction.emoji] in ("volume_down", "volume_up"):
				if utilities.get_permission(ctx, "volume", id = user.id) or user.id in (ctx.message.server.owner, credentials.myid):
					try:
						current_volume = self.bot.cogs["Audio"].players[ctx.message.server.id].get_volume()
					except errors.AudioNotPlaying:
						await self.bot.embed_reply(":no_entry: Couldn't change volume\nThere's nothing playing right now")
					if self.controls[reaction.emoji] == "volume_down": set_volume = current_volume - 10
					elif self.controls[reaction.emoji] == "volume_up": set_volume = current_volume + 10
					message = copy.copy(ctx.message)
					message.content = "{}volume {}".format(ctx.prefix, set_volume)
					await self.bot.process_commands(message)
			
	
async def process_reactions(reaction, user):
	await clients.client.cogs["Reactions"].reaction_messages[reaction.message.id](reaction, user)
	with open("data/stats.json", 'r') as stats_file:
		stats = json.load(stats_file)
	stats["reaction_responses"] += 1
	with open("data/stats.json", 'w') as stats_file:
		json.dump(stats, stats_file, indent = 4)
	
@clients.client.event
async def on_reaction_add(reaction, user):
	if "Reactions" in clients.client.cogs and reaction.message.id in clients.client.cogs["Reactions"].reaction_messages:
		await process_reactions(reaction, user)

@clients.client.event
async def on_reaction_remove(reaction, user):
	if "Reactions" in clients.client.cogs and reaction.message.id in clients.client.cogs["Reactions"].reaction_messages:
		await process_reactions(reaction, user)

