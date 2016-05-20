
from discord.ext import commands

import asyncio
import discord
import inflect
import os
# import queue
import random
import requests
import subprocess
# import time
import urllib
import youtube_dl

import keys
from modules import utilities
from utilities import checks
from client import client

inflect_engine = inflect.engine()

players = []

@client.group(pass_context = True, aliases = ["yt", "youtube", "soundcloud", "audio", "stream", "playlist", "spotify"], 
	invoke_without_command = True)
async def voice(ctx, *options : str): # no_pm = True #elif options[0] == "full":
	if not not client.is_voice_connected(ctx.message.server):
		if (ctx.message.author.id == keys.myid or ctx.message.author == ctx.message.server.owner):
			await client.reply("I'm not in a voice channel. Please use `!voice (or !yt) join <channel>` first.")
		else:
			await client.reply("I'm not in a voice channel. Please ask someone with permission to use `!voice (or !yt) join <channel>` first.")
	elif "playlist" in ctx.message.content:
		await player_add_playlist(ctx.message)
	elif "spotify" in ctx.message.content:
		youtube_link = spotify_to_youtube(options[0])
		if youtube_link:
			stream = await player_add_song(ctx.message, link = youtube_link)
			if stream:
				await client.reply("Your song, " + stream.title + ", has been added to the queue.")
				return
		await client.reply("Error")
	else:
		response = await client.reply("Loading...")
		added = await player_add_song(ctx.message)
		if not added:
			await client.reply("Error")
		else:
			await client.edit_message(response, ctx.message.author.mention + " Your song has been added to the queue.")

@client.command(pass_context = True)
@checks.is_server_owner()
async def join(ctx, *channel : str):
	if ctx.message.author.voice_channel:
		voice_channel = ctx.message.author.voice_channel
	else:
		voice_channel = discord.utils.find( lambda _channel: _channel.type == discord.ChannelType.voice and \
			utilities.remove_symbols(_channel.name).startswith(' '.join(channel)), 
			ctx.message.server.channels)
	if not voice_channel:
		await client.reply("Voice channel not found.")
	elif client.is_voice_connected(ctx.message.server):
		await client.voice_client_in(ctx.message.server).move_to(voice_channel)
		await client.reply("I've moved to the voice channel.")
	else:
		await client.join_voice_channel(voice_channel)
		await client.reply("I've joined the voice channel.")
		player = {"server" : ctx.message.server, "queue" : asyncio.Queue(), "current" : None, "radio_on" : False}
		players.append(player)
		while client.is_voice_connected(ctx.message.server):
			current = await player["queue"].get()
			player["current"] = current
			stream = current["stream"]
			stream.start()
			await client.say(":arrow_forward: Now Playing: " + stream.title)
			while not stream.is_done():
				await asyncio.sleep(1)
		players.remove(player)

@client.command(pass_context = True)
@checks.is_server_owner()
@checks.is_voice_connected()
async def leave(ctx):
	if client.is_voice_connected(ctx.message.server):
		await client.voice_client_in(ctx.message.server).disconnect()
		await client.reply("I've left the voice channel.")

@client.command(pass_context = True, aliases = ["stop"])
@checks.is_server_owner()
@checks.is_voice_connected()
async def pause(ctx):
	player = get_player(ctx.message)
	player["current"]["stream"].pause()
	await client.reply("Song paused")

@client.command(pass_context = True, aliases = ["start"])
@checks.is_server_owner()
@checks.is_voice_connected()
async def resume(ctx):
	player = get_player(ctx.message)
	player["current"]["stream"].resume()
	await client.reply("Song resumed")

@client.command(pass_context = True, aliases = ["next"])
@checks.is_server_owner()
@checks.is_voice_connected()
async def skip(ctx):
	player = get_player(ctx.message)
	player["current"]["stream"].stop()
	await client.reply("Song skipped")

@client.command(pass_context = True, aliases = ["repeat"]) # "restart"
@checks.is_server_owner()
@checks.is_voice_connected()
async def replay(ctx):
	response = await client.reply("Restarting song...")
	player = get_player(ctx.message)
	player["current"]["stream"].pause()
	stream = await client.voice_client_in(ctx.message.server).create_ytdl_player(player["current"]["stream"].url)
	old_stream = player["current"]["stream"]
	player["current"]["stream"] = stream
	stream.start()
	await client.edit_message(response, ctx.message.author.mention + " Restarted song")
	while not stream.is_done():
		await asyncio.sleep(1)
	old_stream.stop()

@client.command(pass_context = True, aliases = ["clear"])
@checks.is_server_owner()
@checks.is_voice_connected()
async def empty(ctx):
	player = get_player(ctx.message)
	while not player["queue"].empty():
		stream = await player["queue"].get()
		stream["stream"].start()
		stream["stream"].stop()	
	await client.reply("Queue emptied")

@client.command(pass_context = True)
@checks.is_server_owner()
@checks.is_voice_connected()
async def shuffle(ctx):
	response = await client.reply("Shuffling...")
	player = get_player(ctx.message)
	song_list = []
	while not player["queue"].empty():
		song_list.append(await player["queue"].get())
	random.shuffle(song_list)
	for song in song_list:
		await player["queue"].put(song)
	await client.edit_message(response, ctx.message.author.mention + " Shuffled songs")

@client.group(pass_context = True)
@checks.is_server_owner()
@checks.is_voice_connected()
async def radio(ctx):
	pass

@radio.command(name = "on", pass_context = True, aliases = ["start"])
@checks.is_server_owner()
@checks.is_voice_connected()
async def radio_on(ctx):
	response = await client.reply("Starting Radio...")
	player = get_player(ctx.message)
	player["current"]["stream"].pause()
	url_data = urllib.parse.urlparse(player["current"]["stream"].url)
	query = urllib.parse.parse_qs(url_data.query)
	videoid = query["v"][0]
	url = "https://www.googleapis.com/youtube/v3/search?part=snippet&relatedToVideoId=" + videoid + "&type=video&key=" + keys.google_apikey
	data = requests.get(url).json()
	radio_currently_playing = data["items"][0]["id"]["videoId"]
	stream = await client.voice_client_in(ctx.message.server).create_ytdl_player("https://www.youtube.com/watch?v=" + radio_currently_playing)
	old_stream = player["current"]["stream"]
	player["current"]["stream"] = stream
	stream.start()
	player["radio_on"] = True
	await client.edit_message(response, ctx.message.author.mention + " Radio is now on")
	await client.say(":arrow_forward: Now Playing: " + stream.title)
	while player["radio_on"]:
		while not stream.is_done():
			await asyncio.sleep(1)
		if not player["radio_on"]:
			break
		url = "https://www.googleapis.com/youtube/v3/search?part=snippet&relatedToVideoId=" + radio_currently_playing + "&type=video&key=" + keys.google_apikey
		data = requests.get(url).json()
		radio_currently_playing = random.choice(data["items"])["id"]["videoId"]
		stream = await client.voice_client_in(ctx.message.server).create_ytdl_player("https://www.youtube.com/watch?v=" + radio_currently_playing)
		player["current"]["stream"] = stream
		stream.start()
		await client.say(":arrow_forward: Now Playing: " + stream.title)
	player["current"]["stream"] = old_stream
	old_stream.resume()

@radio.command(name = "off", pass_context = True, aliases = ["stop"])
@checks.is_server_owner()
@checks.is_voice_connected()
async def radio_off(ctx):
	player = get_player(ctx.message)
	if player["radio_on"]:
		player = get_player(ctx.message)
		player["radio_on"] = False
		player["current"]["stream"].stop()
		await client.reply("Radio is now off")

@client.command(pass_context = True)
@checks.is_server_owner()
@checks.is_voice_connected()
async def tts(ctx, *message : str):
	player = get_player(ctx.message)
	subprocess.call(["espeak", "-s 150", "-ven-us+f1", "-w data/tts.wav", " ".join(message)], shell = True)
	stream = client.voice_client_in(ctx.message.server).create_ffmpeg_player("data/tts.wav")
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

@client.command(pass_context = True)
@checks.is_server_owner()
@checks.is_voice_connected()
async def volume(ctx, volume_setting : float):
	player = get_player(ctx.message)
	player["current"]["stream"].volume = volume_setting / 100

@client.command(pass_context = True, aliases = ["queue"])
@checks.is_voice_connected()
async def current(ctx):
	player = get_player(ctx.message)
	if not player["current"] or player["current"]["stream"].is_done():
		await client.say("There is no song currently playing.")
	else:
		current = player["current"]
		if current["stream"].views:
			views = utilities.add_commas(current["stream"].views)
		else:
			views = ""
		if current["stream"].likes:
			likes = utilities.add_commas(current["stream"].likes)
		else:
			likes = ""
		if current["stream"].dislikes:
			dislikes = utilities.add_commas(current["stream"].dislikes)
		else:
			dislikes = ""
		await client.say("Currently playing: " + current["stream"].url + "\n" + views + ":eye: | " + likes + ":thumbsup::skin-tone-2: | " + dislikes + ":thumbsdown::skin-tone-2:\nAdded by: " + current["author"].name)
	if player["radio_on"]:
		await client.say(":radio: Radio is currently on")
	else:
		if player["queue"].qsize() == 0:
			await client.say("The queue is currently empty.")
		else:
			queue = player["queue"]
			queue_string = ""
			count = 1
			for stream in list(queue._queue):
				if count <= 10:
					queue_string += ':' + inflect_engine.number_to_words(count) + ": **" + stream["stream"].title + "** (<" + stream["stream"].url + ">) Added by: " + stream["author"].name + "\n"
					count += 1
				else:
					more_songs = queue.qsize() - 10
					queue_string += "There " + inflect_engine.plural("is", more_songs) + " " + str(more_songs) + " more " + inflect_engine.plural("song", more_songs) + " in the queue"
					break
			await client.say("\nQueue:\n" + queue_string)

for command in [join, leave, pause, resume, skip, replay, empty, shuffle, radio, tts, volume, current]:
	voice.add_command(command)

# Player Add Functions

async def player_add_song(message, **kwargs):
	if "link" in kwargs:
		link = kwargs["link"]
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
		try:
			link = utilities.youtubesearch(message.content.split()[1:])
			stream = await client.voice_client_in(message.server).create_ytdl_player(link)
		except:
			return False
	player = get_player(message)
	await player["queue"].put({"stream" : stream, "author" : message.author})
	return stream
	
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
				await player_instance["queue"].put({"stream" : stream, "author" : message.author})
			if not "nextPageToken" in data:
				break
			else:
				url = base_url + "&pageToken=" + data["nextPageToken"]
		await client.edit_message(response, message.author.mention + " Your songs have been added to the queue.")
		return
	else:
		await utilities.send_mention_space(message, "Error")
		return

# Utility

def get_player(message):
	for player in players:
		if player["server"] == message.server:
			return player
	return None

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
		if "videoId" not in data["id"]:
			data = requests.get(url).json()["items"][1]
		link = "https://www.youtube.com/watch?v=" + data["id"]["videoId"]
		return link
	else:
		return False

# Garbage Collection

async def stop_all_streams():
	for player in players:
		while not player["queue"].empty():
			stream = await player["queue"].get()
			stream["stream"].start()
			stream["stream"].stop()
		if player["radio_on"]:
			player["radio_on"] = False
			player["current"]["stream"].stop()
		if player["current"] and not player["current"]["stream"].is_done():
			player["current"]["stream"].stop()

