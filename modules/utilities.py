
import discord

import aiohttp
import datetime
import dateutil.parser
import json
import math
import random

import keys
from client import client
from client import rss_client
from client import online_time
from modules import voice
from client import aiohttp_session

# Utility

def is_number(characters):
	try:
		float(characters)
		return True
	except ValueError:
		return False

def is_hex(characters):
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

def message_is_digit_gtz(m):
	return m.content.isdigit() and m.content != '0'

def is_digit_gtz(s):
	return s.isdigit() and s != '0'

def secs_to_duration(secs):
	duration = []
	time_in_secs = [31536000, 604800, 86400, 3600, 60]
	# years, weeks, days, hours, minutes
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
	letters = ["y", "w", "d", "h", "m", "s"]
	for i in range(6):
		if duration[i]:
			output += str(duration[i]) + letters[i] + ' '
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
	if number:
		return "{:,}".format(number)
	else:
		return number

def remove_symbols(string):
	plain_string = ""
	for character in string:
		if 0 <= ord(character) <= 127:
			plain_string += character
	if plain_string.startswith(' '):
		plain_string = plain_string[1:]
	return plain_string

async def youtubesearch(search):
	url = "https://www.googleapis.com/youtube/v3/search?part=snippet&q={0}&key={1}".format("+".join(search), keys.google_apikey)
	async with aiohttp_session.get(url) as resp:
		data = await resp.json()
	data = data["items"][0]
	if "videoId" not in data["id"]:
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		data = data["items"][1]
	return "https://www.youtube.com/watch?v={0}".format(data["id"]["videoId"])

# Discord

async def random_game_status():
	statuses = ["with i7-2670QM", "with mainframes", "with Cleverbot", "tic-tac-toe with Joshua", "tic-tac-toe with WOPR", "the Turing test", 
	"with my memory", "with R2-D2", "with C-3PO", "with BB-8", "with machine learning", "gigs", "with Siri", "with TARS", "with KIPP", "with humans", 
	"with Skynet", "Goldbach's conjecture", "Goldbach's conjecture solution", "with quantum foam", "with quantum entanglement", "with P vs NP", 
	"the Reimann hypothesis", "the Reimann proof", "with the infinity gauntlet", "for the other team", "hard to get", "to win", "world domination", 
	"with Opportunity", "with Spirit in the sand pit", "with Curiousity", "with Voyager 1", "music", "Google Ultron", "not enough space here to", 
	"the meaning of life is", "with the NSA", "with RSS Bot"]
	updated_game = discord.utils.get(client.servers).me.game
	if not updated_game:
		updated_game = discord.Game(name = random.choice(statuses))
	else:
		updated_game.name = random.choice(statuses)
	await client.change_status(game = updated_game)

async def set_streaming_status(client):
	updated_game = discord.utils.get(client.servers).me.game
	if not updated_game:
		updated_game = discord.Game(url = "https://www.twitch.tv/discordapp", type = 1) # https://discord.gg/0oyodN94Y3CgCT6I
	else:
		updated_game.url = "https://www.twitch.tv/discordapp"
		updated_game.type = 1
	await client.change_status(game = updated_game)

async def send_mention_space(message, response):
	return await client.send_message(message.channel, message.author.mention + ' ' + response)

async def send_mention_newline(message, response):
	return await client.send_message(message.channel, message.author.mention + "\n" + response)

async def send_mention_code(message, response):
	return await client.send_message(message.channel, message.author.mention + "\n```" + response + "```")

# Restart/Shutdown Tasks

def add_uptime():
	with open("data/stats.json", "r") as stats_file:
			stats = json.load(stats_file)
	now = datetime.datetime.utcnow()
	uptime = now - online_time
	stats["uptime"] += uptime.total_seconds()
	with open("data/stats.json", "w") as stats_file:
		json.dump(stats, stats_file)

def add_restart():
	with open("data/stats.json", "r") as stats_file:
		stats = json.load(stats_file)
	stats["restarts"] += 1
	with open("data/stats.json", "w") as stats_file:
		json.dump(stats, stats_file)

async def leave_all_voice():
	for voice_client in client.voice_clients:
		await voice_client.disconnect()

async def shutdown_tasks():
	await voice.stop_all_streams()
	# await leave_all_voice()
	add_uptime()

async def restart_tasks():
	await shutdown_tasks()
	add_restart()

