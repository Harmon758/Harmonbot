
print("Starting up...")

import discord
# from discord.ext import commands
import asyncio
from bs4 import BeautifulSoup
import chess
import cleverbot
import conversions
import datetime
import gofish
import json
import html
import inflect
import isodate
import keys
import logging
import math
from maze import maze
import moviepy.editor
import os
import permissions
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
import war
import wolframalpha
import youtube_dl

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

client = discord.Client()
discord.opus.load_opus("libopus-0.dll")
waclient = wolframalpha.Client(keys.wolframalpha_appid)
spotify = spotipy.Spotify()
board = chess.Board()
cleverbot_instance = cleverbot.Cleverbot()
inflect_engine = inflect.engine()
voice = None
player = None
voices = []
players = []
song_restarted = False
online_time = datetime.datetime.utcnow()
wait_time = 10.0

try:
	with open("data/trivia_points.json", "x") as trivia_file:
		json.dump({}, trivia_file)
except FileExistsError:
	pass

trivia_active = False
trivia_bet = False
trivia_answers = {}
trivia_bets = {}
radio_playing = False
radio_currently_playing = ""
radio_paused = False
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
commands = "Commands: !8ball (!eightball) !add !audiodefine !avatar !calc !cat !chess !choose !coin !color (!colour) !commands !date\
 !define !fancify !google (!search) !guess !haveibeenpwned !imdb !imfeelinglucky !insult !joke !lmbtfy !lmgtfy !longurl !map !math !maze !mycolor (!mycolour) !number !randomidea\
 !randomlocation !randomword !rng !rolecolor (!rolecolour) !shorturl !spotifyinfo !spotifytoyoutube (!sptoyt) !steam !streetview !trivia !urbandictionary !wiki !xkcd !year\
 !youtubeinfo !youtubesearch\n\
Conversions: temperature unit conversions (![c, f, k, r, de]to[c, f, k, r, de, n, re, ro]), weight unit conversions (![amu, me, bagc, bagpc, barge, kt, ct, \
clove, crith, da, drt, drav, ev, gamma, gr, gv, longcwt, cwt, shcwt, kg, kip, mark, mite, mitem, ozt, ozav, oz, dwt, pwt, point, lb, lbav, lbm, lbt, \
quarterimp, quarterinf, quarterlinf, q, sap, sheet, slug, st, atl, ats, longtn, ton, shtn, t, wey, g]to[amu, me, bagc, bagpc, barge, kt, ct, clove, crith, \
da, drt, drav, ev, gamma, gr, gv, longcwt, cwt, shcwt, kg, kip, mark, mite, mitem, ozt, ozav, oz, dwt, pwt, point, lb, lbav, lbm, lbt, quarterimp, \
quarterinf, quarterlinf, q, sap, sheet, slug, st, atl, ats, longtn, ton, shtn, t, wey, g])\n\
In Progress: !adventure !everyone !gifvtogif !giphy !gofish !help (!whatis) !radio !tempchannel !timer !youtube (!audio !soundcloud !yt) !war !webmtogif\n\
Misc/Admin Only: !channel !delete !discriminator !eval !idtoname !libraryversion !load !nametoid !owner !servericon !serverowner !test !tts !updateavatar\n\
@Harmon758 (!cleverbot) (!talk) (!ask), f (F)\n\
Use !help or !whatis *command* for more information on a command"
#wolframalpha (wa)
commands_info = {
	"!8ball" : "Ask !8ball a yes or no question", "!eightball" : "Ask !eightball a yes or no question",
	"!add" : "Use !add to add numbers",
	"!adventure" : "!adventure",
	"!audiodefine" : "Use !audiodefine to find out how to pronounce a word",
	"!avatar" : "Use !avatar to see someone's avatar",
	"!calc" : "!calc",
	"!cat" : "Use !cat for a random image of a cat. !cat categories for different categories you can choose from. !cat <category> for a random image of a cat from that category",
	"!channel" : "!channel",
	"!chess" : "!chess",
	"!choose" : "Use !choose and I will choose between multiple options (e.g. !choose <option1> <option2> <...>)",
	"!cleverbot" : "!cleverbot", "!talk" : "!talk", "!ask" : "!ask",
	"!coin" : "Use !coin to flip a coin",
	"!color" : "!color", "!colour" : "!colour",
	"!commands" : "!commands",
	"!date" : "!date",
	"!define" : "!define",
	"!delete" : "!delete",
	"!everyone" : "Use !everyone to see if you can mention everyone in that channel",
	"!gofish" : "!gofish",
	"!google" : "!google", "!search" : "!search",
	"!guess" : "!guess",
	"!haveibeenpwned" : "!haveibeenpwned",
	"!help" : "!help", "!whatis" : "!whatis",
	"!idtoname" : "!idtoname",
	"!imdb" : "!imdb",
	"!imfeelinglucky" : "!imfeelinglucky",
	"!insult" : "!insult",
	"!joke" : "!joke",
	"!lmgtfy" : "!lmgtfy",
	"!longurl" : "!longurl",
	"!map" : "!map",
	"!math" : "!math",
	"!mycolor" : "!mycolor", "!mycolour" : "!mycolour",
	"!nametoid" : "!nametoid",
	"!number" : "!number",
	"!owner" : "Use !owner to find out the owner of the server",
	"!randomidea" : "!randomidea",
	"!randomlocation" : "!randomlocation",
	"!randomword" : "!randomword",
	"!rng" : "!rng",
	"!rolecolor" : "!rolecolor", "!rolecolour" : "!rolecolour",
	"!servericon" : "!servericon",
	"!shorturl" : "!shorturl",
	"!spotifyinfo" : "!spotifyinfo",
	"!spotifytoyoutube" : "!spotifytoyoutube", "!sptoyt" : "!sptoyt",
	"!steam" : "!steam",
	"!streetview" : "!streetview",
	"!tempchannel" : "!tempchannel",
	"!test" : "!test",
	"!timer" : "!timer",
	"!trivia" : "!trivia",
	"!tts" : "!tts",
	"!war" : "!war",
	"!wiki" : "Use !wiki to look something up on Wikipedia",
	"!xkcd" : "!xkcd",
	"!year" : "!year",
	"!youtube" : "!youtube",
	"!youtubeinfo" : "!youtubeinfo",
	"!youtubesearch" : "!youtubesearch",
}

# description = '''Harmonbot'''
# bot = commands.Bot(command_prefix='!', description=description)

@client.event
async def on_ready():
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("------")

@client.event
async def on_message(message):
	global voice, player, trivia_answers
	if (message.server == None or message.channel.is_private) and message.author != client.user:
		for member in client.get_all_members():
			if member.id == keys.myid:
				my_member = member
				break
		await client.send_message(my_member, "From " + message.author.name + "#" + message.author.discriminator + ": " + message.content)
	if message.author == client.user:
		pass
	if not permissions.get_permission(message, "user", message.author.id, message.content.split()[0]):# and keys.myid != message.author.id:
		await send_mention_space(message, "You don't have permision to use that command here")
	elif message.content.startswith("!test"):
		await client.send_message(message.channel, "Hello, World!")
	elif message.content.startswith("!commands"):
		await client.send_message(message.author, commands)
		await client.send_message(message.channel, message.author.mention + " Check your DM's for my commands.")
	elif message.content.startswith("!help") or message.content.startswith("!whatis"):
		if message.content.startswith("!help") and len(message.content.split()) == 1:
			await send_mention_space(message, "What do you need help with?")
		elif message.content.startswith("!whatis") and len(message.content.split()) == 1:
			await send_mention_space(message, "What is what?")
		elif message.content.split()[1] == "commands":
			await client.send_message(message.author, commands)
			await send_mention_space(message, "Check your DM's for my commands.")
		elif commands_info.get(message.content.split()[1], 0):
			await send_mention_space(message, commands_info[message.content.split()[1]])
	elif message.content.startswith("!8ball") or message.content.startswith("!eightball"):
		responses = ["It is certain", "It is decidedly so", "Without a doubt", "Yes, definitely", "You may rely on it", "As I see it, yes", "Most likely",
			"Outlook good", "Yes", "Signs point to yes", "Reply hazy try again", "Ask again later", "Better not tell you now", "Cannot predit now",
			"Concentrate and ask again", "Don't count on it", "My reply is no", "My sources say no", "Outlook not so good", "Very doubtful"]
		await send_mention_space(message, random.choice(responses))
	elif message.content.startswith("!add"):
		sum = 0
		numbers = []
		for part in message.content.split():
			if isnumber(part):
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
	elif message.content.startswith("!cleverbot") or message.content.startswith("!talk") or message.content.startswith("!ask"):
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
	elif message.content.startswith("!color") or message.content.startswith("!colour"):
		if len(message.content.split()) == 1 or message.content.split()[1] == "random":
			url = "http://www.colourlovers.com/api/colors/random?numResults=1&format=json"
		elif ishex(message.content.split()[1]) and len(message.content.split()[1]) == 6:
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
	elif message.content.startswith("!date"):
		url = "http://numbersapi.com/" + message.content.split()[1] + "/date"
		await send_mention_space(message, requests.get(url).text)
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
		if not message.channel.permissions_for(message.author):
			await send_mention_space(message, "You don't have permission to do that here.")
		if message.channel.permissions_for(message.author).manage_messages or message.author.id == keys.myid:
			name = message.content.split()[1]
			if name.isdigit():
				number = int(name)
			elif message.content.split()[2].isdigit():
				number = int(message.content.split()[2])
			else:
				number = 0
			count = 0
			try:
				await client.delete_message(message)
				async for client_message in client.logs_from(message.channel):
					if not name.isdigit() and client_message.author.name == name and count != number:
						await client.delete_message(client_message)
						count += 1
					elif name.isdigit() and count != number:
						await client.delete_message(client_message)
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
	elif message.content.startswith("!eval"):
		if message.author.id == keys.myid:
			await send_mention_code(message, str(eval(" ".join(message.content.split()[1:]))))
	elif message.content.startswith("!everyone"):
		if message.author.permissions_in(message.channel).mention_everyone:
			await send_mention_space(message, "You are able to mention everyone in this channel.")
		else:
			await send_mention_space(message, "You are not able to mention everyone in this channel.")
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
			permissions.set_permission(message, type, to_find, permission)
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
	elif message.content.startswith("!googleimage") or message.content.startswith("!imagesearch"):
		url = "https://www.googleapis.com/customsearch/v1?key={0}&cx={1}&searchType=image&q={2}".format(keys.google_apikey, keys.google_cse_cx, '+'.join(message.content.split()[1:]))
		data = requests.get(url).json()
		image_link = data["items"][0]["link"]
		await send_mention_space(message, image_link)
		# handle 403 daily limit exceeded error
	elif message.content.startswith("!google") or message.content.startswith("!search"):
		await send_mention_space(message, "https://www.google.com/search?q=" + ('+').join(message.content.split()[1:]))
	elif message.content.startswith("!guess"):
		tries = False
		if len(message.content.split()) >= 3 and string_isdigit(message.content.split()[2]):
			tries = int(message.content.split()[2])
		if len(message.content.split()) >= 2 and string_isdigit(message.content.split()[1]):
			max_value = int(message.content.split()[1])
		else:
			await client.send_message(message.channel, message.author.mention + " What range of numbers would you like to guess to? 1 to _")
			max_value = await client.wait_for_message(timeout=wait_time, author=message.author, check=message_isdigit)
			if max_value is None:
				max_value = 10
			else:
				max_value = int(max_value.content)
		answer = random.randint(1, max_value)
		if not tries:
			await client.send_message(message.channel, message.author.mention + " How many tries would you like?")
			tries = await client.wait_for_message(timeout=wait_time, author=message.author, check=message_isdigit)
			if tries is None:
				tries = 1
			else:
				tries = int(tries.content)
		await client.send_message(message.channel, message.author.mention + " Guess a number between 1 to " + str(max_value))
		while tries != 0:
			guess = await client.wait_for_message(timeout=wait_time, author=message.author, check=message_isdigit)
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
	elif message.content.startswith("!radio"):
		if message.author.id == keys.myid or message.author.id == "108131092430589952":
			global radio_playing, radio_currently_playing, radio_paused
			if message.content.split()[1] == "stop" and radio_playing:
				if client.is_voice_connected():
					player.stop()
					await voice.disconnect()
				radio_playing = False
			elif message.content.split()[1] == "current":
				await send_mention_space(message, "https://www.youtube.com/watch?v=" + radio_currently_playing)
			elif message.content.split()[1] == "pause":
				player.pause()
				radio_paused = True
			elif message.content.split()[1] == "resume":
				player.resume()
				radio_paused = False
			else:
				if message.content.split()[1] == "next": #or client.is_voice_connected() or (player and player.is_playing()):
					player.stop()
					if not message.content.split()[1] == "next":
						await voice.disconnect()
					radio_playing = False
					await asyncio.sleep(2)
				radio_playing = True
				if message.content.split()[1] == "next":
					url = "https://www.googleapis.com/youtube/v3/search?part=snippet&relatedToVideoId=" + radio_currently_playing + "&type=video&key=" + keys.google_apikey
					data = requests.get(url).json()
					radio_currently_playing = data["items"][0]["id"]["videoId"]
				else:
					for channel in message.server.channels:
						plain_channel_name = remove_symbols(channel.name)
						if plain_channel_name == (' ').join(message.content.split()[1].split('_')) or plain_channel_name.startswith((' ').join(message.content.split()[1].split('_'))):
							voice_channel = channel
							break
					voice = await client.join_voice_channel(voice_channel)
					url_data = urllib.parse.urlparse(message.content.split()[2])
					query = urllib.parse.parse_qs(url_data.query)
					videoid = query["v"][0]
					radio_currently_playing = videoid
				player = await voice.create_ytdl_player(radio_currently_playing)
				player.start()
				while radio_playing:
					# if player.duration:
						# await asyncio.sleep(player.duration)
					# else:
					while not player.is_done() or radio_paused:
						await asyncio.sleep(1)
					if not radio_playing:
						break
					player.stop()
					url = "https://www.googleapis.com/youtube/v3/search?part=snippet&relatedToVideoId=" + radio_currently_playing + "&type=video&key=" + keys.google_apikey
					data = requests.get(url).json()
					radio_currently_playing = data["items"][0]["id"]["videoId"]
					player = await voice.create_ytdl_player(radio_currently_playing)
					player.start()
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
	elif message.content.startswith("!rng"):
		if len(message.content.split()) > 1 and string_isdigit(message.content.split()[1]):
			await client.send_message(message.channel, message.author.mention + " " + str(random.randint(1, int(message.content.split()[1]))))
		else:
			await client.send_message(message.channel, message.author.mention + " " + str(random.randint(1, 10)))
	elif message.content.startswith("!rolecolor") or message.content.startswith("!rolecolour"):
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
	elif message.content.startswith("!spotifytoyoutube") or message.content.startswith("!sptoyt"):
		path = urllib.parse.urlparse(message.content.split()[1]).path
		if path[:7] == "/track/":
			trackid = path[7:]
			url = "https://api.spotify.com/v1/tracks/" + trackid
			data = requests.get(url).json()
			songname = "+".join(data["name"].split())
			artistname = "+".join(data["artists"][0]["name"].split())
			url = "https://www.googleapis.com/youtube/v3/search?part=snippet&q=" + songname + "+by+" + artistname + "&key=" + keys.google_apikey
			data = requests.get(url).json()["items"][0]
			link = "https://www.youtube.com/watch?v=" + data["id"]["videoId"]
			await client.send_message(message.channel, message.author.mention + " " + link)
		else:
			pass
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
	elif message.content.startswith("!tts"):
		if message.author.id == keys.myid:
			subprocess.call(["espeak", "-s 150", "-ven-us+f1", "-w data/tts.wav", " ".join(message.content.split()[2:])], shell=True)
			for channel in message.server.channels:
				plain_channel_name = remove_symbols(channel.name)
				if plain_channel_name == (' ').join(message.content.split()[1].split('_')) or plain_channel_name.startswith((' ').join(message.content.split()[1].split('_'))):
					voice_channel = channel
					break
			if client.is_voice_connected():
				player.stop()
				await voice.disconnect()
			voice = await client.join_voice_channel(voice_channel)
			player = voice.create_ffmpeg_player("data/tts.wav")
			player.start()
			while player.is_playing():
				pass
			await voice.disconnect()
			os.remove("data/tts.wav")
	elif message.content.startswith("!updateavatar"):
		if message.author.id == keys.myid:
			with open("data/discord_harmonbot_icon.png", "rb") as avatar_file:
				await client.edit_profile(avatar=avatar_file.read())
			await send_mention_space(message, "avatar updated")
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
	elif message.content.startswith("!wolframalpha") or message.content.startswith("!wa"):
		if message.author.id == keys.myid:
			result = waclient.query(" ".join(message.content.split()[1:]))
			for pod in result.pods:
				await client.send_message(message.channel, message.author.mention + " " + pod.img)
				await client.send_message(message.channel, message.author.mention + " " + pod.text)
			#await client.send_message(message.channel, message.author.mention + " " + next(result.results).text)
	elif message.content.startswith("!xkcd"):
		if len(message.content.split()) == 1:
			url = "http://xkcd.com/info.0.json" # http://dynamic.xkcd.com/api-0/jsonp/comic/
		elif string_isdigit(message.content.split()[1]):
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
	elif message.content.startswith("!youtubeinfo"):
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
	elif message.content.startswith("!youtubesearch"):
		url = "https://www.googleapis.com/youtube/v3/search?part=snippet&q=" + "+".join(message.content.split()[1:]) + "&key=" + keys.google_apikey
		data = requests.get(url).json()["items"][0]
		if "videoId" not in data["id"]:
			data = requests.get(url).json()["items"][1]
		link = "https://www.youtube.com/watch?v=" + data["id"]["videoId"]
		await client.send_message(message.channel, message.author.mention + " " + link)
	elif message.content.startswith("!youtube") or message.content.startswith("!soundcloud") or message.content.startswith("!audio") or message.content.startswith("!yt") or message.content.startswith("!voice") or message.content.startswith("!stream") or message.content.startswith("!spotify") or message.content.startswith("!playlist"):
		global voices, players, song_restarted
		if message.author.id == keys.myid or message.author.id == "108131092430589952":
			if message.content.split()[1] == "join":
				if len(voices) != 0:
					for voice in voices:
						if voice.channel.server == message.server:
							await voice.disconnect()
							voices.remove(voice)
							break
				voice_channel = None
				for channel in message.server.channels:
					if channel.type == discord.ChannelType.text:
						continue
					plain_channel_name = remove_symbols(channel.name)
					if plain_channel_name == (' ').join(message.content.split()[2].split('_')) or plain_channel_name.startswith((' ').join(message.content.split()[2].split('_'))):
						voice_channel = channel
						break
				if not voice_channel:
					await send_mention_space(message, "Voice channel not found")
					return
				voice = await client.join_voice_channel(voice_channel)
				voices.append(voice)
				player = {"server" : message.server, "queue" : queue.Queue(), "stream" : None}
				players.append(player)
				await send_mention_space(message, "I've joined the voice channel")
				while voice.is_connected():
					if player["queue"].empty():
						await asyncio.sleep(1)
					else:
						stream = player["queue"].get()
						player["stream"] = stream
						stream.start()
						while not stream.is_done() or song_restarted:
							await asyncio.sleep(1)
				return
			elif not check_voice_connected(message):
				await send_mention_space(message, "I'm not in a voice channel. Please use `!voice (or !yt) join <channel>` first.")
				return
			if message.content.split()[1] == "leave":
				for voice in voices:
					if voice.channel.server == message.server:
						await voice.disconnect()
						voices.remove(voice)
						await send_mention_space(message, "I've left the voice channel")
						return
			elif message.content.split()[1] == "pause" or message.content.split()[1] == "stop":
				for player in players:
					if player["server"] == message.server:
						player["stream"].pause()
						await send_mention_space(message, "Song paused")
						return
			elif message.content.split()[1] == "resume" or message.content.split()[1] == "start":
				for player in players:
					if player["server"] == message.server:
						player["stream"].resume()
						await send_mention_space(message, "Song resumed")
						return
			elif message.content.split()[1] == "skip" or message.content.split()[1] == "next":
				for player in players:
					if player["server"] == message.server:
						player["stream"].stop()
						await send_mention_space(message, "Song skipped")
						return
			elif message.content.split()[1] == "restart" or message.content.split()[1] == "replay":
				for player in players:
					if player["server"] == message.server:
						song_restarted = True
						response = await send_mention_space(message, "Restarting song...")
						player["stream"].stop()
						stream = await voice.create_ytdl_player(player["stream"].url)
						player["stream"] = stream
						stream.start()
						await client.edit_message(response, message.author.mention + " Restarted song")
						while not stream.is_done():
							await asyncio.sleep(1)
						song_restarted = False
						return
			elif message.content.split()[1] == "empty" or message.content.split()[1] == "clear":
				for player in players:
					if player["server"] == message.server:
						while not player["queue"].empty():
							player["queue"].get()
						await send_mention_space(message, "Queue emptied")
						return
			elif message.content.split()[1] == "shuffle":
				for player in players:
					if player["server"] == message.server:
						song_list = []
						response = await send_mention_space(message, "Shuffling...")
						while not player["queue"].empty():
							song_list.append(player["queue"].get())
						random.shuffle(song_list)
						for song in song_list:
							player["queue"].put(song)
						await client.edit_message(response, message.author.mention + " Shuffled songs")
						return
		if not check_voice_connected(message):
			await send_mention_space(message, "I'm not in a voice channel. Please ask someone with permission to use `!voice (or !yt) join <channel>` first.")
			return
		elif message.content.split()[1] in ["leave", "pause", "stop", "resume", "start", "skip", "next", "restart", "replay", "empty", "clear", "shuffle"]:
			await send_mention_space(message, "You don't have permission to do that.")
			return
		elif message.content.split()[1] == "current" or message.content.split()[1] == "queue":
			for player in players:
				if player["server"] == message.server:
					queue_string = ""
					count = 1
					for stream in list(player["queue"].queue):
						if count <= 10:
							number = ':' + inflect_engine.number_to_words(count) + ": "
						else:
							number = str(count) + ". "
						queue_string += number + stream.title + " (`" + stream.url + "`)\n"
						count += 1
					if player["stream"].is_done():
						await client.send_message(message.channel, "There is no song currently playing.")
					else:
						await client.send_message(message.channel, "Currently playing: " + player["stream"].url + "\n" + "{:,}".format(player["stream"].views) + ":eye: | " + "{:,}".format(player["stream"].likes) + ":thumbsup::skin-tone-2: | " + "{:,}".format(player["stream"].dislikes) + ":thumbsdown::skin-tone-2:")
					if not queue_string:
						await client.send_message(message.channel, "The queue is currently empty.")
					else:
						await client.send_message(message.channel, "\nQueue:\n" + queue_string)
					return
		elif message.content.startswith("!playlist"):
			parsed_url = urllib.parse.urlparse(message.content.split()[1])
			path = parsed_url.path
			query = parsed_url.query
			if path[:9] == "/playlist" and query[:5] == "list=":
				response = await send_mention_space(message, "Loading...")
				playlistid = query[5:]
				base_url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&key={0}&playlistId={1}".format(keys.google_apikey, playlistid)
				url = base_url
				player_instance = None
				for player in players:
					if player["server"] == message.server:
						player_instance = player 
						break
				while True:
					data = requests.get(url).json()
					total = data["pageInfo"]["totalResults"]
					for item in data["items"]:
						position = item["snippet"]["position"] + 1
						link = "https://www.youtube.com/watch?v=" + item["snippet"]["resourceId"]["videoId"]
						await client.edit_message(response, message.author.mention + " Loading " + str(position) + '/' + str(total))
						try:
							stream = await voice.create_ytdl_player(link)
						except youtube_dl.utils.DownloadError:
							await send_mention_space(message, "Error loading video " + str(position) + " (`" + link + "`) from `" + message.content.split()[1] + '`')
							continue
						player_instance["queue"].put(stream)
					if not "nextPageToken" in data:
						break
					else:
						url = base_url + "&pageToken=" + data["nextPageToken"]
				await client.edit_message(response, message.author.mention + " Your songs have been added to the queue.")
				return
			else:
				await send_mention_space(message, "Error")
				return
		elif message.content.startswith("!spotify"):
			path = urllib.parse.urlparse(message.content.split()[1]).path
			if path[:7] == "/track/":
				trackid = path[7:]
				url = "https://api.spotify.com/v1/tracks/" + trackid
				data = requests.get(url).json()
				songname = "+".join(data["name"].split())
				artistname = "+".join(data["artists"][0]["name"].split())
				url = "https://www.googleapis.com/youtube/v3/search?part=snippet&q=" + songname + "+by+" + artistname + "&key=" + keys.google_apikey
				data = requests.get(url).json()["items"][0]
				link = "https://www.youtube.com/watch?v=" + data["id"]["videoId"]
				await send_mention_space(message, "Playing: " + link)
			else:
				await send_mention_space(message, "Error")
				return
		else:
			link = message.content.split()[1]
		response = await send_mention_space(message, "Loading...")
		try:
			stream = await voice.create_ytdl_player(link)
		except:
			await send_mention_space(message, "Error")
			return
		for player in players:
			if player["server"] == message.server:
				player["queue"].put(stream)
				break
		await client.edit_message(response, message.author.mention + " Your song has been added to the queue")

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
	elif message.content == 'f' or message.content == 'F':
		with open("data/f.json", "r") as counter_file:
			counter_info = json.load(counter_file)
		counter_info["counter"] += 1
		with open("data/f.json", "w") as counter_file:
			json.dump(counter_info, counter_file)
		await client.send_message(message.channel, message.author.name + " has paid their respects.\nRespects paid so far: " + str(counter_info["counter"]))
	# conversions
	elif message.content.startswith("!ctof"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			celsius = message.content.split()[1]
			fahrenheit = str(conversions.ctof(float(celsius)))
			await send_mention_space(message, celsius + " °C = " + fahrenheit + " °F")
	elif message.content.startswith("!ctok"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			celsius = message.content.split()[1]
			kelvin = str(conversions.ctok(float(celsius)))
			await send_mention_space(message, celsius + " °C = " + kelvin + " K")
	elif message.content.startswith("!ctor"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			celsius = message.content.split()[1]
			rankine = str(conversions.ctor(float(celsius)))
			await send_mention_space(message, celsius + " °C = " + rankine + " °R")
	elif message.content.startswith("!ctode"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			celsius = message.content.split()[1]
			delisle = str(conversions.ctode(float(celsius)))
			await send_mention_space(message, celsius + " °C = " + delisle + " °De")
	elif message.content.startswith("!cton"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			celsius = message.content.split()[1]
			newton = str(conversions.cton(float(celsius)))
			await send_mention_space(message, celsius + " °C = " + newton + " °N")
	elif message.content.startswith("!ctore"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			celsius = message.content.split()[1]
			reaumur = str(conversions.ctor(float(celsius)))
			await send_mention_space(message, celsius + " °C = " + reaumur + " °Re")
	elif message.content.startswith("!ctoro"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			celsius = message.content.split()[1]
			romer = str(conversions.ctoro(float(celsius)))
			await send_mention_space(message, celsius + " °C = " + romer + " °Rø")
	elif message.content.startswith("!ftoc"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			fahrenheit = message.content.split()[1]
			celcius = str(conversions.ftoc(float(fahrenheit)))
			await send_mention_space(message, celsius + " °F = " + celsius + " °C")
	elif message.content.startswith("!ftok"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			fahrenheit = message.content.split()[1]
			kelvin = str(conversions.ftok(float(fahrenheit)))
			await send_mention_space(message, celsius + " °F = " + celsius + " K")
	elif message.content.startswith("!ftorc"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			fahrenheit = message.content.split()[1]
			rankine = str(conversions.ftorc(float(fahrenheit)))
			await send_mention_space(message, celsius + " °F = " + rankine + " °R")
	elif message.content.startswith("!ftode"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			fahrenheit = message.content.split()[1]
			delisle = str(conversions.ftode(float(fahrenheit)))
			await send_mention_space(message, celsius + " °F = " + delisle + " °De")
	elif message.content.startswith("!fton"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			fahrenheit = message.content.split()[1]
			newton = str(conversions.fton(float(fahrenheit)))
			await send_mention_space(message, celsius + " °F = " + newton + " °N")
	elif message.content.startswith("!ftore"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			fahrenheit = message.content.split()[1]
			reaumur = str(conversions.ftore(float(fahrenheit)))
			await send_mention_space(message, celsius + " °F = " + reaumur + " °Ré")
	elif message.content.startswith("!ftoro"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			fahrenheit = message.content.split()[1]
			romer = str(conversions.ftoro(float(fahrenheit)))
			await send_mention_space(message, celsius + " °F = " + romer + " °Rø")
	elif message.content.startswith("!ktoc"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			kelvin = message.content.split()[1]
			celsius = str(conversions.ktoc(float(kelvin)))
			await send_mention_space(message, kelvin + " K = " + celsius + " °C")
	elif message.content.startswith("!ktof"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			kelvin = message.content.split()[1]
			fahrenheit = str(conversions.ktof(float(kelvin)))
			await send_mention_space(message, kelvin + " K = " + fahrenheit + " °F")
	elif message.content.startswith("!ktor"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			kelvin = message.content.split()[1]
			rankine = str(conversions.ktor(float(kelvin)))
			await send_mention_space(message, kelvin + " K = " + rankine + " °R")
	elif message.content.startswith("!ktode"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			kelvin = message.content.split()[1]
			delisle = str(conversions.ktode(float(kelvin)))
			await send_mention_space(message, kelvin + " K = " + delisle + " °De")
	elif message.content.startswith("!kton"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			kelvin = message.content.split()[1]
			newton = str(conversions.kton(float(kelvin)))
			await send_mention_space(message, kelvin + " K = " + newton + " °N")
	elif message.content.startswith("!ktore"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			kelvin = message.content.split()[1]
			reaumur = str(conversions.ktore(float(kelvin)))
			await send_mention_space(message, kelvin + " K = " + reaumur + " °Ré")
	elif message.content.startswith("!ktoro"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			kelvin = message.content.split()[1]
			romer = str(conversions.ktoro(float(kelvin)))
			await send_mention_space(message, kelvin + " K = " + romer + " °Rø")
	elif message.content.startswith("!rtoc"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			rankine = message.content.split()[1]
			celsius = str(conversions.rtoc(float(rankine)))
			await send_mention_space(message, rankine + " °R = " + celsius + " °C")
	elif message.content.startswith("!rtof"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			rankine = message.content.split()[1]
			fahrenheit = str(conversions.rtof(float(rankine)))
			await send_mention_space(message, rankine + " °R = " + fahrenheit + " °F")
	elif message.content.startswith("!rtok"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			rankine = message.content.split()[1]
			kelvin = str(conversions.rtok(float(rankine)))
			await send_mention_space(message, rankine + " °R = " + kelvin + " K")
	elif message.content.startswith("!rtode"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			rankine = message.content.split()[1]
			delisle = str(conversions.rtode(float(rankine)))
			await send_mention_space(message, rankine + " °R = " + delisle + " °De")
	elif message.content.startswith("!rton"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			rankine = message.content.split()[1]
			newton = str(conversions.rton(float(rankine)))
			await send_mention_space(message, rankine + " °R = " + newton + " °N")
	elif message.content.startswith("!rtore"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			rankine = message.content.split()[1]
			reaumur = str(conversions.rtore(float(rankine)))
			await send_mention_space(message, rankine + " °R = " + reaumur + " °Ré")
	elif message.content.startswith("!rtoro"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			rankine = message.content.split()[1]
			romer = str(conversions.rtoro(float(rankine)))
			await send_mention_space(message, rankine + " °R = " + romer + " °Rø")
	elif message.content.startswith("!detoc"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			delisle = message.content.split()[1]
			celsius = str(conversions.detoc(float(delisle)))
			await send_mention_space(message, delisle + " °De = " + celsius + " °C")
	elif message.content.startswith("!detof"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			delisle = message.content.split()[1]
			fahrenheit = str(conversions.detof(float(delisle)))
			await send_mention_space(message, delisle + " °De = " + fahrenheit + " °F")
	elif message.content.startswith("!detok"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			delisle = message.content.split()[1]
			kelvin = str(conversions.detok(float(delisle)))
			await send_mention_space(message, delisle + " °De = " + kelvin + " K")
	elif message.content.startswith("!detor"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			delisle = message.content.split()[1]
			rankine = str(conversions.detor(float(delisle)))
			await send_mention_space(message, delisle + " °De = " + rankin + " °R")
	elif message.content.startswith("!deton"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			delisle = message.content.split()[1]
			newton = str(conversions.deton(float(delisle)))
			await send_mention_space(message, delisle + " °De = " + newton + " °N")
	elif message.content.startswith("!detore"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			delisle = message.content.split()[1]
			reaumur = str(conversions.detore(float(delisle)))
			await send_mention_space(message, delisle + " °De = " + reaumur + " °Ré")
	elif message.content.startswith("!detoro"):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			delisle = message.content.split()[1]
			romer = str(conversions.detoro(float(delisle)))
			await send_mention_space(message, delisle + " °De = " + romer + " °Rø")
	elif re.match(r"^!(\w+)to(\w+)", message.content.split()[0], re.I):
		if len(message.content.split()) == 1:
			await send_mention_space(message, "Please enter input.")
		elif not isnumber(message.content.split()[1]):
			await send_mention_space(message, "Syntax error.")
		else:
			value = int(message.content.split()[1])
			units = re.match(r"^!(\w+)to(\w+)", message.content.split()[0], re.I)
			unit1 = units.group(1)
			unit2 = units.group(2)
			await send_mention_space(message, str(value) + " " + unit1 + " = " + str(conversions.massconversion(value, unit1, unit2)) + " " + unit2)

def isnumber(characters):
	try:
		float(characters)
		return True
	except ValueError:
		return False

def ishex(characters):
    try:
        int(characters, 16)
        return True
    except ValueError:
        return False

'''
import string
def is_hex(s):
     hex_digits = set(string.hexdigits)
     # if s is long, then it is faster to check against a set
     return all(c in hex_digits for c in s)
'''

def check_voice_connected(message):
	for voice in voices:
		if voice.channel.server == message.server:
			return True
	return False

def message_isdigit(m):
	return m.content.isdigit() and m.content != '0'

def string_isdigit(s):
	return s.isdigit() and s != '0'

def secs_to_duration(secs):
	duration = []
	time_in_secs = [31536000, 604800, 86400, 3600, 60]
	# years, months, days, hours, minutes
	for length_of_time in time_in_secs:
		if secs > length_of_time:
			duration.append(int(math.floor(secs / length_of_time)))
			secs -= math.floor(secs / length_of_time) * length_of_time
		else:
			duration.append(0)
	duration.append(int(secs))
	return duration

def duration_to_letter_format(duration):
	output = ""
	letters = ["y", "m", "d", "h", "m", "s"]
	for i in range(6):
		if duration[i]:
			output += str(duration[i]) + letters[i] + " "
	return output[:-1]

def duration_to_colon_format(duration):
	output = ""
	started = False
	for i in range(6):
		if duration[i]:
			started = True
			output += str(duration[i]) + ":"
		elif started:
			output += "00:"
	return output[:-1]

def secs_to_letter_format(secs):
	return duration_to_letter_format(secs_to_duration(secs))

def secs_to_colon_format(secs):
	return duration_to_colon_format(secs_to_duration(secs))

def add_commas(number):
	return "{:,}".format(number)

def remove_symbols(string):
	plain_string = ""
	for character in string:
		if 0 <= ord(character) <= 127:
			plain_string += character
	if plain_string.startswith(' '):
		plain_string = plain_string[1:]
	return plain_string

async def send_mention_space(message, response):
	return await client.send_message(message.channel, message.author.mention + " " + response)

async def send_mention_newline(message, response):
	return await client.send_message(message.channel, message.author.mention + "\n" + response)

async def send_mention_code(message, response):
	return await client.send_message(message.channel, message.author.mention + "\n" + "```" + response + "```")

#client.run(keys.username, keys.password)
client.run(keys.token)

'''
try:
    client.loop.run_until_complete(client.start(keys.username, keys.password))
except KeyboardInterrupt:
    client.loop.run_until_complete(client.logout())
    # cancel all tasks lingering
except:
	traceback.print_exc()
	while True:
		pass
'''
'''
while True:
	# try:
	try:
		if client.is_logged_in:
			client.loop.run_until_complete(client.logout())
			client.loop.run_until_complete(client.close())
		client.loop.run_until_complete(client.start(keys.username, keys.password))
	except KeyboardInterrupt:
		client.loop.run_until_complete(client.logout())
			# cancel all tasks lingering
		# finally:
			# client.loop.close()
			# client.loop.stop()
	# except RuntimeError:
	except:
		# client.loop.run_until_complete(client.logout())
		traceback.print_exc()
		time.sleep(10)
'''
