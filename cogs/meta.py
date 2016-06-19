
import discord
from discord.ext import commands

import datetime
import inspect
import json
import re
import subprocess
import traceback

import credentials
from modules import utilities
from modules import voice
from utilities import checks
from clients import online_time
from clients import py_code_block

def setup(bot):
	bot.add_cog(Meta(bot))

class Meta:
	
	def __init__(self, bot):
		self.bot = bot
		try:
			with open("data/stats.json", "x") as stats_file:
				json.dump({"uptime" : 0, "restarts" : 0, "cogs_reloaded" : 0, "commands_executed" : 0}, stats_file)
		except FileExistsError:
			pass

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
		self.bot.commands["tts"].enabled = True
		await self.bot.say("{} has been enabled.".format(command))
	
	@commands.command(hidden = True)
	@checks.is_owner()
	async def servers(self):
		'''Every server I'm in'''
		for server in self.bot.servers:
			server_info = "```Name: " + server.name + "\n"
			server_info += "ID: " + server.id + "\n"
			server_info += "Owner: " + server.owner.name + "\n"
			server_info += "Server Region: " + str(server.region) + "\n"
			server_info += "Members: " + str(server.member_count) + "\n"
			server_info += "Created at: " + str(server.created_at) + "\n```"
			server_info += "Icon: " + server.icon_url
			await self.bot.whisper(server_info)
	
	@commands.command(aliases = ["setprefixes"], pass_context = True)
	@checks.is_permitted()
	async def setprefix(self, ctx, *prefixes : str):
		'''
		Set the bot prefixes for the server or for DMs
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
	
	@commands.command(hidden = True)
	async def about(self):
		'''WIP'''
		return
	
	@commands.command()
	async def changelog(self):
		'''Link to changelog'''
		await self.bot.reply("https://discord.gg/0oyodN94Y3CgCT6I")
	
	@commands.command(name = "commands", pass_context = True)
	async def _commands(self, ctx):
		'''Some additional commands and information'''
		await self.bot.whisper("**Commands not in help**: test_on_message [conversion commands (see conversion command)]\n"
			"**In Progress**: adventure getpermission gifvtogif gofish help redditsearch roleposition rolepositions setpermission taboo timer urbandictionary userlimit weather wolframalpha webmtogif whatis\n"
			"**Misc**: discordlibraryversion echo load randomgame test\n"
			"**Owner Only**: allcommands changenickname deletetest cleargame clearstreaming eval exec invite restart servers setgame setstreaming shutdown updateavatar\n"
			"**No prefix**: @Harmonbot :8ball: (exactly: f|F) (anywhere in message: getprefix)")
		if not ctx.message.channel.is_private:
			await self.bot.reply("Check your DMs for some of my additional commands. Use help for the main commands.")
	
	@commands.command(pass_context = True)
	async def conversions(self, ctx):
		'''All conversion commands'''
		await self.bot.whisper("__Conversion Commands__\n"
		"**Temperature Unit Conversions**: [c, f, k, r, de]**to**[c, f, k, r, de, n, re, ro] \n"
		"**Weight Unit Conversions**: <unit>to<unit> units: [amu, me, bagc, bagpc, barge, kt, ct, clove, crith, da, drt, drav, ev, gamma, gr, gv, longcwt, cwt, shcwt, kg, kip, mark, mite, mitem, ozt, ozav, oz, dwt, pwt, point, lb, lbav, lbm, lbt, quarterimp, quarterinf, quarterlinf, q, sap, sheet, slug, st, atl, ats, longtn, ton, shtn, t, wey, g]")
		if not ctx.message.channel.is_private:
			await self.bot.reply("Check your DMs for my conversion commands.")
	
	@commands.command(hidden = True)
	async def discordlibraryversion(self):
		'''The discord.py library version I'm currently using'''
		await self.bot.reply(discord.__version__)
	
	@commands.command(aliases = ["oauth"], hidden = True)
	async def invite(self):
		'''Link to invite me to a server'''
		application_info = await self.bot.application_info()
		await self.bot.reply(discord.utils.oauth_url(application_info.id))
	
	@commands.command()
	async def stats(self, *option : str):
		'''Bot stats'''
		with open("data/stats.json", "r") as stats_file:
			stats = json.load(stats_file)
		if not option:
			uptime = utilities.duration_to_letter_format(utilities.secs_to_duration(int(stats["uptime"])))
			restarts = str(stats["restarts"])
			cogs_reloaded = str(stats["cogs_reloaded"])
			commands_executed = str(stats["commands_executed"])
			await self.bot.reply("\n"
			"Total Recorded Uptime: {}\n"
			"Total Recorded Restarts: {}\n"
			"Total Cogs Reloaded: {}\n"
			"Total Recorded Commands Executed: {}".format(uptime, restarts, cogs_reloaded, commands_executed))
		elif option[0] == "uptime": # since 4/17/16, fixed 5/10/16
			uptime = utilities.duration_to_letter_format(utilities.secs_to_duration(int(stats["uptime"])))
			await self.bot.reply("Total Recorded Uptime: {}".format(uptime))
		elif option[0] == "restarts": # since 4/17/16, fixed 5/10/16
			restarts = str(stats["restarts"])
			await self.bot.reply("Total Recorded Restarts: {}".format(restarts))
		elif ' '.join(option[:2]) == "cogs reloaded": # since 6/10/16 - implemented cog reloading
			cogs_reloaded = str(stats["cogs_reloaded"])
			await self.bot.reply("Total Cogs Reloaded: {}".format(cogs_reloaded))
		elif ' '.join(option[:2]) == "commands executed": # since 6/10/16 (cog commands)
			commands_executed = str(stats["commands_executed"])
			await self.bot.reply("Total Record Commands Executed".format(commands_executed))
	
	@commands.command()
	async def uptime(self):
		'''Bot uptime'''
		now = datetime.datetime.utcnow()
		uptime = now - online_time
		await self.bot.reply(utilities.duration_to_letter_format(utilities.secs_to_duration(int(uptime.total_seconds()))))
	
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
		await utilities.random_game_status()
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
				await utilities.set_streaming_status()
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
	
	@commands.command(pass_context = True, aliases = ["!clearplaying"], hidden = True)
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
		voice_channels = [[voice_client.channel.id, voice.get_player(voice_client.server)["text"]] for voice_client in self.bot.voice_clients]
		with open("data/restart_channel.json", "x+") as restart_channel_file:
			json.dump({"restart_channel" : ctx.message.channel.id, "voice_channels" : voice_channels}, restart_channel_file)
		#raise KeyboardInterrupt
		await utilities.restart_tasks()
		await self.bot.logout()
	
	@commands.command(aliases = ["crash", "panic"], hidden = True)
	@checks.is_owner()
	async def shutdown(self):
		'''Shut me down'''
		await self.bot.say(":scream: Shutting down.")
		print("Forcing Shutdown...")
		await utilities.shutdown_tasks()
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
					except:
						await self.bot.reply(py_code_block.format("{}: {}".format(type(e).__name__, e)))
				variables["last"] = result

