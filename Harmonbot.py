
print("Starting up...")

import discord
# from discord.ext import commands
import asyncio
from bs4 import BeautifulSoup
import chess
import cleverbot
import datetime
import json
import html
import inflect
import isodate
import logging
import math
import moviepy.editor
import os
import pydealer
import queue
import random
import re
import requests
import spotipy
import string
import subprocess
import sys
import time
import traceback
import urllib
import xml.etree.ElementTree
import wolframalpha
import youtube_dl

from modules import ciphers
from modules import conversions
from modules import documentation
from modules import gofish
from modules.maze import maze
from modules import permissions
from modules.utilities import *
from modules.voice import *
from modules import war

import keys
from client import client

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
board = chess.Board()
cleverbot_instance = cleverbot.Cleverbot()
inflect_engine = inflect.engine()
online_time = datetime.datetime.utcnow()

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
		json.dump({}, ags_file) #fix
except FileExistsError:
	pass

wait_time = 10.0

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

# description = '''Harmonbot'''
# bot = commands.Bot(command_prefix='!', description=description)

@client.event
async def on_ready():
	print("Logged in as")
	print(client.user.name)
	print(client.user.id)
	print("------")
	if os.path.isfile("data/restart_channel.json"):
		with open("data/restart_channel.json", "r") as restart_channel_file:
			restart_channel = client.get_channel(json.load(restart_channel_file)["restart_channel"])
		os.remove("data/restart_channel.json")
		await client.send_message(restart_channel, "Restarted.")
	await random_game_status()
	await set_streaming_status()

@client.event
async def on_message(message):
	global trivia_answers
	if (message.server == None or message.channel.is_private) and not (message.author == client.user and message.channel.user.id == keys.myid):
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
	elif not (message.server == None or message.channel.is_private) and not permissions.get_permission(message, "user", message.author.id, message.content.split()[0]) and keys.myid != message.author.id:
		await send_mention_space(message, "You don't have permision to use that command here")
	elif message.content.startswith("!test"):
		await client.send_message(message.channel, "Hello, World!")
	elif message.content.startswith("!echo"):
		await client.send_message(message.channel, message.content)
	elif message.content.startswith("!commands"):
		await client.send_message(message.author, documentation.commands)
		await client.send_message(message.channel, message.author.mention + " Check your DM's for my commands.")
	elif message.content.startswith(("!help", "!whatis")):
		if message.content.startswith("!help") and len(message.content.split()) == 1:
			await send_mention_space(message, "What do you need help with?")
		elif message.content.startswith("!whatis") and len(message.content.split()) == 1:
			await send_mention_space(message, "What is what?")
		elif message.content.split()[1] == "commands":
			await client.send_message(message.author, documentation.commands)
			await send_mention_space(message, "Check your DM's for my commands.")
		elif documentation.commands_info.get(message.content.split()[1], 0):
			await send_mention_space(message, documentation.commands_info[message.content.split()[1]])
		else:
			await send_mention_space(message, "I don't know what that is.")
	elif message.content.startswith(("!8ball", "!eightball")):
		responses = ["It is certain", "It is decidedly so", "Without a doubt", "Yes, definitely", "You may rely on it", "As I see it, yes", "Most likely",
			"Outlook good", "Yes", "Signs point to yes", "Reply hazy try again", "Ask again later", "Better not tell you now", "Cannot predit now",
			"Concentrate and ask again", "Don't count on it", "My reply is no", "My sources say no", "Outlook not so good", "Very doubtful"]
		await send_mention_space(message, random.choice(responses))
	elif message.content.startswith("!addrole"):
		if message.channel.permissions_for(message.author).manage_roles or message.author.id == keys.myid:
			if message.server:
				for member in message.server.members:
					if member.name == message.content.split()[1]:
						selected_member = member
						break
				for role in message.server.roles:
					if remove_symbols(role.name).startswith((' ').join(message.content.split()[2].split('_'))):
						selected_role = role
						break
				await client.add_roles(selected_member, selected_role)
	elif message.content.startswith("!add"):
		sum = 0.0
		numbers = []
		if not any(is_number(part) for part in message.content.split()):
			return
		for part in message.content.split():
			if is_number(part):
				sum += float(part)
				numbers.append(part)
		if sum.is_integer():
			sum = int(sum)
		await send_mention_space(message, " + ".join(numbers) + " = " + str(sum))
	elif message.content.startswith("!audiodefine"):
		url = "http://api.wordnik.com:80/v4/word.json/" + " ".join(message.content.split()[1:]) + "/audio?useCanonical=false&limit=1&api_key=" + keys.wordnik_apikey
		if requests.get(url).json():
			data = requests.get(url).json()[0]
			audio = data["fileUrl"]
			word = data["word"]
			await client.send_message(message.channel, message.author.mention + " " + word.capitalize() + ": " + audio)
		else:
			await client.send_message(message.channel, message.author.mention + " Word or audio not found.")
	elif message.content.startswith("!avatar"):
		name = " ".join(message.content.split()[1:])
		flag = True
		if message.server:
			for member in message.server.members:
				if member.name == name:
					if member.avatar_url:
						await send_mention_space(message, name + "'s avatar: " + member.avatar_url)
					else:
						await send_mention_space(message, name + "'s avatar: " + member.default_avatar_url)
					flag = False
			if flag and name:
				await client.send_message(message.channel, message.author.mention + " " + name + " was not found on this server.")
			elif flag:
				await client.send_message(message.channel, message.author.mention + " Your avatar: " + message.author.avatar_url)
		else:
			await send_mention_space(message, "Please use that command in a server.")
	elif message.content.startswith("!bing"):
		await send_mention_space(message, "http://www.bing.com/search?q=" + ('+').join(message.content.split()[1:]))
	elif message.content.startswith("!calc"):
		equation = message.content.split()
		if len(equation) >= 4 and equation[1].isnumeric and equation[3].isnumeric and (equation[2] == '+' or equation[2] == '-' or equation[2] == '*' or equation[2] == '/'):
			await client.send_message(message.channel, message.author.mention + " " + " ".join(equation[1:4]) + " = " + str(eval("".join(equation[1:4]))))
		else:
			await send_mention_space(message, "That's not a valid input.")
	elif message.content.startswith("!cat"):
		if len(message.content.split()) > 1 and (message.content.split()[1] == "categories" or message.content.split()[1] == "cats"):
			url = "http://thecatapi.com/api/categories/list"
			root = xml.etree.ElementTree.fromstring(requests.get(url).text)
			categories = ""
			for category in root.findall(".//name"):
				categories += category.text + " "
			await send_mention_space(message, categories[:-1])
		elif len(message.content.split()) > 1 and message.content.split()[1]:
			url = "http://thecatapi.com/api/images/get?format=xml&results_per_page=1&category=" + message.content.split()[1]
			root = xml.etree.ElementTree.fromstring(requests.get(url).text)
			if root.find(".//url") is not None:
				await send_mention_space(message, root.find(".//url").text)
			else:
				url = "http://thecatapi.com/api/images/get?format=xml&results_per_page=1"
				root = xml.etree.ElementTree.fromstring(requests.get(url).text)
				await send_mention_space(message, root.find(".//url").text)
		else:
			url = "http://thecatapi.com/api/images/get?format=xml&results_per_page=1"
			root = xml.etree.ElementTree.fromstring(requests.get(url).text)
			await send_mention_space(message, root.find(".//url").text)
	elif message.content.startswith("!changenickname"):
		await client.change_nickname(message.server.me, ' '.join(message.content.split()[1:]))
	elif message.content.startswith("!channel"):
		if message.channel.permissions_for(message.author).manage_channels and len(message.content.split()) >= 2:
			if message.content.split()[1] == "voice":
				await client.create_channel(message.server, message.content.split()[2], type="voice")
			elif message.content.split()[1] == "text":
				await client.create_channel(message.server, message.content.split()[2], type="text")
			else:
				await client.create_channel(message.server, message.content.split()[1], type="text")
	elif message.content.startswith("!chess"):
		if len(message.content.split()) == 1:
			await send_mention_code(message, "Options: reset, board, undo, standard algebraic notation move")
		elif message.content.split()[1] == "reset":
			board.reset()
			await send_mention_code(message, "The board has been reset.")
		elif message.content.split()[1] == "board":
			await send_mention_code(message, str(board))
		elif message.content.split()[1] == "undo":
			try:
				board.pop()
				await send_mention_code(message, str(board))
			except IndexError:
				await send_mention_code(message, "There's no more moves to undo.")
		elif message.content.split()[1] == "(╯°□°）╯︵":
			board.reset()
			await send_mention_code(message, message.author.name + " flipped the table over in anger!\nThe board has been reset.")
		else:
			try:
				board.push_san(message.content.split()[1])
				await send_mention_code(message, str(board))
			except ValueError:
				await send_mention_code(message, "Invalid move.")
		#await client.send_message(message.channel, message.author.mention + "\n" + "```" + board.__unicode__() + "```")
	elif message.content.startswith("!choose"):
		if len(message.content.split()) == 1:
			await client.send_message(message.channel, message.author.mention + " Choose between what?")
		choices = message.content.split()[1:]
		await client.send_message(message.channel, message.author.mention + " " + random.choice(choices))
	elif message.content.startswith(("!cleargame", "!clearplaying")):
		updated_game = message.server.me.game
		if updated_game and updated_game.name:
			updated_game.name = None
			await client.change_status(game = updated_game)
			await send_mention_space(message, "Game status cleared.")
		else:
			await send_mention_space(message, "There is no game status to clear.")
	elif message.content.startswith("!clearstreaming"):
		updated_game = message.server.me.game
		if updated_game and (updated_game.url or updated_game.type):
			updated_game.url = None
			if len(message.content.split()) == 1 or message.content.split()[1] != "url":
				updated_game.type = 0
			await client.change_status(game = updated_game)
			await send_mention_space(message, "Streaming status and/or url cleared.")
		else:
			await send_mention_space(message, "There is no streaming status or url to clear.")
	elif message.content.startswith(("!cleverbot", "!talk", "!ask")):
		await send_mention_space(message, cleverbot_instance.ask(" ".join(message.content.split()[1:])))
	elif message.server != None and message.server.me in message.mentions:
		mentionless_message = ""
		for word in message.clean_content.split():
			if not word.startswith("@"):
				mentionless_message += word
		await send_mention_space(message, cleverbot_instance.ask(mentionless_message))
	elif message.content.startswith("!coin"):
		number = random.randint(0, 1)
		if number == 0:
			await send_mention_space(message, "Heads!")
		else:
			await send_mention_space(message, "Tails!")
	elif message.content.startswith(("!color", "!colour")):
		if len(message.content.split()) == 1 or message.content.split()[1] == "random":
			url = "http://www.colourlovers.com/api/colors/random?numResults=1&format=json"
		elif is_hex(message.content.split()[1]) and len(message.content.split()[1]) == 6:
			url = "http://www.colourlovers.com/api/color/" + message.content.split()[1] + "?format=json"
		else:
			url = "http://www.colourlovers.com/api/colors?numResults=1&format=json&keywords=" + '+'.join(message.content.split()[1:])
		data = requests.get(url).json()[0]
		name = data["title"].capitalize()
		hex = '#' + data["hex"]
		rgb = data["rgb"]
		red = str(rgb["red"])
		green = str(rgb["green"])
		blue = str(rgb["blue"])
		hsv = data["hsv"]
		hue = str(hsv["hue"]) + chr(176) # degrees
		saturation = str(hsv["saturation"]) + '%'
		value = str(hsv["value"]) + '%'
		image = data["imageUrl"]
		await send_mention_newline(message, name + " (" + hex + ")\n" + "RGB: (" + red + ", " + green + ", " + blue + ")\nHSV: (" + hue + ", " + saturation + ", " + value + ")\n" + image)
	elif message.content.startswith(("!shutdown", "!crash", "!panic")):
		if message.author.id == keys.myid:
			await client.send_message(message.channel, "Shutting down.")
			await shutdown_tasks()
			subprocess.call(["taskkill", "/f", "/im", "cmd.exe"])
			subprocess.call(["taskkill", "/f", "/im", "python.exe"])
	elif message.content.startswith("!date"):
		url = "http://numbersapi.com/" + message.content.split()[1] + "/date"
		await send_mention_space(message, requests.get(url).text)
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
	elif message.content.startswith("!define"):
		url = "http://api.wordnik.com:80/v4/word.json/" + " ".join(message.content.split()[1:]) + "/definitions?limit=1&includeRelated=false&useCanonical=false&includeTags=false&api_key=" + keys.wordnik_apikey
		# page = urllib.request.urlopen(url)
		if requests.get(url).json():
			data = requests.get(url).json()[0]
			definition = data["text"]
			word = data["word"]
			await client.send_message(message.channel, message.author.mention + " " + word.capitalize() + ": " + definition)
		else:
			await client.send_message(message.channel, message.author.mention + " Definition not found.")
	elif message.content.startswith("!delete"):
		if not message.channel.permissions_for(message.author).manage_messages:
			# await send_mention_space(message, "You don't have permission to do that here.")
			pass
		if message.channel.permissions_for(message.author).manage_messages or message.author.id == keys.myid:
			name = message.content.split()[1]
			if name.isdigit():
				number = int(name)
			elif len(message.content.split()) > 2 and message.content.split()[2].isdigit():
				number = int(message.content.split()[2])
			else:
				await send_mention_space(message, "Syntax error.")
				return
			count = 0
			try:
				await client.delete_message(message)
				await asyncio.sleep(0.2)
				async for client_message in client.logs_from(message.channel):
					if not name.isdigit() and client_message.author.name == name and count != number:
						await client.delete_message(client_message)
						await asyncio.sleep(0.2)
						count += 1
					elif name.isdigit() and count != number:
						await client.delete_message(client_message)
						await asyncio.sleep(0.2)
						count += 1
			except discord.errors.Forbidden:
				await send_mention_space(message, "I don't have permission to do that here. I need the \"Manage Messages\" permission to delete messages.")
	elif message.content.startswith("!discriminator"):
		name = " ".join(message.content.split()[1:])
		flag = True
		if message.server:
			for member in message.server.members:
				if member.name == name:
					await client.send_message(message.channel, message.author.mention + " " + name + "'s discriminator: #" + member.discriminator)
					flag = False
			if flag and name:
				await client.send_message(message.channel, message.author.mention + " " + name + " was not found on this server.")
			elif flag:
				await client.send_message(message.channel, message.author.mention + " Your discriminator: #" + message.author.discriminator)
		else:
			await send_mention_space(message, "Please use that command in a server.")
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
			await send_mention_code(message, str(eval(" ".join(message.content.split()[1:]))))
	elif message.content.startswith("!everyone"):
		if message.author.permissions_in(message.channel).mention_everyone:
			await send_mention_space(message, "You are able to mention everyone in this channel.")
		else:
			await send_mention_space(message, "You are not able to mention everyone in this channel.")
	elif message.content.startswith("!exec"):
		if message.author.id == keys.myid:
			exec(" ".join(message.content.split()[1:]))
			await send_mention_space(message, "successfully executed")
	elif message.content.startswith("!fancify"):
		output = ""
		for letter in " ".join(message.content.split()[1:]):
			if 65 <= ord(letter) <= 90:
				output += chr(ord(letter) + 119951)
			elif 97 <= ord(letter) <= 122:
				output += chr(ord(letter) + 119919)
			elif letter == ' ':
				output += ' '
		await send_mention_space(message, output)
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
	elif message.content.startswith("!giphy"):
		if message.content.split()[1] == "random":
			url = "http://api.giphy.com/v1/gifs/random?api_key=dc6zaTOxFJmzC"
			data = requests.get(url).json()["data"]
			await send_mention_space(message, data["url"])
		elif message.content.split()[1] == "trending":
			url = "http://api.giphy.com/v1/gifs/trending?api_key=dc6zaTOxFJmzC"
			data = requests.get(url).json()["data"]
			await send_mention_space(message, data[0]["url"])
		else:
			url = "http://api.giphy.com/v1/gifs/search?q=" + "+".join(message.content.split()[1:]) + "&limit=1&api_key=dc6zaTOxFJmzC"
			data = requests.get(url).json()["data"]
			await send_mention_space(message, data[0]["url"])
	elif message.content.startswith("!gofish"):
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
	elif message.content.startswith(("!googleimage", "!imagesearch")):
		url = "https://www.googleapis.com/customsearch/v1?key={0}&cx={1}&searchType=image&q={2}".format(keys.google_apikey, keys.google_cse_cx, '+'.join(message.content.split()[1:]))
		data = requests.get(url).json()
		image_link = data["items"][0]["link"]
		await send_mention_space(message, image_link)
		# handle 403 daily limit exceeded error
	elif message.content.startswith(("!google", "!search")):
		await send_mention_space(message, "https://www.google.com/search?q=" + ('+').join(message.content.split()[1:]))
	elif message.content.startswith("!guess"):
		tries = False
		if len(message.content.split()) >= 3 and is_digit_gtz(message.content.split()[2]):
			tries = int(message.content.split()[2])
		if len(message.content.split()) >= 2 and is_digit_gtz(message.content.split()[1]):
			max_value = int(message.content.split()[1])
		else:
			await client.send_message(message.channel, message.author.mention + " What range of numbers would you like to guess to? 1 to _")
			max_value = await client.wait_for_message(timeout=wait_time, author=message.author, check=message_is_digit_gtz)
			if max_value is None:
				max_value = 10
			else:
				max_value = int(max_value.content)
		answer = random.randint(1, max_value)
		if not tries:
			await client.send_message(message.channel, message.author.mention + " How many tries would you like?")
			tries = await client.wait_for_message(timeout=wait_time, author=message.author, check=message_is_digit_gtz)
			if tries is None:
				tries = 1
			else:
				tries = int(tries.content)
		await client.send_message(message.channel, message.author.mention + " Guess a number between 1 to " + str(max_value))
		while tries != 0:
			guess = await client.wait_for_message(timeout=wait_time, author=message.author, check=message_is_digit_gtz)
			if guess is None:
				await client.send_message(message.channel, message.author.mention + " Sorry, you took too long. It was " + str(answer))
				return
			if int(guess.content) == answer:
				await client.send_message(message.channel, message.author.mention + " You are right!")
				return
			elif tries != 1 and int(guess.content) > answer:
				await client.send_message(message.channel, message.author.mention + " It's less than " + guess.content)
				tries -= 1
			elif tries != 1 and int(guess.content) < answer:
				await client.send_message(message.channel, message.author.mention + " It's greater than " + guess.content)
				tries -= 1
			else:
				await client.send_message(message.channel, message.author.mention + " Sorry, it was actually " + str(answer))
				return
	elif message.content.startswith("!haveibeenpwned"):
		url = "https://haveibeenpwned.com/api/v2/breachedaccount/" + message.content.split()[1] + "?truncateResponse=true"
		data = requests.get(url)
		if data.status_code == 404 or data.status_code == 400:
			breachedaccounts = "None"
		else:
			data = data.json()
			breachedaccounts = ""
			for breachedaccount in data:
				breachedaccounts += breachedaccount["Name"] + ", "
			breachedaccounts = breachedaccounts[:-2]
		url = "https://haveibeenpwned.com/api/v2/pasteaccount/" + message.content.split()[1]
		data = requests.get(url)
		if data.status_code == 404 or data.status_code == 400:
			pastedaccounts = "None"
		else:
			data = data.json()
			pastedaccounts = ""
			for pastedaccount in data:
				pastedaccounts += pastedaccount["Source"] + " (" + pastedaccount["Id"] + "), "
			pastedaccounts = pastedaccounts[:-2]
		await send_mention_space(message, "Breached accounts: " + breachedaccounts + "\nPastes: " + pastedaccounts)
	elif message.content.startswith("!idtoname"):
		id = message.content.split()[1]
		await send_mention_space(message, "<@" + id + ">")
	elif message.content.startswith("!imdb"):
		url = "http://www.omdbapi.com/?t=" + " ".join(message.content.split()[1:]) + "&y=&plot=short&r=json"
		data = requests.get(url).json()
		title = data["Title"]
		year = data["Year"]
		runtime = data["Runtime"]
		genre = data["Genre"]
		plot = data["Plot"]
		poster = data["Poster"]
		imdb_rating = data["imdbRating"]
		type = data["Type"]
		await client.send_message(message.channel, message.author.mention + "```\n" + title + " (" + year + ")\nType: " + type + "\nIMDb Rating: " + imdb_rating + "\nRuntime: " + runtime + "\nGenre(s): " + genre + "\nPlot: " + plot + "```Poster: " + poster)
	elif message.content.startswith("!imfeelinglucky"):
		await client.send_message(message.channel, message.author.mention + " https://www.google.com/search?btnI&q=" + ('+').join(message.content.split()[1:]))
	elif message.content.startswith("!insult"):
		url = "http://quandyfactory.com/insult/json"
		data = requests.get(url).json()
		await client.send_message(message.channel, data["insult"])
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
	elif message.content.startswith("!joke"):
		url = "http://tambal.azurewebsites.net/joke/random"
		data = requests.get(url).json()
		joke = data["joke"]
		await client.send_message(message.channel, message.author.mention + " " + joke)
	elif message.content.startswith("!libraryversion"):
		await send_mention_space(message, discord.__version__)
	elif message.content.startswith("!lmbtfy"):
		await client.send_message(message.channel, message.author.mention + " http://lmbtfy.com/?q=" + ('+').join(message.content.split()[1:]))
	elif message.content.startswith("!lmgtfy"):
		await client.send_message(message.channel, message.author.mention + " http://www.lmgtfy.com/?q=" + ('+').join(message.content.split()[1:]))
	elif message.content.startswith("!load"):
		counter = 0
		bar = chr(9633) * 10
		loading_message = await client.send_message(message.channel, "Loading: [" + bar + "]")
		while counter <= 10:
			counter += 1
			bar = chr(9632) + bar[:-1] #9608
			await asyncio.sleep(1)
			await client.edit_message(loading_message, "Loading: [" + bar + "]")
	elif message.content.startswith("!longurl"):
		url = "https://www.googleapis.com/urlshortener/v1/url?shortUrl=" + message.content.split()[1] + "&key=" + keys.google_apikey
		data = requests.get(url).json()
		await send_mention_space(message, data["longUrl"])
	elif message.content.startswith("!map"):
		if message.content.split()[1] == "random":
			latitude = random.uniform(-90, 90)
			longitude = random.uniform(-180, 180)
			await send_mention_space(message, "https://maps.googleapis.com/maps/api/staticmap?center=" + str(latitude) + "," + str(longitude) + "&zoom=13&size=600x300")
		else:
			await send_mention_space(message, "https://maps.googleapis.com/maps/api/staticmap?center=" + "+".join(message.content.split()[1:]) + "&zoom=13&size=600x300")
	elif message.content.startswith("!math"):
		url = "http://numbersapi.com/" + message.content.split()[1] + "/math"
		await send_mention_space(message, requests.get(url).text)
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
	elif message.content.startswith("!mycolor") or message.content.startswith("!mycolour"):
		if len(message.content.split()) == 1:
			selected_role = message.author.roles[1]
			color = selected_role.color
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
	elif message.content.startswith("!nametoid"):
		search_name = " ".join(message.content.split()[1:])
		member = discord.utils.get(message.server.members, name=search_name)
		await send_mention_space(message, member.id)
	elif message.content.startswith("!number"):
		url = "http://numbersapi.com/" + message.content.split()[1]
		await send_mention_space(message, requests.get(url).text)
	elif message.content.startswith("!owner"):
		await send_mention_space(message, "The owner of this server is " + message.server.owner.mention)
	elif message.content.startswith("!randomgame"):
		await random_game_status()
		# await send_mention_space(message, "I changed to a random game status.")
	elif message.content.startswith("!randomidea"):
		url = "http://itsthisforthat.com/api.php?json"
		data = requests.get(url).json()
		await send_mention_space(message, data["this"] + " for " + data["that"])
	elif message.content.startswith("!randomlocation"):
		latitude = random.uniform(-90, 90)
		longitude = random.uniform(-180, 180)
		await send_mention_space(message, str(latitude) + ", " + str(longitude))
	elif message.content.startswith("!randomword"):
		url = "http://api.wordnik.com:80/v4/words.json/randomWord?hasDictionaryDef=false&minCorpusCount=0&maxCorpusCount=-1&minDictionaryCount=1&maxDictionaryCount=-1&minLength=5&maxLength=-1&api_key=" + keys.wordnik_apikey
		data = requests.get(url).json()
		word = data["word"]
		await client.send_message(message.channel, message.author.mention + " " + word.capitalize())
	elif message.content.startswith("!redditsearch"):
		pass
	elif message.content.startswith("!restart"):
		if message.author.id == keys.myid:
			await client.send_message(message.channel, "Restarting...")
			with open("data/restart_channel.json", "x+") as restart_channel_file:
				json.dump({"restart_channel" : message.channel.id}, restart_channel_file)
			raise KeyboardInterrupt
	elif message.content.startswith("!rng"):
		if len(message.content.split()) > 1 and is_digit_gtz(message.content.split()[1]):
			await client.send_message(message.channel, message.author.mention + " " + str(random.randint(1, int(message.content.split()[1]))))
		else:
			await client.send_message(message.channel, message.author.mention + " " + str(random.randint(1, 10)))
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
	elif message.content.startswith("!roleid"):
		for role in message.server.roles:
			if remove_symbols(role.name).startswith((' ').join(message.content.split()[1].split('_'))):
				await send_mention_space(message, role.id)
	elif message.content.startswith("!servericon"):
		if message.server:
			await send_mention_space(message, "This server's icon: https://cdn.discordapp.com/icons/" + message.server.id + "/" + message.server.icon + ".jpg")
		else:
			await send_mention_space(message, "Please use that command in a server.")
	elif message.content.startswith("!serverowner"):
		if message.server:
			await send_mention_space(message, "This server is owned by " + message.server.owner.name + "#" + str(message.server.owner.discriminator))
		else:
			await send_mention_space(message, "Please use that command in a server.")
	elif message.content.startswith("!servers"):
		if message.author.id == keys.myid:
			for server in client.servers:
				server_info = "```Name: " + server.name + "\n"
				server_info += "ID: " + server.id + "\n"
				server_info += "Owner: " + server.owner.name + "\n"
				server_info += "Server Region: " + str(server.region) + "\n"
				server_info += "Members: " + str(server.member_count) + "\n"
				server_info += "Created at: " + str(server.created_at) + "\n```"
				server_info += "Icon: " + server.icon_url
				await client.send_message(message.author, server_info)
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
	elif message.content.startswith("!setstreaming"):
		if message.author.id == keys.myid:
			if message.content.split()[1] == "on" or message.content.split()[1] == "true":
				if len(message.content.split()) == 2:
					await set_streaming_status()
					return
				elif len(message.content.split()) > 2:
					updated_game = message.server.me.game
					if not updated_game:
						updated_game = discord.Game(url = message.content.split()[2], type = 1)
					else:
						updated_game.url = message.content.split()[2]
						updated_game.type = 1
			else:
				updated_game = message.server.me.game
				updated_game.type = 0
			await client.change_status(game = updated_game)
	elif message.content.startswith("!shorturl"):
		await send_mention_space(message, requests.post('https://www.googleapis.com/urlshortener/v1/url?key=' + keys.google_apikey, headers={'Content-Type': 'application/json'}, data= '{"longUrl": "' + message.content.split()[1] +'"}').json()["id"])
	elif message.content.startswith("!spotifyinfo"):
		path = urllib.parse.urlparse(message.content.split()[1]).path
		if path[:7] == "/track/":
			trackid = path[7:]
			url = "https://api.spotify.com/v1/tracks/" + trackid
			data = requests.get(url).json()
			songname = data["name"]
			artistname = data["artists"][0]["name"]
			albumname = data["album"]["name"]
			# tracknumber = str(data["track_number"])
			duration = secs_to_colon_format(data["duration_ms"] / 1000)
			preview = data["preview_url"]
			artistlink = data["artists"][0]["external_urls"]["spotify"]
			# albumlink = data["album"]["href"]
			albumlink = data["album"]["external_urls"]["spotify"]
			await client.send_message(message.channel, message.author.mention + "```\n" + songname + " by " + artistname + "\n" + albumname + "\n" + duration + "```Preview: " + preview + "\nArtist: " + artistlink + "\nAlbum: " + albumlink)
		else:
			pass
	elif message.content.startswith(("!spotifytoyoutube", "!sptoyt")):
		link = spotify_to_youtube(message.content.split()[1])
		if link:
			await send_mention_space(message, link)
		else:
			await send_mention_space(message, "Error")
	elif message.content.startswith("!stats"):
		if message.content.split()[1] == "uptime": # since 4/17/16
			with open("data/stats.json", "r") as stats_file:
				stats = json.load(stats_file)
			total_uptime = stats["uptime"]
			await send_mention_space(message, "Total Recorded Uptime: " + duration_to_letter_format(secs_to_duration(int(total_uptime))))
		if message.content.split()[1] == "restarts": # since 4/17/16
			with open("data/stats.json", "r") as stats_file:
				stats = json.load(stats_file)
			restarts = stats["restarts"]
			await send_mention_space(message, "Total Recorded Restarts: " + str(restarts))
	elif message.content.startswith("!steam"):
		if message.content.split()[1] == "appid":
			url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/"
			apps = requests.get(url).json()["applist"]["apps"]
			appid = 0
			for app in apps:
				if app["name"].lower() == " ".join(message.content.split()[2:]).lower():
					appid = app["appid"]
					break
			await send_mention_space(message, str(appid))
		elif message.content.split()[1] == "gamecount":
			url = "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key=" + keys.steam_apikey + "&vanityurl=" + message.content.split()[2]
			id = requests.get(url).json()["response"]["steamid"]
			url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=" + keys.steam_apikey + "&steamid=" + id
			gamecount = requests.get(url).json()["response"]["game_count"]
			await send_mention_space(message, message.content.split()[2] + " has " + str(gamecount) + " games.")
		elif message.content.split()[1] == "gameinfo":
			url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/"
			apps = requests.get(url).json()["applist"]["apps"]
			appid = 0
			for app in apps:
				if app["name"].lower() == " ".join(message.content.split()[2:]).lower():
					appid = app["appid"]
					break
			url = "http://store.steampowered.com/api/appdetails/?appids=" + str(appid)
			data = requests.get(url).json()[str(appid)]["data"]
			type = data["type"]
			name = data["name"]
			appid = data["steam_appid"]
			#required_age = data["required_age"]
			isfree = data["is_free"]
			if isfree:
				isfree = "Yes"
			else:
				isfree = "No"
			detaileddescription = data["detailed_description"]
			description = data["about_the_game"]
			header_image = data["header_image"]
			website = data["website"]
			await send_mention_space(message, name + "\n" + str(appid) + "\nFree?: " + isfree + "\n" + website + "\n" + header_image)
	elif message.content.startswith("!streetview"):
		if message.content.split()[1] == "random":
			latitude = random.uniform(-90, 90)
			longitude = random.uniform(-180, 180)
			await send_mention_space(message, "https://maps.googleapis.com/maps/api/streetview?size=400x400&location=" + str(latitude) + "," + str(longitude))
		else:
			await send_mention_space(message, "https://maps.googleapis.com/maps/api/streetview?size=400x400&location=" + "+".join(message.content.split()[1:]))
	elif message.content.startswith("!taboo"):
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
		temp_channel = await client.create_channel(message.server, "Temp Channel", type = discord.ChannelType.voice)
		await client.move_member(message.author, temp_channel)
		await send_mention_space(message, "Temporary voice channel created")
		await asyncio.sleep(15)
		while True:
			temp_channel = discord.utils.find(lambda t: t == temp_channel, message.server.channels)
			if len(temp_channel.voice_members) == 0:
				await client.delete_channel(temp_channel)
				return
			await asyncio.sleep(15)
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
	elif message.content.startswith("!updateavatar"):
		if message.author.id == keys.myid:
			with open("data/discord_harmonbot_icon.png", "rb") as avatar_file:
				await client.edit_profile(avatar=avatar_file.read())
			await send_mention_space(message, "avatar updated")
	elif message.content.startswith(("!updateplaying", "!updategame", "!changeplaying", "!changegame", "!setplaying", "!setgame")):
		if message.author.id == keys.myid:
			updated_game = message.server.me.game
			if not updated_game:
				updated_game = discord.Game(name = " ".join(message.content.split()[1:]))
			else:
				updated_game.name = " ".join(message.content.split()[1:])
			await client.change_status(game = updated_game)
			await send_mention_space(message, "game updated")
	elif message.content.startswith("!uptime"):
		now = datetime.datetime.utcnow()
		uptime = now - online_time
		await send_mention_space(message, duration_to_letter_format(secs_to_duration(int(uptime.total_seconds()))))
	elif message.content.startswith("!urbandictionary"):
		await send_mention_space(message, "http://www.urbandictionary.com/define.php?term=" + ('+').join(message.content.split()[1:]))
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
	elif message.content.startswith("!wiki"):
		await client.send_message(message.channel, message.author.mention + " https://en.wikipedia.org/wiki/" + "_".join(message.content.split()[1:]))
	elif message.content.startswith(("!wolframalpha", "!wa")):
		if message.author.id == keys.myid:
			result = waclient.query(" ".join(message.content.split()[1:]))
			for pod in result.pods:
				await client.send_message(message.channel, message.author.mention + " " + pod.img)
				await client.send_message(message.channel, message.author.mention + " " + pod.text)
			#await client.send_message(message.channel, message.author.mention + " " + next(result.results).text)
	elif message.content.startswith("!xkcd"):
		if len(message.content.split()) == 1:
			url = "http://xkcd.com/info.0.json" # http://dynamic.xkcd.com/api-0/jsonp/comic/
		elif is_digit_gtz(message.content.split()[1]):
			url = "http://xkcd.com/" + message.content.split()[1] + "/info.0.json" # http://dynamic.xkcd.com/api-0/jsonp/comic/#
		elif message.content.split()[1] == "random":
			total = json.loads(requests.get("http://xkcd.com/info.0.json").text)["num"]
			number = random.randint(1, total)
			url = "http://xkcd.com/" + str(number) + "/info.0.json"
		data = requests.get(url).json()
		link = "http://xkcd.com/" + str(data["num"])
		title = data["title"]
		image_link = data["img"]
		alt_text = data["alt"]
		date = data["month"] + "/" + data["day"] + "/" + data["year"]
		await send_mention_space(message, link + " (" + date + ")\n" + image_link + "\n" + title + "\nAlt Text: " + alt_text)
	elif message.content.startswith("!year"):
		url = "http://numbersapi.com/" + message.content.split()[1] + "/year"
		await send_mention_space(message, requests.get(url).text)
	elif message.content.startswith(("!youtubeinfo", "!ytinfo")):
		# toggles = {}
		# with open(message.server.name + "_toggles.json", "r") as toggles_file:
			# toggles = json.load(toggles_file)
		# if message.content.split()[1] == "on":
			# toggles["youtubeinfo"] = True
			# with open(message.server.name + "_toggles.json", "w") as toggles_file:
				# json.dump(toggles, toggles_file)
		# elif message.content.split()[1] == "off":
			# toggles["youtubeinfo"] = False
			# with open(message.server.name + "_toggles.json", "w") as toggles_file:
				# json.dump(toggles, toggles_file)
		# else:
		url_data = urllib.parse.urlparse(message.content.split()[1])
		query = urllib.parse.parse_qs(url_data.query)
		videoid = query["v"][0]
		url = "https://www.googleapis.com/youtube/v3/videos?id=" + videoid + "&key=" + keys.google_apikey + "&part=snippet,contentDetails,statistics"
		if requests.get(url).json():
			data = requests.get(url).json()["items"][0]
			title = data["snippet"]["title"]
			length_iso = data["contentDetails"]["duration"]
			length_timedelta = isodate.parse_duration(length_iso)
			length = secs_to_letter_format(length_timedelta.total_seconds())
			likes = data["statistics"]["likeCount"]
			dislikes = data["statistics"]["dislikeCount"]
			likepercentage = round(float(likes) / (float(likes) + float(dislikes)) * 100, 2)
			likes = add_commas(int(likes))
			dislikes = add_commas(int(dislikes))
			views = add_commas(int(data["statistics"]["viewCount"]))
			channel = data["snippet"]["channelTitle"]
			published = data["snippet"]["publishedAt"][:10]
			# await client.send_message(message.channel, message.author.mention + "\n**" + title + "**\n**Length**: " + str(length) + "\n**Likes**: " + likes + ", **Dislikes**: " + dislikes + " (" + str(likepercentage) + "%)\n**Views**: " + views + "\n" + channel + " on " + published)
			await client.send_message(message.channel, message.author.mention + "```\n" + title + "\nLength: " + str(length) + "\nLikes: " + likes + ", Dislikes: " + dislikes + " (" + str(likepercentage) + "%)\nViews: " + views + "\n" + channel + " on " + published + "```")
	elif message.content.startswith(("!youtubesearch", "!ytsearch")):
		url = "https://www.googleapis.com/youtube/v3/search?part=snippet&q=" + "+".join(message.content.split()[1:]) + "&key=" + keys.google_apikey
		data = requests.get(url).json()["items"][0]
		if "videoId" not in data["id"]:
			data = requests.get(url).json()["items"][1]
		link = "https://www.youtube.com/watch?v=" + data["id"]["videoId"]
		await client.send_message(message.channel, message.author.mention + " " + link)
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
			elif message.content.split()[1] == "restart" or message.content.split()[1] == "replay":
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
			elif message.content.split()[1] == "full":
				return
		if not client.is_voice_connected(message.server):
			await send_mention_space(message, "I'm not in a voice channel. Please ask someone with permission to use `!voice (or !yt) join <channel>` first.")
		elif message.content.split()[0] in ["!radio"] or message.content.split()[1] in ["join", "leave", "pause", "stop", "resume", "start", "skip", "next", "restart", "replay", "empty", "clear", "shuffle", "radio"]:
			await send_mention_space(message, "You don't have permission to do that.")
		elif message.content.split()[1] == "current" or message.content.split()[1] == "queue":
			current = player_current(message)
			if not current:
				await client.send_message(message.channel, "There is no song currently playing.")
			else:
				await client.send_message(message.channel, "Currently playing: " + current["stream"].url + "\n" + add_commas(current["stream"].views) + ":eye: | " + add_commas(current["stream"].likes) + ":thumbsup::skin-tone-2: | " + add_commas(current["stream"].dislikes) + ":thumbsdown::skin-tone-2:\nAdded by: " + current["author"].name)
			if radio_on(message):
				await client.send_message(message.channel, ":radio: Radio is currently on")
			else:
				queue = player_queue(message)
				if not queue:
					await client.send_message(message.channel, "The queue is currently empty.")
				else:
					queue_string = ""
					count = 1
					for stream in list(queue.queue):
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
			link = await player_add_spotify_song(message)
			if link:
				await send_mention_space(message, "Playing: " + link)
			else:
				await send_mention_space(message, "Error")
		else:
			response = await send_mention_space(message, "Loading...")
			added = await player_add_song(message)
			if not added:
				await send_mention_space(message, "Error")
			else:
				await client.edit_message(response, message.author.mention + " Your song has been added to the queue.")

#    if message.content.startswith("!test"):
#        counter = 0
#        tmp = await client.send_message(message.channel, "Calculating messages...")
#        async for log in client.logs_from(message.channel, limit=100):
#            if log.author == message.author:
#                counter += 1
#
#        await client.edit_message(tmp, "You have {} messages.".format(counter))
#    elif message.content.startswith("!sleep"):
#        await asyncio.sleep(5)
#        await client.send_message(message.channel, "Done sleeping")
	elif message.content.lower() == 'f':
		with open("data/f.json", "r") as counter_file:
			counter_info = json.load(counter_file)
		counter_info["counter"] += 1
		with open("data/f.json", "w") as counter_file:
			json.dump(counter_info, counter_file)
		await client.send_message(message.channel, message.author.name + " has paid their respects.\nRespects paid so far: " + str(counter_info["counter"]))
	# conversions
	elif re.match(r"^!(\w+)to(\w+)", message.content.split()[0], re.I):
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
	restart_tasks()
	loop.run_until_complete(client.logout())
finally:
	loop.close()

'''
except:
	traceback.print_exc()
'''
'''
try:
	if client.is_logged_in:
		client.loop.run_until_complete(client.logout())
		client.loop.run_until_complete(client.close())

		# client.loop.stop()
'''
