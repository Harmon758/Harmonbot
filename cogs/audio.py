
import discord
from discord.ext import commands

import aiohttp
import asyncio
import inspect
import os
import random
import speech_recognition
import subprocess
import urllib
import youtube_dl

import credentials
from modules import utilities
from utilities import checks
from clients import aiohttp_session
from clients import cleverbot_instance
from clients import inflect_engine

def setup(bot):
	bot.add_cog(Audio(bot))

class Audio:
	
	def __init__(self, bot):
		self.bot = bot
		self.players = {}
		self.recognizer = speech_recognition.Recognizer()
		for name, command in inspect.getmembers(self):
			if isinstance(command, commands.Command) and command.parent is None and name != "audio":
				self.bot.add_command(command)
				self.audio.add_command(command)
	
	@commands.group(pass_context = True, aliases = ["yt", "youtube", "soundcloud", "voice", "stream", "play", "playlist", "spotify"], 
		invoke_without_command = True, no_pm = True)
	@checks.is_voice_connected()
	@checks.not_forbidden()
	async def audio(self, ctx, *options : str): #elif options[0] == "full":
		'''Audio System'''
		if "playlist" in ctx.message.content:
			await self.player_add_playlist(ctx.message)
		elif "spotify" in ctx.message.content:
			youtube_link = await self.spotify_to_youtube(options[0])
			if youtube_link:
				stream = await self.player_add_song(ctx.message, link = youtube_link)
				if stream:
					await self.bot.reply("Your song, " + stream.title + ", has been added to the queue.")
					return
			await self.bot.reply("Error")
		else:
			response = await self.bot.reply("Loading...")
			added = await self.player_add_song(ctx.message)
			if not added:
				await self.bot.reply("Error")
			else:
				await self.bot.edit_message(response, ctx.message.author.mention + " Your song has been added to the queue.")
	
	@commands.command(pass_context = True, no_pm = True)
	@checks.is_server_owner()
	async def join(self, ctx, *channel : str):
		'''Get me to join a voice channel'''
		if ctx.message.author.voice_channel:
			voice_channel = ctx.message.author.voice_channel
		else:
			voice_channel = discord.utils.find( lambda _channel: _channel.type == discord.ChannelType.voice and \
				utilities.remove_symbols(_channel.name).startswith(' '.join(channel)), 
				ctx.message.server.channels)
		if not voice_channel:
			await self.bot.reply("Voice channel not found.")
		elif self.bot.is_voice_connected(ctx.message.server):
			await self.bot.voice_client_in(ctx.message.server).move_to(voice_channel)
			await self.bot.reply("I've moved to the voice channel.")
		else:
			await self.bot.join_voice_channel(voice_channel)
			await self.bot.reply("I've joined the voice channel.")
			await self.start_player(ctx.message.channel)
	
	@commands.command(pass_context = True, no_pm = True)
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def leave(self, ctx):
		'''Tell me to leave the voice channel'''
		if self.bot.is_voice_connected(ctx.message.server):
			await self.bot.voice_client_in(ctx.message.server).disconnect()
			await self.bot.reply("I've left the voice channel.")
	
	@commands.command(pass_context = True, aliases = ["stop"], no_pm = True)
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def pause(self, ctx):
		'''Pause the current song'''
		player = self.players[ctx.message.server.id]
		player["current"]["stream"].pause()
		await self.bot.reply("Song paused")
	
	@commands.command(pass_context = True, aliases = ["start"], no_pm = True)
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def resume(self, ctx):
		'''Resume the current song'''
		player = self.players[ctx.message.server.id]
		player["current"]["stream"].resume()
		await self.bot.reply("Song resumed")
	
	@commands.command(pass_context = True, aliases = ["next"], no_pm = True)
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def skip(self, ctx):
		'''Skip the current song'''
		player = self.players[ctx.message.server.id]
		player["current"]["stream"].stop()
		await self.bot.reply("Song skipped")
	
	@commands.command(pass_context = True, aliases = ["repeat"], no_pm = True) # "restart"
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def replay(self, ctx):
		'''Repeat the current song'''
		response = await self.bot.reply("Restarting song...")
		player = self.players[ctx.message.server.id]
		player["current"]["stream"].pause()
		stream = await self.bot.voice_client_in(ctx.message.server).create_ytdl_player(player["current"]["stream"].url)
		old_stream = player["current"]["stream"]
		player["current"]["stream"] = stream
		stream.start()
		await self.bot.edit_message(response, ctx.message.author.mention + " Restarted song")
		while not stream.is_done():
			await asyncio.sleep(1)
		old_stream.stop()
	
	@commands.command(pass_context = True, aliases = ["clear"], no_pm = True)
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def empty(self, ctx):
		'''Empty the queue'''
		player = self.players[ctx.message.server.id]
		while not player["queue"].empty():
			stream = await player["queue"].get()
			stream["stream"].start()
			stream["stream"].stop()	
		await self.bot.reply("Queue emptied")
	
	@commands.command(pass_context = True, no_pm = True)
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def shuffle(self, ctx):
		'''Shuffle the queue'''
		response = await self.bot.reply("Shuffling...")
		player = self.players[ctx.message.server.id]
		song_list = []
		while not player["queue"].empty():
			song_list.append(await player["queue"].get())
		random.shuffle(song_list)
		for song in song_list:
			await player["queue"].put(song)
		await self.bot.edit_message(response, ctx.message.author.mention + " Shuffled songs")
	
	@commands.group(pass_context = True, no_pm = True)
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def radio(self, ctx):
		'''Radio station based on the current song'''
		pass
	
	@radio.command(name = "on", pass_context = True, aliases = ["start"], no_pm = True)
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def radio_on(self, ctx):
		'''Turn radio on'''
		response = await self.bot.reply("Starting Radio...")
		player = self.players[ctx.message.server.id]
		player["current"]["stream"].pause()
		url_data = urllib.parse.urlparse(player["current"]["stream"].url)
		query = urllib.parse.parse_qs(url_data.query)
		videoid = query["v"][0]
		url = "https://www.googleapis.com/youtube/v3/search?part=snippet&relatedToVideoId=" + videoid + "&type=video&key=" + credentials.google_apikey
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		radio_currently_playing = data["items"][0]["id"]["videoId"]
		stream = await self.bot.voice_client_in(ctx.message.server).create_ytdl_player("https://www.youtube.com/watch?v=" + radio_currently_playing)
		old_stream = player["current"]["stream"]
		player["current"]["stream"] = stream
		stream.start()
		player["radio_on"] = True
		await self.bot.edit_message(response, ctx.message.author.mention + " Radio is now on")
		await self.bot.say(":arrow_forward: Now Playing: " + stream.title)
		while player["radio_on"]:
			while not stream.is_done():
				await asyncio.sleep(1)
			if not player["radio_on"]:
				break
			url = "https://www.googleapis.com/youtube/v3/search?part=snippet&relatedToVideoId=" + radio_currently_playing + "&type=video&key=" + credentials.google_apikey
			async with aiohttp_session.get(url) as resp:
				data = await resp.json()
			radio_currently_playing = random.choice(data["items"])["id"]["videoId"]
			stream = await self.bot.voice_client_in(ctx.message.server).create_ytdl_player("https://www.youtube.com/watch?v=" + radio_currently_playing)
			player["current"]["stream"] = stream
			stream.start()
			await self.bot.say(":arrow_forward: Now Playing: " + stream.title)
		player["current"]["stream"] = old_stream
		old_stream.resume()
	
	@radio.command(name = "off", pass_context = True, aliases = ["stop"], no_pm = True)
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def radio_off(self, ctx):
		'''Turn radio off'''
		player = self.players[ctx.message.server.id]
		if player["radio_on"]:
			player["radio_on"] = False
			player["current"]["stream"].stop()
			await self.bot.reply("Radio is now off")
	
	@commands.command(pass_context = True, no_pm = True, hidden = True)
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def settext(self, ctx):
		'''Set text channel for audio'''
		player = self.players[ctx.message.server.id]
		player["text"] = ctx.message.channel.id
		await self.bot.reply("Text channel changed.")
	
	@commands.command(pass_context = True, no_pm = True)
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def tts(self, ctx, *, message : str):
		'''Text to speech'''
		_tts(ctx, message)
	
	def _tts(self, ctx, message):
		player = self.players[ctx.message.server.id]
		subprocess.call(["espeak", "-s 150", "-ven-us+f1", "-w data/tts.wav", message], shell = True)
		stream = self.bot.voice_client_in(ctx.message.server).create_ffmpeg_player("data/tts.wav")
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
	
	@commands.command(pass_context = True, no_pm = True)
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def play_file(self, ctx, filename : str):
		'''Plays an audio file'''
		player = self.players[ctx.message.server.id]
		stream = self.bot.voice_client_in(ctx.message.server).create_ffmpeg_player("data/audio_files/" + filename)
		paused = False
		if player["current"] and player["current"]["stream"].is_playing():
			player["current"]["stream"].pause()
			paused = True
		stream.start()
		while stream.is_playing():
			pass
		if paused:
			player["current"]["stream"].resume()
	
	@commands.command(pass_context = True, no_pm = True)
	@checks.is_server_owner()
	@checks.is_voice_connected()
	async def volume(self, ctx, volume_setting : float):
		'''
		Change the volume of the current song
		volume_setting : 0 - 200
		'''
		player = self.players[ctx.message.server.id]
		player["current"]["stream"].volume = volume_setting / 100
	
	@commands.command(pass_context = True, aliases = ["queue"], no_pm = True)
	@checks.is_voice_connected()
	async def current(self, ctx):
		'''See the current song and queue'''
		player = self.players[ctx.message.server.id]
		if not player["current"] or player["current"]["stream"].is_done():
			await self.bot.say("There is no song currently playing.")
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
			await self.bot.say("Currently playing: " + current["stream"].url + "\n" + views + ":eye: | " + likes + ":thumbsup::skin-tone-2: | " + dislikes + ":thumbsdown::skin-tone-2:\nAdded by: " + current["author"].name)
		if player["radio_on"]:
			await self.bot.say(":radio: Radio is currently on")
		else:
			if player["queue"].qsize() == 0:
				await self.bot.say("The queue is currently empty.")
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
						queue_string += "There " + inflect_engine.plural("is", more_songs) + ' ' + str(more_songs) + " more " + inflect_engine.plural("song", more_songs) + " in the queue"
						break
				await self.bot.say("\nQueue:\n" + queue_string)

	async def start_player(self, channel):
		player = {"queue" : asyncio.Queue(), "current" : None, "radio_on" : False, "text" : channel.id}
		self.players[channel.server.id] = player
		while self.bot.is_voice_connected(channel.server):
			current = await player["queue"].get()
			player["current"] = current
			stream = current["stream"]
			stream.start()
			await self.bot.send_message(channel.server.get_channel(player["text"]), ":arrow_forward: Now Playing: " + stream.title)
			while not stream.is_done():
				await asyncio.sleep(1)
		del self.players[channel.server.id]
	
	# Voice Input
	
	@commands.command(hidden = True, pass_context = True)
	@checks.not_forbidden()
	async def listen(self, ctx):
		await self.detectvoice(ctx)
	
	async def detectvoice(self, ctx):
		while True:
			while not os.path.isfile("data/testing.pcm") or os.stat("data/testing.pcm").st_size == 0:
				await asyncio.sleep(1)
			subprocess.call(["ffmpeg", "-f", "s16le", "-y", "-ar", "44.1k", "-ac", "2", "-i", "data/testing.pcm", "data/testing.wav"], shell=True)
			with speech_recognition.AudioFile("data/testing.wav") as source:
				audio = self.recognizer.record(source)
			try:
				text = self.recognizer.recognize_google(audio)
				await self.bot.send_message(ctx.message.channel, "I think you said: " + text)
			except speech_recognition.UnknownValueError:
				await self.bot.send_message(ctx.message.channel, "Google Speech Recognition could not understand audio")
			except speech_recognition.RequestError as e:
				await self.bot.send_message(ctx.message.channel, "Could not request results from Google Speech Recognition service; {0}".format(e))
			else:
				response = cleverbot_instance.ask(text)
				await self.bot.send_message(ctx.message.channel, "Responding with: " + response)
				self._tts(ctx, response)
			open("data/testing.pcm", 'w').close()
			
	@commands.command(hidden = True, pass_context = True)
	@checks.not_forbidden()
	async def srtest(self, ctx):
		subprocess.call(["ffmpeg", "-f", "s16le", "-y", "-ar", "44.1k", "-ac", "2", "-i", "data/testing.pcm", "data/testing.wav"], shell=True)
		with speech_recognition.AudioFile("data/testing.wav") as source:
			audio = self.recognizer.record(source)
		'''
		try:
			await self.bot.reply("Sphinx thinks you said: " + recognizer.recognize_sphinx(audio))
		except speech_recognition.UnknownValueError:
			await self.bot.reply("Sphinx could not understand audio")
		except speech_recognition.RequestError as e:
			await self.bot.reply("Sphinx error; {0}".format(e))
		'''
		try:
			text = self.recognizer.recognize_google(audio)
			await self.bot.say("I think you said: " + text)
		except speech_recognition.UnknownValueError:
			await self.bot.reply("Google Speech Recognition could not understand audio")
			return
		except speech_recognition.RequestError as e:
			await self.bot.reply("Could not request results from Google Speech Recognition service; {0}".format(e))
			return
		response = cleverbot_instance.ask(text)
		await self.bot.say("Responding with: " + response)
		self._tts(ctx, response)
	
	# Player Add Functions
	
	async def player_add_song(self, message, **kwargs):
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
			stream = await self.bot.voice_client_in(message.server).create_ytdl_player(link)
		except:
			try:
				link = await utilities.youtubesearch(message.content.split()[1:])
				stream = await self.bot.voice_client_in(message.server).create_ytdl_player(link)
			except:
				return False
		player = self.players[message.server.id]
		await player["queue"].put({"stream" : stream, "author" : message.author})
		return stream
	
	async def player_add_playlist(self, message):
		parsed_url = urllib.parse.urlparse(message.content.split()[1])
		path = parsed_url.path
		query = parsed_url.query
		if path[:9] == "/playlist" and query[:5] == "list=":
			response = await utilities.reply(message, "Loading...")
			playlistid = query[5:]
			base_url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&key={0}&playlistId={1}&maxResults=50".format(credentials.google_apikey, playlistid)
			url = base_url
			player_instance = self.players[message.server.id]
			while True:
				async with aiohttp_session.get(url) as resp:
					data = await resp.json()
				total = data["pageInfo"]["totalResults"]
				for item in data["items"]:
					position = item["snippet"]["position"] + 1
					link = "https://www.youtube.com/watch?v=" + item["snippet"]["resourceId"]["videoId"]
					await self.bot.edit_message(response, message.author.mention + " Loading " + str(position) + '/' + str(total))
					try:
						stream = await self.bot.voice_client_in(message.server).create_ytdl_player(link)
					except youtube_dl.utils.DownloadError:
						await utilities.reply(message, "Error loading video " + str(position) + " (`" + link + "`) from `" + message.content.split()[1] + '`')
						continue
					await player_instance["queue"].put({"stream" : stream, "author" : message.author})
				if not "nextPageToken" in data:
					break
				else:
					url = base_url + "&pageToken=" + data["nextPageToken"]
			await self.bot.edit_message(response, message.author.mention + " Your songs have been added to the queue.")
			return
		else:
			await utilities.reply(message, "Error")
			return
	
	# Utility

	async def spotify_to_youtube(self, link):
		path = urllib.parse.urlparse(link).path
		if path[:7] == "/track/":
			trackid = path[7:]
			url = "https://api.spotify.com/v1/tracks/" + trackid
			async with aiohttp_session.get(url) as resp:
				data = await resp.json()
			songname = "+".join(data["name"].split())
			artistname = "+".join(data["artists"][0]["name"].split())
			url = "https://www.googleapis.com/youtube/v3/search?part=snippet&q=" + songname + "+by+" + artistname + "&key=" + credentials.google_apikey
			async with aiohttp_session.get(url) as resp:
				data = await resp.json()
			data = data["items"][0]
			if "videoId" not in data["id"]:
				async with aiohttp_session.get(url) as resp:
					data = await resp.json()
				data = data["items"][1]
			link = "https://www.youtube.com/watch?v=" + data["id"]["videoId"]
			return link
		else:
			return False
	
	# Garbage Collection
	
	async def stop_all_streams(self):
		for player in self.players.values():
			while not player["queue"].empty():
				stream = await player["queue"].get()
				stream["stream"].start()
				stream["stream"].stop()
			if player["radio_on"]:
				player["radio_on"] = False
				player["current"]["stream"].stop()
			if player["current"] and not player["current"]["stream"].is_done():
				player["current"]["stream"].stop()

