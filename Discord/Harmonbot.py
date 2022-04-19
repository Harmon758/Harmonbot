
if __name__ == "__main__":
	
	print("Starting up Discord Harmonbot...")
	
	import discord
	
	import asyncio
	import ctypes
	import datetime
	import os
	import re
	import sys
	
	from aiohttp import web
	import dotenv
	import pkg_resources  # from setuptools
	
	import bot
	from modules import conversions
	
	discord.http._set_api_version(9)
	
	mention_spammers = []
	
	# Load credentials from .env
	dotenv.load_dotenv()
	
	# Initialize client
	client = bot.Bot()
	
	# TODO: Move to utilities
	def replace_null_character(data):
		data_type = type(data)
		if data_type is str:
			return data.replace('\N{NULL}', "")
		if data_type is dict:
			return {key: replace_null_character(value) for key, value in data.items()}
		if data_type is list:
			return [replace_null_character(item) for item in data]
		return data
	
	@client.event
	async def on_message(message):
		
		# Get Context
		ctx = await client.get_context(message)
		
		author = message.author
		channel = message.channel
		guild = message.guild
		
		# Log message
		if isinstance(channel, discord.Thread):
			await ctx.bot.db.execute(
				"""
				INSERT INTO chat.messages (
					created_at, message_id, 
					author_id, author_name, author_discriminator, author_display_name, 
					direct_message, channel_id, channel_name, guild_id, guild_name, 
					message_content, embeds, 
					thread, thread_id, thread_name
				)
				VALUES ($1, $2, $3, $4, $5, $6, FALSE, $7, $8, $9, $10, $11, CAST($12 AS jsonb[]), TRUE, $13, $14)
				""", 
				message.created_at.replace(tzinfo = datetime.timezone.utc), message.id, 
				author.id, author.name, author.discriminator, author.display_name, 
				channel.parent_id, channel.parent.name, guild.id, guild.name, 
				message.content.replace('\N{NULL}', ""), 
				[replace_null_character(embed.to_dict()) for embed in message.embeds], 
				channel.id, channel.name
			)
		elif channel.type is discord.ChannelType.private:
			await ctx.bot.db.execute(
				"""
				INSERT INTO chat.messages (
					created_at, message_id, 
					author_id, author_name, author_discriminator, author_display_name, 
					direct_message, 
					message_content, embeds, 
					thread
				)
				VALUES ($1, $2, $3, $4, $5, $6, TRUE, $7, CAST($8 AS jsonb[]), FALSE)
				""", 
				message.created_at.replace(tzinfo = datetime.timezone.utc), message.id, 
				author.id, author.name, author.discriminator, author.display_name, 
				message.content.replace('\N{NULL}', ""), 
				[replace_null_character(embed.to_dict()) for embed in message.embeds]
			)
		else:
			await ctx.bot.db.execute(
				"""
				INSERT INTO chat.messages (
					created_at, message_id, 
					author_id, author_name, author_discriminator, author_display_name, 
					direct_message, channel_id, channel_name, guild_id, guild_name, 
					message_content, embeds, 
					thread
				)
				VALUES ($1, $2, $3, $4, $5, $6, FALSE, $7, $8, $9, $10, $11, CAST($12 AS jsonb[]), FALSE)
				""", 
				message.created_at.replace(tzinfo = datetime.timezone.utc), message.id, 
				author.id, author.name, author.discriminator, author.display_name, 
				channel.id, channel.name, guild.id, guild.name, 
				message.content.replace('\N{NULL}', ""), 
				[replace_null_character(embed.to_dict()) for embed in message.embeds]
			)
		
		# Server specific settings
		if guild is not None:
			guild_settings = await ctx.bot.get_guild_settings(guild.id)
			if guild_settings.get("anti-spam") and len(message.mentions) > 10:
				global mention_spammers
				if author.id in mention_spammers:
					# TODO: Handle across different servers
					if channel.permissions_for(guild.me).kick_members:
						# TODO: Check hierarchy, if able to kick
						await ctx.bot.kick(author)
						await ctx.send(f"{author} has been kicked for spamming mentions")
						await ctx.whisper(f"You were kicked from {guild} for spamming mentions")
					else:
						await ctx.send("I need permission to kick members from the server to enforce anti-spam")
				else:
					await ctx.embed_reply(":warning: You will be kicked if you continue spamming mentions")
					mention_spammers.append(author.id)
					await asyncio.sleep(3600)
					mention_spammers.remove(author.id)
			if not guild_settings.get("respond_to_bots") and author.bot:
				return
		
		# Invoke Commands
		await ctx.bot.invoke(ctx)
		
		# Forward DMs
		if channel.type is discord.ChannelType.private:
			if not channel.recipient:
				channel = await ctx.bot.fetch_channel(channel.id)
			# `message.channel` is a `DMChannel` here for an ephemeral message
			# even if it was not sent as a DM.
			# This is an issue with discord.py caused by Discord's API not
			# providing `guild_id` for ephemeral messages for the
			# `MESSAGE_CREATE` event.
			# This might eventually be fixed by Discord.
			# https://github.com/Rapptz/discord.py/issues/7370
			# https://discord.com/channels/336642139381301249/336642776609456130/875382864919797760
			if channel.type is not discord.ChannelType.private:
				ctx.bot.print(f"Ephemeral message with erroneous DMChannel channel attribute: {message.id}")
			elif channel.recipient.id != ctx.bot.owner_id:
				if not (me := discord.utils.get(ctx.bot.get_all_members(), id = ctx.bot.owner_id)):
					me = await ctx.bot.fetch_user(ctx.bot.owner_id)
				if author == ctx.bot.user:
					try:
						await me.send(f"To {channel.recipient}: {message.content}", embed = message.embeds[0] if message.embeds else None)
					except discord.HTTPException:
						# TODO: use textwrap/paginate
						await me.send(f"To {channel.recipient}: `DM too long to forward`")
				else:
					await me.send(f"From {author}: {message.content}", embed = message.embeds[0] if message.embeds else None)
		
		# Ignore own and blank messages
		if author == ctx.bot.user or not message.content:
			return
		
		# Test on_message command
		if ctx.prefix and message.content.startswith(ctx.prefix + "test on_message"):
			return await ctx.send("Hello, World!")
		
		# Conversion commands (regex)
		if ctx.prefix and not ctx.command:
			units = re.match(r"^(\w+)to(\w+)", message.content[len(ctx.prefix):], re.I)
			if not units: return
			if len(message.content.split()) == 1:
				return await ctx.embed_reply(":no_entry: Please enter input")
			try:
				value = float(message.content.split()[1])
			except ValueError:
				return await ctx.embed_reply(":no_entry: Syntax error")
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
				return await ctx.embed_reply(f"Units, {unit1} and/or {unit2}, not found\nSee the conversions command")
			return await ctx.embed_reply(f"{value} {unit1} = {converted_value} {unit2}")
		
		# DM or mention
		if channel.type is discord.ChannelType.private or ctx.me.mention in message.content:
			content = message.content.replace(ctx.me.mention, "").strip()
			content = content.lower()
			try:
				prefixes = await ctx.bot.command_prefix(ctx.bot, message)
			except TypeError:  # if Beta (*)
				prefixes = ctx.bot.command_prefix
			# help
			if content in ('?', "commands", "help"):
				ctx.prefix = prefixes[0]
				return await ctx.send_help()
			# prefix(es)
			if content in ("prefix", "prefixes"):
				return await ctx.embed_reply("Prefixes: " + ' '.join(f"`{prefix}`" for prefix in prefixes))
		
		# Chatbot
		if message.content.startswith(ctx.me.mention):
			content = message.clean_content.replace('@' + ctx.me.display_name, "", 1).strip()
			embed = discord.Embed(color = ctx.bot.bot_color)
			# TODO: Handle brain not loaded?
			if aiml_response := ctx.bot.aiml_kernel.respond(content, sessionID = author.id):
				embed.description = aiml_response
				return await message.reply(embed = embed)
			if games_cog := ctx.bot.get_cog("Games"):
				embed.description = await games_cog.cleverbot_get_reply(content)
				return await message.reply(embed = embed)
		
		# TODO: Server setting to disable prefix-less commands
		
		# :8ball: command
		if message.content.startswith('\N{BILLIARDS}') and (command := ctx.bot.get_command('\N{BILLIARDS}')):
			return await ctx.invoke(command)
		
		# Respects (f) system
		if message.content.lower() == 'f' or message.content == '\N{REGIONAL INDICATOR SYMBOL LETTER F}':
			# TODO: Server setting to disable respects system
			if respects_command := ctx.bot.get_command("respects"):
				if points_cog := ctx.bot.get_cog("Points"):
					await points_cog.add(user = ctx.author)
				return await ctx.invoke(respects_command.get_command("pay"))
	
	async def main():
		async with client:
			ci = os.getenv("CI")
			github_action = os.getenv("GITHUB_ACTION")
			
			if ci or github_action or client.beta:
				client.command_prefix = '*'
				token = os.getenv("DISCORD_BETA_BOT_TOKEN")
			else:
				token = os.getenv("DISCORD_BOT_TOKEN")
				# Load Opus
				## Get Opus version in bin folder
				opus = discord.opus.libopus_loader("bin/opus.dll")
				opus.opus_get_version_string.restype = ctypes.c_char_p
				harmonbot_opus_version = opus.opus_get_version_string().decode("UTF-8")
				if harmonbot_opus_version.startswith("libopus "):
					harmonbot_opus_version = harmonbot_opus_version[8:]
				### Discard additional information from git describe
				harmonbot_opus_version = harmonbot_opus_version.split('-')[0]
				harmonbot_opus_version = pkg_resources.parse_version(harmonbot_opus_version)
				## Load Opus provided by discord.py
				discord.opus._load_default()
				## Get Opus version provided by discord.py
				discord.opus._lib.opus_get_version_string.restype = ctypes.c_char_p
				library_opus_version = discord.opus._lib.opus_get_version_string().decode("UTF-8")
				if library_opus_version.startswith("libopus "):
					library_opus_version = library_opus_version[8:]
				### Discard additional information from git describe
				library_opus_version = library_opus_version.split('-')[0]
				library_opus_version = pkg_resources.parse_version(library_opus_version)
				## Compare Opus versions and use bin folder one if newer
				if harmonbot_opus_version > library_opus_version:
					discord.opus._lib = opus
				# Start web server
				await client.aiohttp_app_runner.setup()
				client.aiohttp_site = web.TCPSite(client.aiohttp_app_runner, port = 80)
				await client.aiohttp_site.start()
				# Can't bind to/open port 80 without being root on Linux
				# Try port >1024? or sudo? for CI
			
			try:
				if ci or github_action:
					client.loop.create_task(client.start(token), name = "Client")
					await asyncio.sleep(10)
					# TODO: stop after ready
				else:
					await client.start(token)
			finally:
				await client.shutdown_tasks()
				# client.loop.close()  # unnecessary?, causing Event loop is closed exceptions on restart
				sys.exit(0)
				os._exit(0)  # Shouldn't be necessary
	
	asyncio.run(main())

