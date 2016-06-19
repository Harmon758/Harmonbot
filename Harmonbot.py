
print("Starting up Harmonbot...")

import discord
from discord.ext import commands

import asyncio
import json
import logging
import os
import re
import sys
import traceback

from modules import conversions
from modules.utilities import *
from modules import voice
from utilities import checks
from utilities import errors

import credentials
from clients import client
from clients import cleverbot_instance

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename = "data/discord.log", encoding = "utf-8", mode = 'a')
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)

harmonbot_logger = logging.getLogger("harmonbot")
harmonbot_logger.setLevel(logging.DEBUG)
harmonbot_logger_handler = logging.FileHandler(filename = "data/harmonbot.log", encoding = "utf-8", mode = 'a')
harmonbot_logger_handler.setFormatter(logging.Formatter("%(message)s"))
harmonbot_logger.addHandler(harmonbot_logger_handler)

try:
	with open("data/f.json", "x") as f_file:
		json.dump({"counter" : 0}, f_file)
except FileExistsError:
	pass

@client.event
async def on_ready():
	print("Started up {0} ({1})".format(str(client.user), client.user.id))
	if os.path.isfile("data/restart_channel.json"):
		with open("data/restart_channel.json", "r") as restart_channel_file:
			restart_data = json.load(restart_channel_file)
		os.remove("data/restart_channel.json")
		restart_channel = client.get_channel(restart_data["restart_channel"])
		await client.send_message(restart_channel, ":thumbsup::skin-tone-2: Restarted.")
		for voice_channel in restart_data["voice_channels"]:
			await client.join_voice_channel(client.get_channel(voice_channel[0]))
			asyncio.ensure_future(voice.start_player(client.get_channel(voice_channel[1])))
	await random_game_status()
	await set_streaming_status(client)
	# await voice.detectvoice()

@client.event
async def on_resumed():
	await client.send_message(client.get_channel("147264078258110464"), client.get_server("147208000132743168").get_member("115691005197549570").mention + ": resumed.")

@client.event
async def on_command(command, ctx):
	with open("data/stats.json", "r") as stats_file:
		stats = json.load(stats_file)
	stats["commands_executed"] += 1
	with open("data/stats.json", "w") as stats_file:
		json.dump(stats, stats_file, indent = 4)

@client.command(hidden = True)
@checks.is_owner()
async def load(cog : str):
	'''Loads a cog'''
	try:
		client.load_extension("cogs." + cog)
	except Exception as e:
		await client.say(":thumbsdown::skin-tone-2: Failed to load cog.\n"
		"{}: {}".format(type(e).__name__, e))
	else:
		await client.say(":thumbsup::skin-tone-2: Loaded cog.")

@client.command(hidden = True)
@checks.is_owner()
async def unload(cog : str):
	'''Unloads a cog'''
	try:
		client.unload_extension("cogs." + cog)
	except Exception as e:
		await client.say(":thumbsdown::skin-tone-2: Failed to unload cog.\n"
		"{}: {}".format(type(e).__name__, e))
	else:
		await client.say(':ok_hand::skin-tone-2: Unloaded cog.')

@client.command(hidden = True)
@checks.is_owner()
async def reload(cog : str):
	'''Reloads a cog'''
	try:
		client.unload_extension("cogs." + cog)
		client.load_extension("cogs." + cog)
	except Exception as e:
		await client.say(":thumbsdown::skin-tone-2: Failed to reload cog.\n"
		"{}: {}".format(type(e).__name__, e))
	else:
		with open("data/stats.json", "r") as stats_file:
			stats = json.load(stats_file)
		stats["cogs_reloaded"] += 1
		with open("data/stats.json", "w") as stats_file:
			json.dump(stats, stats_file)
		await client.say(":thumbsup::skin-tone-2: Reloaded cog.")

@client.event
async def on_message(message):
	if message.channel.is_private:
		destination = "Direct Message"
	else:
		destination = "#{0.channel.name} ({0.channel.id}) [{0.server.name} ({0.server.id})]".format(message)
	harmonbot_logger.info("{0.timestamp}: [{0.id}] {0.author.display_name} ({0.author.name}) ({0.author.id}) in {1}: {0.content}".format(message, destination))
	await client.process_commands(message)
	if message.channel.is_private and message.channel.user.id != credentials.myid: # forward DMs
		me = discord.utils.get(client.get_all_members(), id = credentials.myid)
		if message.author == client.user:
			await client.send_message(me, "To " + message.channel.user.name + '#' + message.channel.user.discriminator + ": " + message.content)
		else:
			await client.send_message(me, "From " + message.author.name + '#' + message.author.discriminator + ": " + message.content)
	if message.author == client.user or not message.content: # ignore own and blank messages
		return
	prefixes = client.command_prefix(client, message)
	prefix = discord.utils.find(message.content.startswith, prefixes)
	if "getprefix" in message.content: # getprefix
		await client.send_message(message.channel, "Prefixes: {}".format(' '.join(['`"{}"`'.format(prefix) for prefix in prefixes])))
	elif prefix: # other commands
		command = message.content[len(prefix):]
		if command.startswith("test_on_message"):
			await client.send_message(message.channel, "Hello, World!")
		elif re.match(r"^(\w+)to(\w+)", command, re.I): # conversions
			if command.split()[0] in client.commands:
				return
			elif len(message.content.split()) == 1:
				await reply(message, "Please enter input.")
			elif not is_number(message.content.split()[1]):
				await reply(message, "Syntax error.")
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
					await reply(message, "Units, {} and/or {}, not found. See the conversions command.".format(unit1, unit2))
					return
				await reply(message, str(value) + ' ' + unit1 + " = " + str(converted_value) + ' ' + unit2)
	elif message.content.startswith("\U0001f3b1") and "Games" in client.cogs: # :8ball:
		await reply(message, ":8ball: {}".format(client.cogs["Games"]._eightball()))
	elif message.content.lower() == 'f': # f
		with open("data/f.json", "r") as counter_file:
			counter_info = json.load(counter_file)
		counter_info["counter"] += 1
		with open("data/f.json", "w") as counter_file:
			json.dump(counter_info, counter_file, indent = 4)
		await client.send_message(message.channel, message.author.name + " has paid their respects.\nRespects paid so far: " + str(counter_info["counter"]))
	elif client.user.mentioned_in(message): # cleverbot
		mentionless_message = ""
		for word in message.clean_content.split():
			if not word.startswith("@"):
				mentionless_message += word
		await reply(message, cleverbot_instance.ask(mentionless_message))

@client.event
async def on_command_error(error, ctx):
	if isinstance(error, (errors.NotOwner, errors.NotServerOwner, errors.MissingPermissions)):
		await ctx.bot.send_message(ctx.message.channel, "You don't have permission to do that.")
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
		await ctx.bot.send_message(ctx.message.channel, "You don't have permission to use that command here.")
	elif isinstance(error, commands.errors.CommandInvokeError) and isinstance(error.original, (errors.NoTag, errors.NoTags)):
		pass # handled with local error handler
	else:
		print("Ignoring exception in command {}".format(ctx.command), file = sys.stderr)
		traceback.print_exception(type(error), error, error.__traceback__, file = sys.stderr)

try:
	client.loop.create_task(client.cogs["RSS"].check_rss_feeds())
	client.loop.run_until_complete(client.start(credentials.token))
except KeyboardInterrupt:
	print("Shutting down Harmonbot...")
	client.loop.run_until_complete(restart_tasks())
	client.loop.run_until_complete(client.logout())
finally:
	client.loop.close()

