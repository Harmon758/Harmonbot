
import discord

import asyncio
import functools
import json
import logging
import os
import random
import speech_recognition
import subprocess
import youtube_dl

import credentials
from modules import utilities

import clients
from clients import aiohttp_session
from clients import cleverbot_instance
from clients import inflect_engine

playlist_logger = logging.getLogger("playlist")
playlist_logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename = "data/temp/playlist_info.json", encoding = "utf-8", mode = 'w')
playlist_logger.addHandler(handler)

class AudioPlayer:
	
	def __init__(self, client, text_channel):
		self.bot = client
		self.text_channel = text_channel
		self.server = text_channel.server
		self.queue = asyncio.Queue()
		self.current = None
		self.play_next_song = asyncio.Event()
		self.ytdl_options = {"default_search": "auto", "noplaylist": True, "quiet": True, 
			"format": "webm[abr>0]/bestaudio/best", "prefer_ffmpeg": True}
		self.ytdl_playlist_options = {"default_search": "auto", "extract_flat": True, "forcejson": True, "quiet": True, 
			"logger": playlist_logger}
		self.default_volume = 100.0
		self.skip_votes_required = 0
		self.skip_votes = set()
		self.player = self.bot.loop.create_task(self.player_task())
		self.resume_flag = asyncio.Event()
		self.not_interrupted = asyncio.Event()
		self.not_interrupted.set()
		self.audio_files = os.listdir("data/audio_files/")
		self.library_files = [f for f in os.listdir("D:/Data (D)/Music/") if f.endswith((".mp3", ".m4a"))]
		self.library_flag = False
		self.radio_flag = False
		self.recognizer = speech_recognition.Recognizer()
		self.listener = None
		self.listen_paused = False

	async def join_channel(self, user, channel):
		# join logic
		if user.voice_channel:
			voice_channel = user.voice_channel
		else:
			voice_channel = discord.utils.find(lambda _channel: _channel.type == discord.ChannelType.voice and \
				utilities.remove_symbols(_channel.name).startswith(' '.join(channel)), self.server.channels)
		if not voice_channel:
			await self.bot.reply(":no_entry: Voice channel not found.")
		elif self.bot.is_voice_connected(self.server):
			await self.server.voice_client.move_to(voice_channel)
			await self.bot.say(":arrow_right_hook: I've moved to the voice channel.")
		else:
			await self.bot.join_voice_channel(voice_channel)
			await self.bot.say(":headphones: I've joined the voice channel.")
	
	async def leave_channel(self):
		if self.bot.is_voice_connected(self.server):
			if self.current and self.current["stream"].is_playing():
				self.current["stream"].stop()
			self.player.cancel()
			await self.server.voice_client.disconnect()
			await self.bot.say(":door: I've left the voice channel.")
	
	async def add_song(self, song, requester):
		info = await self._get_song_info(song)
		await self.queue.put({"info": info, "requester": requester})
		return info["title"]
	
	async def add_song_interrupt(self, videoid, requester):
		info = await self._get_song_info(videoid)
		return (await self._interrupt(info["url"], info["title"], requester))
	
	async def insert_song(self, song, requester, position):
		info = await self._get_song_info(song)
		self.queue._queue.insert(position - 1, {"info": info, "requester": requester})
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
	
	def _play_next_song(self):
		self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

	async def player_task(self):
		while True:
			self.play_next_song.clear()
			_current = await self.queue.get()
			await self.not_interrupted.wait()
			with open("data/logs/ffmpeg.log", 'a') as ffmpeg_log:
				stream = self.server.voice_client.create_ffmpeg_player(_current["info"]["url"], after = self._play_next_song, stderr = ffmpeg_log)
			stream.volume = self.default_volume / 100
			self.current = _current
			self.current["stream"] = stream
			self.current["stream"].start()
			await self.bot.send_message(self.text_channel, ":arrow_forward: Now Playing: `{}`".format(self.current["info"].get("title", "N/A")))
			number_of_listeners = len(self.server.voice_client.channel.voice_members) - 1
			self.skip_votes_required = number_of_listeners // 2 + number_of_listeners % 2
			self.skip_votes.clear()
			await self.play_next_song.wait()
	
	def pause(self):
		if not self.current or self.current["stream"].is_done():
			return False
		elif not self.current["stream"].is_playing():
			return None
		else:
			self.current["stream"].pause()
			return True
	
	def resume(self):
		if not self.current or self.current["stream"].is_done():
			return False
		elif self.current["stream"].is_playing():
			return None
		else:
			self.current["stream"].resume()
			return True
	
	def skip(self):
		if not self.current or self.current["stream"].is_done():
			return False
		else:
			self.current["stream"].stop()
			self.skip_votes.clear()
			return True
	
	def vote_skip(self, voter):
		if not self.current or self.current["stream"].is_done():
			return False
		elif voter.id in self.skip_votes:
			return None
		else:
			self.skip_votes.add(voter.id)
			vote_count = len(self.skip_votes)
			if vote_count >= self.skip_votes_required or voter.id == self.current["requester"].id:
				self.skip()
				return True
			else:
				return len(self.skip_votes)
	
	async def skip_specific(self, number):
		if 1 <= number <= self.queue.qsize():
			self.queue._queue.rotate(-(number - 1))
			song = await self.queue.get()
			self.queue._queue.rotate(number - 1)
			return song
		else:
			return False
	
	async def skip_to_song(self, number):
		if 1 <= number <= self.queue.qsize():
			songs = []
			for i in range(number - 1):
				songs.append(await self.queue.get())
			self.skip()
			return songs
		else:
			return False
	
	async def replay(self):
		if not self.current or not self.current.get("info").get("url"):
			return False
		with open("data/logs/ffmpeg.log", 'a') as ffmpeg_log:
			stream = self.server.voice_client.create_ffmpeg_player(self.current["info"]["url"], after = self._play_next_song, stderr = ffmpeg_log)
		stream.volume = self.default_volume / 100
		duplicate = self.current.copy()
		duplicate["stream"] = stream
		if not self.current["stream"].is_done():
			self.skip()
		self.queue._queue.appendleft(duplicate)
		await self.queue.put(None) # trigger get
		self.queue._queue.pop()
		return True
	
	def get_volume(self):
		if not self.current: return None
		return self.current["stream"].volume * 100
	
	def set_volume(self, volume_setting):
		if not self.current: return False
		self.current["stream"].volume = volume_setting / 100
		return True
	
	def current_output(self):
		if not self.current or self.current["stream"].is_done():
			return ":speaker: There is no song currently playing."
		else:
			views = utilities.add_commas(self.current["info"].get("view_count"))
			likes = utilities.add_commas(self.current["info"].get("like_count"))
			dislikes = utilities.add_commas(self.current["info"].get("dislike_count"))
			if self.radio_flag:
				output = ":radio: Radio is currently playing: "
			elif self.library_flag:
				output = ":notes: Playing song from my library: "
			else:
				output = ":musical_note: Currently playing: "
			output += self.current["info"].get("webpage_url")
			output += '\n' if views or likes or dislikes else ""
			output += views + ":eye:" if views else ""
			output += " | " if views and (likes or dislikes) else ""
			output += likes + ":thumbsup::skin-tone-2:" if likes else ""
			output += " | " if likes and dislikes else ""
			output += dislikes + ":thumbsdown::skin-tone-2:" if dislikes else ""
			output += "\nAdded by: " + self.current["requester"].display_name if not self.radio_flag and not self.library_flag else ""
			return output
	
	def queue_output(self):
		if self.radio_flag:
			return ":radio: Radio is currently on"
		elif self.library_flag:
			return ":notes: Playing songs from my library"
		elif self.queue.qsize() == 0:
			return ":hole: The queue is currently empty."
		else:
			queue_string = ""
			for number, stream in enumerate(list(self.queue._queue)[:10], start = 1):
				queue_string += ":{}: **{}** (<{}>) Added by: {}\n".format("keycap_ten" if number == 10 else inflect_engine.number_to_words(number), stream["info"].get("title", "N/A"), stream["info"].get("webpage_url", "N/A"), stream["requester"].display_name)
			if self.queue.qsize() > 10:
				more_songs = self.queue.qsize() - 10
				queue_string += ":arrow_right: There {} {} more {} in the queue".format(inflect_engine.plural("is", more_songs), more_songs, inflect_engine.plural("song", more_songs))
			return ":musical_score: Queue:\n" + queue_string
	
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
	
	async def play_tts(self, message, requester, *, amplitude = 100, pitch = 50, speed = 150, word_gap = 0, voice = "en-us+f1"):
		if not self.not_interrupted.is_set():
			return False
		func = functools.partial(subprocess.call, ["espeak", "-a {}".format(amplitude), "-p {}".format(pitch), "-s {}".format(speed), "-g {}".format(word_gap), "-v{}".format(voice), "-w data/temp/tts.wav", message], shell = True)
		await self.bot.loop.run_in_executor(None, func)
		interrupt_message = await self._interrupt("data/temp/tts.wav", "TTS message", requester)
		if interrupt_message: await self.bot.delete_message(interrupt_message)
		if os.path.exists("data/temp/tts.wav"): os.remove("data/temp/tts.wav")
		return interrupt_message
	
	async def play_file(self, filename, requester):
		if not filename:
			filename = random.choice(self.audio_files)
		elif filename not in self.audio_files:
			await self.bot.reply(":no_entry: File not found")
			return True
		return (await self._interrupt("data/audio_files/" + filename, filename, requester))
	
	def list_files(self):
		return ", ".join(self.audio_files)
	
	async def play_from_library(self, filename, requester, *, clear_flag = True):
		if not filename:
			filename = random.choice(self.library_files)
		elif filename not in self.library_files:
			await self.bot.reply(":no_entry: Song file not found")
			return True
		return (await self._interrupt("D:/Data (D)/Music/" + filename, filename, requester, clear_flag = clear_flag))
		# print([f for f in os.listdir("D:/Data (D)/Music/") if not f.endswith((".mp3", ".m4a", ".jpg"))])
	
	async def play_library(self, requester):
		if not self.not_interrupted.is_set():
			return False
		if not self.library_flag:
			await self.bot.say(":notes: Playing songs from my library")
			self.library_flag = True
			paused = self.pause()
			self.not_interrupted.clear()
			while self.bot.is_voice_connected(self.server) and self.library_flag:
				await self.play_from_library("", requester, clear_flag = False)
				await asyncio.sleep(0.1) # wait to check
			self.not_interrupted.set()
			if paused: self.resume()
			return True
	
	def stop_library(self):
		if self.library_flag:
			self.library_flag = False
			self.skip()
	
	async def _interrupt(self, source, title, requester, *, clear_flag = True):
		if not self.not_interrupted.is_set() and clear_flag:
			return False
		with open("data/logs/ffmpeg.log", 'a') as ffmpeg_log:
			stream = self.server.voice_client.create_ffmpeg_player(source, after = self._resume_from_interruption, stderr = ffmpeg_log)
		stream.volume = self.default_volume / 100
		paused = self.pause()
		stream.start()
		temp_current = self.current
		self.current = {"stream": stream, "info": {"webpage_url": title}, "requester": requester}
		if clear_flag: self.not_interrupted.clear()
		interrupt_message = await self.bot.send_message(self.text_channel, ":arrow_forward: Now Playing: " + title)
		await self.resume_flag.wait()
		self.current = temp_current
		if paused: self.resume()
		if clear_flag: self.not_interrupted.set()
		self.bot.loop.call_soon_threadsafe(self.resume_flag.clear)
		return interrupt_message
	
	def _resume_from_interruption(self):
		self.bot.loop.call_soon_threadsafe(self.resume_flag.set)
	
	async def add_playlist(self, playlist, requester):
		response = await self.bot.reply(":cd: Loading..")
		ydl = youtube_dl.YoutubeDL(self.ytdl_playlist_options)
		func = functools.partial(ydl.extract_info, playlist, download = False)
		await self.bot.loop.run_in_executor(None, func)
		with open("data/temp/playlist_info.json", "r+") as playlist_info_file:
			videos = [json.loads(line) for line in playlist_info_file if line.startswith('{')]
			playlist_info_file.seek(0)
			playlist_info_file.truncate()
		for position, video in enumerate(videos, start = 1):
			await self.bot.edit_message(response, requester.mention + " :cd: Loading {}/{}".format(position, len(videos)))
			try:
				await self.add_song(video["url"], requester)
			except Exception as e:
				try:
					await self.bot.send_message(self.text_channel, "{}: :warning: Error loading video {} (<{}>) from <{}>\n{}: {}".format(requester.mention, position, "https://www.youtube.com/watch?v=" + video["id"], playlist, type(e).__name__, e))
				except discord.errors.HTTPException:
					await self.bot.send_message(self.text_channel, "{}: :warning: Error loading video {} (<{}>) from <{}>".format(requester.mention, position, "https://www.youtube.com/watch?v=" + video["id"], playlist))
		await self.bot.edit_message(response, requester.mention + " :ballot_box_with_check: Your songs have been added to the queue.")
	
	async def radio_on(self, requester):
		if not self.not_interrupted.is_set():
			return False
		if not self.radio_flag:
			if not self.current:
				await self.bot.reply(":no_entry: Please play a song to base the radio station off of first")
				return None
			await self.bot.say(":radio: Radio based on `{}` is now on".format(self.current["info"]["title"]))
			self.radio_flag = True
			videoid = self.current["info"]["id"]
			paused = self.pause()
			while self.bot.is_voice_connected(self.server) and self.radio_flag:
				url = "https://www.googleapis.com/youtube/v3/search?part=snippet&relatedToVideoId={}&type=video&key={}".format(videoid, credentials.google_apikey)
				async with aiohttp_session.get(url) as resp:
					data = await resp.json()
				videoid = random.choice(data["items"])["id"]["videoId"]
				await self.add_song_interrupt(videoid, requester)
				await asyncio.sleep(0.1) # wait to check
			if paused: self.resume()
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
		if not self.not_interrupted.is_set():
			return False
		if clients.harmonbot_listener not in self.server.voice_client.channel.voice_members:
			await self.bot.send_message(self.text_channel, ":no_entry: {} needs to be in the voice channel".format(clients.harmonbot_listener.mention))
			return None
		self.listen_paused = self.pause()
		self.not_interrupted.clear()
		if not self.listener:
			self.listener = True
		listen_message = await self.bot.send_message(self.text_channel, ">listen")
		await self.bot.wait_for_message(author = clients.harmonbot_listener, content = ":ear::skin-tone-2: I'm listening..")
		await self.bot.delete_message(listen_message)
		await self.bot.wait_for_message(author = clients.harmonbot_listener, content = ":stop_sign: I stopped listening.")
		await self.process_listen()
		if self.listen_paused: self.resume()
		self.not_interrupted.set()
		if self.listener is True:
			self.listener = None
		return True
	
	async def finish_listening(self):
		stop_message = await self.bot.send_message(self.text_channel, ">stoplistening")
		await self.bot.wait_for_message(author = clients.harmonbot_listener, content = ":stop_sign: I stopped listening.")
		await self.bot.delete_message(stop_message)
	
	async def process_listen(self):
		if not os.path.isfile("data/temp/heard.pcm") or os.stat("data/temp/heard.pcm").st_size == 0:
			await self.bot.send_message(self.text_channel, ":warning: No input found")
			return
		func = functools.partial(subprocess.call, ["ffmpeg", "-f", "s16le", "-y", "-ar", "44.1k", "-ac", "2", "-i", "data/temp/heard.pcm", "data/temp/heard.wav"], shell = True)
		await self.bot.loop.run_in_executor(None, func)
		with speech_recognition.AudioFile("data/temp/heard.wav") as source:
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
			await self.bot.send_message(self.text_channel, "I think you said: " + text)
		except speech_recognition.UnknownValueError:
			# await self.bot.send_message(self.text_channel, ":no_entry: Google Speech Recognition could not understand audio")
			await self.bot.send_message(self.text_channel, ":no_entry: I couldn't understand that")
		except speech_recognition.RequestError as e:
			await self.bot.send_message(self.text_channel, ":warning: Could not request results from Google Speech Recognition service; {0}".format(e))
		else:
			response = cleverbot_instance.ask(text)
			await self.bot.send_message(self.text_channel, "Responding with: " + response)
			await self.play_tts(response, self.bot.user)
		# open("data/heard.pcm", 'w').close() # necessary?
		# os.remove ?

