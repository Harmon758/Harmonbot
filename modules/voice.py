
import asyncio
import discord
import os
import queue
import random
import requests
import subprocess
# import time
import urllib

import keys
from client import client
from modules import utilities

players = []

async def join_voice_channel(message):
	if client.is_voice_connected(message.server):
		await client.voice_client_in(message.server).disconnect()
	voice_channel = discord.utils.find( \
		lambda channel: channel.type == discord.ChannelType.voice and utilities.remove_symbols(channel.name).startswith((' ').join(message.content.split()[2].split('_'))), 
		message.server.channels)
	if not voice_channel:
		await utilities.send_mention_space(message, "Voice channel not found.")
		return False
	await client.join_voice_channel(voice_channel)
	await utilities.send_mention_space(message, "I've joined the voice channel.")
	await player_start(message)
	return True

async def leave_voice_channel(message):
	if client.is_voice_connected(message.server):
		await client.voice_client_in(message.server).disconnect()
		return True

async def player_start(message):
	player = {"server" : message.server, "queue" : queue.Queue(), "current" : None, "radio_on" : False}
	players.append(player)
	while client.is_voice_connected(message.server):
		if player["queue"].empty():
			await asyncio.sleep(1)
		else:
			current = player["queue"].get()
			player["current"] = current
			stream = current["stream"]
			stream.start()
			while not stream.is_done():
				await asyncio.sleep(1)

# Player Add Functions

async def player_add_song(message, **options):
	if "link" in options:
		link = options["link"]
	else:
		link = message.content.split()[1]
	if "list" in link:
		parsed_link = urllib.parse.urlparse(link)
		query = urllib.parse.parse_qs(parsed_link.query)
		del query["list"]
		parsed_link = parsed_link._replace(query = urllib.parse.urlencode(query, True))
		link = parsed_link.geturl()
	try:
		stream = await client.voice_client_in(message.server).create_ytdl_player(link)
	except:
		return False
	player = get_player(message)
	player["queue"].put({"stream" : stream, "author" : message.author})
	return True
	
async def player_add_spotify_song(message):
	youtube_link = spotify_to_youtube(message.content.split()[1])
	if youtube_link:
		added = await player_add_song(message, link = youtube_link)
		if added:
			return youtube_link
	return False

async def player_add_playlist(message):
	parsed_url = urllib.parse.urlparse(message.content.split()[1])
	path = parsed_url.path
	query = parsed_url.query
	if path[:9] == "/playlist" and query[:5] == "list=":
		response = await utilities.send_mention_space(message, "Loading...")
		playlistid = query[5:]
		base_url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&key={0}&playlistId={1}&maxResults=50".format(keys.google_apikey, playlistid)
		url = base_url
		player_instance = get_player(message)
		while True:
			data = requests.get(url).json()
			total = data["pageInfo"]["totalResults"]
			for item in data["items"]:
				position = item["snippet"]["position"] + 1
				link = "https://www.youtube.com/watch?v=" + item["snippet"]["resourceId"]["videoId"]
				await client.edit_message(response, message.author.mention + " Loading " + str(position) + '/' + str(total))
				try:
					stream = await client.voice_client_in(message.server).create_ytdl_player(link)
				except youtube_dl.utils.DownloadError:
					await utilities.send_mention_space(message, "Error loading video " + str(position) + " (`" + link + "`) from `" + message.content.split()[1] + '`')
					continue
				player_instance["queue"].put({"stream" : stream, "author" : message.author})
			if not "nextPageToken" in data:
				break
			else:
				url = base_url + "&pageToken=" + data["nextPageToken"]
		await client.edit_message(response, message.author.mention + " Your songs have been added to the queue.")
		return
	else:
		await utilities.send_mention_space(message, "Error")
		return

# Player Current Song Functions

async def player_pause(message):
	player = get_player(message)
	player["current"]["stream"].pause()
	return True

async def player_resume(message):
	player = get_player(message)
	player["current"]["stream"].resume()
	return True

async def player_skip(message):
	player = get_player(message)
	player["current"]["stream"].stop()
	return True

async def player_restart(message):
	response = await utilities.send_mention_space(message, "Restarting song...")
	player = get_player(message)
	player["current"]["stream"].pause()
	stream = await client.voice_client_in(message.server).create_ytdl_player(player["current"]["stream"].url)
	old_stream = player["current"]["stream"]
	player["current"]["stream"] = stream
	stream.start()
	await client.edit_message(response, message.author.mention + " Restarted song")
	while not stream.is_done():
		await asyncio.sleep(1)
	old_stream.stop()
	return

# Player Queue Functions

async def player_empty_queue(message):
	player = get_player(message)
	while not player["queue"].empty():
		stream = player["queue"].get()
		stream["stream"].start()
		stream["stream"].stop()
	return True

async def player_shuffle_queue(message):
	player = get_player(message)
	song_list = []
	while not player["queue"].empty():
		song_list.append(player["queue"].get())
	random.shuffle(song_list)
	for song in song_list:
		player["queue"].put(song)
	return True

# Player Radio Functions

async def player_start_radio(message):
	response = await utilities.send_mention_space(message, "Starting Radio...")
	player = get_player(message)
	player["current"]["stream"].pause()
	url_data = urllib.parse.urlparse(player["current"]["stream"].url)
	query = urllib.parse.parse_qs(url_data.query)
	videoid = query["v"][0]
	url = "https://www.googleapis.com/youtube/v3/search?part=snippet&relatedToVideoId=" + videoid + "&type=video&key=" + keys.google_apikey
	data = requests.get(url).json()
	radio_currently_playing = data["items"][0]["id"]["videoId"]
	stream = await client.voice_client_in(message.server).create_ytdl_player("https://www.youtube.com/watch?v=" + radio_currently_playing)
	old_stream = player["current"]["stream"]
	player["current"]["stream"] = stream
	stream.start()
	player["radio_on"] = True
	await client.edit_message(response, message.author.mention + " Radio is now on")
	while player["radio_on"]:
		while not stream.is_done():
			await asyncio.sleep(1)
		if not player["radio_on"]:
			break
		url = "https://www.googleapis.com/youtube/v3/search?part=snippet&relatedToVideoId=" + radio_currently_playing + "&type=video&key=" + keys.google_apikey
		data = requests.get(url).json()
		radio_currently_playing = data["items"][0]["id"]["videoId"]
		stream = await client.voice_client_in(message.server).create_ytdl_player("https://www.youtube.com/watch?v=" + radio_currently_playing)
		player["current"]["stream"] = stream
		stream.start()
	player["current"]["stream"] = old_stream
	old_stream.resume()

async def player_stop_radio(message):
	player = get_player(message)
	if player["radio_on"]:
		player = get_player(message)
		player["radio_on"] = False
		player["current"]["stream"].stop()
		await utilities.send_mention_space(message, "Radio is now off")
		return True
	else:
		return False

# Text To Speech

async def tts(message):
	player = get_player(message)
	if message.content.split()[0] == "!tts":
		tts_message = message.content.split()[1:]
	elif message.content.split()[1] == "tts":
		tts_message = message.content.split()[2:]
	else:
		tts_message = message
	subprocess.call(["espeak", "-s 150", "-ven-us+f1", "-w data/tts.wav", " ".join(tts_message)], shell = True)
	stream = client.voice_client_in(message.server).create_ffmpeg_player("data/tts.wav")
	paused = False
	if player["current"] and player["current"]["stream"].is_playing():
		player["current"]["stream"].pause()
		paused = True
	stream.start()
	while stream.is_playing():
		pass
	if paused:
		player["current"]["stream"].resume()
	os.remove("data/tts.wav")

# Utility

def get_player(message):
	for player in players:
		if player["server"] == message.server:
			return player
	return None

def player_current(message):
	player = get_player(message)
	if not player["current"] or player["current"]["stream"].is_done():
		return None
	else:
		return player["current"]

def player_queue(message):
	player = get_player(message)
	if player["queue"].qsize() == 0:
		return None
	else:
		return player["queue"]

def radio_on(message):
	player = get_player(message)
	return player["radio_on"]

def spotify_to_youtube(link):
	path = urllib.parse.urlparse(link).path
	if path[:7] == "/track/":
		trackid = path[7:]
		url = "https://api.spotify.com/v1/tracks/" + trackid
		data = requests.get(url).json()
		songname = "+".join(data["name"].split())
		artistname = "+".join(data["artists"][0]["name"].split())
		url = "https://www.googleapis.com/youtube/v3/search?part=snippet&q=" + songname + "+by+" + artistname + "&key=" + keys.google_apikey
		data = requests.get(url).json()["items"][0]
		link = "https://www.youtube.com/watch?v=" + data["id"]["videoId"]
		return link
	else:
		return False

# Garbage Collection

def stop_all_streams():
	for player in players:
		while not player["queue"].empty():
			stream = player["queue"].get()
			stream["stream"].start()
			stream["stream"].stop()
		if player["radio_on"]:
			player["radio_on"] = False
			player["current"]["stream"].stop()
		if not player["current"]["stream"].is_done():
			player["current"]["stream"].stop()
