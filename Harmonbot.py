
print("Starting up Harmonbot...")

import discord
from discord.ext import commands

import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
import html
import logging
import os
import re
# import spotipy
import string
#import subprocess
import sys
import time
import traceback
import urllib

from modules import conversions
from modules import documentation
from modules import permissions
from modules.utilities import *
from modules import voice
from cogs.rss import check_rss_feeds
from utilities import checks
from utilities import errors

import credentials
from client import client
from client import aiohttp_session
from client import cleverbot_instance

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

# spotify = spotipy.Spotify()

try:
	with open("data/trivia_points.json", "x") as trivia_file:
		json.dump({}, trivia_file) #fix
except FileExistsError:
	pass
try:
	with open("data/f.json", "x") as f_file:
		json.dump({"counter" : 0}, f_file)
except FileExistsError:
	pass
try:
	with open("data/stats.json", "x") as stats_file:
		json.dump({"uptime" : 0, "restarts" : 0, "cogs_reloaded" : 0, "commands_executed" : 0}, stats_file)
except FileExistsError:
	pass
try:
	with open("data/tags.json", "x") as tags_file:
		json.dump({}, tags_file) #fix
except FileExistsError:
	pass
try:
	with open("data/rss_feeds.json", "x") as feeds_file:
		json.dump({"channels" : []}, feeds_file)
except FileExistsError:
	pass

trivia_active = False
trivia_bet = False
trivia_answers = {}
trivia_bets = {}
jeopardy_active = False
jeopardy_question_active = False
jeopardy_board = []
jeopardy_answer = ""
jeopardy_answered = False
jeopardy_scores = {}
jeopardy_board_output = ""
jeopardy_max_width = 0

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
		json.dump(stats, stats_file)

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
	global trivia_answers
	if message.channel.is_private:
		destination = "Direct Message"
	else:
		destination = "#{0.channel.name} ({0.channel.id}) [{0.server.name} ({0.server.id})]".format(message)
	harmonbot_logger.info("{0.timestamp}: [{0.id}] {0.author.display_name} ({0.author.name}) ({0.author.id}) in {1}: {0.content}".format(message, destination))
	await client.process_commands(message)
	if message.channel.is_private and message.channel.user.id != credentials.myid:
		me = discord.utils.get(client.get_all_members(), id = credentials.myid)
		if message.author == client.user:
			await client.send_message(me, "To " + message.channel.user.name + '#' + message.channel.user.discriminator + ": " + message.content)
		else:
			await client.send_message(me, "From " + message.author.name + '#' + message.author.discriminator + ": " + message.content)
	if message.author == client.user or not message.content:
		return
	elif not message.channel.is_private and not permissions.get_permission(message, "user", message.author.id, message.content.split()[0]) and credentials.myid != message.author.id: #rework
		await send_mention_space(message, "You don't have permission to use that command here")
	elif message.content.startswith("!test_on_message"):
		await client.send_message(message.channel, "Hello, World!")
	elif message.content.startswith("!help"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "I've DM'ed you my commands. Also see !commands. What else do you need help with?")
		elif documentation.commands_info.get(message.content.split()[1], 0):
			await send_mention_space(message, documentation.commands_info[message.content.split()[1]])
		#else:
			#await send_mention_space(message, "Check your DMs.")
	elif client.user.mentioned_in(message):
		mentionless_message = ""
		for word in message.clean_content.split():
			if not word.startswith("@"):
				mentionless_message += word
		await send_mention_space(message, cleverbot_instance.ask(mentionless_message))
	elif message.content.startswith("!aeval"):
		if message.author.id == credentials.myid:
			try:
				await send_mention_code(message, str(await eval(' '.join(message.content.split()[1:]))))
			except:
				await send_mention_code(message, traceback.format_exc())
	elif message.content.startswith("!eval"):
		if message.author.id == credentials.myid:
			try:
				await send_mention_code(message, str(eval(' '.join(message.content.split()[1:]))))
			except:
				await send_mention_code(message, traceback.format_exc())
	elif message.content.startswith("!exec"):
		if message.author.id == credentials.myid:
			try:
				exec(' '.join(message.content.split()[1:]))
				await send_mention_space(message, "successfully executed")
			except:
				await send_mention_code(message, traceback.format_exc())
	elif message.content.startswith("!jeopardy"):
		global jeopardy_active, jeopardy_question_active, jeopardy_board, jeopardy_answer, jeopardy_answered, jeopardy_scores, jeopardy_board_output, jeopardy_max_width
		if len(message.content.split()) > 1 and message.content.split()[1] == "start" and not jeopardy_active:
			jeopardy_active = True
			categories = []
			category_titles = []
			jeopardy_board_output = ""
			url = "http://jservice.io/api/random"
			for i in range(6):
				async with aiohttp_session.get(url) as resp:
					data = await resp.json()
				categories.append(data[0]["category_id"])
			for category in categories:
				url = "http://jservice.io/api/category?id=" + str(category)
				async with aiohttp_session.get(url) as resp:
					data = await resp.json()
				category_titles.append(string.capwords(data["title"]))
				jeopardy_board.append([category, False, False, False, False, False])
			jeopardy_max_width = max(len(category_title) for category_title in category_titles)
			for category_title in category_titles:
				jeopardy_board_output += category_title.ljust(jeopardy_max_width) + "  200 400 600 800 1000\n"
			await client.send_message(message.channel, "```" + jeopardy_board_output + "```")
		elif len(message.content.split()) > 2 and jeopardy_active and not jeopardy_question_active:
			category = int(message.content.split()[1])
			value = message.content.split()[2]
			if 1 <= category <= 6 and value in ["200", "400", "600", "800", "1000"]:
				value_index = ["200", "400", "600", "800", "1000"].index(value)
				if not jeopardy_board[category - 1][value_index + 1]:
					jeopardy_question_active = True
					jeopardy_answered = False
					url = "http://jservice.io/api/category?id=" + str(jeopardy_board[category - 1][0])
					async with aiohttp_session.get(url) as resp:
						data = await resp.json()
					jeopardy_answer = data["clues"][value_index]["answer"]
					await client.send_message(message.channel, "Category: " + string.capwords(data["title"]) + "\n" + data["clues"][value_index]["question"])
					counter = 15
					answer_message = await client.send_message(message.channel, "You have " + str(counter) + " seconds left to answer.")
					while counter:
						await asyncio.sleep(1)
						counter -= 1
						await client.edit_message(answer_message, "You have " + str(counter) + " seconds left to answer.")
						if jeopardy_answered:
							break
					await client.edit_message(answer_message, "Time's up!")
					if jeopardy_answered:
						if jeopardy_answered in jeopardy_scores:
							jeopardy_scores[jeopardy_answered] += int(value)
						else:
							jeopardy_scores[jeopardy_answered] = int(value)
						answered_message = jeopardy_answered.name + " was right! They now have $" + str(jeopardy_scores[jeopardy_answered]) + "."
					else:
						answered_message = "Nobody got it right."
					score_output = ""
					for player, score in jeopardy_scores.items():
						score_output += player.name + ": $" + str(score) + ", "
					score_output = score_output[:-2]
					jeopardy_board[category - 1][value_index + 1] = True
					clue_delete_cursor = (jeopardy_max_width + 2) * category + 1 * (category - 1) + 20 * (category - 1) + 4 * value_index
					if value_index == 4:
						jeopardy_board_output = jeopardy_board_output[:clue_delete_cursor] + "    " + jeopardy_board_output[clue_delete_cursor + 4:]
					else:
						jeopardy_board_output = jeopardy_board_output[:clue_delete_cursor] + "   " + jeopardy_board_output[clue_delete_cursor + 3:]
					await client.send_message(message.channel, "The answer was " + BeautifulSoup(html.unescape(jeopardy_answer), "html.parser").get_text() + "\n" + answered_message + "\n" + score_output + "\n```" + jeopardy_board_output + "```")
					jeopardy_question_active = False
	elif jeopardy_question_active and not (message.content.startswith('!') or message.server.me in message.mentions):
		if message.content.lower() == jeopardy_answer.lower() or message.content.lower() == BeautifulSoup(html.unescape(jeopardy_answer.lower()), "html.parser").get_text().lower() or "a " + message.content.lower() == jeopardy_answer.lower() or "an " + message.content.lower() == jeopardy_answer.lower() or "the " + message.content.lower() == jeopardy_answer.lower():
			jeopardy_answered = message.author
		'''
		if len(message.content.split()) > 1 and (message.content.split()[1] == "score" or message.content.split()[1] == "points"):
			with open("data/trivia_points.json", "r") as trivia_file:
				score = json.load(trivia_file)
			correct = score[message.author.id][0]
			incorrect = score[message.author.id][1]
			correct_percentage = round(float(correct) / (float(correct) + float(incorrect)) * 100, 2)
			await send_mention_space(message, "You have answered " + str(correct) + "/" + str(correct + incorrect) + " (" + str(correct_percentage) + "%) correctly.")
		elif not trivia_active:
			with open("data/trivia_points.json", "r") as trivia_file:
				score = json.load(trivia_file)
			for correct_player in correct_players:
				if correct_player.id in score:
					score[correct_player.id][0] += 1
				else:
					score[correct_player.id] = [1, 0]
			for incorrect_player in incorrect_players:
				if incorrect_player.id in score:
					score[incorrect_player.id][1] += 1
				else:
					score[incorrect_player.id] = [0, 1]
			with open("data/trivia_points.json", "w") as trivia_file:
				json.dump(score, trivia_file)
		else:
			pass
		'''
	elif message.content.startswith("!trivia"):
		global trivia_active, trivia_bet, trivia_bets
		if len(message.content.split()) > 1 and (message.content.split()[1] in ["score", "points"]):
			with open("data/trivia_points.json", "r") as trivia_file:
				score = json.load(trivia_file)
			correct = score[message.author.id][0]
			incorrect = score[message.author.id][1]
			correct_percentage = round(float(correct) / (float(correct) + float(incorrect)) * 100, 2)
			await send_mention_space(message, "You have answered " + str(correct) + "/" + str(correct + incorrect) + " (" + str(correct_percentage) + "%) correctly.")
		elif len(message.content.split()) > 1 and (message.content.split()[1] in ["cash", "money"]):
			with open("data/trivia_points.json", "r") as trivia_file:
				score = json.load(trivia_file)
			cash = score[message.author.id][2]
			await send_mention_space(message, "You have $" + add_commas(cash))
		elif len(message.content.split()) > 1 and message.content.split()[1] == "bet" and not trivia_bet:
			trivia_bet = True
			url = "http://jservice.io/api/random"
			async with aiohttp_session.get(url) as resp:
				data = await resp.json()
			data = data[0]
			await client.send_message(message.channel, "Category: " + string.capwords(data["category"]["title"]))
			while trivia_bet:
				await asyncio.sleep(1)
			trivia_active = True
			await client.send_message(message.channel, "Category: " + string.capwords(data["category"]["title"]) + "\n" + data["question"])
			counter = 15
			answer_message = await client.send_message(message.channel, "You have " + str(counter) + " seconds left to answer.")
			while counter:
				await asyncio.sleep(1)
				counter -= 1
				await client.edit_message(answer_message, "You have " + str(counter) + " seconds left to answer.")
			await client.edit_message(answer_message, "Time's up!")
			correct_players = []
			incorrect_players = []
			for player, answer in trivia_answers.items():
				if answer.lower() == data["answer"].lower() or answer.lower() == BeautifulSoup(html.unescape(data["answer"]), "html.parser").get_text().lower() or "a " + answer.lower() == data["answer"].lower() or "the " + answer.lower() == data["answer"].lower():
					correct_players.append(player)
				else:
					incorrect_players.append(player)
			correct_players_output = ""
			if len(correct_players) == 0:
				correct_players_output = "Nobody got it right!"
			else:
				if len(correct_players) == 1:
					correct_players_output = correct_players[0].name + " was right!"
				elif len(correct_players) == 2:
					correct_players_output = correct_players[0].name + " and " + correct_players[1].name + " were right!"
				elif len(correct_players) > 2:
					for i in range(len(correct_players) - 1):
						correct_players_output += correct_players[i].name + ", "
					correct_players_output += "and " + correct_players[len(correct_players) - 1].name + " were right!"
			with open("data/trivia_points.json", "r") as trivia_file:
				score = json.load(trivia_file)
			for correct_player in correct_players:
				if correct_player.id in score:
					score[correct_player.id][0] += 1
				else:
					score[correct_player.id] = [1, 0, 100000]
				if correct_player in trivia_bets:
					score[correct_player.id][2] += trivia_bets[correct_player]
			for incorrect_player in incorrect_players:
				if incorrect_player.id in score:
					score[incorrect_player.id][1] += 1
				else:
					score[incorrect_player.id] = [0, 1, 100000]
				if incorrect_player in trivia_bets:
					score[incorrect_player.id][2] -= trivia_bets[incorrect_player]
			trivia_bets_output = ""
			for trivia_player in trivia_bets:
				if trivia_player in correct_players:
					trivia_bets_output += trivia_player.name + " won $" + add_commas(trivia_bets[trivia_player]) + " and now has $" + add_commas(score[trivia_player.id][2]) + ". "
				elif trivia_player in incorrect_players:
					trivia_bets_output += trivia_player.name + " lost $" + add_commas(trivia_bets[trivia_player]) + " and now has $" + add_commas(score[trivia_player.id][2]) + ". "
				else:
					score[trivia_player.id][2] -= trivia_bets[trivia_player]
					trivia_bets_output += trivia_player.name + " lost $" + add_commas(trivia_bets[trivia_player]) + " and now has $" + add_commas(score[trivia_player.id][2]) + ". "
			trivia_bets_output = trivia_bets_output[:-1]
			with open("data/trivia_points.json", "w") as trivia_file:
				json.dump(score, trivia_file)
			await client.send_message(message.channel, "The answer was " + BeautifulSoup(html.unescape(data["answer"]), "html.parser").get_text() + "\n" + correct_players_output + "\n" + trivia_bets_output)
			trivia_active = False
			trivia_answers = {}
			trivia_bets = {}
		elif len(message.content.split()) > 2 and message.content.split()[1] == "bet" and message.content.split()[2].isdigit() and trivia_bet:
			trivia_bets[message.author] = int(message.content.split()[2])
			await client.send_message(message.channel, message.author.name + " has bet $" + message.content.split()[2])
		elif len(message.content.split()) > 1 and message.content.split()[1] == "start" and trivia_bet:
			trivia_bet = False
		elif not trivia_active:
			trivia_active = True
			# url = "http://api.futuretraxex.com/v1/getRandomQuestion
			url = "http://jservice.io/api/random"
			async with aiohttp_session.get(url) as resp:
				data = await resp.json()
			data = data[0]
			# await client.send_message(message.channel, BeautifulSoup(html.unescape(data["q_text"]), "html.parser").get_text() + "\n1. " + data["q_options_1"] + "\n2. " + data["q_options_2"] + "\n3. " + data["q_options_3"] + "\n4. " + data["q_options_4"])
			await client.send_message(message.channel, "Category: " + string.capwords(data["category"]["title"]) + "\n" + data["question"])
			counter = 15
			answer_message = await client.send_message(message.channel, "You have " + str(counter) + " seconds left to answer.")
			while counter:
				await asyncio.sleep(1)
				counter -= 1
				try:
					await client.edit_message(answer_message, "You have " + str(counter) + " seconds left to answer.")
				except:
					trivia_active = False
			await client.edit_message(answer_message, "Time's up!")
			correct_players = []
			incorrect_players = []
			for player, answer in trivia_answers.items():
				# if answer == data["q_correct_option"]:
				if answer.lower() == data["answer"].lower() or answer.lower() == BeautifulSoup(html.unescape(data["answer"]), "html.parser").get_text().lower() or "a " + answer.lower() == data["answer"].lower() or "an " + answer.lower() == data["answer"].lower() or "the " + answer.lower() == data["answer"].lower():
					correct_players.append(player)
				else:
					incorrect_players.append(player)
			correct_players_output = ""
			if len(correct_players) == 0:
				correct_players_output = "Nobody got it right!"
			else:
				if len(correct_players) == 1:
					correct_players_output = correct_players[0].name + " was right!"
				elif len(correct_players) == 2:
					correct_players_output = correct_players[0].name + " and " + correct_players[1].name + " were right!"
				elif len(correct_players) > 2:
					for i in range(len(correct_players) - 1):
						correct_players_output += correct_players[i].name + ", "
					correct_players_output += "and " + correct_players[len(correct_players) - 1].name + " were right!"
			with open("data/trivia_points.json", "r") as trivia_file:
				score = json.load(trivia_file)
			for correct_player in correct_players:
				if correct_player.id in score:
					score[correct_player.id][0] += 1
				else:
					score[correct_player.id] = [1, 0, 100000]
			for incorrect_player in incorrect_players:
				if incorrect_player.id in score:
					score[incorrect_player.id][1] += 1
				else:
					score[incorrect_player.id] = [0, 1, 100000]
			with open("data/trivia_points.json", "w") as trivia_file:
				json.dump(score, trivia_file)
			# await client.send_message(message.channel, "The answer was " + str(data["q_correct_option"]) + ". " + data["q_options_" + str(data["q_correct_option"])] + "\n" + correct_players_output)
			await client.send_message(message.channel, "The answer was " + BeautifulSoup(html.unescape(data["answer"]), "html.parser").get_text() + "\n" + correct_players_output)
			trivia_active = False
			trivia_answers = {}
		else:
			pass
	elif trivia_active and not (message.content.startswith('!') or message.server.me in message.mentions):
		trivia_answers[message.author] = message.content
	elif message.content.lower() == 'f':
		with open("data/f.json", "r") as counter_file:
			counter_info = json.load(counter_file)
		counter_info["counter"] += 1
		with open("data/f.json", "w") as counter_file:
			json.dump(counter_info, counter_file)
		await client.send_message(message.channel, message.author.name + " has paid their respects.\nRespects paid so far: " + str(counter_info["counter"]))
	elif re.match(r"^!(\w+)to(\w+)", message.content.split()[0], re.I): # conversions
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not is_number(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			value = float(message.content.split()[1])
			units = re.match(r"^!(\w+)to(\w+)", message.content.split()[0], re.I)
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
				return
			await send_mention_space(message, str(value) + ' ' + unit1 + " = " + str(converted_value) + ' ' + unit2)

@client.event
async def on_command_error(error, ctx):
	if isinstance(error, (errors.NotServerOwner, errors.MissingPermissions)):
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
	elif isinstance(error, commands.errors.CommandInvokeError) and isinstance(error.original, (errors.NoTag, errors.NoTags)):
		pass
	else:
		print("Ignoring exception in command {}".format(ctx.command), file = sys.stderr)
		traceback.print_exception(type(error), error, error.__traceback__, file = sys.stderr)

try:
	client.loop.create_task(check_rss_feeds())
	client.loop.run_until_complete(client.start(credentials.token))
except KeyboardInterrupt:
	print("Shutting down Harmonbot...")
	client.loop.run_until_complete(restart_tasks())
	client.loop.run_until_complete(client.logout())
finally:
	client.loop.close()

