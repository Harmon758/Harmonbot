
print("Starting up...")

import discord
from discord.ext import commands

import asyncio
from bs4 import BeautifulSoup
import json
import html
import logging
import moviepy.editor
import os
# import pydealer
import re
import requests
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
from modules.voice import *

from commands.games import Games

from utilities import errors

import keys
from client import client
#from client import rss_client

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode='a')
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)

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
		json.dump({"uptime" : 0, "restarts" : 0}, stats_file)
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
		await client.send_message(restart_channel, "Restarted.")
		for voice_channel in restart_data["voice_channels"]:
			await client.join_voice_channel(client.get_channel(voice_channel))
	await random_game_status()
	await set_streaming_status(client)
	#loop = asyncio.ProactorEventLoop()
	#asyncio.set_event_loop(loop)
	#loop.run_until_complete(asyncio.create_subprocess_exec(*["py", "-3.5", "rss_bot.py"]))

@client.event
async def on_message(message):
	global trivia_answers
	await client.process_commands(message)
	if message.channel.is_private and not (message.author == client.user and message.channel.user.id == keys.myid):
		for member in client.get_all_members():
			if member.id == keys.myid:
				my_member = member
				break
		if message.author == client.user:
			await client.send_message(my_member, "To " + message.channel.user.name + '#' + message.channel.user.discriminator + ": " + message.content)
		else:
			await client.send_message(my_member, "From " + message.author.name + '#' + message.author.discriminator + ": " + message.content)
	if message.author == client.user or not message.content:
		return
	elif not message.channel.is_private and not permissions.get_permission(message, "user", message.author.id, message.content.split()[0]) and keys.myid != message.author.id: #rework
		await send_mention_space(message, "You don't have permision to use that command here")
	elif message.content.startswith("!test_on_message"):
		await client.send_message(message.channel, "Hello, World!")
	elif message.content.startswith("!help"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "I've DM'ed you my commands. Also see !commands. What else do you need help with?")
		elif documentation.commands_info.get(message.content.split()[1], 0):
			await send_mention_space(message, documentation.commands_info[message.content.split()[1]])
		#else:
			#await send_mention_space(message, "Check your DMs.")
	elif message.server and message.server.me in message.mentions:
		mentionless_message = ""
		for word in message.clean_content.split():
			if not word.startswith("@"):
				mentionless_message += word
		await send_mention_space(message, Games.cleverbot_instance.ask(mentionless_message))
	elif message.content.startswith("!aeval"):
		if message.author.id == keys.myid:
			try:
				await send_mention_code(message, str(await eval(" ".join(message.content.split()[1:]))))
			except:
				await send_mention_code(message, traceback.format_exc())
	elif message.content.startswith("!eval"):
		if message.author.id == keys.myid:
			try:
				await send_mention_code(message, str(eval(" ".join(message.content.split()[1:]))))
			except:
				await send_mention_code(message, traceback.format_exc())
	elif message.content.startswith("!exec"):
		if message.author.id == keys.myid:
			try:
				exec(" ".join(message.content.split()[1:]))
				await send_mention_space(message, "successfully executed")
			except:
				await send_mention_code(message, traceback.format_exc())
	elif message.content.startswith("!getpermission"): #rework
		if len(message.content.split()) < 4:
			await send_mention_space(message, "Invalid input")
		else:
			type = message.content.split()[1]
			if type == "everyone":
				to_find = message.content.split()[2]
			elif type == "role":
				role_names = []
				for role in message.server.roles:
					role_names.append(remove_symbols(role.name))
				if role_names.count(message.content.split()[2]) > 1:
					await send_mention_space(message, "Error: multiple roles with this name")
				elif role_names.count(message.content.split()[2]) == 0:
					await send_mention_space(message, "Error: role with this name not found")
				else:
					for role in message.server.roles:
						if remove_symbols(role.name) == message.content.split()[2]:
							to_find = role.id
							break
			elif type == "user":
				pass
			else:
				await send_mention_space(message, "Invalid permission type")
			permission = message.content.split()[3]
			permissions.get_permission(message, type, to_find, permission)
	elif message.content.startswith("!jeopardy"):
		global jeopardy_active, jeopardy_question_active, jeopardy_board, jeopardy_answer, jeopardy_answered, jeopardy_scores, jeopardy_board_output, jeopardy_max_width
		if len(message.content.split()) > 1 and message.content.split()[1] == "start" and not jeopardy_active:
			jeopardy_active = True
			categories = []
			category_titles = []
			jeopardy_board_output = ""
			url = "http://jservice.io/api/random"
			for i in range(6):
				categories.append(requests.get(url).json()[0]["category_id"])
			for category in categories:
				url = "http://jservice.io/api/category?id=" + str(category)
				data = requests.get(url).json()
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
					data = requests.get(url).json()
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
	elif message.content.startswith("!setpermission"): #rework
		if message.author.id == keys.myid or message.author == message.server.owner:
			if len(message.content.split()) < 5:
				await send_mention_space(message, "Invalid input")
			else:
				type = message.content.split()[1]
				if type == "everyone":
					to_set = message.content.split()[2]
				elif type == "role":
					role_names = []
					for role in message.server.roles:
						role_names.append(remove_symbols(role.name))
					if role_names.count(' '.join(message.content.split()[2].split('_'))) > 1:
						await send_mention_space(message, "Error: multiple roles with this name")
						return
					elif role_names.count(' '.join(message.content.split()[2].split('_'))) == 0:
						await send_mention_space(message, "Error: role with this name not found")
						return
					else:
						for role in message.server.roles:
							if remove_symbols(role.name) == ' '.join(message.content.split()[2].split('_')):
								to_set = role.id
								break
				elif type == "user":
					if re.match(r"^(\w+)#(\d{4})", message.content.split()[2]):
						user_info = re.match(r"^(\w+)#(\d{4})", message.content.split()[2])
						user_name = ' '.join(user_info.group(1).split('_'))
						user_discriminator = user_info.group(2)
						to_set = False
						for member in message.server.members:
							if member.name == user_name and str(member.discriminator) == user_discriminator:
								to_set = member.id
								break
						if not to_set:
							await send_mention_space(message, "Error: user not found")
							return
					else:
						user_names = []
						for member in message.server.members:
							user_names.append(member.name)
						if user_names.count(' '.join(message.content.split()[2].split('_'))) > 1:
							await send_mention_space(message, "Error: multiple users with this name; please include discriminator")
							return
						elif user_names.count(' '.join(message.content.split()[2].split('_'))) == 0:
							await send_mention_space(message, "Error: user with this name not found")
						else:
							for member in message.server.members:
								if member.name == ' '.join(message.content.split()[2].split('_')):
									to_set = member.id
									break
				else:
					await send_mention_space(message, "Invalid permission type")
					return
				permission = message.content.split()[3]
				if message.content.split()[4].lower() in ["yes", "true", "on"]:
					setting = True
				elif message.content.split()[4].lower() in ["no", "false", "off"]:
					setting = False
				else:
					await send_mention_space(message, "Invalid permission setting")
					return
				permissions.set_permission(message, type, to_set, permission, setting)
				await send_mention_space(message, "Permission updated")
	elif message.content.startswith("!trivia"):
		global trivia_active, trivia_bet, trivia_bets
		if len(message.content.split()) > 1 and (message.content.split()[1] == "score" or message.content.split()[1] == "points"):
			with open("data/trivia_points.json", "r") as trivia_file:
				score = json.load(trivia_file)
			correct = score[message.author.id][0]
			incorrect = score[message.author.id][1]
			correct_percentage = round(float(correct) / (float(correct) + float(incorrect)) * 100, 2)
			await send_mention_space(message, "You have answered " + str(correct) + "/" + str(correct + incorrect) + " (" + str(correct_percentage) + "%) correctly.")
		elif len(message.content.split()) > 1 and (message.content.split()[1] == "cash" or message.content.split()[1] == "money"):
			with open("data/trivia_points.json", "r") as trivia_file:
				score = json.load(trivia_file)
			cash = score[message.author.id][2]
			await send_mention_space(message, "You have $" + add_commas(cash))
		elif len(message.content.split()) > 1 and message.content.split()[1] == "bet" and not trivia_bet:
			trivia_bet = True
			url = "http://jservice.io/api/random"
			data = requests.get(url).json()[0]
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
			data = requests.get(url).json()[0]
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
	elif message.content.startswith("!webmtogif"):
		webmfile = urllib.request.urlretrieve(message.content.split()[1], "data/webtogif.webm")
		# subprocess.call(["ffmpeg", "-i", "data/webtogif.webm", "-pix_fmt", "rgb8", "data/webtogif.gif"], shell=True)
		clip = moviepy.editor.VideoFileClip("data/webtogif.webm")
		clip.write_gif("data/webtogif.gif", fps=1, program="ffmpeg")
		# clip.write_gif("data/webtogif.gif", fps=15, program="ImageMagick", opt="optimizeplus")
		await client.send_file(message.channel, "data/webtogif.gif")
		#subprocess.call(["ffmpeg", "-i", "data/webtogif.webm", "-pix_fmt", "rgb8", "data/webtogif.gif"], shell=True)
		#await client.send_file(message.channel, "data/webtogif.gif")
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
			await send_mention_space(message, str(value) + " " + unit1 + " = " + str(converted_value) + " " + unit2)

@client.event
async def on_command_error(error, ctx):
	if isinstance(error, errors.NotServerOwner):
		await send_mention_space(ctx.message, "You don't have permission to do that.")
	elif isinstance(error, errors.SO_VoiceNotConnected):
		await send_mention_space(ctx.message, "I'm not in a voice channel. Please use `!voice (or !yt) join <channel>` first.")
	elif isinstance(error, errors.NSO_VoiceNotConnected):
		await send_mention_space(ctx.message, "I'm not in a voice channel. Please ask someone with permission to use `!voice (or !yt) join <channel>` first.")
		
#client.run(keys.username, keys.password)
#client.run(keys.token)

loop = asyncio.get_event_loop()
try:
	loop.run_until_complete(client.start(keys.token))
except KeyboardInterrupt:
	print("Shutting down...")
	loop.run_until_complete(restart_tasks())
	loop.run_until_complete(client.logout())
	# loop.run_until_complete(rss_client.logout())
finally:
	loop.close()
