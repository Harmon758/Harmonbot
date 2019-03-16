
import discord
from discord.ext import commands
from discord.ext.commands.bot import _mention_pattern, _mentions_transforms

import asyncio
import datetime
import copy
import ctypes
import difflib
import inspect
import json
import os
import random
import subprocess
import sys
import traceback

import git
import pkg_resources  # from setuptools
import psutil

import clients
from modules import utilities
from utilities import checks

def setup(bot):
	bot.add_cog(Meta(bot))

class Meta(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		clients.create_file("stats", content = {"uptime" : 0, "restarts" : 0, "cogs_reloaded" : 0, "commands_executed" : 0, "commands_usage": {}, "reaction_responses": 0})
		self.command_not_found = "No command called `{}` found"
	
	@commands.group(aliases = ["commands"], hidden = True, invoke_without_command = True)
	@checks.dm_or_has_capability("embed_links")
	async def help(self, ctx, *commands : str):
		'''
		Shows this message
		Inputs in angle brackets, <>, are required
		Inputs in square brackets, [], are optional
		If you are not currently able to use a command in the channel where you executed help, it will not be displayed in the corresponding help message
		'''
		# TODO: pass alias used to help formatter?
		if len(commands) == 0:
			embed = discord.Embed(title = "Categories", color = ctx.bot.bot_color)
			embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url)
			embed.description = "  ".join("`{}`".format(category) for category in sorted(self.bot.cogs, key = str.lower))
			embed.add_field(name = "For more info:", value = "`{0}{1} [category]`\n`{0}{1} [command]`\n`{0}{1} [command] [subcommand]`".format(ctx.prefix, ctx.invoked_with))
			embed.add_field(name = "Also see:", value = "`{0}about`\n`{0}{1} help`\n`{0}{1} other`".format(ctx.prefix, ctx.invoked_with))  # TODO: include stats?
			embed.add_field(name = "For all commands:", value = "`{}{} all`".format(ctx.prefix, ctx.invoked_with), inline = False)
			await ctx.send(embed = embed)
			return
		
		def repl(obj):
			return _mentions_transforms.get(obj.group(0), '')
		
		if len(commands) == 1:
			name = _mention_pattern.sub(repl, commands[0])
			if name in self.bot.cogs:
				command = self.bot.cogs[name]
			elif name.lower() in self.bot.all_commands:
				command = self.bot.all_commands[name.lower()]
			elif name.lower() in [cog.lower() for cog in self.bot.cogs.keys()]:  # TODO: More efficient way?
				command = discord.utils.find(lambda c: c[0].lower() == name.lower(), self.bot.cogs.items())[1]
			else:
				output = self.command_not_found.format(name)
				close_matches = difflib.get_close_matches(name, self.bot.all_commands.keys(), n = 1)
				if close_matches:
					output += "\nDid you mean `{}`?".format(close_matches[0])
				await ctx.embed_reply(output)
				return
			embeds = await self.bot.formatter.format_help_for(ctx, command)
		else:
			name = _mention_pattern.sub(repl, commands[0])
			command = self.bot.all_commands.get(name)
			if command is None:
				await ctx.embed_reply(self.command_not_found.format(name))
				return
			for key in commands[1:]:
				try:
					key = _mention_pattern.sub(repl, key)
					command = command.all_commands.get(key)
					if command is None:
						await ctx.embed_reply(self.command_not_found.format(key))
						return
				except AttributeError:
					await ctx.embed_reply("`{}` command has no subcommands".format(command.name))
					return
			embeds = await self.bot.formatter.format_help_for(ctx, command)
		
		if len(embeds) > 1:
			destination = ctx.author
			if not isinstance(ctx.channel, discord.DMChannel):
				await ctx.embed_reply("Check your DMs")
		else:
			destination = ctx.channel
		for embed in embeds:
			if destination == ctx.channel:
				embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url)
			await destination.send(embed = embed)
	
	@help.command(name = "all")
	async def help_all(self, ctx):
		'''All commands'''
		embeds = await self.bot.formatter.format_help_for(ctx, self.bot)
		for embed in embeds:
			await ctx.whisper(embed = embed)
		if not isinstance(ctx.channel, discord.DMChannel):
			await ctx.embed_reply("Check your DMs")
	
	@help.command(name = "other")
	async def help_other(self, ctx):
		'''Additional commands and information'''
		# TODO: Update
		# TODO: Add last updated date?
		embed = discord.Embed(title = "Commands not in {}help".format(ctx.prefix), color = ctx.bot.bot_color)
		embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url)
		embed.description = "See `{}help` for the main commands".format(ctx.prefix)
		embed.add_field(name = "Conversion Commands", value = "see `{}conversions`".format(ctx.prefix), inline = False)
		embed.add_field(name = "In Progress", value = "gofish redditsearch roleposition rolepositions taboo userlimit webmtogif whatis", inline = False)
		embed.add_field(name = "Misc", value = "invite randomgame test test_on_message", inline = False)
		embed.add_field(name = "Owner Only", value = "allcommands changenickname deletetest cleargame clearstreaming echo eval exec load reload repl restart servers setgame setstreaming shutdown unload updateavatar", inline = False)
		embed.add_field(name = "No Prefix", value = "@Harmonbot :8ball: (exactly: f|F) (anywhere in message: getprefix)", inline = False)
		await ctx.send(embed = embed)
	
	@commands.command()
	@commands.is_owner()
	async def allcommands(self, ctx):
		'''All the commands'''
		# TODO: Fix/Deprecate?, all_commands alias
		formatter = commands.HelpFormatter(show_check_failure = True, show_hidden = True)
		await formatter.format_help_for(ctx, self.bot)
		_commands = await formatter.filter_command_list()
		_allcommands = ""
		for name, _command in _commands:
			_allcommands += name + ' '
		await ctx.whisper(_allcommands[:-1])
	
	@commands.command()
	@commands.is_owner()
	async def benchmark(self, ctx):
		'''Benchmark'''
		process = psutil.Process()
		memory = process.memory_info().rss / 2 ** 20
		process.cpu_percent()
		embed = discord.Embed(color = ctx.bot.bot_color)
		embed.add_field(name = "RAM", value = "{:.2f} MiB".format(memory))
		embed.add_field(name = "CPU", value = "Calculating CPU usage..")
		message = await ctx.send(embed = embed)
		await asyncio.sleep(1)
		cpu = process.cpu_percent() / psutil.cpu_count()
		embed.set_field_at(1, name = "CPU", value = "{}%".format(cpu))
		await message.edit(embed = embed)
	
	@commands.command(aliases = ["category"])
	@checks.not_forbidden()
	async def cog(self, ctx, command):
		'''Find what cog/category a command is in'''
		if command not in self.bot.all_commands:
			await ctx.embed_reply(":no_entry: Error: command not found")
			return
		await ctx.embed_reply(self.bot.all_commands[command].cog_name)
	
	@commands.command()
	@commands.is_owner()
	async def disable(self, ctx, command : str):
		'''Disable a command'''
		self.bot.all_commands[command].enabled = False
		await ctx.embed_reply("`{}{}` has been disabled".format(ctx.prefix, command))
	
	@commands.command()
	@commands.is_owner()
	async def enable(self, ctx, command : str):
		'''Enable a command'''
		self.bot.all_commands[command].enabled = True
		await ctx.embed_reply("`{}{}` has been enabled".format(ctx.prefix, command))
	
	@commands.command()
	async def points(self, ctx):
		'''WIP'''
		commands_executed = await ctx.bot.db.fetchval(
			"""
			SELECT commands_executed
			FROM users.stats
			WHERE user_id = $1
			""", 
			ctx.author.id
		)
		await ctx.embed_reply(f"You have {commands_executed} points")
	
	@commands.command(aliases = ["server_setting"])
	@checks.is_server_owner()
	async def server_settings(self, ctx, setting : str, on_off : bool):
		'''WIP'''
		with open(clients.data_path + "/server_data/{}/settings.json".format(ctx.guild.id), 'r') as settings_file:
			data = json.load(settings_file)
		if setting in data:
			data[setting] = on_off
		else:
			await ctx.embed_reply("Setting not found")
			return
		with open(clients.data_path + "/server_data/{}/settings.json".format(ctx.guild.id), 'w') as settings_file:
			json.dump(data, settings_file, indent = 4)
		await ctx.embed_reply("{} set to {}".format(setting, on_off))
	
	@commands.command()
	@commands.is_owner()
	async def servers(self, ctx):
		'''Every server I'm in'''
		for guild in self.bot.guilds:
			embed = discord.Embed(color = ctx.bot.bot_color)
			embed.description = (f"```Name: {guild.name}\n"
									f"ID: {guild.id}\n"
									f"Owner: {guild.owner} ({guild.owner.id})\n"
									f"Server Region: {guild.region}\n"
									f"Members: {guild.member_count}\n"
									f"Created at: {guild.created_at}\n```")
			embed.set_thumbnail(url = guild.icon_url)
			await ctx.whisper(embed = embed)
	
	@commands.command(aliases = ["setprefixes"])
	@checks.is_permitted()
	async def setprefix(self, ctx, *prefixes : str):
		'''
		Set the bot prefix(es)
		For the server or for DMs
		Separate prefixes with spaces
		Use quotation marks for prefixes with spaces
		'''
		if not prefixes:
			prefixes = ['!']
		with open(clients.data_path + "/prefixes.json", 'r') as prefixes_file:
			all_prefixes = json.load(prefixes_file)
		if isinstance(ctx.channel, discord.DMChannel):
			all_prefixes[ctx.channel.id] = prefixes
		else:
			all_prefixes[ctx.guild.id] = prefixes
		with open(clients.data_path + "/prefixes.json", 'w') as prefixes_file:
			json.dump(all_prefixes, prefixes_file, indent = 4)
		await ctx.embed_reply("Prefix(es) set: {}".format(' '.join(['`"{}"`'.format(prefix) for prefix in prefixes])))
	
	@commands.command(aliases = ["typing"], hidden = True)
	@checks.not_forbidden()
	async def type(self, ctx):
		'''Sends typing status'''
		# TODO: Add seconds option
		await ctx.trigger_typing()
	
	# Public Info
	
	# TODO: Move to info cog
	# aliases = ["info"]
	@commands.command()
	async def about(self, ctx):
		'''About me'''
		changes = git.Repo("..").git.log("-3", "--first-parent", 
											format = "[`%h`](https://github.com/Harmon758/Harmonbot/commit/%H) %s (%cr)")
		discord_py_version = pkg_resources.get_distribution("discord.py").version
		embed = discord.Embed(title = "About Me", color = ctx.bot.bot_color)
		embed.description = "[Changelog (Harmonbot Server)]({})\n[Invite Link]({})".format(self.bot.changelog, discord.utils.oauth_url(ctx.bot.application_info_data.id))
		# avatar = ctx.author.avatar_url
		# embed.set_author(name = ctx.author.display_name, icon_url = avatar)
		avatar = self.bot.user.avatar_url
		# embed.set_thumbnail(url = avatar)
		embed.set_author(name = "Harmonbot (Discord ID: {})".format(self.bot.user.id), icon_url = avatar)
		if changes: embed.add_field(name = "Latest Changes:", value = changes, inline = False)
		embed.add_field(name = "Created on:", value = "February 10th, 2016")
		embed.add_field(name = "Version", value = self.bot.version)
		embed.add_field(name = "Library", value = "[discord.py](https://github.com/Rapptz/discord.py) v{0}\n([Python](https://www.python.org/) v{1.major}.{1.minor}.{1.micro})".format(discord_py_version, sys.version_info))
		owner = discord.utils.get(self.bot.get_all_members(), id = self.bot.owner_id)
		embed.set_footer(text = "Developer/Owner: {0} (Discord ID: {0.id})".format(owner), icon_url = owner.avatar_url)
		await ctx.reply("", embed = embed)
		await ctx.send("Changelog (Harmonbot Server): {}".format(self.bot.changelog))
	
	@commands.command()
	async def changelog(self, ctx):
		'''Link to changelog'''
		await ctx.reply(self.bot.changelog)
	
	@commands.command()
	async def conversions(self, ctx):
		'''All conversion commands'''
		await ctx.embed_reply("**Temperature Unit Conversions**: {0}[c, f, k, r, de]__to__[c, f, k, r, de, n, re, ro]\n"
		"**Weight Unit Conversions**: {0}<unit>__to__<unit>\nunits: [amu, me, bagc, bagpc, barge, kt, ct, clove, crith, da, drt, drav, ev, gamma, gr, gv, longcwt, cwt, shcwt, kg, kip, mark, mite, mitem, ozt, ozav, oz, dwt, pwt, point, lb, lbav, lbm, lbt, quarterimp, quarterinf, quarterlinf, q, sap, sheet, slug, st, atl, ats, longtn, ton, shtn, t, wey, g]".format(ctx.prefix), title = "Conversion Commands")
	
	@commands.command(aliases = ["oauth"])
	async def invite(self, ctx):
		'''Link to invite me to a server'''
		await ctx.embed_reply(discord.utils.oauth_url(ctx.bot.application_info_data.id))
	
	@commands.command()
	async def stats(self, ctx):
		'''Bot stats'''
		with open(clients.data_path + "/stats.json", 'r') as stats_file:
			stats = json.load(stats_file)
		
		now = datetime.datetime.utcnow()
		uptime = now - clients.online_time
		uptime = utilities.secs_to_letter_format(int(uptime.total_seconds()))
		total_members = sum(len(g.members) for g in self.bot.guilds)
		total_members_online = sum(1 for m in self.bot.get_all_members() if m.status != discord.Status.offline)
		unique_members = set(self.bot.get_all_members())
		unique_members_online = sum(1 for m in unique_members if m.status != discord.Status.offline)
		channel_types = [type(c) for c in self.bot.get_all_channels()]
		text_count = channel_types.count(discord.TextChannel)
		voice_count = channel_types.count(discord.VoiceChannel)
		total_uptime = utilities.secs_to_letter_format(int(stats["uptime"]))
		top_commands = sorted(stats["commands_usage"].items(), key = lambda i: i[1], reverse = True)
		session_top_5 = sorted(self.bot.session_commands_usage.items(), key = lambda i: i[1], reverse = True)[:5]
		in_voice_count = len(self.bot.cogs["Audio"].players)
		playing_in_voice_count = sum(player.current is not None and player.current["stream"].is_playing() for player in self.bot.cogs["Audio"].players.values())
		
		embed = discord.Embed(description = "__**Stats**__ :bar_chart:", color = ctx.bot.bot_color)
		embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url) # url?
		embed.add_field(name = "Uptime", value = uptime)
		embed.add_field(name = "Total Recorded Uptime", value = total_uptime) ## since 2016-04-17, fixed 2016-05-10
		embed.add_field(name = "Recorded Restarts", value = "{:,}".format(stats["restarts"])) ## since 2016-04-17, fixed 2016-05-10
		embed.add_field(name = "Main Commands", value = len(set(self.bot.commands.values())))
		embed.add_field(name = "Commands Executed", 
			value = "{} this session\n{:,} total recorded".format(self.bot.session_commands_executed, stats["commands_executed"])) 
		# since 2016-06-10 (cog commands)
		embed.add_field(name = "Cogs Reloaded", value = "{:,}".format(stats["cogs_reloaded"])) ## since 2016-06-10 - implemented cog reloading
		# TODO: cogs reloaded this session
		embed.add_field(name = "Servers", value = len(self.bot.guilds))
		embed.add_field(name = "Channels", value = "{} text\n{} voice (playing in {}/{})".format(text_count, voice_count, playing_in_voice_count, in_voice_count))
		embed.add_field(name = "Members", 
			value = "{:,} total\n({:,} online)\n{:,} unique\n({:,} online)".format(total_members, total_members_online, len(unique_members), unique_members_online))
		embed.add_field(name = "Top Commands Executed", 
			value = "\n".join("{:,} {}".format(uses, command) for command, uses in top_commands[:5])) ## since 2016-11-14
		embed.add_field(name = "(Total Recorded)", 
			value = "\n".join("{:,} {}".format(uses, command) for command, uses in top_commands[5:10])) ## since 2016-11-14
		if session_top_5: embed.add_field(name = "(This Session)", 
			value = "\n".join("{:,} {}".format(uses, command) for command, uses in session_top_5))
		await ctx.send(embed = embed)
	
	@commands.command()
	async def uptime(self, ctx):
		'''Bot uptime'''
		now = datetime.datetime.utcnow()
		uptime = now - clients.online_time
		await ctx.embed_reply(utilities.secs_to_letter_format(uptime.total_seconds()))
	
	@commands.group(invoke_without_command = True)
	async def version(self, ctx):
		'''Bot version'''
		await ctx.embed_reply("I am Harmonbot `v{}`".format(self.bot.version))
	
	@version.command(name = "ffmpeg")
	async def version_ffmpeg(self, ctx):
		'''FFmpeg version'''
		output = subprocess.run("bin\\ffmpeg -version", capture_output = True, 
								creationflags = subprocess.CREATE_NO_WINDOW).stdout
		await ctx.embed_reply(clients.code_block.format(output.decode("UTF-8")))
	
	@version.command(name = "library", aliases = ["requirement"])
	@commands.is_owner()
	async def version_library(self, ctx, library : str):
		try:
			await ctx.embed_reply(pkg_resources.get_distribution(library).version)
		except pkg_resources.DistributionNotFound as e:
			await ctx.embed_reply(":no_entry: Error: {}".format(e))
	
	@version.command(name = "opus", aliases = ["libopus"])
	async def version_opus(self, ctx):
		discord.opus._lib.opus_get_version_string.restype = ctypes.c_char_p  # Necessary?
		await ctx.embed_reply(discord.opus._lib.opus_get_version_string().decode("UTF-8"))
	
	
	# Update Bot Stuff
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def harmonbot(self, ctx):
		'''Me'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	@harmonbot.group(name = "activity", aliases = ["game", "playing", "status"], invoke_without_command = True)
	@commands.guild_only()
	@checks.not_forbidden()
	async def harmonbot_activity(self, ctx, *, name : str = ""):
		'''My activity'''
		# TODO: Handle in DMs
		activity = ctx.me.activity
		if not name:
			await ctx.embed_reply(activity.name)
		elif checks.is_owner_check(ctx):
			if not activity:
				activity = discord.Activity(name = name, type = discord.ActivityType.playing)
			else:
				activity.name = name
			await self.bot.change_presence(activity = activity)
			await ctx.embed_reply("Activity updated")
		else:
			raise commands.NotOwner
	
	@harmonbot_activity.command(name = "clear")
	@commands.is_owner()
	@commands.guild_only()
	async def harmonbot_activity_clear(self, ctx):
		'''Clear my activity'''
		if ctx.me.activity:
			await self.bot.change_presence() # status
			await ctx.embed_reply("Activity cleared")
		else:
			await ctx.embed_reply(":no_entry: There is no activity to clear")
	
	@harmonbot_activity.command(name = "random", hidden = True)
	@commands.guild_only()
	@checks.not_forbidden()
	async def harmonbot_activity_random(self, ctx):
		'''Change my activity to a random one'''
		activity = ctx.me.activity
		if not activity:
			activity = discord.Activity(name = random.choice(self.bot.game_statuses), type = discord.ActivityType.playing)
		else:
			activity.name = random.choice(self.bot.game_statuses)
		await self.bot.change_presence(activity = activity)
		await ctx.embed_reply("I changed my activity to a random one")
	
	@harmonbot_activity.command(name = "type")
	@commands.guild_only()
	@checks.not_forbidden()
	async def harmonbot_activity_type(self, ctx, type : str = ""):
		'''
		My activity type
		Valid types: playing, streaming, listening, watching
		'''
		activity = ctx.me.activity
		if not type:
			await ctx.embed_reply(str(activity.type).replace("ActivityType.", ""))
		elif checks.is_owner_check(ctx):
			# TODO: lowercase converter
			if type.lower() in ("play", "stream", "listen", "watch"):
				type = type.lower() + "ing"
			if type.lower() in ("playing", "streaming", "listening", "watching"):
				activity_type = getattr(discord.ActivityType, type.lower())
				if not activity:
					activity = discord.Activity(name = random.choice(self.bot.game_statuses), type = activity_type)
				else:
					activity = discord.Activity(name = activity.name, url = activity.url, type = activity_type)
				if type.lower() == "streaming" and not activity.url:
					activity.url = self.bot.stream_url
				await self.bot.change_presence(activity = activity)
				await ctx.embed_reply("Updated activity type")
			else:
				await ctx.embed_reply(":no_entry: That's not a valid activity type")
		else:
			raise commands.NotOwner
	
	@harmonbot_activity.command(name = "url")
	@commands.guild_only()
	@checks.not_forbidden()
	async def harmonbot_activty_url(self, ctx, url : str = ""):
		'''My activity url'''
		activity = ctx.me.activity
		if not url:
			await ctx.embed_reply(activity.url)
		elif checks.is_owner_check(ctx):
			if not activity:
				activity = discord.Stream(name = random.choice(self.bot.game_statuses), url = url)
			else:
				activity.url = url
			await self.bot.change_presence(activity = activity)
			await ctx.embed_reply("Updated activity url")
		else:
			raise commands.NotOwner
	
	@harmonbot.command(name = "avatar")
	@checks.not_forbidden()
	async def harmonbot_avatar(self, ctx, filename : str = ""):
		'''My avatar'''
		if not filename:
			await ctx.embed_reply(title = "My avatar", image_url = ctx.me.avatar_url)
		elif checks.is_owner_check(ctx):
			if not os.path.isfile(clients.data_path + "/avatars/{}".format(filename)):
				await ctx.embed_reply(":no_entry: Avatar not found")
				return
			with open(clients.data_path + "/avatars/{}".format(filename), "rb") as avatar_file:
				await self.bot.user.edit(avatar = avatar_file.read())
			await ctx.embed_reply("Updated avatar")
		else:
			raise commands.NotOwner
	
	@harmonbot.command(name = "nickname")
	@commands.guild_only()
	@checks.not_forbidden()
	async def harmonbot_nickname(self, ctx, *, nickname : str = ""):
		'''My nickname'''
		if not nickname:
			await ctx.embed_reply(ctx.me.nick)
		elif checks.is_owner_check(ctx):
			await ctx.me.edit(nick = nickname)
		else:
			raise commands.NotOwner
	
	@commands.command(hidden = True)
	@commands.is_owner()
	async def update_listing_stats(self, ctx, site = None):
		'''
		Update stats on sites listing Discord bots
		Discord Bots (https://discord.bots.gg/)
		Discord Bot List (https://discordbots.org/)
		Discord Bot List (https://discordbotlist.com/)
		'''
		if site:
			response = await ctx.bot.update_listing_stats(site)
			title = title_url = discord.Embed.Empty
			if site in ctx.bot.listing_sites:
				title = ctx.bot.listing_sites[site]["name"]
				title_url = f"https://{site}/"
			await ctx.embed_reply(f"`{response}`", title = title, title_url = title_url)
		else:
			output = []
			for site, site_info in ctx.bot.listing_sites.items():
				response = await ctx.bot.update_listing_stats(site)
				output.append(f"{site_info['name']} (https://{site}/): `{response}`")
			await ctx.embed_reply('\n'.join(output))
	
	# Restart/Shutdown
	
	@commands.command()
	@commands.is_owner()
	async def restart(self, ctx):
		'''Restart me'''
		await ctx.embed_say(":ok_hand::skin-tone-2: Restarting...")
		print("Shutting down Discord Harmonbot...")
		await ctx.bot.restart_tasks(ctx.channel.id)
		await ctx.bot.logout()
	
	@commands.command(aliases = ["crash", "panic"])
	@commands.is_owner()
	async def shutdown(self, ctx):
		'''Shut me down'''
		await ctx.embed_say(":scream: Shutting down.")
		print("Forcing Shutdown...")
		await ctx.bot.shutdown_tasks()
		subprocess.call(["taskkill", "/f", "/im", "cmd.exe"])
		subprocess.call(["taskkill", "/f", "/im", "python.exe"])
	
	# Testing
	
	@commands.group(hidden = True, invoke_without_command = True)
	@checks.not_forbidden()
	async def test(self, ctx):
		'''Basic test command'''
		await ctx.send("Hello, World!")
	
	@test.command(name = "global_rate_limit", aliases = ["globalratelimit"])
	@commands.is_owner()
	async def test_global_rate_limit(self, ctx):
		'''Used to test global rate limits'''
		for i in range(1, 101):
			async for message in ctx.history():
				pass
			print(f"global ratelimit test {i}")
	
	@test.command(name = "on_message")
	async def test_on_message(self, ctx):
		'''Test on_message event'''
		# Implemented in on_message
		return
	
	@commands.group(aliases = ["code_block"], invoke_without_command = True)
	@checks.not_forbidden()
	async def codeblock(self, ctx, *, input : str):
		'''Wrap your message in a code block'''
		await ctx.embed_reply(clients.code_block.format(input))
	
	@codeblock.command(name = "python", aliases = ["py"])
	@checks.not_forbidden()
	async def codeblock_python(self, ctx, *, input : str):
		'''Wrap your message in a Python code block'''
		await ctx.embed_reply(clients.py_code_block.format(input))
	
	@commands.command()
	@commands.is_owner()
	async def do(self, ctx, times : int, *, command):
		'''Repeats a command a specified number of times'''
		msg = copy.copy(ctx.message)
		msg.content = command
		for _ in range(times):
			await self.bot.process_commands(msg)
	
	@commands.group(aliases = ["say"], invoke_without_command = True)
	@commands.is_owner()
	async def echo(self, ctx, *, message):
		'''Echoes the message'''
		await ctx.send(message)
	
	@echo.command(name = "embed")
	@commands.is_owner()
	async def echo_embed(self, ctx, *, message):
		'''Echoes the message in an embed'''
		await ctx.embed_say(message)
	
	@commands.command()
	@commands.is_owner()
	async def eval(self, ctx, *, code : str):
		code = code.strip('`')
		try:
			result = eval(code)
			if inspect.isawaitable(result):
				result = await result
			await ctx.reply(clients.py_code_block.format(result))
		except Exception as e:
			await ctx.reply(clients.py_code_block.format("{}: {}".format(type(e).__name__, e)))
	
	@commands.command()
	@commands.is_owner()
	async def exec(self, ctx, *, code : str):
		code = code.strip('`')
		try:
			exec(code)
		except Exception as e:
			await ctx.reply(clients.py_code_block.format("{}: {}".format(type(e).__name__, e)))
			return
		await ctx.embed_reply("Successfully executed")
	
	@commands.command(aliases = ["deletetest"])
	@commands.is_owner()
	async def delete_test(self, ctx):
		'''Sends 100 messages'''
		for i in range(1, 101):
			await ctx.send(i)
	
	@commands.command(aliases = ["repeattext"])
	@commands.is_owner()
	async def repeat_text(self, ctx, number : int, *, text):
		'''Repeat text'''
		for _ in range(number):
			await ctx.send(text)
	
	@commands.command()
	@commands.is_owner()
	async def repl(self, ctx):
		variables = {"self" : self, "ctx" : ctx, "last" : None}
		await ctx.embed_reply("Enter code to execute or evaluate\n`exit` or `quit` to exit")
		while True:
			message = await self.bot.wait_for("message", check = lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.startswith('`'))
			if message.content.startswith("```py") and message.content.endswith("```"):
				code = message.content[5:-3].strip(" \n")
			else:
				code = message.content.strip("` \n")
			if code in ("quit", "exit", "quit()", "exit()"):
				await ctx.embed_reply('Exiting repl')
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
					await ctx.reply(clients.py_code_block.format("{0.text}{1:>{0.offset}}\n{2}: {0}".format(e, '^', type(e).__name__)))
					continue
			try:
				result = function(code, variables)
				if inspect.isawaitable(result):
					result = await result
			except:
				await ctx.reply(clients.py_code_block.format("\n".join(traceback.format_exc().splitlines()[-2:]).strip()))
			else:
				if function is eval:
					try:
						await ctx.reply(clients.py_code_block.format(result))
					except Exception as e:
						await ctx.reply(clients.py_code_block.format("{}: {}".format(type(e).__name__, e)))
				variables["last"] = result
	
	@commands.command(aliases = ["github"])
	@checks.not_forbidden()
	async def source(self, ctx, *, command : str = ""):
		'''
		Displays my full source code or for a specific command
		To display the source code of a subcommand, separate it by spaces or periods
		Based on [R. Danny](https://github.com/Rapptz/RoboDanny)'s source command
		'''
		source_url = "https://github.com/Harmon758/Harmonbot"
		if not command:
			return await ctx.embed_reply(source_url)
		
		obj = ctx.bot.get_command(command.replace('.', ' '))
		if obj is None:
			return await ctx.embed_reply("\N{NO ENTRY} Command not found")
		
		# Access code
		src = obj.callback.__code__
		lines, firstlineno = inspect.getsourcelines(src)
		## if not obj.callback.__module__.startswith("discord"):
		## 	# not a built-in command
		location = os.path.relpath(src.co_filename).replace('\\', '/')
		## else:
		## 	location = obj.callback.__module__.replace('.', '/') + ".py"
		## 	source_url = "https://github.com/Rapptz/discord.py"
		branch = git.Repo("..").active_branch.name
		final_url = f"{source_url}/blob/{branch}/Discord/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}"
		await ctx.embed_reply(final_url)

