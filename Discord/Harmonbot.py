
if __name__ == "__main__":
	
	print("Starting up Discord Harmonbot...")
	
	import discord
	from discord.ext import commands
	
	import aiohttp
	from aiohttp import web
	import asyncio
	import json
	import os
	import re
	import sys
	import traceback
	import youtube_dl
	
	import clients
	import credentials
	from clients import client
	from modules import conversions
	from modules import logging
	from modules import utilities
	from utilities import checks
	from utilities import errors
	from utilities import audio_player
	
	clients.create_file('f', content = {"total": 0})
	with open(clients.data_path + "/f.json", 'r') as f_file:
		f_counter_info = json.load(f_file)
	
	mention_spammers = []
	
	@client.listen()
	async def on_ready():
		# data = await client.http.get(client.http.GATEWAY + "/bot")
		# print(data)
		print("Started up Discord {0} ({1})".format(str(client.user), client.user.id))
		if os.path.isfile(clients.data_path + "/temp/restart_channel.json"):
			with open(clients.data_path + "/temp/restart_channel.json", 'r') as restart_channel_file:
				restart_data = json.load(restart_channel_file)
			os.remove(clients.data_path + "/temp/restart_channel.json")
			restart_channel = client.get_channel(restart_data["restart_channel"])
			await client.send_embed(restart_channel, ":thumbsup::skin-tone-2: Restarted")
			for voice_channel in restart_data["voice_channels"]:
				# asyncio.ensure_future(client.cogs["Audio"].start_player(client.get_channel(voice_channel[1])))
				text_channel = client.get_channel(voice_channel[1])
				if text_channel:
					client.cogs["Audio"].players[text_channel.guild.id] = audio_player.AudioPlayer(client, text_channel)
					await client.get_channel(voice_channel[0]).connect()
		'''
		for folder in os.listdir(clients.data_path + "/server_data"):
			with open(clients.data_path + "/server_data/{}/settings.json".format(folder), 'r') as settings_file:
				data = json.load(settings_file)
			data["anti-spam"] = False
			with open(clients.data_path + "/server_data/{}/settings.json".format(folder), 'w') as settings_file:
				json.dump(data, settings_file, indent = 4)
		'''
		for guild in client.guilds:
			clients.create_folder(clients.data_path + "/server_data/{}".format(guild.id))
			clients.create_file("server_data/{}/settings".format(guild.id), content = {"anti-spam": False, "respond_to_bots": False})
			if guild.name:
				clean_name = re.sub(r"[\|/\\:\?\*\"<>]", "", guild.name) # | / \ : ? * " < >
				clients.create_file("server_data/{}/{}".format(guild.id, clean_name))
			# TODO: DM if joined new server
			# TODO: DM if left server
		# await voice.detectvoice()
	
	@client.listen()
	async def on_guild_join(guild):
		clients.create_folder(clients.data_path + "/server_data/{}".format(guild.id))
		clients.create_file("server_data/{}/settings".format(guild.id), content = {"anti-spam": False, "respond_to_bots": False})
		me = discord.utils.get(client.get_all_members(), id = clients.client.owner_id)
		await client.send_embed(me, None, title = "Joined Server", timestamp = guild.created_at, thumbnail_url = guild.icon_url, fields = (("Name", guild.name), ("ID", guild.id), ("Owner", str(guild.owner)), ("Members", str(guild.member_count)), ("Server Region", str(guild.region))))
		clean_name = re.sub(r"[\|/\\:\?\*\"<>]", "", guild.name) # | / \ : ? * " < >
		clients.create_file("server_data/{}/{}".format(guild.id, clean_name))
	
	@client.listen()
	async def on_guild_remove(guild):
		me = discord.utils.get(client.get_all_members(), id = clients.client.owner_id)
		await client.send_embed(me, None, title = "Left Server", timestamp = guild.created_at, thumbnail_url = guild.icon_url, fields = (("Name", guild.name), ("ID", guild.id), ("Owner", str(guild.owner)), ("Members", str(guild.member_count)), ("Server Region", str(guild.region))))
	
	@client.listen()
	async def on_command(ctx):
		with open(clients.data_path + "/stats.json", 'r') as stats_file:
			stats = json.load(stats_file)
		stats["commands_executed"] += 1
		stats["commands_usage"][ctx.command.name] = stats["commands_usage"].get(ctx.command.name, 0) + 1
		with open(clients.data_path + "/stats.json", 'w') as stats_file:
			json.dump(stats, stats_file, indent = 4)
		clients.create_folder(clients.data_path + "/user_data/{}".format(ctx.author.id))
		clients.create_file("user_data/{}/stats".format(ctx.author.id), content = {"commands_executed": 0, "points": 0, "respects_paid": 0})
		# TODO: Transfer respects paid data?
		clean_name = re.sub(r"[\|/\\:\?\*\"<>]", "", ctx.author.name) # | / \ : ? * " < >
		clients.create_file("user_data/{}/{}".format(ctx.author.id, clean_name))
		with open(clients.data_path + "/user_data/{}/stats.json".format(ctx.author.id), "r") as stats_file:
			stats = json.load(stats_file)
		stats["commands_executed"] += 1
		stats["points"] += 1
		with open(clients.data_path + "/user_data/{}/stats.json".format(ctx.author.id), 'w') as stats_file:
			json.dump(stats, stats_file, indent = 4)
	
	# TODO: log message edits
	
	@client.event
	async def on_message(message):
		
		# Log message
		log_entry = "{0.created_at}: [{0.id}] {0.author.display_name} ({0.author}) ({0.author.id}) in ".format(message)
		if isinstance(message.channel, discord.DMChannel):
			log_entry += "Direct Message"
		else:
			log_entry += "#{0.channel.name} ({0.channel.id}) [{0.guild.name} ({0.guild.id})]".format(message)
		log_entry += f": {message.content} {[embed.to_dict() for embed in message.embeds]}"
		logging.chat_logger.info(log_entry)
		
		# Get Context
		ctx = await client.get_context(message)
		
		# Server specific settings
		if message.guild is not None:
			try:
				with open(clients.data_path + "/server_data/{}/settings.json".format(message.guild.id), 'r') as settings_file:
					data = json.load(settings_file)
			except FileNotFoundError:
				# TODO: Handle/Fix, create new file with default settings
				data = {}
			if data.get("anti-spam") and len(message.mentions) > 10:
				global mention_spammers
				if message.author.id in mention_spammers:
					# TODO: Handle across different servers
					if message.guild.me.permissions_in(message.channel).kick_members:
						# TODO: Check hierarchy, if able to kick
						await ctx.author.send("You were kicked from {} for spamming mentions".format(message.guild))
						await client.kick(message.author)
						await ctx.send("{} has been kicked for spamming mentions".format(message.author))
					else:
						await ctx.send("I need permission to kick members from the server to enforce anti-spam")
				else:
					await ctx.embed_reply(":warning: You will be kicked if you continue spamming mentions")
					mention_spammers.append(message.author.id)
					await asyncio.sleep(3600)
					mention_spammers.remove(message.author.id)
			if not data.get("respond_to_bots") and message.author.bot:
				return
		
		# Invoke Commands
		await client.invoke(ctx)
		
		# Forward DMs
		if isinstance(message.channel, discord.DMChannel) and message.channel.recipient.id != ctx.bot.owner_id:
			me = discord.utils.get(client.get_all_members(), id = ctx.bot.owner_id)
			if message.author == client.user:
				try:
					await me.send("To {0.channel.recipient}: {0.content}".format(message), embed = message.embeds[0] if message.embeds else None)
				except discord.HTTPException:
					# TODO: use textwrap/paginate
					await me.send("To {0.channel.recipient}: `DM too long to forward`".format(message))
			else:
				await me.send("From {0.author}: {0.content}".format(message), embed = message.embeds[0] if message.embeds else None)
		
		# Ignore own and blank messages
		if message.author == client.user or not message.content:
			return
		
		# Test on_message command
		if ctx.prefix and message.content.startswith(ctx.prefix + "test on_message"):
			await ctx.send("Hello, World!")
		
		# Conversion commands (regex)
		elif ctx.prefix and not ctx.command:
			units = re.match(r"^(\w+)to(\w+)", message.content[len(ctx.prefix):], re.I)
			if not units: return
			elif len(message.content.split()) == 1:
				await ctx.embed_reply(":no_entry: Please enter input")
			elif not utilities.is_number(message.content.split()[1]):
				await ctx.embed_reply(":no_entry: Syntax error")
			else:
				value = float(message.content.split()[1])
				unit1 = units.group(1)
				unit2 = units.group(2)
				converted_temperature_value, temperature_unit1, temperature_unit2 = conversions.temperatureconversion(value, unit1, unit2)
				converted_mass_value = conversions.massconversion(value, unit1, unit2)
				if converted_temperature_value:
					converted_value = converted_temperature_value
					unit1 = temperature_unit1
					unit2 = temperature_unit2
				elif converted_mass_value:
					converted_value = converted_mass_value
				else:
					await ctx.embed_reply(f"Units, {unit1} and/or {unit2}, not found\nSee the conversions command")
					return
				await ctx.embed_reply(f"{value} {unit1} = {converted_value} {unit2}")
				
		# help or prefix/es DM or mention
		elif (message.content.lower() in ("help", "prefix", "prefixes") and isinstance(message.channel, discord.DMChannel)) or ctx.me.mention in message.content and message.content.replace(ctx.me.mention, "").strip().lower() in ("help", "prefix", "prefixes"):
			try:
				prefixes = ctx.bot.command_prefix(ctx.bot, message)
			except TypeError: # if Beta (*)
				prefixes = ctx.bot.command_prefix
			if "help" in message.content.lower():
				ctx.prefix = prefixes[0]
				ctx.invoked_with = "help"
				await ctx.invoke(ctx.bot.get_command("help"))
			else:
				await ctx.embed_reply("Prefixes: " + ' '.join("`{}`".format(prefix) for prefix in prefixes))
		
		# Chatbot
		elif message.content.startswith(ctx.me.mention):
			content = message.clean_content.replace('@' + ctx.me.display_name, "", 1).strip()
			aiml_response = ctx.bot.aiml_kernel.respond(content, sessionID = message.author.id)
			# TODO: Handle brain not loaded?
			if aiml_response:
				await ctx.embed_reply(aiml_response, attempt_delete = False)
			else:
				games_cog = client.get_cog("Games")
				if games_cog:
					cleverbot_response = await games_cog.cleverbot_get_reply(content)
					await ctx.embed_reply(cleverbot_response, attempt_delete = False)
		
		
		# :8ball:
		elif message.content.startswith('\N{BILLIARDS}'):
			if '\N{BILLIARDS}' in ctx.bot.all_commands:
				await ctx.invoke(ctx.bot.all_commands['\N{BILLIARDS}'])
		
		# f
		elif message.content.lower() == 'f':
			f_counter_info["total"] += 1
			f_counter_info[str(message.author.id)] = f_counter_info.get(str(message.author.id), 0) + 1
			with open(clients.data_path + "/f.json", 'w') as f_file:
				json.dump(f_counter_info, f_file, indent = 4)
			description = "{} has paid their respects\n".format(message.author.display_name)
			description += "Total respects paid so far: {}\n".format(f_counter_info["total"])
			description += "Recorded respects paid by {}: {}".format(message.author.display_name, f_counter_info[str(message.author.id)]) # since 2016-12-20
			try:
				await ctx.embed_reply(description)
			except discord.Forbidden: # necessary?
				raise
			except discord.HTTPException: # necessary?
				await ctx.send(description)
	
	@client.event
	async def on_error(event_method, *args, **kwargs):
		type, value, _traceback = sys.exc_info()
		if type is discord.Forbidden:
			for arg in args:
				if isinstance(arg, commands.context.Context):
					print("{0.bot.console_message_prefix}Missing Permissions for {0.command.name} in #{0.channel.name} in {0.guild.name}".format(arg))
					return
				elif isinstance(arg, discord.Message):
					print("Missing Permissions for #{0.channel.name} in {0.guild.name}".format(arg))
					return
		print('Ignoring exception in {}'.format(event_method), file = sys.stderr)
		traceback.print_exc()
		logging.errors_logger.error("Uncaught exception\n", exc_info = (type, value, _traceback))
	
	@client.event
	async def on_command_error(ctx, error):
		if isinstance(error, commands.NotOwner): return # not owner
		if isinstance(error, (commands.CommandNotFound, commands.DisabledCommand)): return # disabled or not found
		if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, youtube_dl.utils.DownloadError): return # handled with local error handler
		if isinstance(error, (errors.NotServerOwner, errors.MissingPermissions)): # commands.NotOwner?
			await ctx.embed_reply(":no_entry: You don't have permission to do that")
		elif isinstance(error, errors.MissingCapability):
			if "embed_links" in error.permissions:
				await ctx.send("I don't have permission to do that here\nI need the permission(s): " + ', '.join(error.permissions))
			else:
				await ctx.embed_reply("I don't have permission to do that here\nI need the permission(s): " + ', '.join(error.permissions))
		elif isinstance(error, errors.PermittedVoiceNotConnected):
			await ctx.embed_reply("I'm not in a voice channel\nPlease use `{}join` first".format(ctx.prefix))
		elif isinstance(error, errors.NotPermittedVoiceNotConnected):
			await ctx.embed_reply("I'm not in a voice channel\nPlease ask someone with permission to use `{}join` first".format(ctx.prefix))
		elif isinstance(error, commands.NoPrivateMessage):
			await ctx.embed_reply("Please use that command in a server")
		elif isinstance(error, commands.MissingRequiredArgument):
			await ctx.embed_reply(str(error).rstrip('.').replace("argument", "input"))
		elif isinstance(error, errors.NotPermitted):
			await ctx.embed_reply(":no_entry: You don't have permission to use that command here")
		elif isinstance(error, commands.BadArgument):
			await ctx.embed_reply(":no_entry: Error: Invalid Input: {}".format(error))
		elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, discord.HTTPException) and error.original.code == 50034:
			await ctx.embed_reply(":no_entry: Error: You can only bulk delete messages that are under 14 days old")
		# TODO: check embed links permission
		elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, (discord.Forbidden)):
			print("{0.bot.console_message_prefix}Missing Permissions for {0.command.name} in #{0.channel.name} in {0.guild.name}".format(ctx))
		else:
			print("Ignoring exception in command {}".format(ctx.command), file = sys.stderr)
			traceback.print_exception(type(error), error, error.__traceback__, file = sys.stderr)
			logging.errors_logger.error("Uncaught exception\n", exc_info = (type(error), error, error.__traceback__))
	
	ci = (os.getenv("CIRCLECI") or os.getenv("TRAVIS")) and os.getenv("CI")
	
	if not ci and not clients.beta:
		# Start web server
		client.loop.run_until_complete(client.aiohttp_app_runner.setup())
		client.aiohttp_site = web.TCPSite(client.aiohttp_app_runner, port = 80)
		client.loop.run_until_complete(client.aiohttp_site.start())
	# Can't bind to/open port 80 without being root on Linux
	# Try port >1024?, sudo?
	
	if clients.beta: client.command_prefix = '*'
	token = credentials.beta_token if clients.beta else credentials.token
	
	try:
		if ci:
			client.loop.create_task(client.start(token))
			client.loop.run_until_complete(asyncio.sleep(10))
			# TODO: stop after ready
		else:
			client.loop.run_until_complete(client.start(token))
	except aiohttp.errors.ClientOSError:
		pass
	finally:
		client.loop.run_until_complete(clients.shutdown_tasks())
		client.loop.close()
		os._exit(0)

