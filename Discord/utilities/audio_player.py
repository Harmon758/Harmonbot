
import discord

import asyncio
import functools
import json
import logging
import os
import random
import subprocess

import speech_recognition

from modules import utilities
from utilities import errors

class AudioPlayer:
	
	def __init__(self, bot, text_channel):
		self.bot = bot
		self.text_channel = text_channel
		self.guild = text_channel.guild
		self.queue = asyncio.Queue()
		self.current = None
		self.play_next_song = asyncio.Event()
		self.default_volume = 100.0
		self.skip_votes_required = 0
		self.skip_votes = set()
		self.player = self.bot.loop.create_task(self.player_task())
		self.resume_flag = asyncio.Event()
		self.not_interrupted = asyncio.Event()
		self.not_interrupted.set()
		self.audio_files = os.listdir(self.bot.data_path + "/audio_files/")
		self.library_files = [f for f in os.listdir(self.bot.library_path) if f.endswith((".mp3", ".m4a"))]
		self.library_flag = False
		self.radio_flag = False
		self.recognizer = speech_recognition.Recognizer()
		self.listener = None
		self.listen_paused = False
		self.previous_played_time = 0
	
	@classmethod
	def from_context(cls, ctx):
		return cls(ctx.bot, ctx.channel)
	
	@property
	def interrupted(self):
		return not self.not_interrupted.is_set()
	
	async def join_channel(self, user, channel):
		# join logic
		if user.voice_channel:
			voice_channel = user.voice_channel
		else:
			voice_channel = discord.utils.find(lambda _channel: _channel.type == discord.ChannelType.voice and \
				utilities.remove_symbols(_channel.name).startswith(' '.join(channel)), self.guild.channels)
		if not voice_channel:
			raise errors.AudioError("Voice channel not found")
		if self.guild.voice_client:
			await self.guild.voice_client.move_to(voice_channel)
			return True
		await voice_channel.connect()
	
	async def leave_channel(self):
		if self.guild.voice_client:
			if self.guild.voice_client.is_playing():
				self.guild.voice_client.stop()
			self.player.cancel()
			await self.guild.voice_client.disconnect()
			return True
	
	async def add_song(self, song, requester, timestamp, *, stream = False):
		info = await self._get_song_info(song)
		await self.queue.put({"info": info, "requester": requester, "timestamp": timestamp, "stream": stream})
		return info["title"], info["webpage_url"]
	
	async def add_song_interrupt(self, videoid, requester, timestamp):
		info = await self._get_song_info(videoid)
		return (await self._interrupt(info["url"], info["title"], requester, timestamp))
	
	async def insert_song(self, song, requester, timestamp, position):
		info = await self._get_song_info(song)
		self.queue._queue.insert(position - 1, {"info": info, "requester": requester, "timestamp": timestamp})
		await self.queue.put(None) # trigger get
		self.queue._queue.pop()
		return info["title"]
	
	async def _get_song_info(self, song):
		ydl = youtube_dl.YoutubeDL(self.ytdl_options)
		func = functools.partial(ydl.extract_info, song, download = False)
		info = await self.bot.loop.run_in_executor(None, func)
		if "entries" in info:
			info = info["entries"][0]
		logging.getLogger("discord").info("playing URL {}".format(song))
		return info
	
	async def _download_song(self, song):
		ydl = youtube_dl.YoutubeDL(self.ytdl_download_options)
		func = functools.partial(ydl.extract_info, song, download = True)
		info = await self.bot.loop.run_in_executor(None, func)
		return ydl.prepare_filename(info)
	
	def _play_next_song(self):
		self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

	async def player_task(self):
		filename = None
		while True:
			self.play_next_song.clear()
			if filename:
				try:
					os.remove(filename)
				except PermissionError as e:
					print(str(e))
			current = await self.queue.get()
			await self.not_interrupted.wait()
			if current["info"].get("is_live") or current.get("stream"):
				with open("data/logs/ffmpeg.log", 'a') as ffmpeg_log:
					stream = self.guild.voice_client.create_ffmpeg_player(current["info"]["url"], after = self._play_next_song, stderr = ffmpeg_log)
				stream.volume = self.default_volume / 1000
				self.current = current
				self.current["stream"] = stream
				self.current["stream"].start()
				await self.bot.send_embed(self.text_channel, ":arrow_forward: Now Playing", title = current["info"].get("title", "N/A"), title_url = current["info"].get("webpage_url"), timestamp = current["timestamp"], footer_text = current["requester"].display_name, footer_icon_url = current["requester"].avatar_url or current["requester"].default_avatar_url, thumbnail_url = current["info"].get("thumbnail"))
			else:
				embed = discord.Embed(title = current["info"].get("title", "N/A"), url = current["info"].get("webpage_url"), description = ":arrow_down: Downloading..", timestamp = current["timestamp"], color = self.bot.bot_color)
				embed.set_footer(text = current["requester"].display_name, icon_url = current["requester"].avatar_url or current["requester"].default_avatar_url)
				thumbnail = current["info"].get("thumbnail")
				if thumbnail: embed.set_thumbnail(url = thumbnail)
				now_playing_message = await self.bot.send_message(self.text_channel, embed = embed)
				filename = await self._download_song(current["info"]["webpage_url"]) #
				before_options = None
				if current["info"].get("start_time"): before_options = "-ss {}".format(current["info"]["start_time"])
				self.previous_played_time = current["info"].get("start_time") if current["info"].get("start_time") else 0
				with open("data/logs/ffmpeg.log", 'a') as ffmpeg_log:
					stream = self.guild.voice_client.create_ffmpeg_player(filename, before_options = before_options, after = self._play_next_song, stderr = ffmpeg_log)
				stream.volume = self.default_volume / 1000
				self.current = current
				self.current["stream"] = stream
				self.current["stream"].start()
				embed.description = ":arrow_forward: Now playing"
				await now_playing_message.edit(embed = embed)
			## stream.buff.read(stream.frame_size * 100 / stream.delay)
			number_of_listeners = len(self.guild.voice_client.channel.voice_members) - 1
			self.skip_votes_required = number_of_listeners // 2 + number_of_listeners % 2
			self.skip_votes.clear()
			await self.play_next_song.wait()
	
	def skip(self):
		if self.guild.voice_client and self.guild.voice_client.is_playing() or self.guild.voice_client.is_paused():
			# Avoid setting _player to None (with voice_client.stop()) in case of use (e.g. replay) after skip
			self.guild.voice_client._player.stop()
			self.skip_votes.clear()
			return True
	
	def vote_skip(self, voter):
		self.skip_votes.add(voter.id)
		vote_count = len(self.skip_votes)
		if vote_count < self.skip_votes_required and voter.id != self.guild.voice_client.source.requester.id:
			return len(self.skip_votes)
		self.skip()
	
	async def skip_specific(self, number):
		if not 1 <= number <= self.queue.qsize():
			raise errors.AudioError("There aren't that many songs in the queue")
		self.queue._queue.rotate(-(number - 1))
		song = await self.queue.get()
		self.queue._queue.rotate(number - 1)
		return song
	
	async def skip_to_song(self, number):
		if not 1 <= number <= self.queue.qsize():
			raise errors.AudioError("There aren't that many songs in the queue")
		songs = []
		for i in range(number - 1):
			songs.append(await self.queue.get())
		self.skip()
		return songs
	
	async def replay(self):
		if not self.current or not self.current.get("info").get("url"):
			return False
		with open("data/logs/ffmpeg.log", 'a') as ffmpeg_log:
			stream = self.guild.voice_client.create_ffmpeg_player(self.current["info"]["url"], after = self._play_next_song, stderr = ffmpeg_log)
		stream.volume = self.default_volume / 1000
		duplicate = self.current.copy()
		duplicate["stream"] = stream
		if not self.current["stream"].is_done():
			self.skip()
		self.queue._queue.appendleft(duplicate)
		await self.queue.put(None) # trigger get
		self.queue._queue.pop()
		return True
	
	def queue_embed(self):
		if self.radio_flag:
			return discord.Embed(title = ":radio: Radio is currently on", color = self.bot.bot_color)
		elif self.library_flag:
			return discord.Embed(title = ":notes: Playing songs from my library", color = self.bot.bot_color)
		elif self.queue.qsize() == 0:
			return discord.Embed(title = ":hole: The queue is currently empty", color = self.bot.bot_color)
		else:
			queue_string = ""
			for number, source in enumerate(list(self.queue._queue)[:10], start = 1):
				queue_string += ":{}: **[{}]({})** (Added by: {})\n".format("keycap_ten" if number == 10 else self.bot.inflect_engine.number_to_words(number), source.info.get("title", "N/A"), source.info.get("webpage_url", "N/A"), source.requester.display_name)
			if self.queue.qsize() > 10:
				more_songs = self.queue.qsize() - 10
				queue_string += ":arrow_right: There {} {} more {} in the queue".format(self.bot.inflect_engine.plural("is", more_songs), more_songs, self.bot.inflect_engine.plural("song", more_songs))
			return discord.Embed(title = ":musical_score: Queue:", description = queue_string, color = self.bot.bot_color)
	
	async def empty_queue(self):
		while not self.queue.empty():
			song = await self.queue.get()
			del song
		# self.queue._queue.clear() ?
	
	async def shuffle_queue(self):
		song_list = []
		while not self.queue.empty():
			song_list.append(await self.queue.get())
		random.shuffle(song_list)
		for song in song_list:
			await self.queue.put(song)
	
	async def add_playlist(self, playlist, requester, timestamp):
		response = await ctx.embed_reply(":cd: Loading..")
		func = functools.partial(self.bot.ytdl_playlist.extract_info, playlist, download = False)
		info = await self.bot.loop.run_in_executor(None, func)
		embed = response.embeds[0]
		for position, video in enumerate(info["entries"], start = 1):
			if not video: continue
			embed.description = ":cd: Loading {}/{}".format(position, len(info["entries"]))
			await self.bot.edit_message(response, embed = embed)
			try:
				await self.add_song(video["url"], requester, timestamp)
			except Exception as e:
				try:
					await self.bot.send_embed(self.text_channel, "{}: :warning: Error loading video {} (<{}>) from <{}>\n{}: {}".format(requester.mention, position, "https://www.youtube.com/watch?v=" + video["id"], playlist, type(e).__name__, e))
				except discord.HTTPException:
					await self.bot.send_embed(self.text_channel, "{}: :warning: Error loading video {} (<{}>) from <{}>".format(requester.mention, position, "https://www.youtube.com/watch?v=" + video["id"], playlist))
		embed.description = ":ballot_box_with_check: Your songs have been added to the queue"
		await response.edit(embed = embed)
	
	async def interrupt(self, source, *, clear_flag = True):
		if self.interrupted and clear_flag:
			return False
		was_playing = self.guild.voice_client.is_playing()
		if was_playing:  # Use := in Python 3.8
			self.guild.voice_client.pause()
		interrupted_source = self.guild.voice_client.source if isinstance(self.guild.voice_client.source, YTDLSource) else None
		self.guild.voice_client.play(source, after = lambda e: self.bot.loop.call_soon_threadsafe(self.resume_flag.set))
		if clear_flag:
			self.not_interrupted.clear()
		interrupt_message = await self.bot.send_embed(self.text_channel, ":arrow_forward: Now Playing: " + source.title)
		await self.resume_flag.wait()
		if interrupted_source:
			self.guild.voice_client.play(interrupted_source)
		if was_playing:
			self.guild.voice_client.resume()
		if clear_flag:
			self.not_interrupted.set()
		self.bot.loop.call_soon_threadsafe(self.resume_flag.clear)
		return interrupt_message
	
	async def play_file(self, ctx, filename):
		if not filename:
			filename = random.choice(self.audio_files)
		elif filename not in self.audio_files:
			await ctx.embed_reply(":no_entry: File not found")
			return True
		return await self.interrupt(FileSource(ctx, ctx.bot.data_path + "/audio_files/" + filename, self.default_volume, title_prefix = "Audio File: "))
	
	def list_files(self):
		return ", ".join(self.audio_files)
	
	async def play_tts(self, ctx, message, *, amplitude = 100, pitch = 50, speed = 150, word_gap = 0, voice = "en-us+f1"):
		if self.interrupted: return False
		source = TTSSource(ctx, message, amplitude = amplitude, pitch = pitch, speed = speed, word_gap = word_gap, voice = voice)
		await source.generate_file()
		source.initialize_source(self.default_volume)
		interrupt_message = await self.interrupt(source)
		return interrupt_message
	
	async def play_from_library(self, filename, requester, timestamp, *, clear_flag = True):
		if not filename:
			filename = random.choice(self.library_files)
		elif filename not in self.library_files:
			await ctx.embed_reply(":no_entry: Song file not found")
			return True
		return (await self._interrupt(self.bot.library_path + filename, filename, requester, timestamp, clear_flag = clear_flag))
		## print([f for f in os.listdir(self.bot.library_path) if not f.endswith((".mp3", ".m4a", ".jpg"))])
	
	async def play_library(self, requester, timestamp):
		if self.interrupted:
			return False
		if not self.library_flag:
			await ctx.embed_send(":notes: Playing songs from my library")
			self.library_flag = True
			was_playing = self.guild.voice_client.is_playing()
			if was_playing:  # Use := in Python 3.8
				self.guild.voice_client.pause()
			self.not_interrupted.clear()
			while self.guild.voice_client and self.library_flag:
				await self.play_from_library("", requester, timestamp, clear_flag = False)
				await asyncio.sleep(0.1)  # wait to check
			self.not_interrupted.set()
			if self.guild.voice_client and was_playing:
				self.guild.voice_client.resume()
			return True
	
	def stop_library(self):
		if self.library_flag:
			self.library_flag = False
			self.skip()
	
	async def radio_on(self, ctx):
		if self.interrupted:
			return False
		if not self.radio_flag:
			if not self.guild.voice_client.source:
				await ctx.embed_reply(":no_entry: Please play a song to base the radio station off of first")
				# TODO: Non song based station?
				return None
			await self.bot.send_embed(self.text_channel, f":radio: Radio based on `{self.guild.voice_client.source.info['title']}` is now on")
			self.radio_flag = True
			videoid = self.guild.voice_client.source.info["id"]
			was_playing = self.guild.voice_client.is_playing()
			if was_playing:  # Use := in Python 3.8
				self.guild.voice_client.pause()
			while self.guild.voice_client and self.radio_flag:
				url = f"https://www.googleapis.com/youtube/v3/search"
				params = {"part": "snippet", "type": "video", 
							"relatedToVideoId": videoid, "key": ctx.bot.GOOGLE_API_KEY}
				async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
					data = await resp.json()
				videoid = random.choice(data["items"])["id"]["videoId"]
				
				source = YTDLSource(ctx, videoid, stream = True)
				await source.get_info()
				await source.initialize_source(self.default_volume)
				await self.interrupt(source)
				
				await asyncio.sleep(0.1)  # wait to check
			if self.guild.voice_client and was_playing:
				self.guild.voice_client.resume()
			return True
	
	def radio_off(self):
		if self.radio_flag:
			self.radio_flag = False
			self.skip()
	
	async def start_listening(self):
		if not self.listener and self.not_interrupted.is_set():
			self.listener = self.bot.loop.create_task(self.listen_task())
			return True
	
	async def stop_listening(self):
		if self.listener:
			if not (self.listener is True):
				self.listener.cancel()
			self.listener = None
			await self.finish_listening()
			if self.listen_paused: self.resume()
			self.not_interrupted.set()
	
	async def listen_task(self):
		while (await self.listen_once()): pass
		self.listener = None
				
	async def listen_once(self):
		if self.interrupted:
			return False
		if self.bot.listener_bot not in self.guild.voice_client.channel.voice_members:
			await self.bot.send_embed(self.text_channel, ":no_entry: {} needs to be in the voice channel".format(self.bot.listener_bot.mention))
			return None
		try:
			self.pause()
		except errors.AudioError:
			self.listen_paused = False
		else:
			self.listen_paused = True
		self.not_interrupted.clear()
		if not self.listener:
			self.listener = True
		listen_message = await self.bot.send_message(self.text_channel, ">listen")
		await self.bot.wait_for_message(author = self.bot.listener_bot, content = ":ear::skin-tone-2: I'm listening..")
		await self.bot.delete_message(listen_message)
		await self.bot.wait_for_message(author = self.bot.listener_bot, content = ":stop_sign: I stopped listening.")
		await self.process_listen()
		if self.listen_paused: self.resume()
		self.not_interrupted.set()
		if self.listener is True:
			self.listener = None
		return True
	
	async def finish_listening(self):
		stop_message = await self.bot.send_message(self.text_channel, ">stoplistening")
		await self.bot.wait_for_message(author = self.bot.listener_bot, content = ":stop_sign: I stopped listening.")
		await self.bot.delete_message(stop_message)
	
	async def process_listen(self):
		if not os.path.isfile(self.bot.data_path + "/temp/heard.pcm") or os.stat(self.bot.data_path + "/temp/heard.pcm").st_size == 0:
			await self.bot.send_embed(self.text_channel, ":warning: No input found")
			return
		func = functools.partial(subprocess.call, ["ffmpeg", "-f", "s16le", "-y", "-ar", "44.1k", "-ac", "2", "-i", self.bot.data_path + "/temp/heard.pcm", self.bot.data_path + "/temp/heard.wav"], shell = True)
		# TODO: Use creationflags = subprocess.CREATE_NO_WINDOW in place of shell = True
		await self.bot.loop.run_in_executor(None, func)
		with speech_recognition.AudioFile(self.bot.data_path + "/temp/heard.wav") as source:
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
			await self.bot.send_embed(self.text_channel, "I think you said: `{}`".format(text))
		except speech_recognition.UnknownValueError:
			# await self.bot.send_embed(self.text_channel, ":no_entry: Google Speech Recognition could not understand audio")
			await self.bot.send_embed(self.text_channel, ":no_entry: I couldn't understand that")
		except speech_recognition.RequestError as e:
			await self.bot.send_embed(self.text_channel, ":warning: Could not request results from Google Speech Recognition service; {}".format(e))
		else:
			response = self.bot.aiml_kernel.respond(text)
			# TODO: Handle brain not loaded?
			if not response:
				games_cog = client.get_cog("Games")
				if not games_cog: return
				response = await games_cog.cleverbot_get_reply(text)
			await self.bot.send_embed(self.text_channel, "Responding with: `{}`".format(response))
			await self.play_tts(response, self.bot.user)
		# open(self.bot.data_path + "/heard.pcm", 'w').close() # necessary?
		# os.remove ?

