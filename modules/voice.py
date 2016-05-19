
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

def setup(bot):
	bot.add_cog(Voice())

# For testing
@client.group(hidden = True)
async def testing3():
	print("testing3")

# For testing
@client.command(hidden = True)
async def testing4():
	print("testing4")

testing3.add_command(testing4)

class Voice:

	def __init__(self):
		self.voice.add_command(self.join)
		self.voice.add_command(self.leave)
	
	@commands.group(pass_context = True, aliases = ["yt", "youtube", "soundcloud", "audio", "stream", "playlist", "spotify"], 
		invoke_without_command = True)
	async def voice(self, ctx, *options : str):
		if ctx.message.author.id == keys.myid or ctx.message.author == ctx.message.server.owner:
			if ctx.invoked_with in self.voice.commands:
				await eval("self.{0}.invoke(ctx)".format(ctx.invoked_with))
				return
			elif not client.is_voice_connected(ctx.message.server):
				await client.reply("I'm not in a voice channel. Please use `!voice (or !yt) join <channel>` first.")
				return
			elif ctx.invoked_with == "radio":
				await self.radio.invoke(ctx)
				return
			#elif options[0] == "full":
				#return
		if not client.is_voice_connected(ctx.message.server):
			await client.reply("I'm not in a voice channel. Please ask someone with permission to use `!voice (or !yt) join <channel>` first.")
		elif ctx.invoked_with in ["radio", "tts"] or options[0] in ["radio"]:
			await client.reply("You don't have permission to do that.")
		elif "playlist" in ctx.message.content:
			await player_add_playlist(ctx.message)
		elif "spotify" in ctx.message.content:
			stream = await player_add_spotify_song(ctx.message)
			if stream:
				await client.reply("Your song, " + stream.title + ", has been added to the queue.")
			else:
				await client.reply("Error")
		else:
			response = await client.reply("Loading...")
			added = await player_add_song(ctx.message)
			if not added:
				await client.reply("Error")
			else:
				await client.edit_message(response, ctx.message.author.mention + " Your song has been added to the queue.")
	
	@commands.command(pass_context = True)
	@checks.is_server_owner()
	async def join(self, ctx):
		await join_voice_channel(ctx.message)
	
	@commands.command(pass_context = True)
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def leave(self, ctx):
		await leave_voice_channel(ctx.message)
		await client.reply("I've left the voice channel.")
	
	@voice.command(pass_context = True, aliases = ["stop"])
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def pause(self, ctx):
		await player_pause(ctx.message)
		await client.reply("Song paused")
	
	@voice.command(pass_context = True, aliases = ["start"])
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def resume(self, ctx):
		await player_resume(ctx.message)
		await client.reply("Song resumed")
	
	@voice.command(pass_context = True, aliases = ["next"])
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def skip(self, ctx):
		await player_skip(ctx.message)
		await client.reply("Song skipped")
	
	@voice.command(pass_context = True, aliases = ["replay", "repeat"])
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def restart(self, ctx):
		await player_restart(ctx.message)
	
	@voice.command(pass_context = True, aliases = ["clear"])
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def empty(self, ctx):
		await player_empty_queue(ctx.message)
		await client.reply("Queue emptied")
	
	@voice.command(pass_context = True)
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def shuffle(self, ctx):
		response = await client.reply("Shuffling...")
		await player_shuffle_queue(ctx.message)
		await client.edit_ctx.message(response, ctx.message.author.mention + " Shuffled songs")
	
	@voice.group(pass_context = True)
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def radio(self, ctx):
		pass
	
	@radio.command(pass_context = True, aliases = ["start"])
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def on(self, ctx):
		await player_start_radio(ctx.message)
	
	@radio.command(pass_context = True, aliases = ["stop"])
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def off(self, ctx):
		await player_stop_radio(ctx.message)
	
	@voice.command(pass_context = True)
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def tts(self, ctx):
		await tts(ctx.message)
	
	@voice.command(pass_context = True)
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def volume(self, ctx, volume_setting : float):
		await player_volume(ctx.message, float(volume_setting) / 100)
	
	@voice.command(pass_context = True, aliases = ["queue"])
	@checks.is_voice_connected()
	async def current(self, ctx):
		current = player_current(ctx.message)
		if not current:
			await client.say("There is no song currently playing.")
		else:
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
		if radio_on(ctx.message):
			await client.say(":radio: Radio is currently on")
		else:
			queue = player_queue(ctx.message)
			if not queue:
				await client.say("The queue is currently empty.")
			else:
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
	
	# voice.aliases += list(voice.commands.keys())
	# for alias in list(voice.commands.keys()):
		# commands.command(name = alias, pass_context = True, invoke_without_command = True)(voice)

async def join_voice_channel(message):
	if message.author.voice_channel:
		voice_channel = message.author.voice_channel
	else:
		voice_channel = discord.utils.find( \
			lambda channel: channel.type == discord.ChannelType.voice and utilities.remove_symbols(channel.name).startswith((' ').join(message.content.split()[2].split('_'))), 
			message.server.channels)
	if not voice_channel:
		await utilities.send_mention_space(message, "Voice channel not found.")
		return False
	if client.is_voice_connected(message.server):
		await client.voice_client_in(message.server).move_to(voice_channel)
		return True
	await client.join_voice_channel(voice_channel)
	await utilities.send_mention_space(message, "I've joined the voice channel.")
	await player_start(message)
	return True

async def leave_voice_channel(message):
	if client.is_voice_connected(message.server):
		await client.voice_client_in(message.server).disconnect()
		return True

async def player_start(message):
	player = {"server" : message.server, "queue" : asyncio.Queue(), "current" : None, "radio_on" : False}
	players.append(player)
	while client.is_voice_connected(message.server):
		current = await player["queue"].get()
		player["current"] = current
		stream = current["stream"]
		stream.start()
		await client.send_message(message.channel, ":arrow_forward: Now Playing: " + stream.title)
		while not stream.is_done():
			await asyncio.sleep(1)
	players.remove(player)

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
	
async def player_add_spotify_song(message):
	youtube_link = spotify_to_youtube(message.content.split()[1])
	if youtube_link:
		added = await player_add_song(message, link = youtube_link)
		if added:
			return added
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

# Player Current Song Functions

async def player_volume(message, setting):
	player = get_player(message)
	player["current"]["stream"].volume = setting
	return True

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
		stream = await player["queue"].get()
		stream["stream"].start()
		stream["stream"].stop()
	return True

async def player_shuffle_queue(message):
	player = get_player(message)
	song_list = []
	while not player["queue"].empty():
		song_list.append(await player["queue"].get())
	random.shuffle(song_list)
	for song in song_list:
		await player["queue"].put(song)
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
	await client.send_message(message.channel, ":arrow_forward: Now Playing: " + stream.title)
	while player["radio_on"]:
		while not stream.is_done():
			await asyncio.sleep(1)
		if not player["radio_on"]:
			break
		url = "https://www.googleapis.com/youtube/v3/search?part=snippet&relatedToVideoId=" + radio_currently_playing + "&type=video&key=" + keys.google_apikey
		data = requests.get(url).json()
		radio_currently_playing = random.choice(data["items"])["id"]["videoId"]
		stream = await client.voice_client_in(message.server).create_ytdl_player("https://www.youtube.com/watch?v=" + radio_currently_playing)
		player["current"]["stream"] = stream
		stream.start()
		await client.send_message(message.channel, ":arrow_forward: Now Playing: " + stream.title)
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

