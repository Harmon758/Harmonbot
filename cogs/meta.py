
import discord
from discord.ext import commands
from discord.ext.commands.bot import _mention_pattern, _mentions_transforms

import datetime
import inspect
import json
import re
import subprocess
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
		utilities.create_file("stats", content = {"uptime" : 0, "restarts" : 0, "cogs_reloaded" : 0, "commands_executed" : 0})
	
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
			if name in bot.cogs:
				command = bot.cogs[name]
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
	
	@commands.command(hidden = True, pass_context = True)
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
	async def disable(self, command : str):
		'''Disable a command'''
		self.bot.commands[command].enabled = False
		await self.bot.say("{} has been disabled.".format(command))
	
	@commands.command()
	@checks.is_owner()
	async def enable(self, command : str):
		'''Enable a command'''
		self.bot.commands[command].enabled = True
		await self.bot.say("{} has been enabled.".format(command))
	
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
		await self.bot.reply("Prefix(es) set: {}".format(' '.join(['`"{}"`'.format(prefix) for prefix in prefixes])))
	
	# Public Info
	
	@commands.command(aliases = ["info"])
	async def about(self):
		'''About me'''
		output = ["", "__**About Me**__"]
		output.append("**Harmonbot** (Discord ID: `160677293252018177`)")
		output.append("**Author/Owner:** Harmon758 (Discord ID: `115691005197549570`)")
		output.append("**Version:** `{}`".format(clients.version))
		output.append("**Library:** discord.py (Python) `v{}`".format(discord.__version__))
		output.append("**Changelog (Harmonbot Server):** {}".format(clients.changelog))
		await self.bot.reply('\n'.join(output))
	
	@commands.command()
	async def changelog(self):
		'''Link to changelog'''
		await self.bot.reply(clients.changelog)
	
	@commands.command(pass_context = True)
	async def conversions(self, ctx):
		'''All conversion commands'''
		await self.bot.whisper("__Conversion Commands__\n"
		"**Temperature Unit Conversions**: {0}[c, f, k, r, de]**to**[c, f, k, r, de, n, re, ro] \n"
		"**Weight Unit Conversions**: {0}<unit>to<unit> units: [amu, me, bagc, bagpc, barge, kt, ct, clove, crith, da, drt, drav, ev, gamma, gr, gv, longcwt, cwt, shcwt, kg, kip, mark, mite, mitem, ozt, ozav, oz, dwt, pwt, point, lb, lbav, lbm, lbt, quarterimp, quarterinf, quarterlinf, q, sap, sheet, slug, st, atl, ats, longtn, ton, shtn, t, wey, g]".format(ctx.prefix))
		if not ctx.message.channel.is_private:
			await self.bot.reply("Check your DMs for my conversion commands.")
	
	@commands.command(hidden = True)
	async def discordlibraryversion(self):
		'''The discord.py library version I'm currently using'''
		await self.bot.reply(discord.__version__)
	
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
	
	@commands.command()
	async def stats(self):
		'''Bot stats'''
		with open("data/stats.json", "r") as stats_file:
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
		output = ["", "__**Stats**__ :chart_with_upwards_trend:"]
		output.append("**Uptime:** `{}`".format(uptime))
		output.append("**Servers:** `{}`".format(len(self.bot.servers)))
		output.append("**Total Members:** `{}` (`{}` online)".format(total_members, total_members_online))
		output.append("**Unique Members:** `{}` (`{}` online)".format(len(unique_members), unique_members_online))
		output.append("**Text Channels:** `{}`, **Voice Channels:** `{}`".format(text_count, voice_count))
		output.append("**Main Commands:** `{}`".format(len(set((c for c in self.bot.commands.values())))))
		output.append("**Total Recorded Uptime:** `{}`".format(total_uptime)) # since 4/17/16, fixed 5/10/16
		output.append("**Recorded Restarts:** `{}`".format(stats["restarts"])) # since 4/17/16, fixed 5/10/16
		output.append("**Cogs Reloaded:** `{}`".format(stats["cogs_reloaded"])) # since 6/10/16 - implemented cog reloading
		output.append("**Total Recorded Commands Executed:** `{}`".format(stats["commands_executed"])) # since 6/10/16 (cog commands)
		await self.bot.reply('\n'.join(output))
	
	@commands.command()
	async def uptime(self):
		'''Bot uptime'''
		now = datetime.datetime.utcnow()
		uptime = now - clients.online_time
		await self.bot.reply(utilities.duration_to_letter_format(utilities.secs_to_duration(int(uptime.total_seconds()))))
	
	@commands.command()
	async def version(self):
		'''Bot version'''
		await self.bot.reply("I am Harmonbot `v{}`".format(version))
	
	# Update Bot Stuff
	
	@commands.command(pass_context = True, hidden = True)
	@checks.is_owner()
	async def changenickname(self, ctx, *, nickname : str):
		'''Update my nickname'''
		await self.bot.change_nickname(ctx.message.server.me, nickname)
	
	@commands.command(hidden = True)
	@checks.is_owner()
	async def updateavatar(self):
		'''Update my avatar'''
		with open("data/discord_harmonbot_icon.png", "rb") as avatar_file:
			await self.bot.edit_profile(avatar = avatar_file.read())
		await self.bot.reply("Avatar updated.")
	
	@commands.command(hidden = True)
	@checks.not_forbidden()
	async def randomgame(self):
		'''Update to a random playing/game status message'''
		await clients.random_game_status()
		# await self.bot.reply("I changed to a random game status.")
	
	@commands.command(pass_context = True, aliases = ["updateplaying", "updategame", "changeplaying", "changegame", "setplaying"], hidden = True)
	@checks.is_owner()
	async def setgame(self, ctx, *, name : str):
		'''Set my playing/game status message'''
		updated_game = ctx.message.server.me.game
		if not updated_game:
			updated_game = discord.Game(name = name)
		else:
			updated_game.name = name
		await self.bot.change_status(game = updated_game)
		await self.bot.reply("Game updated.")
	
	@commands.command(pass_context = True, hidden = True)
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
	
	@commands.command(pass_context = True, aliases = ["clearplaying"], hidden = True)
	@checks.is_owner()
	async def cleargame(self, ctx):
		'''Clear my playing/game status message'''
		updated_game = ctx.message.server.me.game
		if updated_game and updated_game.name:
			updated_game.name = None
			await self.bot.change_status(game = updated_game)
			await self.bot.reply("Game status cleared.")
		else:
			await self.bot.reply("There is no game status to clear.")
	
	@commands.command(pass_context = True, hidden = True)
	@checks.is_owner()
	async def clearstreaming(self, ctx, *option : str):
		'''Clear my streaming status'''
		updated_game = ctx.message.server.me.game
		if updated_game and (updated_game.url or updated_game.type):
			updated_game.url = None
			if option and option[0] == "url":
				await self.bot.change_status(game = updated_game)
				await self.bot.reply("Streaming url cleared.")
				return
			updated_game.type = 0
			await self.bot.change_status(game = updated_game)
			await self.bot.reply("Streaming status and url cleared.")
		else:
			await self.bot.reply("There is no streaming status or url to clear.")
	
	# Restart/Shutdown
	
	@commands.command(pass_context = True, hidden = True)
	@checks.is_owner()
	async def restart(self, ctx):
		'''Restart me'''
		await self.bot.say(":ok_hand::skin-tone-2: Restarting...")
		print("Shutting down Harmonbot...")
		voice_channels = [[voice_client.channel.id, self.bot.cogs["Audio"].players[voice_client.server.id]["text"]] for voice_client in self.bot.voice_clients]
		with open("data/restart_channel.json", "x+") as restart_channel_file:
			json.dump({"restart_channel" : ctx.message.channel.id, "voice_channels" : voice_channels}, restart_channel_file)
		# raise KeyboardInterrupt
		await clients.restart_tasks()
		await self.bot.logout()
	
	@commands.command(aliases = ["crash", "panic"], hidden = True)
	@checks.is_owner()
	async def shutdown(self):
		'''Shut me down'''
		await self.bot.say(":scream: Shutting down.")
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
	
	@commands.command(hidden = True)
	@checks.is_owner()
	async def echo(self, *, message):
		'''Echoes the message'''
		await self.bot.say(message)
	
	@commands.command(pass_context = True, hidden = True)
	@checks.is_owner()
	async def eval(self, ctx, *, code : str):
		code = code.strip('`')
		try:
			result = eval(code)
			if inspect.isawaitable(result):
				result = await result
			await self.bot.reply(py_code_block.format(result))
		except Exception as e:
			await self.bot.reply(py_code_block.format("{}: {}".format(type(e).__name__, e)))
	
	@commands.command(pass_context = True, hidden = True)
	@checks.is_owner()
	async def exec(self, ctx, *, code : str):
		code = code.strip('`')
		try:
			exec(code)
		except Exception as e:
			await self.bot.reply(py_code_block.format("{}: {}".format(type(e).__name__, e)))
			return
		await self.bot.reply("Successfully executed.")
	
	@commands.command(hidden = True)
	@checks.is_owner()
	async def deletetest(self):
		'''Sends 100 messages'''
		for i in range(1, 101):
			await self.bot.say(str(i))
	
	@commands.command(hidden = True)
	@checks.not_forbidden()
	async def loading_bar(self):
		'''
		Just for fun loading bar
		Currently does nothing.. or does it?
		'''
		counter = 0
		bar = chr(9633) * 10
		loading_message = await self.bot.say("Loading: [" + bar + "]")
		while counter <= 10:
			counter += 1
			bar = chr(9632) + bar[:-1] #9608
			await asyncio.sleep(1)
			await self.bot.edit_message(loading_message, "Loading: [" + bar + "]")

	@commands.command(hidden = True)
	async def ping(self):
		'''Basic ping - pong command'''
		await self.bot.say("pong")
	
	@commands.command(pass_context = True, hidden = True)
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

