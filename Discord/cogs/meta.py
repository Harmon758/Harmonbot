
import discord
from discord import app_commands
from discord.ext import commands

import asyncio
import datetime
import copy
import ctypes
import importlib.metadata
import inspect
import os
import random
import subprocess
import sys
import traceback
from typing import Optional

import chess.engine
import git
import psutil

from cogs.chess import STOCKFISH_EXECUTABLE
from utilities import checks

sys.path.insert(0, "..")
from units.time import duration_to_string
sys.path.pop(0)

async def setup(bot):
	await bot.add_cog(Meta(bot))
	bot.tree.add_command(link, override = True)
	bot.tree.add_command(avatar, override = True)

class Meta(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
	
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
		process.cpu_percent()
		message = await ctx.embed_reply(fields = (("RAM", f"{process.memory_info().rss / 2 ** 20:.2f} MiB"), 
													("CPU", "Calculating CPU usage..")))
		await asyncio.sleep(1)
		embed = message.embeds[0]
		embed.set_field_at(1, name = "CPU", value = f"{process.cpu_percent() / psutil.cpu_count():.5g}%")
		await message.edit(embed = embed)
	
	@commands.command(aliases = ["category"])
	@checks.not_forbidden()
	async def cog(self, ctx, command):
		'''Find what cog/category a command is in'''
		if command not in self.bot.all_commands:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: command not found")
		await ctx.embed_reply(self.bot.all_commands[command].cog_name)
	
	@commands.command()
	@commands.is_owner()
	async def disable(self, ctx, command: str):
		'''Disable a command'''
		self.bot.all_commands[command].enabled = False
		await ctx.embed_reply(f"`{ctx.prefix}{command}` has been disabled")
	
	@commands.command()
	@commands.is_owner()
	async def enable(self, ctx, command: str):
		'''Enable a command'''
		self.bot.all_commands[command].enabled = True
		await ctx.embed_reply(f"`{ctx.prefix}{command}` has been enabled")
	
	@commands.command()
	async def points(self, ctx):
		'''WIP'''
		commands_invoked = await ctx.bot.db.fetchval(
			"""
			SELECT commands_invoked
			FROM users.stats
			WHERE user_id = $1
			""", 
			ctx.author.id
		)
		await ctx.embed_reply(f"You have {commands_invoked} points")
	
	@commands.command()
	@commands.is_owner()
	async def servers(self, ctx):
		'''Every server I'm in'''
		for guild in self.bot.guilds:
			embed = discord.Embed(color = ctx.bot.bot_color)
			embed.description = (f"```Name: {guild.name}\n"
									f"ID: {guild.id}\n"
									f"Owner: {guild.owner} ({guild.owner.id})\n"
									f"Members: {guild.member_count}\n"
									f"Created at: {guild.created_at}\n```")
			embed.set_thumbnail(url = guild.icon.url)
			await ctx.whisper(embed = embed)
	
	@commands.command(aliases = ["setprefixes"])
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def setprefix(self, ctx, *prefixes: str):
		'''
		Set the bot prefix(es)
		For the server or for DMs
		Separate prefixes with spaces
		Use quotation marks for prefixes with spaces
		'''
		if not prefixes:
			prefixes = ['!']
		if ctx.channel.type is discord.ChannelType.private:
			await ctx.bot.db.execute(
				"""
				INSERT INTO direct_messages.prefixes (channel_id, prefixes)
				VALUES ($1, $2)
				ON CONFLICT (channel_id) DO
				UPDATE SET prefixes = $2
				""", 
				ctx.channel.id, prefixes
			)
		else:
			await ctx.bot.db.execute(
				"""
				INSERT INTO guilds.prefixes (guild_id, prefixes)
				VALUES ($1, $2)
				ON CONFLICT (guild_id) DO
				UPDATE SET prefixes = $2
				""", 
				ctx.guild.id, prefixes
			)
		await ctx.embed_reply("Prefix(es) set: " + ' '.join(f'`"{prefix}"`' for prefix in prefixes))
	
	@commands.group(aliases = ["shard"], case_insensitive = True, invoke_without_command = True)
	async def shards(self, ctx):
		'''Current number of shards'''
		await ctx.embed_reply(ctx.bot.shard_count or 1)
	
	@shards.command(aliases = ["recommend"])
	async def recommended(self, ctx):
		'''Recommended number of shards to use by Discord API'''
		count, _ = await ctx.bot.http.get_bot_gateway()
		await ctx.embed_reply(count)
	
	@commands.command(aliases = ["typing"], hidden = True)
	@checks.not_forbidden()
	async def type(self, ctx):
		'''Sends typing status'''
		# TODO: Add seconds option
		await ctx.trigger_typing()
	
	# Public Info
	
	@commands.command()
	async def about(self, ctx):
		'''About me'''
		fields = []
		if (changes := git.Repo("..").git.log(
			"-3", "--first-parent", 
			format = "[`%h`](https://github.com/Harmon758/Harmonbot/commit/%H) %s (<t:%ct:R>)"
		)):
			fields.append(("Latest Changes:", changes, False))
		created_time = discord.utils.snowflake_time(147207200945733632)
		fields.append((
			"Created on:", discord.utils.format_dt(created_time, style = 'D')
		))
		fields.append(("Version", ctx.bot.version))
		fields.append((
			"Library", 
			f"[discord.py](https://github.com/Rapptz/discord.py) v{importlib.metadata.version('discord.py')}\n"
			f"([Python](https://www.python.org/) v{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro})"
		))
		if not (owner := discord.utils.get(ctx.bot.get_all_members(), id = ctx.bot.owner_id)):
			owner = await ctx.bot.fetch_user(ctx.bot.owner_id)
		
		view = discord.ui.View()
		view.add_item(discord.ui.Button(
			label = "Invite", 
			url = ctx.bot.invite_url
		))
		view.add_item(discord.ui.Button(
			label = "Discord Server (#changelog)", 
			url = ctx.bot.changelog
		))
		
		# TODO: Move out of command?
		class ServerInviteButton(discord.ui.Button):
			async def callback(self, interaction):
				await interaction.response.send_message(
					f"{interaction.user.mention}: Harmonbot Discord Server (#changelog): {ctx.bot.changelog}"
				)
		
		view.add_item(ServerInviteButton(
			label = "Send Discord Server Invite", 
			style = discord.ButtonStyle.blurple
		))
		
		await ctx.embed_reply(
			author_icon_url = ctx.bot.user.display_avatar.url,
			author_name = f"Harmonbot (Discord ID: {ctx.bot.user.id})",
			title = "About Me",
			fields = fields,
			footer_icon_url = owner.display_avatar.url,
			footer_text = f"Developer/Owner: {owner} (Discord ID: {owner.id})",
			view = view
		)
	
	@commands.command()
	async def changelog(self, ctx):
		'''Link to changelog'''
		await ctx.message.reply(ctx.bot.changelog)
	
	@commands.command()
	async def conversions(self, ctx):
		'''All conversion commands'''
		await ctx.embed_reply(f"**Temperature Unit Conversions**: {ctx.prefix}[c, f, k, r, de]__to__[c, f, k, r, de, n, re, ro]\n"
								f"**Weight Unit Conversions**: {ctx.prefix}<unit>__to__<unit>\n"
								"units: [amu, me, bagc, bagpc, barge, kt, ct, clove, crith, da, drt, drav, ev, gamma, gr, gv, longcwt, cwt, shcwt, kg, kip, mark, mite, mitem, ozt, ozav, oz, dwt, pwt, point, lb, lbav, lbm, lbt, quarterimp, quarterinf, quarterlinf, q, sap, sheet, slug, st, atl, ats, longtn, ton, shtn, t, wey, g]", 
								title = "Conversion Commands")
	
	@commands.command(aliases = ["oauth"])
	async def invite(self, ctx):
		'''Link to invite me to a server'''
		await ctx.embed_reply(ctx.bot.invite_url)
	
	@commands.command(aliases = ["ping"])
	async def latency(self, ctx):
		'''Discord WebSocket protocol latency between a HEARTBEAT and a HEARTBEAT_ACK in seconds'''
		if ctx.bot.latency < 1:
			websocket_latency = f"{ctx.bot.latency * 1000:.6} ms"
		else:
			websocket_latency = f"{ctx.bot.latency:.6} s"
		await ctx.embed_reply(
			title = "Pong" if ctx.invoked_with == "ping" else None,
			fields = (("Discord WebSocket Latency", websocket_latency),)
		)
	
	@commands.command()
	async def stats(self, ctx):
		'''
		Bot stats
		Total uptime and restarts recorded since 2016-04-17
		Total commands invoked and cogs reloaded recorded since 2016-06-10
		Top total commands invoked recorded since 2016-11-14
		'''
		stats = await ctx.bot.db.fetchrow(
			"""
			SELECT * FROM meta.stats
			WHERE timestamp = $1
			""", 
			ctx.bot.online_time
		)
		records = await ctx.bot.db.fetch(
			"""
			SELECT * FROM meta.commands_invoked
			ORDER BY invokes DESC
			LIMIT 10
			"""
		)
		
		channel_types = [type(c) for c in ctx.bot.get_all_channels()]
		voice_count = channel_types.count(discord.VoiceChannel)
		playing_in_voice_count = sum(vc.is_playing() for vc in ctx.bot.voice_clients)
		in_voice_count = len(ctx.bot.cogs["Audio"].players)
		total_members = sum(len(g.members) for g in ctx.bot.guilds)
		total_members_online = sum(1 for m in ctx.bot.get_all_members() if m.status != discord.Status.offline)
		unique_members = set(ctx.bot.get_all_members())
		unique_members_online = sum(1 for m in unique_members if m.status != discord.Status.offline)
		top_commands = [(record["command"], record["invokes"]) for record in records]
		session_top_5 = sorted(ctx.bot.session_commands_invoked.items(), key = lambda i: i[1], reverse = True)[:5]
		
		fields = [("Uptime", duration_to_string(datetime.datetime.now(datetime.timezone.utc) - ctx.bot.online_time, abbreviate = True)), 
					("Total Recorded Uptime", duration_to_string(stats["uptime"], abbreviate = True)), 
					("Recorded Restarts", f"{stats['restarts']:,}"), 
					("Commands", f"{len(ctx.bot.commands)} main\n{len(set(ctx.bot.walk_commands()))} total"), 
					("Commands Invoked", f"{sum(ctx.bot.session_commands_invoked.values())} this session\n"
											f"{stats['commands_invoked']:,} total recorded"), 
					("Cogs Reloaded", f"{stats['cogs_reloaded']:,}"),  # TODO: cogs reloaded this session
					("Servers", len(ctx.bot.guilds)), 
					("Channels", f"{channel_types.count(discord.TextChannel)} text\n"
									f"{voice_count} voice (playing in {playing_in_voice_count}/{in_voice_count})"), 
					("Members (Online)", f"{total_members:,} total ({total_members_online:,})\n"
											f"{len(unique_members):,} unique ({unique_members_online:,})")]
		if top_commands[:5]:
			fields.append(("Top Commands Invoked", '\n'.join(f"{uses:,} {command}" for command, uses in top_commands[:5])))
		if top_commands[5:10]:
			fields.append(("(Total Recorded)", '\n'.join(f"{uses:,} {command}" for command, uses in top_commands[5:10])))
		if session_top_5:
			fields.append(("(This Session)", '\n'.join(f"{uses:,} {command}" for command, uses in session_top_5)))
		await ctx.embed_reply("__**Stats**__ :bar_chart:", fields = fields)
	
	@commands.command()
	async def uptime(self, ctx):
		'''Bot uptime'''
		await ctx.embed_reply(duration_to_string(datetime.datetime.now(datetime.timezone.utc) - ctx.bot.online_time, 
													abbreviate = True))
	
	@commands.group(case_insensitive = True, invoke_without_command = True)
	async def version(self, ctx):
		'''Bot version'''
		await ctx.embed_reply(f"I am Harmonbot `v{self.bot.version}`")
	
	@version.command(name = "ffmpeg")
	async def version_ffmpeg(self, ctx):
		'''FFmpeg version'''
		output = subprocess.run("bin/ffmpeg -version", capture_output = True, 
								creationflags = subprocess.CREATE_NO_WINDOW).stdout
		await ctx.embed_reply(ctx.bot.CODE_BLOCK.format(output.decode("UTF-8")))
	
	@version.command(name = "library", aliases = ["requirement"])
	@commands.is_owner()
	async def version_library(self, ctx, library: str):
		try:
			await ctx.embed_reply(importlib.metadata.version(library))
		except importlib.metadata.PackageNotFoundError:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {library} library not found")
	
	@version.command(name = "opus", aliases = ["libopus"])
	async def version_opus(self, ctx):
		discord.opus._lib.opus_get_version_string.restype = ctypes.c_char_p  # Necessary?
		await ctx.embed_reply(discord.opus._lib.opus_get_version_string().decode("UTF-8"))
	
	@version.command(name = "postgresql", aliases = ["database"])
	async def version_postgresql(self, ctx):
		postgresql_version = await ctx.bot.db.fetchval("SELECT version()")
		await ctx.embed_reply(postgresql_version)
	
	@version.command(name = "stockfish")
	async def version_stockfish(self, ctx):
		transport, engine = await chess.engine.popen_uci(f"bin/{STOCKFISH_EXECUTABLE}", creationflags = subprocess.CREATE_NO_WINDOW)
		await ctx.embed_reply(engine.id["name"])
	
	# Update Bot Stuff
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def harmonbot(self, ctx):
		'''
		Me
		Also see help and about commands
		'''
		await ctx.send_help(ctx.command)
	
	@harmonbot.group(name = "activity", aliases = ["game", "playing", "status"], 
						invoke_without_command = True, case_insensitive = True)
	@commands.guild_only()
	@checks.not_forbidden()
	async def harmonbot_activity(self, ctx, *, name : str = ""):
		'''My activity'''
		# TODO: Handle in DMs
		activity = ctx.me.activity
		if not name:
			return await ctx.embed_reply(activity.name)
		try:
			is_owner = await commands.is_owner().predicate(ctx)
		except commands.NotOwner:
			is_owner = False
		if is_owner:
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
			return await ctx.embed_reply(str(activity.type).replace("ActivityType.", ""))
		try:
			is_owner = await commands.is_owner().predicate(ctx)
		except commands.NotOwner:
			is_owner = False
		if is_owner:
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
			return await ctx.embed_reply(activity.url)
		try:
			is_owner = await commands.is_owner().predicate(ctx)
		except commands.NotOwner:
			is_owner = False
		if is_owner:
			if not activity:
				activity = discord.Streaming(name = random.choice(self.bot.game_statuses), url = url)
			else:
				activity.url = url
			await self.bot.change_presence(activity = activity)
			await ctx.embed_reply("Updated activity url")
		else:
			raise commands.NotOwner
	
	@harmonbot.command(name = "avatar")
	@checks.not_forbidden()
	async def harmonbot_avatar(self, ctx, filename: Optional[str]):
		'''My avatar'''
		if not filename:
			await ctx.embed_reply(
				title = "My avatar",
				image_url = ctx.me.display_avatar.url
			)
			return
		
		await commands.is_owner().predicate(ctx)  # Raises if not owner
		
		# TODO: Change avatar by file upload?
		if not os.path.isfile(f"{self.bot.data_path}/avatars/{filename}"):
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Avatar not found")
			return
		
		with open(f"{self.bot.data_path}/avatars/{filename}", "rb") as avatar_file:
			await self.bot.user.edit(avatar = avatar_file.read())
		
		await ctx.embed_reply("Updated avatar")
	
	@harmonbot.command(name = "nickname")
	@commands.guild_only()
	@checks.not_forbidden()
	async def harmonbot_nickname(self, ctx, *, nickname : str = ""):
		'''My nickname'''
		if not nickname:
			return await ctx.embed_reply(ctx.me.nick)
		try:
			is_owner = await commands.is_owner().predicate(ctx)
		except commands.NotOwner:
			is_owner = False
		if is_owner:
			await ctx.me.edit(nick = nickname)
		else:
			raise commands.NotOwner
	
	@commands.group(
		case_insensitive = True, hidden = True, invoke_without_command = True
	)
	@commands.is_owner()
	async def sync_tree(self, ctx):
		synced = await ctx.bot.tree.sync()
		await ctx.embed_reply(
			title = "Synced",
			description = ctx.bot.PY_CODE_BLOCK.format(synced)
		)
	
	@sync_tree.command(name = "guild", hidden = True)
	@commands.is_owner()
	async def sync_tree_guild(self, ctx):
		synced = await ctx.bot.tree.sync(guild = ctx.guild)
		await ctx.embed_reply(
			title = "Synced",
			description = ctx.bot.PY_CODE_BLOCK.format(synced)
		)
	
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
			title = title_url = None
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
		restart_message = await ctx.embed_send(f"\N{OK HAND SIGN}{ctx.bot.emoji_skin_tone} Restarting...")
		print("Shutting down Discord Harmonbot...")
		await ctx.bot.restart_tasks(ctx.channel.id, restart_message.id)
		await ctx.bot.close()
	
	@commands.command(aliases = ["crash", "panic"])
	@commands.is_owner()
	async def shutdown(self, ctx):
		'''Shut me down'''
		await ctx.embed_send(":scream: Shutting down.")
		print("Forcing Shutdown...")
		await ctx.bot.shutdown_tasks()
		subprocess.call(["taskkill", "/f", "/im", "cmd.exe"])
		subprocess.call(["taskkill", "/f", "/im", "python.exe"])
	
	# Testing
	
	@commands.group(hidden = True, invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def test(self, ctx):
		'''Basic test command'''
		await ctx.send("Hello, World!")
	
	@app_commands.command(name = "test")
	async def slash_test(self, interaction):
		'''Basic test command'''
		await interaction.response.send_message("Hello, World!")
	
	@test.command(name = "delete")
	@commands.is_owner()
	async def test_delete(self, ctx):
		'''Sends 100 messages'''
		for i in range(1, 101):
			await ctx.send(i)
	
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
	
	@commands.group(aliases = ["code_block"], invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def codeblock(self, ctx, *, input: str):
		'''Wrap your message in a code block'''
		await ctx.embed_reply(ctx.bot.CODE_BLOCK.format(input))
	
	@codeblock.command(name = "python", aliases = ["py"])
	@checks.not_forbidden()
	async def codeblock_python(self, ctx, *, input: str):
		'''Wrap your message in a Python code block'''
		await ctx.embed_reply(ctx.bot.PY_CODE_BLOCK.format(input))
	
	@commands.command()
	@commands.is_owner()
	async def do(self, ctx, times : int, *, command):
		'''Repeats a command a specified number of times'''
		msg = copy.copy(ctx.message)
		msg.content = command
		for _ in range(times):
			ctx = await self.bot.get_context(msg)
			await self.bot.invoke(ctx)
	
	@commands.group(aliases = ["say"], invoke_without_command = True, case_insensitive = True)
	@commands.is_owner()
	async def echo(self, ctx, *, message):
		'''Echoes the message'''
		await ctx.send(message)
	
	@echo.command(name = "embed")
	@commands.is_owner()
	async def echo_embed(self, ctx, *, message):
		'''Echoes the message in an embed'''
		await ctx.embed_send(message)
	
	@commands.command()
	@commands.is_owner()
	async def eval(self, ctx, *, code : str):
		code = code.strip('`')
		try:
			result = eval(code)
			if inspect.isawaitable(result):
				result = await result
			await ctx.reply(ctx.bot.PY_CODE_BLOCK.format(result))
		except Exception as e:
			await ctx.reply(ctx.bot.PY_CODE_BLOCK.format(f"{type(e).__name__}: {e}"))
	
	@commands.command()
	@commands.is_owner()
	async def events(self, ctx):
		'''WebSocket events'''
		await ctx.embed_reply(
			ctx.bot.PY_CODE_BLOCK.format(
				ctx.bot.socket_events
			)
		)
	
	@commands.command()
	@commands.is_owner()
	async def exec(self, ctx, *, code : str):
		code = code.strip('`')
		try:
			exec(code)
			# TODO: await?
		except Exception as e:
			await ctx.reply(ctx.bot.PY_CODE_BLOCK.format(f"{type(e).__name__}: {e}"))
			return
		await ctx.embed_reply("Successfully executed")
	
	@commands.command(name = "query")
	@commands.is_owner()
	async def query_command(self, ctx, *, query):
		'''Query database'''
		result = await ctx.bot.db.fetch(query)
		# TODO: Handle errors, e.g. syntax
		await ctx.embed_reply(result)
		# TODO: Improve result/response format
	
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
					await ctx.reply(ctx.bot.PY_CODE_BLOCK.format(f"{e.text}{'^':>{e.offset}}\n{type(e).__name__}: {e}"))
					continue
			try:
				result = function(code, variables)
				if inspect.isawaitable(result):
					result = await result
			except:
				await ctx.reply(ctx.bot.PY_CODE_BLOCK.format('\n'.join(traceback.format_exc().splitlines()[-2:]).strip()))
			else:
				if function is eval:
					try:
						await ctx.reply(ctx.bot.PY_CODE_BLOCK.format(result))
					except Exception as e:
						await ctx.reply(ctx.bot.PY_CODE_BLOCK.format(f"{type(e).__name__}: {e}"))
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
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Command not found")
		
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
	
	@commands.command()
	@commands.is_owner()
	async def tasks(self, ctx):
		await ctx.embed_reply(', '.join(f"`{task.get_coro().__qualname__}`" 
										if (name := task.get_name()).startswith("Task-") 
										else name for task in asyncio.all_tasks()))


@app_commands.context_menu()
async def link(interaction, message: discord.Message):
	await interaction.response.send_message(message.jump_url)


@app_commands.context_menu()
async def avatar(interaction, user: discord.User):
	await interaction.response.send_message(user.display_avatar.url)

