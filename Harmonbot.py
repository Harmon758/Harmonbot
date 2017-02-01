
print("Starting up Discord Harmonbot...")

import discord
from discord.ext import commands

import asyncio
import json
import os
import re
import sys
import traceback

import credentials
import clients
from clients import client
from modules import conversions
from modules import logging
from modules import utilities
from utilities import checks
from utilities import errors
from utilities import audio_player

utilities.create_file("f", content = {"counter" : 0})

@client.event
async def on_ready():
	# data = await client.http.get(client.http.GATEWAY + "/bot")
	# print(data)
	print("Started up Discord {0} ({1})".format(str(client.user), client.user.id))
	if os.path.isfile("data/temp/restart_channel.json"):
		with open("data/temp/restart_channel.json", 'r') as restart_channel_file:
			restart_data = json.load(restart_channel_file)
		os.remove("data/temp/restart_channel.json")
		restart_channel = client.get_channel(restart_data["restart_channel"])
		await client.send_embed(restart_channel, ":thumbsup::skin-tone-2: Restarted")
		for voice_channel in restart_data["voice_channels"]:
			await client.join_voice_channel(client.get_channel(voice_channel[0]))
			# asyncio.ensure_future(client.cogs["Audio"].start_player(client.get_channel(voice_channel[1])))
			text_channel = client.get_channel(voice_channel[1])
			client.cogs["Audio"].players[text_channel.server.id] = audio_player.AudioPlayer(client, text_channel)
	await clients.random_game_status()
	await clients.set_streaming_status(client)
	# await voice.detectvoice()

@client.event
async def on_server_join(server):
	utilities.create_folder("data/server_data/{}".format(server.id))
	utilities.create_file("server_data/{}/{}".format(server.id, server.name.replace('/', '-')))
	utilities.create_file("server_data/{}/settings".format(server.id), content = {"respond_to_bots": False})
	me = discord.utils.get(client.get_all_members(), id = credentials.myid)
	server_info = "```Name: " + server.name + "\n"
	server_info += "ID: " + server.id + "\n"
	server_info += "Owner: " + str(server.owner) + "\n"
	server_info += "Server Region: " + str(server.region) + "\n"
	server_info += "Members: " + str(server.member_count) + "\n"
	server_info += "Created at: " + str(server.created_at) + "\n```"
	server_info += "Icon: " + server.icon_url
	await client.send_message(me, "Joined Server: \n" + server_info)

@client.event
async def on_server_remove(server):
	me = discord.utils.get(client.get_all_members(), id = credentials.myid)
	server_info = "```Name: " + server.name + "\n"
	server_info += "ID: " + server.id + "\n"
	server_info += "Owner: " + str(server.owner) + "\n"
	server_info += "Server Region: " + str(server.region) + "\n"
	server_info += "Members: " + str(server.member_count) + "\n"
	server_info += "Created at: " + str(server.created_at) + "\n```"
	server_info += "Icon: " + server.icon_url
	await client.send_message(me, "Left Server: \n" + server_info)

@client.event
async def on_resumed():
	print("Discord Harmonbot: resumed")

@client.event
async def on_command(command, ctx):
	with open("data/stats.json", "r") as stats_file:
		stats = json.load(stats_file)
	stats["commands_executed"] += 1
	with open("data/stats.json", "w") as stats_file:
		json.dump(stats, stats_file, indent = 4)

@client.command(pass_context = True)
@checks.is_owner()
async def load(ctx, cog : str):
	'''Loads a cog'''
	try:
		client.load_extension("cogs." + cog)
	except Exception as e:
		await client.embed_reply(":thumbsdown::skin-tone-2: Failed to load `{}` cog\n"
		"{}: {}".format(cog, type(e).__name__, e))
	else:
		await client.embed_reply(":thumbsup::skin-tone-2: Loaded `{}` cog :gear:".format(cog))
		await client.delete_message(ctx.message)

@client.command(pass_context = True)
@checks.is_owner()
async def unload(ctx, cog : str):
	'''Unloads a cog'''
	try:
		client.unload_extension("cogs." + cog)
	except Exception as e:
		await client.embed_reply(":thumbsdown::skin-tone-2: Failed to unload `{}` cog\n"
		"{}: {}".format(cog, type(e).__name__, e))
	else:
		await client.embed_reply(":ok_hand::skin-tone-2: Unloaded `{}` cog :gear:".format(cog))
		await client.delete_message(ctx.message)

@client.command(pass_context = True)
@checks.is_owner()
async def reload(ctx, cog : str):
	'''Reloads a cog'''
	try:
		client.unload_extension("cogs." + cog)
		client.load_extension("cogs." + cog)
	except Exception as e:
		await client.embed_reply(":thumbsdown::skin-tone-2: Failed to reload `{}` cog\n"
		"{}: {}".format(cog, type(e).__name__, e))
	else:
		with open("data/stats.json", 'r') as stats_file:
			stats = json.load(stats_file)
		stats["cogs_reloaded"] += 1
		with open("data/stats.json", 'w') as stats_file:
			json.dump(stats, stats_file, indent = 4)
		await client.embed_reply(":thumbsup::skin-tone-2: Reloaded `{}` cog :gear:".format(cog))
		await client.delete_message(ctx.message)

@client.event
async def on_message(message):
	
	# Log message
	if message.channel.is_private:
		destination = "Direct Message"
	else:
		destination = "#{0.channel.name} ({0.channel.id}) [{0.server.name} ({0.server.id})]".format(message)
	logging.chat_logger.info("{0.timestamp}: [{0.id}] {0.author.display_name} ({0.author.name}) ({0.author.id}) in {1}: {0.content} {0.embeds}".format(message, destination))
	
	# Commands
	await client.process_commands(message)
	
	# Forward DMs
	if message.channel.is_private and message.channel.user.id != credentials.myid:
		me = discord.utils.get(client.get_all_members(), id = credentials.myid)
		if message.author == client.user:
			try:
				await client.send_message(me, "To " + message.channel.user.name + '#' + message.channel.user.discriminator + ": " + message.content)
			except discord.errors.HTTPException:
				print("Discord Harmonbot Error: DM too long to forward.")
		else:
			await client.send_message(me, "From " + message.author.name + '#' + message.author.discriminator + ": " + message.content)
	
	# Ignore own and blank messages
	if message.author == client.user or not message.content:
		return
	
	# Other commands
	try:
		prefixes = client.command_prefix(client, message)
	except TypeError:
		prefixes = client.command_prefix
	prefix = discord.utils.find(message.content.startswith, prefixes)
	if prefix:
		command = message.content[len(prefix):]
		if command.startswith("test_on_message"):
			await client.send_message(message.channel, "Hello, World!")
		elif re.match(r"^(\w+)to(\w+)", command, re.I): # conversions
			if command.split()[0] in client.commands:
				return
			elif len(message.content.split()) == 1:
				await clients.reply(message, "Please enter input.")
			elif not utilities.is_number(message.content.split()[1]):
				await clients.reply(message, "Syntax error.")
			else:
				value = float(message.content.split()[1])
				units = re.match(r"^(\w+)to(\w+)", command, re.I)
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
					await clients.reply(message, "Units, {} and/or {}, not found. See the conversions command.".format(unit1, unit2))
					return
				await clients.reply(message, str(value) + ' ' + unit1 + " = " + str(converted_value) + ' ' + unit2)
	
	# getprefix
	elif "getprefix" in message.content:
		await client.send_message(message.channel, "Prefixes: {}".format(' '.join(['`"{}"`'.format(prefix) for prefix in prefixes])))
	
	# help DM
	elif message.content.lower() == "help" and message.channel.is_private:
		await clients.reply(message, "Please see {}help".format(prefixes[0]))
	
	# :8ball:
	elif message.content.startswith("\U0001f3b1") and "Games" in client.cogs:
		await client.send_message(message.channel, "{}: {}".format(message.author.display_name, ":8ball: {}".format(client.cogs["Games"]._eightball())))
	
	# f
	elif message.content.lower() == 'f':
		with open("data/f.json", "r") as counter_file:
			counter_info = json.load(counter_file)
		counter_info["counter"] += 1
		with open("data/f.json", "w") as counter_file:
			json.dump(counter_info, counter_file, indent = 4)
		await client.send_message(message.channel, message.author.display_name + " has paid their respects.\nRespects paid so far: " + str(counter_info["counter"]))
	
	# Chatbot
	elif message.raw_mentions and client.user.id == message.raw_mentions[0] and message.clean_content.startswith('@'):
		mentionless_message = ""
		for word in message.clean_content.split():
			if not word.startswith("@"):
				mentionless_message += word
		await clients.reply(message, clients.cleverbot_instance.ask(mentionless_message))

@client.event
async def on_error(event_method, *args, **kwargs):
	type, value, _traceback = sys.exc_info()
	if type is discord.errors.Forbidden:
		for arg in args:
			if isinstance(arg, commands.context.Context):
				print("Missing Permissions for #{0.channel.name} in {0.server.name}".format(arg.message))
				return
	print('Ignoring exception in {}'.format(event_method), file = sys.stderr)
	traceback.print_exc()
	logging.errors_logger.error("Uncaught exception\n", exc_info = (type, value, _traceback))

@client.event
async def on_command_error(error, ctx):
	if isinstance(error, errors.NotOwner):
		pass
	elif isinstance(error, (commands.errors.CommandNotFound, commands.errors.DisabledCommand)):
		pass
	elif isinstance(error, (errors.NotServerOwner, errors.MissingPermissions)): # errors.NotOwner
		await ctx.bot.send_message(ctx.message.channel, ":no_entry: You don't have permission to do that.")
	elif isinstance(error, errors.MissingCapability):
		await ctx.bot.send_message(ctx.message.channel, "I don't have permission to do that here. I need the permission(s): " + \
		', '.join(error.permissions))
	elif isinstance(error, errors.SO_VoiceNotConnected):
		await ctx.bot.send_message(ctx.message.channel, "I'm not in a voice channel. "
		"Please use `!voice (or !yt) join <channel>` first.")
	elif isinstance(error, errors.NSO_VoiceNotConnected):
		await ctx.bot.send_message(ctx.message.channel, "I'm not in a voice channel. "
		"Please ask someone with permission to use `!voice (or !yt) join <channel>` first.")
	elif isinstance(error, commands.errors.NoPrivateMessage):
		await ctx.bot.send_message(ctx.message.channel, "Please use that command in a server.")
	elif isinstance(error, commands.errors.MissingRequiredArgument):
		await ctx.bot.send_message(ctx.message.channel, error)
	elif isinstance(error, errors.NotPermitted):
		await ctx.bot.send_message(ctx.message.channel, ":no_entry: You don't have permission to use that command here.")
	elif isinstance(error, commands.errors.BadArgument):
		await ctx.bot.send_message(ctx.message.channel, ":warning: Error: invalid input")
	elif isinstance(error, commands.errors.CommandInvokeError) and isinstance(error.original, (errors.NoTag, errors.NoTags, errors.LichessUserNotFound)) or "No video results" in str(error):
		pass # handled with local error handler
	elif isinstance(error, commands.errors.CommandInvokeError) and isinstance(error.original, (discord.errors.Forbidden)):
		print("Missing Permissions for #{0.channel.name} in {0.server.name}".format(ctx.message))
	else:
		print("Ignoring exception in command {}".format(ctx.command), file = sys.stderr)
		traceback.print_exception(type(error), error, error.__traceback__, file = sys.stderr)
		logging.errors_logger.error("Uncaught exception\n", exc_info = (type(error), error, error.__traceback__))

beta = any("beta" in arg.lower() for arg in sys.argv)
if beta:
	client.command_prefix = '*'
	token = credentials.beta_token
else:
	token = credentials.token

try:
	if os.getenv("TRAVIS") and os.getenv("CI"):
		client.loop.create_task(client.start(token))
		client.loop.run_until_complete(asyncio.sleep(10))
	else:
		client.loop.run_until_complete(client.start(token))
except KeyboardInterrupt:
	print("Shutting down Discord Harmonbot...")
	client.loop.run_until_complete(clients.restart_tasks())
	client.loop.run_until_complete(client.logout())
finally:
	client.loop.close()
	os._exit(0)

