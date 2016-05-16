
print("Starting up...")

import discord
from discord.ext import commands

import asyncio
from bs4 import BeautifulSoup
import json
import html
import inflect
import isodate
import logging
import math
import moviepy.editor
import os
import pydealer
import random
import re
import requests
import spotipy
import string
#import subprocess
import sys
import time
import traceback
import urllib
#import xml.etree.ElementTree
import wolframalpha
import youtube_dl

from modules import ciphers
from modules import conversions
from modules import documentation
#from modules import gofish
from modules.maze import maze
from modules import permissions
from modules.utilities import *
from modules.voice import *
from modules import war
from modules import weather

from commands.games import Games

from utilities import checks

import keys
from client import client
from client import rss_client

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode='a')
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)

'''
class TokenBot(discord.Client):

    def run(self, token):
        self.token = token
        self.headers['authorization'] = token
        self._is_logged_in.set()
        try:
            self.loop.run_until_complete(self.connect())
        except KeyboardInterrupt:
            self.loop.run_until_complete(self.logout())
            pending = asyncio.Task.all_tasks()
            gathered = asyncio.gather(*pending)
            try:
                gathered.cancel()
                self.loop.run_forever()
                gathered.exception()
            except:
                pass
        finally:
            self.loop.close()

			
client = TokenBot()
'''

waclient = wolframalpha.Client(keys.wolframalpha_appid)
spotify = spotipy.Spotify()
inflect_engine = inflect.engine()

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
maze_started = False
maze_maze = None
taboo_players = []
#wolframalpha (wa)

@client.event
async def on_ready():
	print("Started up {0} ({1})".format(str(client.user), client.user.id))
	if os.path.isfile("data/restart_channel.json"):
		with open("data/restart_channel.json", "r") as restart_channel_file:
			restart_channel = client.get_channel(json.load(restart_channel_file)["restart_channel"])
		os.remove("data/restart_channel.json")
		await client.send_message(restart_channel, "Restarted.")
	await random_game_status()
	await set_streaming_status(client)
	#loop = asyncio.ProactorEventLoop()
	#asyncio.set_event_loop(loop)
	#loop.run_until_complete(asyncio.create_subprocess_exec(*["py", "-3.5", "rss_bot.py"]))

@client.command(hidden = True)
async def test2():
	await client.say("testing")

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
	if message.author == client.user:
		return
	elif not message.channel.is_private and not permissions.get_permission(message, "user", message.author.id, message.content.split()[0]) and keys.myid != message.author.id:
		await send_mention_space(message, "You don't have permision to use that command here")
	elif message.content.startswith("!test_on_message"):
		await client.send_message(message.channel, "Hello, World!")
	elif message.content.startswith("!commands"):
		await client.send_message(message.author, documentation.commands)
		await client.send_message(message.channel, message.author.mention + " Check your DM's for my commands.")
	elif message.content.startswith(("!help", "!whatis")):
		if message.content.startswith("!help") and len(message.content.split()) == 1:
			await send_mention_space(message, "I've DM'ed you my commands. Also see !commands. What else do you need help with?")
		elif message.content.startswith("!whatis") and len(message.content.split()) == 1:
			await send_mention_space(message, "What is what?")
		elif message.content.split()[1] == "commands":
			await client.send_message(message.author, documentation.commands)
			await send_mention_space(message, "Check your DM's for my commands.")
		elif documentation.commands_info.get(message.content.split()[1], 0):
			await send_mention_space(message, documentation.commands_info[message.content.split()[1]])
		else:
			await send_mention_space(message, "I don't know what that is.")
	elif message.server.me in message.mentions:
		mentionless_message = ""
		for word in message.clean_content.split():
			if not word.startswith("@"):
				mentionless_message += word
		await send_mention_space(message, Games.cleverbot_instance.ask(mentionless_message))
	elif message.content.startswith("!decode"):
		if message.content.split()[1] == "morse":
			await send_mention_space(message, '`' + ciphers.decode_morse(' '.join(message.content.split()[2:])) + '`')
		elif message.content.split()[1] == "reverse":
			await send_mention_space(message, '`' + ' '.join(message.content.split()[2:])[::-1] + '`')
		elif message.content.split()[1] == "caesar" or message.content.split()[1] == "rot":
			if len(message.content.split()) < 4 or not ((message.content.split()[2].isdigit() and 0 <= int(message.content.split()[2]) <= 26) or message.content.split()[2] == "brute"):
				await send_mention_space(message, "Invalid Format. !decode caesar <key (0 - 26) or brute> <content>")
			elif message.content.split()[2] == "brute":
				await send_mention_space(message, '`' + ciphers.brute_force_caesar(' '.join(message.content.split()[3:])) + '`')
			else:
				await send_mention_space(message, '`' + ciphers.decode_caesar(' '.join(message.content.split()[3:]), message.content.split()[2]) + '`')
	elif message.content.startswith(("!delete", "!purge")):
		# if not message.channel.permissions_for(message.author).manage_messages:
			# await send_mention_space(message, "You don't have permission to do that here.")
		if message.channel.is_private:
			if message.content.split()[1].isdigit():
				number = int(message.content.split()[1])
				count = 0
				async for client_message in client.logs_from(message.channel, limit = 10000):
					if client_message.author == client.user:
						await client.delete_message(client_message)
						await asyncio.sleep(0.2)
						count += 1
						if count == number:
							break
			else:
				await client.send_message(message.channel, "Syntax error.")
		elif not message.server.me.permissions_in(message.channel).manage_messages:
			await send_mention_space(message, "I don't have permission to do that here. I need the \"Manage Messages\" permission to delete messages.")
		elif message.channel.permissions_for(message.author).manage_messages or message.author.id == keys.myid:
			name = message.content.split()[1]
			if name.isdigit():
				number = int(name)
				await client.delete_message(message)
				await client.purge_from(message.channel, limit = number)
			elif len(message.content.split()) > 2 and message.content.split()[2].isdigit():
				number = int(message.content.split()[2])
				to_delete = []
				count = 0
				await client.delete_message(message)
				async for client_message in client.logs_from(message.channel, limit = 10000):
					if client_message.author.name == name:
						to_delete.append(client_message)
						count += 1
						if count == number:
							break
						elif len(to_delete) == 100:
							await client.delete_messages(to_delete)
							to_delete = []
							await asyncio.sleep(1)
				if len(to_delete) == 1:
					await client.delete_message(to_delete[0])
				elif len(to_delete) > 1:
					await client.delete_messages(to_delete)
			else:
				await send_mention_space(message, "Syntax error.")
	elif message.content.startswith("!encode"):
		if message.content.split()[1] == "morse":
			await send_mention_space(message, '`' + ciphers.encode_morse(' '.join(message.content.split()[2:])) + '`')
		elif message.content.split()[1] == "reverse":
			await send_mention_space(message, '`' + ' '.join(message.content.split()[2:])[::-1] + '`')
		elif message.content.split()[1] == "caesar" or message.content.split()[1] == "rot":
			if len(message.content.split()) < 4 or not (message.content.split()[2].isdigit() and 0 <= int(message.content.split()[2]) <= 26):
				await send_mention_space(message, "Invalid Format. !encode caesar <key (0 - 26)> <content>")
			else:
				await send_mention_space(message, '`' + ciphers.encode_caesar(' '.join(message.content.split()[3:]), message.content.split()[2]) + '`')
	elif message.content.startswith("!eval"):
		if message.author.id == keys.myid:
			try:
				await send_mention_code(message, str(eval(" ".join(message.content.split()[1:]))))
			except:
				await send_mention_code(message, traceback.format_exc())
	elif message.content.startswith("!exec"):
		if message.author.id == keys.myid:
			exec(" ".join(message.content.split()[1:]))
			await send_mention_space(message, "successfully executed")
	elif message.content.startswith("!getpermission"):
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
	elif message.content.startswith("!gofish"): #WIP
		if message.content.split()[1] == "start" and message.author.id == keys.myid:
			global gofish_channel, gofish_players
			gofish_players = []
			number_of_players = int(message.content.split()[2])
			if message.server:
				for i in range(number_of_players):
					for member in message.server.members:
						if member.name == message.content.split()[i + 3]:
							gofish_players.append(member)
							break
			else:
				await send_mention_space(message, "Please use that command in a server.")
				pass
			gofish.start(number_of_players)
			gofish_channel = message.channel
			gofish_players_string = ""
			for player in gofish_players:
				gofish_players_string += player.name + " and "
			await client.send_message(message.channel, message.author.name + " has started a game of Go Fish between " + gofish_players_string[:-5] + "!")
		elif message.content.split()[1] == "hand" and message.author in gofish_players:
			await client.send_message(message.author, "Your hand: " + gofish.hand(gofish_players.index(message.author) + 1))
		elif message.content.split()[1] == "ask" and message.author in gofish_players:
			pass
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
	elif message.content.startswith("!maze"):
		global maze_started, maze_maze
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter an option (start/current)")
		elif message.content.split()[1] == "start":
			if maze_started:
				await send_mention_space(message, "There's already a maze game going on.")
			elif len(message.content.split()) >= 4 and message.content.split()[2].isdigit() and message.content.split()[3].isdigit():
				maze_started = True
				maze_maze = maze(int(message.content.split()[2]), int(message.content.split()[3]))
				await send_mention_code(message, maze_maze.print_visible())
				'''
				maze_print = ""
				for r in maze_maze.test_print():
					row_print = ""
					for cell in r:
						row_print += cell + " "
					maze_print += row_print + "\n"
				await send_mention_code(message, maze_print)
				'''
				# await send_mention_code(message, repr(maze_maze))
			else:
				await send_mention_space(message, "Please enter a valid maze size. (e.g. !maze start 2 2)")
		elif message.content.split()[1] == "current":
			if maze_started:
				await send_mention_code(message, maze_maze.print_visible())
			else:
				await send_mention_space(message, "There's no maze game currently going on.")
		else:
			await send_mention_space(message, "Please enter a valid option (start/current).")
	elif maze_started and message.content.lower() in ['w', 'a', 's', 'd']:
		moved = False
		if message.content.lower() == 'w':
			moved = maze_maze.move('n')
		elif message.content.lower() == 'a':
			moved = maze_maze.move('w')
		elif message.content.lower() == 's':
			moved = maze_maze.move('s')
		elif message.content.lower() == 'd':
			moved = maze_maze.move('e')
		await send_mention_code(message, maze_maze.print_visible())
		if not moved:
			await send_mention_space(message, "You can't go that way.")
		if maze_maze.reached_end():
			await send_mention_space(message, "Congratulations! You reached the end of the maze.")
			maze_started = False
	elif message.content.startswith(("!mycolor", "!mycolour")): #rework
		if len(message.content.split()) == 1:
			color = message.author.color
			color_value = color.value
			await send_mention_space(message, str(conversions.inttohex(color_value)))
		else:
			if len(message.author.roles) == 1:
				new_role = await client.create_role(message.server, name = message.author.name, hoist = False)
				'''
				for role in message.server.roles:
					if role.name == message.author.name:
						new_role = role
						break
				'''
				await client.add_roles(message.author, new_role)
				new_colour = new_role.colour
				new_colour.value = int(message.content.split()[1], 16)
				await client.edit_role(message.server, new_role, name = message.author.name, colour = new_colour)
			elif message.author.roles[1].name == message.author.name:
				role_to_change = message.author.roles[1]
				new_colour = role_to_change.colour
				new_colour.value = int(message.content.split()[1], 16)
			await client.edit_role(message.server, role_to_change, colour = new_colour)
	elif message.content.startswith("!redditsearch"): #WIP
		pass
	elif message.content.startswith(("!rolecolor", "!rolecolour")):
		if len(message.content.split()) == 2:
			for role in message.server.roles:
				if role.name == (' ').join(message.content.split()[1].split('_')) or role.name.startswith((' ').join(message.content.split()[1].split('_'))):
					selected_role = role
					break
			color = selected_role.colour
			color_value = color.value
			await send_mention_space(message, str(conversions.inttohex(color_value)))
		elif message.channel.permissions_for(message.author).manage_roles or message.author.id == keys.myid:
			for role in message.server.roles:
				if role.name == (' ').join(message.content.split()[1].split('_')) or role.name.startswith((' ').join(message.content.split()[1].split('_'))):
					role_to_change = role
					break
			new_colour = role_to_change.colour
			new_colour.value = conversions.hextoint(message.content.split()[2])
			await client.edit_role(message.server, role_to_change, colour = new_colour)
	elif message.content.startswith("!setpermission"):
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
	elif message.content.startswith("!taboo"): #WIP
		if message.content.split()[1] == "start":
			if message.server:
				taboo_players.append(message.author)
				for member in message.server.members:
					if member.name == message.content.split()[2]:
						taboo_players.append(member)
						break
				await send_mention_space(message, " has started a game of Taboo with " + taboo_players[1].mention)
				await client.send_message(message.author, "You have started a game of Taboo with " + taboo_players[1].name)
				await client.send_message(taboo_players[1], message.author.name + " has started a game of Taboo with you.")
			else:
				await send_mention_space(message, "Please use that command in a server.")
				pass
		elif message.content.split()[1] == "nextround":
			if message.server:
				pass
	elif message.content.startswith(("!tag", "!trigger")):
		with open("data/tags.json", "r") as tags_file:
			tags_data = json.load(tags_file)
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Add a tag with `!tag add <tag> <content>`. Use `!tag <tag>` to trigger the tag you added. `!tag <edit>` to edit, `!tag <remove>` to delete")
			return
		if not message.content.split()[1] in ["add", "make", "new", "create"]:
			if not message.author.id in tags_data:
				await send_mention_space(message, "You don't have any tags :slight_frown: Add one with `!tag add <tag> <content>`")
				return
			tags = tags_data[message.author.id]["tags"]
		if message.content.split()[1] in ["edit", "remove", "delete", "destroy"] and not message.content.split()[2] in tags:
			await send_mention_space(message, "You don't have that tag.")
			return
		if len(message.content.split()) >= 3:
			if message.content.split()[1] in ["add", "make", "new", "create"]:
				if not message.author.id in tags_data:
					tags_data[message.author.id] = {"name" : message.author.name, "tags" : {}}
				tags = tags_data[message.author.id]["tags"]
				if message.content.split()[2] in tags:
					await send_mention_space(message, "You already have that tag. Use `!tag edit <tag> <content>` to edit it.")
					return
				tags[message.content.split()[2]] = ' '.join(message.content.split(' ')[3:])
				await send_mention_space(message, "Your tag has been added.")
			elif message.content.split()[1] == "edit":
				tags[message.content.split()[2]] = " ".join(message.content.split(' ')[3:])
				await send_mention_space(message, "Your tag has been edited.")
			elif message.content.split()[1] in ["remove", "delete", "destroy"]:
				del tags[message.content.split()[2]]
				await client.send_message(message.channel, "Your tag was deleted.")
			else:
				await send_mention_space(message, "Syntax error.")
			with open("data/tags.json", "w") as tags_file:
				json.dump(tags_data, tags_file)
		elif message.content.split()[1] in ["list", "all", "mine"]:
			tag_list = ", ".join(list(tags.keys()))
			await send_mention_space(message, "Your tags: " + tag_list)
		else:
			if not message.content.split()[1] in tags:
				await send_mention_space(message, "You don't have that tag.")
			else:
				await client.send_message(message.channel, tags[message.content.split()[1]])
	elif message.content.startswith("!tempchannel"):
		temp_voice_channel = discord.utils.get(message.server.channels, name = message.author.display_name + "'s Temp Channel")
		temp_text_channel = discord.utils.get(message.server.channels, name = message.author.display_name.lower() + "s_temp_channel")
		if temp_voice_channel and len(message.content.split()) > 2 and message.content.split()[1] == "allow":
			to_allow = discord.utils.get(message.server.members, name = message.content.split()[2])
			if not to_allow:
				await send_mention_space(message, "User not found.")
			voice_channel_permissions = discord.Permissions.none()
			voice_channel_permissions.connect = True
			voice_channel_permissions.speak = True
			voice_channel_permissions.use_voice_activation = True
			await client.edit_channel_permissions(temp_voice_channel, to_allow, allow = voice_channel_permissions)
			text_channel_permissions = discord.Permissions.text()
			text_channel_permissions.manage_messages = False
			await client.edit_channel_permissions(temp_text_channel, to_allow, allow = text_channel_permissions)
			await send_mention_space(message, "You have allowed " + to_allow.display_name + " to join your temporary voice and text channel.")
			return
		if temp_voice_channel:
			await send_mention_space(message, "You already have a temporary voice and text channel.")
			return
		temp_voice_channel = await client.create_channel(message.server, message.author.display_name + "'s Temp Channel", type = discord.ChannelType.voice)
		temp_text_channel = await client.create_channel(message.server, message.author.display_name + "s_Temp_Channel", type = discord.ChannelType.text)
		await client.edit_channel_permissions(temp_voice_channel, message.server.me, allow = discord.Permissions.all())
		await client.edit_channel_permissions(temp_text_channel, message.server.me, allow = discord.Permissions.all())
		await client.edit_channel_permissions(temp_voice_channel, message.author.roles[0], deny = discord.Permissions.all())
		await client.edit_channel_permissions(temp_text_channel, message.author.roles[0], deny = discord.Permissions.all())
		await client.edit_channel_permissions(temp_voice_channel, message.author, allow = discord.Permissions.all())
		await client.edit_channel_permissions(temp_text_channel, message.author, allow = discord.Permissions.all())
		try:
			await client.move_member(message.author, temp_voice_channel)
		except discord.errors.Forbidden:
			await send_mention_space(message, "I can not move you to the new temporary voice channel.")
		await send_mention_space(message, "Temporary voice and text channel created")
		while True:
			await asyncio.sleep(15)
			temp_voice_channel = discord.utils.get(message.server.channels, id = temp_voice_channel.id)
			if len(temp_voice_channel.voice_members) == 0:
				await client.edit_channel_permissions(temp_voice_channel, message.server.me, allow = discord.Permissions.all())
				await client.edit_channel_permissions(temp_text_channel, message.server.me, allow = discord.Permissions.all())
				await client.delete_channel(temp_voice_channel)
				await client.delete_channel(temp_text_channel)
				return
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
	elif message.content.startswith("!war"):
		if message.content.split()[1] == "start" and message.author.id == keys.myid:
			global war_channel, war_players
			war_players = []
			number_of_players = int(message.content.split()[2])
			if message.server:
				for i in range(number_of_players):
					for member in message.server.members:
						if member.name == message.content.split()[i + 3]:
							war_players.append(member)
							break
			else:
				await send_mention_space(message, "Please use that command in a server.")
				pass
			war.start(number_of_players)
			war_channel = message.channel
			war_players_string = ""
			for player in war_players:
				war_players_string += player.name + " and "
			await client.send_message(message.channel, message.author.name + " has started a game of War between " + war_players_string[:-5] + "!")
		elif message.content.split()[1] == "hand" and message.author in war_players:
			await client.send_message(message.author, "Your hand: " + war.hand(war_players.index(message.author) + 1))
		elif message.content.split()[1] == "left" and message.author in war_players:
			await send_mention_space(message, "You have " + str(war.card_count(war_players.index(message.author) + 1)) + " cards left.")
		elif message.content.split()[1] == "play" and message.author in war_players:
			player_number = war_players.index(message.author) + 1
			winner, cardsplayed, tiedplayers = war.play(player_number, " ".join(message.content.split()[2:]))
			if winner == -1:
				await send_mention_space(message, "You have already chosen your card for this battle.")
			elif winner == -3:
				await send_mention_space(message, "You are not in this battle.")
			elif winner == -4:
				await send_mention_space(message, "Card not found in your hand.")
			else:
				await send_mention_space(message, "You chose the " + cardsplayed[player_number - 1].value + " of " + cardsplayed[player_number - 1].suit)
				await client.send_message(message.author, "Your hand: " + war.hand(player_number))
			if winner > 0:
				winner_name = war_players[winner - 1].name
				cards_played_print = ""
				for i in range(len(war_players)):
					cards_played_print += war_players[i].name + " played " + cardsplayed[i].value + " of " + cardsplayed[i].suit + " and "
				cards_played_print = cards_played_print[:-5] + "."
				await client.send_message(war_channel, winner_name + " wins the battle.\n" + cards_played_print)
				for war_player in war_players:
					await client.send_message(war_player, winner_name + " wins the battle.\n" + cards_played_print)
			if winner == -2:
				cards_played_print = ""
				for i in range(len(war_players)):
					cards_played_print += war_players[i].name + " played " + cardsplayed[i].value + " of " + cardsplayed[i].suit + " and "
				cards_played_print = cards_played_print[:-5] + "."
				tiedplayers_print = ""
				for tiedplayer in tiedplayers:
					tiedplayers_print += war_players[tiedplayer - 1].name + " and "
				tiedplayers_print = tiedplayers_print[:-5] + " tied.\n"
				await client.send_message(war_channel, tiedplayers_print + cards_played_print)
				for war_player in war_players:
					await client.send_message(war_player, tiedplayers_print + cards_played_print)
				pass
	elif message.content.startswith("!webmtogif"):
		webmfile = urllib.request.urlretrieve(message.content.split()[1], "data/webtogif.webm")
		# subprocess.call(["ffmpeg", "-i", "data/webtogif.webm", "-pix_fmt", "rgb8", "data/webtogif.gif"], shell=True)
		clip = moviepy.editor.VideoFileClip("data/webtogif.webm")
		clip.write_gif("data/webtogif.gif", fps=1, program="ffmpeg")
		# clip.write_gif("data/webtogif.gif", fps=15, program="ImageMagick", opt="optimizeplus")
		await client.send_file(message.channel, "data/webtogif.gif")
		#subprocess.call(["ffmpeg", "-i", "data/webtogif.webm", "-pix_fmt", "rgb8", "data/webtogif.gif"], shell=True)
		#await client.send_file(message.channel, "data/webtogif.gif")
	elif message.content.startswith("!weather"):
		await send_mention_space(message, str(weather.temp(' '.join(message.content.split()[1:]))))
	elif message.content.startswith(("!wolframalpha", "!wa")):
		if message.author.id == keys.myid:
			result = waclient.query(" ".join(message.content.split()[1:]))
			for pod in result.pods:
				await client.send_message(message.channel, message.author.mention + " " + pod.img)
				await client.send_message(message.channel, message.author.mention + " " + pod.text)
			#await client.send_message(message.channel, message.author.mention + " " + next(result.results).text)
	elif message.content.startswith(("!youtube", "!soundcloud", "!audio", "!yt", "!voice", "!stream", 
		"!playlist", "!spotify", "!radio", "!tts")):
		if message.author.id == keys.myid or message.author.id == "108131092430589952":
			if message.content.split()[1] == "join":
				await join_voice_channel(message)
				return
			elif not client.is_voice_connected(message.server):
				await send_mention_space(message, "I'm not in a voice channel. Please use `!voice (or !yt) join <channel>` first.")
				return
			elif message.content.split()[1] == "leave":
				await leave_voice_channel(message)
				await send_mention_space(message, "I've left the voice channel.")
				return
			elif message.content.split()[1] == "pause" or message.content.split()[1] == "stop":
				await player_pause(message)
				await send_mention_space(message, "Song paused")
				return
			elif message.content.split()[1] == "resume" or message.content.split()[1] == "start":
				await player_resume(message)
				await send_mention_space(message, "Song resumed")
				return
			elif message.content.split()[1] == "skip" or message.content.split()[1] == "next":
				await player_skip(message)
				await send_mention_space(message, "Song skipped")
				return
			elif message.content.split()[1] in ["restart", "replay", "repeat"]:
				await player_restart(message)
				return
			elif message.content.split()[1] == "empty" or message.content.split()[1] == "clear":
				await player_empty_queue(message)
				await send_mention_space(message, "Queue emptied")
				return
			elif message.content.split()[1] == "shuffle":
				response = await send_mention_space(message, "Shuffling...")
				await player_shuffle_queue(message)
				await client.edit_message(response, message.author.mention + " Shuffled songs")
				return
			elif message.content.split()[0] == "!radio" or message.content.split()[1] == "radio":
				if message.content.split()[1] in ["on", "start"] or (len(message.content.split()) > 2 and message.content.split()[2] in ["on", "start"]):
					await player_start_radio(message)
				elif message.content.split()[1] in ["off", "stop"] or (len(message.content.split()) > 2 and message.content.split()[2] in ["off", "stop"]):
					await player_stop_radio(message)
				return
			elif message.content.split()[0] == "!tts" or message.content.split()[1] == "tts":
				await tts(message)
				return
			elif message.content.split()[1] == "volume" and is_number(message.content.split()[2]):
				await player_volume(message, float(message.content.split()[2]) / 100)
				return
			elif message.content.split()[1] == "full":
				return
		if not client.is_voice_connected(message.server):
			await send_mention_space(message, "I'm not in a voice channel. Please ask someone with permission to use `!voice (or !yt) join <channel>` first.")
		elif message.content.split()[0] in ["!radio"] or message.content.split()[1] in ["join", "leave", "pause", "stop", "resume", "start", "skip", "next", "restart", "replay", "empty", "clear", "shuffle", "radio", "volume"]:
			await send_mention_space(message, "You don't have permission to do that.")
		elif message.content.split()[1] == "current" or message.content.split()[1] == "queue":
			current = player_current(message)
			if not current:
				await client.send_message(message.channel, "There is no song currently playing.")
			else:
				if add_commas(current["stream"].views):
					views = add_commas(current["stream"].views)
				else:
					views = ""
				if add_commas(current["stream"].likes):
					likes = add_commas(current["stream"].likes)
				else:
					likes = ""
				if add_commas(current["stream"].dislikes):
					dislikes = add_commas(current["stream"].dislikes)
				else:
					dislikes = ""
				await client.send_message(message.channel, "Currently playing: " + current["stream"].url + "\n" + views + ":eye: | " + likes + ":thumbsup::skin-tone-2: | " + dislikes + ":thumbsdown::skin-tone-2:\nAdded by: " + current["author"].name)
			if radio_on(message):
				await client.send_message(message.channel, ":radio: Radio is currently on")
			else:
				queue = player_queue(message)
				if not queue:
					await client.send_message(message.channel, "The queue is currently empty.")
				else:
					queue_string = ""
					count = 1
					for stream in list(queue._queue):
						if count <= 10:
							queue_string += ':' + inflect_engine.number_to_words(count) + ": **" + stream["stream"].title + "** (`" + stream["stream"].url + "`) Added by: " + stream["author"].name + "\n"
							count += 1
						else:
							more_songs = queue.qsize() - 10
							queue_string += "There " + inflect_engine.plural("is", more_songs) + " " + str(more_songs) + " more " + inflect_engine.plural("song", more_songs) + " in the queue"
							break
					await client.send_message(message.channel, "\nQueue:\n" + queue_string)
		elif "playlist" in message.content:
			await player_add_playlist(message)
		elif "spotify" in message.content:
			stream = await player_add_spotify_song(message)
			if stream:
				await send_mention_space(message, "Your song, " + stream.title + ", has been added to the queue.")
			else:
				await send_mention_space(message, "Error")
		else:
			response = await send_mention_space(message, "Loading...")
			added = await player_add_song(message)
			if not added:
				await send_mention_space(message, "Error")
			else:
				await client.edit_message(response, message.author.mention + " Your song has been added to the queue.")
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
