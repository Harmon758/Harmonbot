
import discord
from discord.ext import commands
from discord.ext.commands.bot import _mention_pattern, _mentions_transforms

import asyncio
import datetime
import copy
import inspect
import json
import os
import psutil
import re
import subprocess
import sys
import traceback

import credentials
from modules import utilities
from utilities import checks

import clients
from clients import py_code_block

def setup(bot):
	bot.add_cog(Meta(bot))

class Meta:
	
	def __init__(self, bot):
		self.bot = bot
		utilities.create_file("stats", content = {"uptime" : 0, "restarts" : 0, "cogs_reloaded" : 0, "commands_executed" : 0, "commands_usage": {}, "reaction_responses": 0})
	
	@commands.command(aliases = ["commands"], hidden = True, pass_context = True)
	async def help(self, ctx, *commands : str):
		'''Shows this message.'''
		bot = ctx.bot
		destination = ctx.message.author if bot.pm_help else ctx.message.channel
		
		def repl(obj):
			return _mentions_transforms.get(obj.group(0), '')
		
		# help by itself just lists our own commands.
		if len(commands) == 0:
			pages = bot.formatter.format_help_for(ctx, "categories")
		elif commands[0] == "all":
			pages = bot.formatter.format_help_for(ctx, bot)
		elif len(commands) == 1:
			# try to see if it is a cog name
			name = _mention_pattern.sub(repl, commands[0])
			command = None
			if name in bot.cogs or (name not in bot.commands and name.capitalize() in bot.cogs):
				command = bot.cogs[name.capitalize()]
			else:
				command = bot.commands.get(name)
				if command is None:
					await bot.send_message(destination, bot.command_not_found.format(name))
					return
			
			pages = bot.formatter.format_help_for(ctx, command)
		else:
			name = _mention_pattern.sub(repl, commands[0])
			command = bot.commands.get(name)
			if command is None:
				await bot.send_message(destination, bot.command_not_found.format(name))
				return
			
			for key in commands[1:]:
				try:
					key = _mention_pattern.sub(repl, key)
					command = command.commands.get(key)
					if command is None:
						await bot.send_message(destination, bot.command_not_found.format(key))
						return
				except AttributeError:
					await bot.send_message(destination, bot.command_has_no_subcommands.format(command, key))
					return
			
			pages = bot.formatter.format_help_for(ctx, command)
		
		if bot.pm_help is None:
			characters = sum(map(lambda l: len(l), pages))
			# modify destination based on length of pages.
			if characters > 1000:
				destination = ctx.message.author
		
		if destination == ctx.message.author and not ctx.message.channel.is_private:
			await bot.reply("Check your DMs.")
		
		for page in pages:
			# yield from bot.send_message(destination, page)
			await bot.send_message(destination, page)
	
	@commands.command(pass_context = True)
	@checks.is_owner()
	async def allcommands(self, ctx):
		'''All the commands'''
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
	
	@commands.command(pass_context = True)
	@checks.is_owner()
	async def disable(self, ctx, command : str):
		'''Disable a command'''
		self.bot.commands[command].enabled = False
		await self.bot.embed_reply("`{}{}` has been disabled".format(ctx.prefix, command))
		await self.bot.delete_message(ctx.message)
	
	@commands.command(pass_context = True)
	@checks.is_owner()
	async def enable(self, ctx, command : str):
		'''Enable a command'''
		self.bot.commands[command].enabled = True
		await self.bot.embed_reply("`{}{}` has been enabled".format(ctx.prefix, command))
		await self.bot.delete_message(ctx.message)
	
	@commands.command(hidden = True)
	@checks.is_owner()
	async def servers(self):
		'''Every server I'm in'''
		for server in self.bot.servers:
			server_info = "```Name: " + server.name + "\n"
			server_info += "ID: " + server.id + "\n"
			server_info += "Owner: " + str(server.owner) + "\n"
			server_info += "Server Region: " + str(server.region) + "\n"
			server_info += "Members: " + str(server.member_count) + "\n"
			server_info += "Created at: " + str(server.created_at) + "\n```"
			server_info += "Icon: " + server.icon_url
			await self.bot.whisper(server_info)
	
	@commands.command(aliases = ["setprefixes"], pass_context = True)
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
		if ctx.message.channel.is_private:
			all_prefixes[ctx.message.channel.id] = prefixes
		else:
			all_prefixes[ctx.message.server.id] = prefixes
		with open("data/prefixes.json", "w") as prefixes_file:
			json.dump(all_prefixes, prefixes_file, indent = 4)
		await self.bot.embed_reply("Prefix(es) set: {}".format(' '.join(['`"{}"`'.format(prefix) for prefix in prefixes])))
	
	@commands.command(pass_context = True, hidden = True)
	@checks.not_forbidden()
	async def type(self, ctx):
		'''Sends typing status'''
		await self.bot.send_typing(ctx.message.channel)
	
	# Public Info
	
	@commands.command(aliases = ["info"], pass_context = True)
	async def about(self, ctx):
		'''About me'''
		from clients import application_info
		changes = os.popen(r'git show -s HEAD~3..HEAD --format="[`%h`](https://github.com/Harmon758/Harmonbot/commit/%H) %s (%cr)"').read().strip()
		embed = discord.Embed(title = "About Me", color = clients.bot_color)
		embed.description = "[Changelog (Harmonbot Server)]({})\n[Invite Link]({})".format(clients.changelog, discord.utils.oauth_url(application_info.id))
		# avatar = ctx.message.author.avatar_url or ctx.message.author.default_avatar_url
		# embed.set_author(name = ctx.message.author.display_name, icon_url = avatar)
		avatar = self.bot.user.avatar_url or self.bot.user.default_avatar_url
		# embed.set_thumbnail(url = avatar)
		embed.set_author(name = "Harmonbot (Discord ID: {})".format(self.bot.user.id), icon_url = avatar)
		if changes: embed.add_field(name = "Latest Changes:", value = changes, inline = False)
		embed.add_field(name = "Created on:", value = "February 10th, 2016")
		embed.add_field(name = "Version", value = clients.version)
		embed.add_field(name = "Library", value = "[discord.py](https://github.com/Rapptz/discord.py) v{0}\n([Python](https://www.python.org/) v{1.major}.{1.minor}.{1.micro})".format(discord.__version__, sys.version_info))
		me = discord.utils.get(self.bot.get_all_members(), id = credentials.myid)
		avatar = me.default_avatar_url if not me.avatar else me.avatar_url
		embed.set_footer(text = "Developer/Owner: {0} (Discord ID: {0.id})".format(me), icon_url = avatar)
		await self.bot.reply("", embed = embed)
		await self.bot.say("Changelog (Harmonbot Server): {}".format(clients.changelog))
	
	@commands.command()
	async def changelog(self):
		'''Link to changelog'''
		await self.bot.reply(clients.changelog)
	
	@commands.command(pass_context = True)
	async def conversions(self, ctx):
		'''All conversion commands'''
		await self.bot.embed_reply("**Temperature Unit Conversions**: {0}[c, f, k, r, de]__to__[c, f, k, r, de, n, re, ro]\n"
		"**Weight Unit Conversions**: {0}<unit>__to__<unit>\nunits: [amu, me, bagc, bagpc, barge, kt, ct, clove, crith, da, drt, drav, ev, gamma, gr, gv, longcwt, cwt, shcwt, kg, kip, mark, mite, mitem, ozt, ozav, oz, dwt, pwt, point, lb, lbav, lbm, lbt, quarterimp, quarterinf, quarterlinf, q, sap, sheet, slug, st, atl, ats, longtn, ton, shtn, t, wey, g]".format(ctx.prefix), title = "Conversion Commands")
	
	@commands.command(aliases = ["oauth"], hidden = True)
	async def invite(self):
		'''Link to invite me to a server'''
		from clients import application_info
		await self.bot.reply(discord.utils.oauth_url(application_info.id))
	
	@commands.command(pass_context = True)
	async def othercommands(self, ctx):
		'''Some additional commands and information'''
		await self.bot.whisper("__Commands not in `{0}help`__\n"
			"**Conversion Commands**: see `{0}conversions`\n"
			"**In Progress**: about gofish redditsearch roleposition rolepositions taboo userlimit weather wolframalpha webmtogif whatis\n"
			"**Misc**: discordlibraryversion invite loading_bar ping randomgame test test_on_message\n"
			"**Owner Only**: allcommands changenickname deletetest cleargame clearstreaming echo eval exec load reload repl restart servers setgame setstreaming shutdown unload updateavatar\n"
			"**No prefix**: @Harmonbot :8ball: (exactly: f|F) (anywhere in message: getprefix)\n"
			"Note: If you are not currently able to use a command in the channel where you executed `{0}help`, it will not be displayed in the corresponding `{0}help` message.\n"
			"See `{0}help` for the main commands.".format(ctx.prefix))
		if not ctx.message.channel.is_private:
			await self.bot.reply("Check your DMs for some of my additional commands.")
	
	@commands.command(pass_context = True)
	async def stats(self, ctx):
		'''Bot stats'''
		from clients import session_commands_executed, session_commands_usage
		with open("data/stats.json", 'r') as stats_file:
			stats = json.load(stats_file)
		
		now = datetime.datetime.utcnow()
		uptime = now - clients.online_time
		uptime = utilities.duration_to_letter_format(utilities.secs_to_duration(int(uptime.total_seconds())))
		total_members = sum(len(s.members) for s in self.bot.servers)
		total_members_online  = sum(1 for m in self.bot.get_all_members() if m.status != discord.Status.offline)
		unique_members = set(self.bot.get_all_members())
		unique_members_online = sum(1 for m in unique_members if m.status != discord.Status.offline)
		channel_types = [c.type for c in self.bot.get_all_channels()]
		text_count = channel_types.count(discord.ChannelType.text)
		voice_count = channel_types.count(discord.ChannelType.voice)
		total_uptime = utilities.duration_to_letter_format(utilities.secs_to_duration(int(stats["uptime"])))
		top_5_commands = sorted(stats["commands_usage"].items(), key = lambda i: i[1], reverse = True)[:5]
		session_top_5 = sorted(session_commands_usage.items(), key = lambda i: i[1], reverse = True)[:5]
		in_voice_count = len(self.bot.cogs["Audio"].players)
		
		embed = discord.Embed(description = "__**Stats**__ :bar_chart:", color = clients.bot_color)
		avatar = ctx.message.author.avatar_url or ctx.message.author.default_avatar_url
		embed.set_author(name = ctx.message.author.display_name, icon_url = avatar) # url?
		embed.add_field(name = "Uptime", value = uptime)
		embed.add_field(name = "Total Recorded Uptime", value = total_uptime) # since 4/17/16, fixed 5/10/16
		embed.add_field(name = "Recorded Restarts", value = stats["restarts"]) # since 4/17/16, fixed 5/10/16
		embed.add_field(name = "Main Commands", value = len(set(self.bot.commands.values())))
		embed.add_field(name = "Commands Executed", 
			value = "{} this session\n{} total recorded".format(session_commands_executed, stats["commands_executed"])) 
			# since 6/10/16 (cog commands)
		embed.add_field(name = "Cogs Reloaded", value = stats["cogs_reloaded"]) # since 6/10/16 - implemented cog reloading
		# TODO: cogs reloaded this session
		embed.add_field(name = "Servers", value = len(self.bot.servers))
		embed.add_field(name = "Channels", value = "{} text\n{} voice (in {})".format(text_count, voice_count, in_voice_count))
		embed.add_field(name = "Members", 
			value = "{} total\n{} online\n{} unique\n{} unique online".format(total_members, total_members_online, len(unique_members), unique_members_online))
		embed.add_field(name = "Top 5 Commands Executed (Total Recorded)", 
			value = "\n".join(["{} {}".format(uses, command) for command, uses in top_5_commands])) # since 11/14/16
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
	
	@commands.command(aliases = ["change_nickname"], pass_context = True)
	@checks.is_owner()
	async def changenickname(self, ctx, *, nickname : str):
		'''Update my nickname'''
		await self.bot.change_nickname(ctx.message.server.me, nickname)
	
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
	
	@commands.command(aliases = ["updateplaying", "updategame", "changeplaying", "changegame", "setplaying", "set_game", "update_playing", "update_game", "change_playing", "change_game", "set_playing"], pass_context = True)
	@checks.is_owner()
	async def setgame(self, ctx, *, name : str):
		'''Set my playing/game status message'''
		updated_game = ctx.message.server.me.game
		if not updated_game:
			updated_game = discord.Game(name = name)
		else:
			updated_game.name = name
		await self.bot.change_status(game = updated_game)
		await self.bot.embed_reply("Game updated")
	
	@commands.command(aliases = ["set_streaming"], pass_context = True)
	@checks.is_owner()
	async def setstreaming(self, ctx, option : str, *url : str):
		'''Set my streaming status'''
		if option == "on" or option == "true":
			if not url:
				await clients.set_streaming_status()
				return
			else:
				updated_game = ctx.message.server.me.game
				if not updated_game:
					updated_game = discord.Game(url = url[0], type = 1)
				else:
					updated_game.url = url[0]
					updated_game.type = 1
		else:
			updated_game = ctx.message.server.me.game
			updated_game.type = 0
		await self.bot.change_status(game = updated_game)
	
	@commands.command(aliases = ["clearplaying", "clear_game", "clear_playing"], pass_context = True)
	@checks.is_owner()
	async def cleargame(self, ctx):
		'''Clear my playing/game status message'''
		updated_game = ctx.message.server.me.game
		if updated_game and updated_game.name:
			updated_game.name = None
			await self.bot.change_status(game = updated_game)
			await self.bot.embed_reply("Game status cleared")
		else:
			await self.bot.embed_reply(":no_entry: There is no game status to clear")
	
	@commands.command(aliases = ["clear_streaming"], pass_context = True)
	@checks.is_owner()
	async def clearstreaming(self, ctx, *option : str):
		'''Clear my streaming status'''
		updated_game = ctx.message.server.me.game
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
	
	@commands.command(pass_context = True)
	@checks.is_owner()
	async def restart(self, ctx):
		'''Restart me'''
		await self.bot.embed_say(":ok_hand::skin-tone-2: Restarting...")
		print("Shutting down Discord Harmonbot...")
		await clients.restart_tasks(ctx.message.channel.id)
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
	
	@commands.command(pass_context = True)
	@checks.is_owner()
	async def do(self, ctx, times : int, *, command):
		'''Repeats a command a specified number of times'''
		msg = copy.copy(ctx.message)
		msg.content = command
		for _ in range(times):
			await self.bot.process_commands(msg)
	
	@commands.command()
	@checks.is_owner()
	async def echo(self, *, message):
		'''Echoes the message'''
		await self.bot.say(message)
	
	@commands.command(pass_context = True)
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
	
	@commands.command(pass_context = True)
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
	
	@commands.command(aliases = ["logsfromtest"], pass_context = True)
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
	
	@commands.command(pass_context = True)
	@checks.is_owner()
	async def repl(self, ctx):
		variables = {"self" : self, "ctx" : ctx, "last" : None}
		await self.bot.say("Enter code to execute or evaluate. `exit` or `quit` to exit.")
		while True:
			message = await self.bot.wait_for_message(author = ctx.message.author, channel = ctx.message.channel, check = lambda m: m.content.startswith('`'))
			if message.content.startswith("```py") and message.content.endswith("```"):
				code = message.content[5:-3].strip(" \n")
			else:
				code = message.content.strip("` \n")
			if code in ("quit", "exit", "quit()", "exit()"):
				await self.bot.say('Exiting repl.')
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
					await self.bot.reply(py_code_block.format("{0.text}{1:>{0.offset}}\n{2}: {0}".format(e, '^', type(e).__name__)))
					continue
			try:
				result = function(code, variables)
				if inspect.isawaitable(result):
					result = await result
			except:
				await self.bot.reply(py_code_block.format("\n".join(traceback.format_exc().splitlines()[-2:]).strip()))
			else:
				if function is eval:
					try:
						await self.bot.reply(py_code_block.format(result))
					except Exception as e:
						await self.bot.reply(py_code_block.format("{}: {}".format(type(e).__name__, e)))
				variables["last"] = result

