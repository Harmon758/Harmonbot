
import discord
from discord.ext import commands
from discord.ext.commands.bot import _mention_pattern, _mentions_transforms
from discord.ext.commands.formatter import Paginator

import asyncio
import datetime
import copy
import difflib
import inspect
import json
import os
import psutil
import re
import subprocess
import sys
import traceback

import clients
import credentials
from modules import utilities
from utilities import checks

def setup(bot):
	bot.add_cog(Meta(bot))

class Meta:
	
	def __init__(self, bot):
		self.bot = bot
		utilities.create_file("stats", content = {"uptime" : 0, "restarts" : 0, "cogs_reloaded" : 0, "commands_executed" : 0, "commands_usage": {}, "reaction_responses": 0})
		self.command_not_found = "No command called `{}` found"
	
	@commands.group(aliases = ["commands"], hidden = True, invoke_without_command = True)
	@checks.dm_or_has_capability("embed_links")
	async def help(self, ctx, *commands : str):
		'''
		Shows this message
		Note: If you are not currently able to use a command in the channel where you executed help, it will not be displayed in the corresponding help message
		'''
		if len(commands) == 0:
			embed = discord.Embed(title = "Categories", color = clients.bot_color)
			avatar = ctx.message.author.avatar_url or ctx.message.author.default_avatar_url
			embed.set_author(name = ctx.message.author.display_name, icon_url = avatar)
			embed.description = "  ".join("__{}__".format(category) for category in sorted(self.bot.cogs, key = str.lower))
			embed.add_field(name = "For more info:", value = "`{0}{1} [category]`\n`{0}{1} [command]`\n`{0}{1} [command] [subcommand]`".format(ctx.prefix, ctx.invoked_with))
			embed.add_field(name = "Also see:", value = "`{0}about`\n`{0}{1} other`".format(ctx.prefix, ctx.invoked_with)) # stats?
			embed.add_field(name = "For all commands:", value = "`{}{} all`".format(ctx.prefix, ctx.invoked_with), inline = False)
			await self.bot.say(embed = embed)
			return
		
		def repl(obj):
			return _mentions_transforms.get(obj.group(0), '')
		
		if len(commands) == 1:
			name = _mention_pattern.sub(repl, commands[0])
			if name in self.bot.cogs:
				command = self.bot.cogs[name]
			elif name.lower() in self.bot.commands:
				command = self.bot.commands[name.lower()]
			elif name.lower() in [cog.lower() for cog in self.bot.cogs.keys()]: # more efficient way?
				command = discord.utils.find(lambda c: c[0].lower() == name.lower(), self.bot.cogs.items())[1]
			else:
				output = self.command_not_found.format(name)
				close_matches = difflib.get_close_matches(name, self.bot.commands.keys(), n = 1)
				if close_matches:
					output += "\nDid you mean `{}`?".format(close_matches[0])
				await self.bot.embed_reply(output)
				return
			embeds = self.bot.formatter.format_help_for(ctx, command)
		else:
			name = _mention_pattern.sub(repl, commands[0])
			command = self.bot.commands.get(name)
			if command is None:
				await self.bot.embed_reply(self.command_not_found.format(name))
				return
			for key in commands[1:]:
				try:
					key = _mention_pattern.sub(repl, key)
					command = command.commands.get(key)
					if command is None:
						await self.bot.embed_reply(self.command_not_found.format(key))
						return
				except AttributeError:
					await self.bot.embed_reply("`{}` command has no subcommands".format(command.name))
					return
			embeds = self.bot.formatter.format_help_for(ctx, command)
		
		if len(embeds) > 1:
			destination = ctx.message.author
			if not isinstance(ctx.message.channel, discord.DMChannel):
				await self.bot.embed_reply("Check your DMs")
		else:
			destination = ctx.message.channel
		for embed in embeds:
			if destination == ctx.message.channel:
				avatar = ctx.message.author.avatar_url or ctx.message.author.default_avatar_url
				embed.set_author(name = ctx.message.author.display_name, icon_url = avatar)
			await self.bot.send_message(destination, embed = embed)
	
	@help.command(name = "all")
	async def help_all(self, ctx):
		'''All commands'''
		embeds = self.bot.formatter.format_help_for(ctx, self.bot)
		for embed in embeds:
			await self.bot.whisper(embed = embed)
		if not isinstance(ctx.message.channel, discord.DMChannel):
			await self.bot.embed_reply("Check your DMs")
	
	@help.command(name = "other")
	async def help_other(self, ctx):
		'''Additional commands and information'''
		# TODO: Update
		# TODO: Add last updated date?
		embed = discord.Embed(title = "Commands not in {}help".format(ctx.prefix), color = clients.bot_color)
		avatar = ctx.message.author.avatar_url or ctx.message.author.default_avatar_url
		embed.set_author(name = ctx.message.author.display_name, icon_url = avatar)
		embed.description = "See `{}help` for the main commands".format(ctx.prefix)
		embed.add_field(name = "Conversion Commands", value = "see `{}conversions`".format(ctx.prefix), inline = False)
		embed.add_field(name = "In Progress", value = "gofish redditsearch roleposition rolepositions taboo userlimit webmtogif whatis", inline = False)
		embed.add_field(name = "Misc", value = "invite randomgame test test_on_message", inline = False)
		embed.add_field(name = "Owner Only", value = "allcommands changenickname deletetest cleargame clearstreaming echo eval exec load reload repl restart servers setgame setstreaming shutdown unload updateavatar", inline = False)
		embed.add_field(name = "No Prefix", value = "@Harmonbot :8ball: (exactly: f|F) (anywhere in message: getprefix)", inline = False)
		await self.bot.say(embed = embed)
	
	@commands.command()
	@checks.is_owner()
	async def allcommands(self, ctx):
		'''All the commands'''
		# TODO: Fix/Deprecate?, all_commands alias
		formatter = commands.HelpFormatter(show_check_failure = True, show_hidden = True)
		formatter.format_help_for(ctx, self.bot)
		_commands = formatter.filter_command_list()
		_allcommands = ""
		for name, _command in _commands:
			_allcommands += name + ' '
		await self.bot.whisper(_allcommands[:-1])
	
	@commands.command()
	@checks.is_owner()
	async def benchmark(self):
		'''Benchmark'''
		process = psutil.Process()
		memory = process.memory_info().rss / 2 ** 20
		process.cpu_percent()
		embed = discord.Embed(color = clients.bot_color)
		embed.add_field(name = "RAM", value = "{:.2f} MiB".format(memory))
		embed.add_field(name = "CPU", value = "Calculating CPU usage..")
		message, embed = await self.bot.say(embed = embed)
		await asyncio.sleep(1)
		cpu = process.cpu_percent() / psutil.cpu_count()
		embed.set_field_at(1, name = "CPU", value = "{}%".format(cpu))
		await self.bot.edit_message(message, embed = embed)
	
	@commands.command()
	@checks.is_owner()
	async def disable(self, ctx, command : str):
		'''Disable a command'''
		self.bot.commands[command].enabled = False
		await self.bot.embed_reply("`{}{}` has been disabled".format(ctx.prefix, command))
		await self.bot.delete_message(ctx.message)
	
	@commands.command()
	@checks.is_owner()
	async def enable(self, ctx, command : str):
		'''Enable a command'''
		self.bot.commands[command].enabled = True
		await self.bot.embed_reply("`{}{}` has been enabled".format(ctx.prefix, command))
		await self.bot.delete_message(ctx.message)
	
	@commands.command()
	async def points(self, ctx):
		'''WIP'''
		with open("data/user_data/{}/stats.json".format(ctx.author.id), "r") as stats_file:
			stats = json.load(stats_file)
		await self.bot.embed_reply("You have {} points".format(stats["points"]))
	
	@commands.command(aliases = ["server_setting"])
	@checks.is_server_owner()
	async def server_settings(self, ctx, setting : str, on_off : bool):
		'''WIP'''
		with open("data/server_data/{}/settings.json".format(ctx.guild.id), 'r') as settings_file:
			data = json.load(settings_file)
		if setting in data:
			data[setting] = on_off
		else:
			await self.bot.embed_reply("Setting not found")
			return
		with open("data/server_data/{}/settings.json".format(ctx.guild.id), 'w') as settings_file:
			json.dump(data, settings_file, indent = 4)
		await self.bot.embed_reply("{} set to {}".format(setting, on_off))
	
	@commands.command()
	@checks.is_owner()
	async def servers(self):
		'''Every server I'm in'''
		for guild in self.bot.guilds:
			embed = discord.Embed(color = clients.bot_color)
			embed.description = "```Name: " + guild.name + "\n"
			embed.description += "ID: " + guild.id + "\n"
			embed.description += "Owner: {0} ({0.id})".format(guild.owner) + "\n"
			embed.description += "Server Region: {}".format(guild.region) + "\n"
			embed.description += "Members: {}".format(guild.member_count) + "\n"
			embed.description += "Created at: {}".format(guild.created_at) + "\n```"
			embed.set_thumbnail(url = guild.icon_url)
			await ctx.whisper(embed = embed)
	
	@commands.command(aliases = ["setprefixes"])
	@checks.is_permitted()
	async def setprefix(self, ctx, *prefixes : str):
		'''
		Set the bot prefix(es)
		For the server or for DMs
		Seperate prefixes with spaces
		Use qoutation marks for prefixes with spaces
		'''
		if not prefixes:
			prefixes = ['!']
		with open("data/prefixes.json", "r") as prefixes_file:
			all_prefixes = json.load(prefixes_file)
		if isinstance(ctx.channel, discord.DMChannel):
			all_prefixes[ctx.channel.id] = prefixes
		else:
			all_prefixes[ctx.guild.id] = prefixes
		with open("data/prefixes.json", "w") as prefixes_file:
			json.dump(all_prefixes, prefixes_file, indent = 4)
		await self.bot.embed_reply("Prefix(es) set: {}".format(' '.join(['`"{}"`'.format(prefix) for prefix in prefixes])))
	
	@commands.command(hidden = True)
	@checks.not_forbidden()
	async def type(self, ctx):
		'''Sends typing status'''
		await self.bot.send_typing(ctx.message.channel)
	
	# Public Info
	
	@commands.command(aliases = ["info"])
	async def about(self, ctx):
		'''About me'''
		from clients import application_info
		changes = os.popen(r'git show -s HEAD~3..HEAD --format="[`%h`](https://github.com/Harmon758/Harmonbot/commit/%H) %s (%cr)"').read().strip()
		embed = discord.Embed(title = "About Me", color = clients.bot_color)
		embed.description = "[Changelog (Harmonbot Server)]({})\n[Invite Link]({})".format(clients.changelog, discord.utils.oauth_url(application_info.id))
		# avatar = ctx.author.avatar_url or ctx.author.default_avatar_url
		# embed.set_author(name = ctx.author.display_name, icon_url = avatar)
		avatar = self.bot.user.avatar_url or self.bot.user.default_avatar_url
		# embed.set_thumbnail(url = avatar)
		embed.set_author(name = "Harmonbot (Discord ID: {})".format(self.bot.user.id), icon_url = avatar)
		if changes: embed.add_field(name = "Latest Changes:", value = changes, inline = False)
		embed.add_field(name = "Created on:", value = "February 10th, 2016")
		embed.add_field(name = "Version", value = clients.version)
		embed.add_field(name = "Library", value = "[discord.py](https://github.com/Rapptz/discord.py) v{0}\n([Python](https://www.python.org/) v{1.major}.{1.minor}.{1.micro})".format(discord.__version__, sys.version_info))
		me = discord.utils.get(self.bot.get_all_members(), id = clients.owner_id)
		avatar = me.default_avatar_url if not me.avatar else me.avatar_url
		embed.set_footer(text = "Developer/Owner: {0} (Discord ID: {0.id})".format(me), icon_url = avatar)
		await self.bot.reply("", embed = embed)
		await self.bot.say("Changelog (Harmonbot Server): {}".format(clients.changelog))
	
	@commands.command()
	async def changelog(self):
		'''Link to changelog'''
		await self.bot.reply(clients.changelog)
	
	@commands.command()
	async def conversions(self, ctx):
		'''All conversion commands'''
		await self.bot.embed_reply("**Temperature Unit Conversions**: {0}[c, f, k, r, de]__to__[c, f, k, r, de, n, re, ro]\n"
		"**Weight Unit Conversions**: {0}<unit>__to__<unit>\nunits: [amu, me, bagc, bagpc, barge, kt, ct, clove, crith, da, drt, drav, ev, gamma, gr, gv, longcwt, cwt, shcwt, kg, kip, mark, mite, mitem, ozt, ozav, oz, dwt, pwt, point, lb, lbav, lbm, lbt, quarterimp, quarterinf, quarterlinf, q, sap, sheet, slug, st, atl, ats, longtn, ton, shtn, t, wey, g]".format(ctx.prefix), title = "Conversion Commands")
	
	@commands.command(aliases = ["oauth"], hidden = True)
	async def invite(self):
		'''Link to invite me to a server'''
		from clients import application_info
		await self.bot.embed_reply(discord.utils.oauth_url(application_info.id))
	
	@commands.command()
	async def stats(self, ctx):
		'''Bot stats'''
		from clients import session_commands_executed, session_commands_usage
		with open("data/stats.json", 'r') as stats_file:
			stats = json.load(stats_file)
		
		now = datetime.datetime.utcnow()
		uptime = now - clients.online_time
		uptime = utilities.duration_to_letter_format(utilities.secs_to_duration(int(uptime.total_seconds())))
		total_members = sum(len(g.members) for g in self.bot.guilds)
		total_members_online  = sum(1 for m in self.bot.get_all_members() if m.status != discord.Status.offline)
		unique_members = set(self.bot.get_all_members())
		unique_members_online = sum(1 for m in unique_members if m.status != discord.Status.offline)
		channel_types = [c.type for c in self.bot.get_all_channels()]
		text_count = channel_types.count(discord.ChannelType.text)
		voice_count = channel_types.count(discord.ChannelType.voice)
		total_uptime = utilities.duration_to_letter_format(utilities.secs_to_duration(int(stats["uptime"])))
		top_commands = sorted(stats["commands_usage"].items(), key = lambda i: i[1], reverse = True)
		session_top_5 = sorted(session_commands_usage.items(), key = lambda i: i[1], reverse = True)[:5]
		in_voice_count = len(self.bot.cogs["Audio"].players)
		playing_in_voice_count = sum(player.current is not None and player.current["stream"].is_playing() for player in self.bot.cogs["Audio"].players.values())
		
		embed = discord.Embed(description = "__**Stats**__ :bar_chart:", color = clients.bot_color)
		avatar = ctx.author.avatar_url or ctx.author.default_avatar_url
		embed.set_author(name = ctx.author.display_name, icon_url = avatar) # url?
		embed.add_field(name = "Uptime", value = uptime)
		embed.add_field(name = "Total Recorded Uptime", value = total_uptime) # since 2016-04-17, fixed 2016-05-10
		embed.add_field(name = "Recorded Restarts", value = stats["restarts"]) # since 2016-04-17, fixed 2016-05-10
		embed.add_field(name = "Main Commands", value = len(set(self.bot.commands.values())))
		embed.add_field(name = "Commands Executed", 
			value = "{} this session\n{} total recorded".format(session_commands_executed, stats["commands_executed"])) 
			# since 2016-06-10 (cog commands)
		embed.add_field(name = "Cogs Reloaded", value = stats["cogs_reloaded"]) # since 2016-06-10 - implemented cog reloading
		# TODO: cogs reloaded this session
		embed.add_field(name = "Servers", value = len(self.bot.guilds))
		embed.add_field(name = "Channels", value = "{} text\n{} voice (playing in {}/{})".format(text_count, voice_count, playing_in_voice_count, in_voice_count))
		embed.add_field(name = "Members", 
			value = "{} total\n{} online\n{} unique\n{} unique online".format(total_members, total_members_online, len(unique_members), unique_members_online))
		embed.add_field(name = "Top Commands Executed", 
			value = "\n".join(["{} {}".format(uses, command) for command, uses in top_commands[:5]])) # since 2016-11-14
		embed.add_field(name = "(Total Recorded)", 
			value = "\n".join(["{} {}".format(uses, command) for command, uses in top_commands[5:10]])) # since 2016-11-14
		if session_top_5: embed.add_field(name = "(This Session)", 
			value = "\n".join(["{} {}".format(uses, command) for command, uses in session_top_5]))
		await self.bot.send_message(ctx.message.channel, embed = embed)
	
	@commands.command()
	async def uptime(self):
		'''Bot uptime'''
		now = datetime.datetime.utcnow()
		uptime = now - clients.online_time
		await self.bot.embed_reply(utilities.secs_to_letter_format(uptime.total_seconds()))
	
	@commands.command()
	async def version(self):
		'''Bot version'''
		await self.bot.embed_reply("I am Harmonbot `v{}`".format(clients.version))
	
	# Update Bot Stuff
	
	@commands.command(aliases = ["change_nickname"])
	@checks.is_owner()
	async def changenickname(self, ctx, *, nickname : str):
		'''Update my nickname'''
		await self.bot.change_nickname(ctx.me, nickname)
	
	@commands.command(aliases = ["setavatar", "update_avatar", "set_avatar"])
	@checks.is_owner()
	async def updateavatar(self, filename : str):
		'''Update my avatar'''
		if not os.path.isfile("data/avatars/{}".format(filename)):
			await self.bot.embed_reply(":no_entry: Avatar not found")
			return
		with open("data/avatars/{}".format(filename), "rb") as avatar_file:
			await self.bot.edit_profile(avatar = avatar_file.read())
		await self.bot.embed_reply("Updated avatar")
	
	@commands.command(aliases = ["random_game"], hidden = True)
	@checks.not_forbidden()
	async def randomgame(self):
		'''Update to a random playing/game status message'''
		await clients.random_game_status()
		# await self.bot.embed_reply("I changed to a random game status")
	
	@commands.command(aliases = ["updateplaying", "updategame", "changeplaying", "changegame", "setplaying", "set_game", "update_playing", "update_game", "change_playing", "change_game", "set_playing"])
	@checks.is_owner()
	async def setgame(self, ctx, *, name : str):
		'''Set my playing/game status message'''
		updated_game = ctx.me.game
		if not updated_game:
			updated_game = discord.Game(name = name)
		else:
			updated_game.name = name
		await self.bot.change_status(game = updated_game)
		await self.bot.embed_reply("Game updated")
	
	@commands.command(aliases = ["set_streaming"])
	@checks.is_owner()
	async def setstreaming(self, ctx, option : str, *url : str):
		'''Set my streaming status'''
		if option == "on" or option == "true":
			if not url:
				await clients.set_streaming_status()
				return
			else:
				updated_game = ctx.me.game
				if not updated_game:
					updated_game = discord.Game(url = url[0], type = 1)
				else:
					updated_game.url = url[0]
					updated_game.type = 1
		else:
			updated_game = ctx.me.game
			updated_game.type = 0
		await self.bot.change_status(game = updated_game)
	
	@commands.command(aliases = ["clearplaying", "clear_game", "clear_playing"])
	@checks.is_owner()
	async def cleargame(self, ctx):
		'''Clear my playing/game status message'''
		updated_game = ctx.me.game
		if updated_game and updated_game.name:
			updated_game.name = None
			await self.bot.change_status(game = updated_game)
			await self.bot.embed_reply("Game status cleared")
		else:
			await self.bot.embed_reply(":no_entry: There is no game status to clear")
	
	@commands.command(aliases = ["clear_streaming"])
	@checks.is_owner()
	async def clearstreaming(self, ctx, *option : str):
		'''Clear my streaming status'''
		updated_game = ctx.me.game
		if updated_game and (updated_game.url or updated_game.type):
			updated_game.url = None
			if option and option[0] == "url":
				await self.bot.change_status(game = updated_game)
				await self.bot.embed_reply("Streaming url cleared")
				return
			updated_game.type = 0
			await self.bot.change_status(game = updated_game)
			await self.bot.embed_reply("Streaming status and url cleared")
		else:
			await self.bot.embed_reply(":no_entry: There is no streaming status or url to clear")
	
	@commands.command(hidden = True)
	@checks.is_owner()
	async def update_discord_bots_stats(self):
		'''Update stats on https://bots.discord.pw'''
		response = await clients._update_discord_bots_stats()
		await self.bot.reply(response)
	
	# Restart/Shutdown
	
	@commands.command()
	@checks.is_owner()
	async def restart(self, ctx):
		'''Restart me'''
		await self.bot.embed_say(":ok_hand::skin-tone-2: Restarting...")
		print("Shutting down Discord Harmonbot...")
		await clients.restart_tasks(ctx.channel.id)
		await self.bot.logout()
	
	@commands.command(aliases = ["crash", "panic"])
	@checks.is_owner()
	async def shutdown(self):
		'''Shut me down'''
		await self.bot.embed_say(":scream: Shutting down.")
		print("Forcing Shutdown...")
		await clients.shutdown_tasks()
		subprocess.call(["taskkill", "/f", "/im", "cmd.exe"])
		subprocess.call(["taskkill", "/f", "/im", "python.exe"])
	
	# Testing
	
	@commands.command(hidden = True)
	@checks.not_forbidden()
	async def test(self):
		'''Basic test command'''
		await self.bot.say("Hello, World!")
	
	@commands.group(aliases = ["code_block"], invoke_without_command = True)
	@checks.not_forbidden()
	async def codeblock(self, *, input : str):
		'''Wrap your message in a code block'''
		await self.bot.embed_reply(clients.code_block.format(input))
	
	@codeblock.command(name = "python", aliases = ["py"])
	@checks.not_forbidden()
	async def codeblock_python(self, *, input : str):
		'''Wrap your message in a Python code block'''
		await self.bot.embed_reply(clients.py_code_block.format(input))
	
	@commands.command()
	@checks.is_owner()
	async def do(self, ctx, times : int, *, command):
		'''Repeats a command a specified number of times'''
		msg = copy.copy(ctx.message)
		msg.content = command
		for _ in range(times):
			await self.bot.process_commands(msg)
	
	@commands.group(invoke_without_command = True)
	@checks.is_owner()
	async def echo(self, *, message):
		'''Echoes the message'''
		await self.bot.say(message)
	
	@echo.command(name = "embed")
	@checks.is_owner()
	async def echo_embed(self, *, message):
		'''Echoes the message in an embed'''
		await self.bot.embed_say(message)
	
	@commands.command()
	@checks.is_owner()
	async def eval(self, ctx, *, code : str):
		code = code.strip('`')
		try:
			result = eval(code)
			if inspect.isawaitable(result):
				result = await result
			await self.bot.reply(clients.py_code_block.format(result))
		except Exception as e:
			await self.bot.reply(clients.py_code_block.format("{}: {}".format(type(e).__name__, e)))
	
	@commands.command()
	@checks.is_owner()
	async def exec(self, ctx, *, code : str):
		code = code.strip('`')
		try:
			exec(code)
		except Exception as e:
			await self.bot.reply(clients.py_code_block.format("{}: {}".format(type(e).__name__, e)))
			return
		await self.bot.embed_reply("Successfully executed")
	
	@commands.command(aliases = ["deletetest"])
	@checks.is_owner()
	async def delete_test(self):
		'''Sends 100 messages'''
		for i in range(1, 101):
			await self.bot.say(str(i))
	
	@commands.command(aliases = ["logsfromtest"])
	@checks.is_owner()
	async def logs_from_test(self, ctx):
		'''Used to test global rate limits'''
		for i in range(1, 101):
			async for message in self.bot.logs_from(ctx.message.channel):
				pass
			print("logs_from_test {}".format(i))
	
	@commands.command(aliases = ["repeattext"])
	@checks.is_owner()
	async def repeat_text(self, number : int, *, text):
		'''Repeat text'''
		for _ in range(number):
			await self.bot.say(text)
	
	@commands.command()
	@checks.is_owner()
	async def repl(self, ctx):
		variables = {"self" : self, "ctx" : ctx, "last" : None}
		await self.bot.embed_reply("Enter code to execute or evaluate\n`exit` or `quit` to exit")
		while True:
			message = await self.bot.wait_for_message(author = ctx.message.author, channel = ctx.message.channel, check = lambda m: m.content.startswith('`'))
			if message.content.startswith("```py") and message.content.endswith("```"):
				code = message.content[5:-3].strip(" \n")
			else:
				code = message.content.strip("` \n")
			if code in ("quit", "exit", "quit()", "exit()"):
				await self.bot.embed_reply('Exiting repl')
				return
			function = exec
			if '\n' not in code:
				try:
					code = compile(code, "<repl>", "eval")
				except SyntaxError:
					pass
				else:
					function = eval
			if function is exec:
				try:
					code = compile(code, "<repl>", "exec")
				except SyntaxError as e:
					await self.bot.reply(clients.py_code_block.format("{0.text}{1:>{0.offset}}\n{2}: {0}".format(e, '^', type(e).__name__)))
					continue
			try:
				result = function(code, variables)
				if inspect.isawaitable(result):
					result = await result
			except:
				await self.bot.reply(clients.py_code_block.format("\n".join(traceback.format_exc().splitlines()[-2:]).strip()))
			else:
				if function is eval:
					try:
						await self.bot.reply(clients.py_code_block.format(result))
					except Exception as e:
						await self.bot.reply(clients.py_code_block.format("{}: {}".format(type(e).__name__, e)))
				variables["last"] = result
	
	@commands.command(aliases = ["github"])
	@checks.not_forbidden()
	async def source(self, command : str = None):
		'''
		Displays my full source code or for a specific command
		To display the source code of a subcommand you have to separate it by
		periods, e.g. tag.create for the create subcommand of the tag command
		Based on [R. Danny](https://github.com/Rapptz/RoboDanny)'s source command
		'''
		source_url = "https://github.com/Harmon758/Harmonbot"
		if command is None:
			await self.bot.embed_reply(source_url)
			return
		code_path = command.split('.')
		obj = self.bot
		for cmd in code_path:
			try:
				obj = obj.get_command(cmd)
				if obj is None:
					await self.bot.embed_reply("Could not find the command " + cmd)
					return
			except AttributeError:
				await self.bot.embed_reply("{0.name} command has no subcommands".format(obj))
				return
		# since we found the command we're looking for, presumably anyway, let's
		# try to access the code itself
		src = obj.callback.__code__
		lines, firstlineno = inspect.getsourcelines(src)
		## if not obj.callback.__module__.startswith("discord"):
		# not a built-in command
		location = os.path.relpath(src.co_filename).replace('\\', '/')
		## else:
		##	location = obj.callback.__module__.replace('.', '/') + ".py"
		##	source_url = "https://github.com/Rapptz/discord.py"
		final_url = '<{}/blob/master/Discord/{}#L{}-L{}>'.format(source_url, location, firstlineno, firstlineno + len(lines) - 1)
		await self.bot.embed_reply(final_url)

