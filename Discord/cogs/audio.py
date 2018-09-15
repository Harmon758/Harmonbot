
import discord
from discord.ext import commands

import base64
import concurrent.futures
import inspect
import random
import urllib

import clients
import credentials
from utilities import audio_player
from utilities import checks
from utilities import errors

def setup(bot):
	bot.add_cog(Audio(bot))

class Audio:
	
	def __init__(self, bot):
		self.bot = bot
		self.players = {}
		for name, command in inspect.getmembers(self):
			if isinstance(command, commands.Command) and command.parent is None and name != "audio":
				self.bot.add_command(command)
				self.audio.add_command(command)
	
	@commands.group(aliases = ["yt", "youtube", "soundcloud", "voice", "stream", "play", "playlist", "spotify", "budio", "music", "download"], description = "Supports [these sites](https://rg3.github.io/youtube-dl/supportedsites.html) and Spotify", invoke_without_command = True)
	@commands.guild_only()
	@checks.is_voice_connected()
	@checks.not_forbidden()
	async def audio(self, ctx, *, song : str = ""): #elif options[0] == "full":
		'''
		Audio System - play a song
		All audio subcommands are also commands
		For cleanup of audio commands, the Manage Messages permission is required
		'''
		if not song:
			await ctx.embed_reply(":grey_question: What would you like to play?")
			return
		if "playlist" in song:
			await self.players[ctx.guild.id].add_playlist(song, ctx.author, ctx.message.created_at)
			return
		if "spotify" in song:
			song = await self.spotify_to_youtube(song)
			if not song:
				await ctx.embed_reply(":warning: Error")
				return
		response = await ctx.embed_reply(":cd: Loading..")
		embed = response.embeds[0]
		stream = ctx.invoked_with == "stream"
		try:
			title, url = await self.players[ctx.guild.id].add_song(song, ctx.author, ctx.message.created_at, stream = stream)
		except Exception as e:
			embed.description = ":warning: Error loading `{}`\n`{}: {}`".format(song, type(e).__name__, e)
			if len(embed.description) > ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT:
				embed.description = embed.description[:ctx.bot.EDCL - 4] + "...`"
				# EDCL: Embed Description Character Limit
		else:
			embed.title = title
			embed.url = url
			embed.description = ":ballot_box_with_check: Successfully added `{}` to the queue".format(song)
		finally:
			await self.bot.edit_message(response, embed = embed)
			await self.bot.attempt_delete_message(ctx.message)
	
	@commands.command(aliases = ["summon", "move"])
	@commands.guild_only()
	@checks.is_permitted()
	async def join(self, ctx, *channel : str):
		'''Get me to join a voice channel'''
		# TODO: Permit all when not in voice channel?
		if ctx.guild.id not in self.players:
			self.players[ctx.guild.id] = audio_player.AudioPlayer(self.bot, ctx.channel)
		try:
			moved = await self.players[ctx.guild.id].join_channel(ctx.author, channel)
		except errors.AudioNotPlaying:
			await ctx.embed_reply(":no_entry: Voice channel not found", footer_text = "In response to: {}".format(ctx.message.content))
		except concurrent.futures._base.TimeoutError:
			await ctx.embed_reply(":no_entry: Error joining the voice channel\nPlease check that I'm permitted to join")
		else:
			await ctx.embed_reply(":arrow_right_hook: I've moved to the voice channel" if moved else ":headphones: I've joined the voice channel")
	
	@commands.command()
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def leave(self, ctx):
		'''Tell me to leave the voice channel'''
		if (await self.players[ctx.guild.id].leave_channel()):
			await ctx.embed_reply(":door: I've left the voice channel")
		del self.players[ctx.guild.id]
		await self.bot.attempt_delete_message(ctx.message)
		## await ctx.embed_reply("The leave command is currently disabled right now, due to an issue/bug with Discord.")
	
	@commands.command(aliases = ["stop"])
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def pause(self, ctx):
		'''Pause the current song'''
		try:
			self.players[ctx.guild.id].pause()
		except errors.AudioNotPlaying:
			await ctx.embed_reply(":no_entry: There is no song to pause")
		except errors.AudioAlreadyDone:
			await ctx.embed_reply(":no_entry: The song is already paused")
		else:
			await ctx.embed_reply(":pause_button: Paused song")
	
	@commands.command(aliases = ["start"])
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def resume(self, ctx):
		'''Resume the current song'''
		try:
			self.players[ctx.guild.id].resume()
		except errors.AudioNotPlaying:
			await ctx.embed_reply(":no_entry: There is no song to resume")
		except errors.AudioAlreadyDone:
			await ctx.embed_reply(":no_entry: The song is already playing")
		else:
			await ctx.embed_reply(":play_pause: Resumed song")
	
	@commands.group(aliases = ["next", "remove"], invoke_without_command = True)
	@commands.guild_only()
	@checks.not_forbidden()
	@checks.is_voice_connected()
	async def skip(self, ctx, *, number : int = 0):
		'''
		Skip a song
		Skip or vote to skip the current song or skip a song number in the queue
		Those permitted and the person who requested the song can immediately skip the song and skip songs in the queue
		Otherwise, a majority vote of the people in the voice channel is required
		'''
		# TODO: Implement override permission
		player = self.players[ctx.guild.id]
		if ctx.author.id in (ctx.guild.owner.id, self.bot.owner_id) or checks.is_permitted_check(ctx):
			if number:
				try:
					song = await player.skip_specific(number)
				except errors.AudioNotPlaying:
					await ctx.embed_reply(":no_entry: There's not that many songs in the queue", footer_text = "In response to: {}".format(ctx.message.content))
				else:
					await ctx.embed_reply(":put_litter_in_its_place: Skipped #{} in the queue: `{}`".format(number, song["info"]["title"]))
					del song
			else:
				try:
					player.skip()
				except errors.AudioNotPlaying:
					await ctx.embed_reply(":no_entry: There is no song to skip")
				else:
					await ctx.embed_reply(":next_track: Song skipped")
					# TODO: Include title of skipped song
		elif ctx.author in self.bot.voice_client_in(ctx.guild).channel.voice_members:
			try:
				vote = player.vote_skip(ctx.author)
			except errors.AudioNotPlaying:
				await ctx.embed_reply(":no_entry: There is no song to skip")
			except errors.AudioAlreadyDone:
				await ctx.embed_reply(":no_entry: You've already voted to skip. Skips: {}/{}".format(len(player.skip_votes), player.skip_votes_required))
			else:
				await ctx.embed_reply(":white_check_mark: You voted to skip the current song\n{}".format("Skips: {}/{}".format(vote, player.skip_votes_required) if vote else ":next_track: Song skipped"))
		else:
			await ctx.embed_reply(":no_entry: You're not even listening!")
	
	@skip.command(name = "to")
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def skip_to(self, ctx, number : int):
		'''
		Skip to a song in the queue
		Skips every song before number
		'''
		try:
			songs = await self.players[ctx.guild.id].skip_to_song(number)
		except errors.AudioNotPlaying:
			await ctx.embed_reply(":no_entry: There aren't that many songs in the queue", footer_text = "In response to: {}".format(ctx.message.content))
		else:
			await ctx.embed_reply(":put_litter_in_its_place: Skipped to #{} in the queue".format(number))
			del songs
	
	@commands.command(aliases = ["repeat"])
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def replay(self, ctx):
		'''Repeat the current song'''
		# TODO: Add restart alias?
		response = await ctx.embed_reply(":repeat_one: Restarting song..")
		embed = response.embeds[0]
		replayed = await self.players[ctx.guild.id].replay()
		embed.description = ":repeat_one: Restarted song" if replayed else ":no_entry: There is nothing to replay"
		await self.bot.edit_message(response, embed = embed)
		await self.bot.attempt_delete_message(ctx.message)
	
	@commands.command()
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def insert(self, ctx, position_number : int, *, song : str):
		'''Insert a song into the queue'''
		if "spotify" in song:
			song = await self.spotify_to_youtube(song)
			if not song:
				await ctx.embed_reply(":warning: Error")
				return
		response = await ctx.embed_reply(":cd: Loading..")
		embed = response.embeds[0]
		try:
			title = await self.players[ctx.guild.id].insert_song(song, ctx.author, ctx.message.created_at, position_number)
		except Exception as e:
			embed.description = ":warning: Error loading `{}`\n`{}: {}`".format(song, type(e).__name__, e)
			if len(embed.description) > ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT:
				embed.description = embed.description[:ctx.bot.EDCL - 4] + "...`"
				# EDCL: Embed Description Character Limit
		else:
			embed.description = ":ballot_box_with_check: `{}` has been inserted into position #{} in the queue".format(title, position_number)
		finally:
			await self.bot.edit_message(response, embed = embed)
			await self.bot.attempt_delete_message(ctx.message)
	
	@commands.command(aliases = ["clear"])
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def empty(self, ctx):
		'''Empty the queue'''
		await self.players[ctx.guild.id].empty_queue()
		await ctx.embed_reply(":wastebasket: Emptied queue")
	
	@commands.command()
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def shuffle(self, ctx):
		'''Shuffle the queue'''
		response = await ctx.embed_reply(":twisted_rightwards_arrows: Shuffling..")
		embed = response.embeds[0]
		await self.players[ctx.guild.id].shuffle_queue()
		embed.description = ":twisted_rightwards_arrows: Shuffled songs"
		await self.bot.edit_message(response, embed = embed)
		await self.bot.attempt_delete_message(ctx.message)
	
	@audio.command(name = "random", aliases = ["top"])
	@commands.guild_only()
	@checks.not_forbidden()
	@checks.is_voice_connected()
	async def audio_random(self, ctx):
		'''Play a random song from YouTube's top 50'''
		url = "https://www.googleapis.com/youtube/v3/videos?part=id&chart=mostPopular&maxResults=50&videoCategoryId=10&key={}".format(ctx.bot.GOOGLE_API_KEY)
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json()
		song = random.choice([video["id"] for video in data["items"]])
		response = await ctx.embed_reply(":cd: Loading..")
		embed = response.embeds[0]
		try:
			title, url = await self.players[ctx.guild.id].add_song(song, ctx.author, ctx.message.created_at)
		except Exception as e:
			embed.description = ":warning: Error loading `{}`\n`{}: {}`".format(song, type(e).__name__, e)
		else:
			embed.title = title
			embed.url = url
			embed.description = ":ballot_box_with_check: Successfully added `{}` to the queue".format(song)
		try:
			await self.bot.edit_message(response, embed = embed)
		except discord.HTTPException:
			embed.description = ":warning: Error loading `{}`".format(song)
			await self.bot.edit_message(response, embed = embed)
	
	@commands.group(invoke_without_command = True)
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def radio(self, ctx):
		'''
		Radio station based on the current song
		No input to turn on/off
		'''
		if self.players[ctx.guild.id].radio_flag:
			self.players[ctx.guild.id].radio_off()
			await ctx.embed_reply(":stop_sign: Turned radio off")
		elif (await self.players[ctx.guild.id].radio_on(ctx.author, ctx.message.created_at)) is False:
			await ctx.embed_reply(":warning: Something else is already playing\nPlease stop it first")
		await self.bot.attempt_delete_message(ctx.message)
	
	@radio.command(name = "on", aliases = ["start"])
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def radio_on(self, ctx):
		'''Turn radio on'''
		if self.players[ctx.guild.id].radio_flag:
			await ctx.embed_reply(":no_entry: Radio is already on")
		elif (await self.players[ctx.guild.id].radio_on(ctx.author, ctx.message.created_at)) is False:
			await ctx.embed_reply(":warning: Something else is already playing\nPlease stop it first", footer_text = "In response to: {}".format(ctx.message.content))
		await self.bot.attempt_delete_message(ctx.message)
	
	@radio.command(name = "off", aliases = ["stop"])
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def radio_off(self, ctx):
		'''Turn radio off'''
		if self.players[ctx.guild.id].radio_flag:
			self.players[ctx.guild.id].radio_off()
			await ctx.embed_reply(":stop_sign: Turned radio off")
		else:
			await ctx.embed_reply(":no_entry: Radio is already off")
	
	@commands.command(aliases = ["set_text"])
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def settext(self, ctx):
		'''Set text channel for messages'''
		self.players[ctx.guild.id].text_channel = ctx.channel
		await ctx.embed_reply(":writing_hand::skin-tone-2: Changed text channel")
	
	@commands.group(invoke_without_command = True)
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def tts(self, ctx, *, message : str):
		'''Text to speech'''
		if not (await self.players[ctx.guild.id].play_tts(message, ctx.author, timestamp = ctx.message.created_at)):
			await ctx.embed_reply(":warning: Something else is already playing\nPlease stop it first")
	
	@tts.command(name = "options")
	@commands.guild_only()
	@checks.not_forbidden()
	@checks.is_voice_connected()
	async def tts_options(self, ctx, amplitude: int, pitch: int, speed: int, word_gap: int, voice: str, *, message : str):
		'''
		Text to speech with options
		amplitude, pitch, speed, word_gap, voice
		defaults: 100, 50, 150, 0, en-us+f1 (input -1 for defaults)
		limits: 0-1000, 0-99, 80-9000, 0-1000, valid voice
		word_gap: length of pause between words, in units of 10 ms
		voice: see http://espeak.sourceforge.net/languages.html
		'''
		if amplitude == -1: amplitude = 100
		if pitch == -1: pitch = 50
		if speed == -1: speed = 150
		if word_gap == -1: word_gap = 0
		if voice == "-1": voice = "en-us+f1"
		if amplitude > 1000: amplitude = 1000
		if speed > 9000: speed = 9000
		if word_gap > 1000: word_gap = 1000
		if not (await self.players[ctx.guild.id].play_tts(message, ctx.author, timestamp = ctx.message.created_at, amplitude = amplitude, pitch = pitch, speed = speed, word_gap = word_gap, voice = voice)):
			await ctx.embed_reply(":warning: Something else is already playing\nPlease stop it first")
	
	@commands.command()
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def file(self, ctx, *, filename : str = ""):
		'''Play an audio file'''
		if not (await self.players[ctx.guild.id].play_file(filename, ctx.author, ctx.message.created_at)):
			await ctx.embed_reply(":warning: Something else is already playing\nPlease stop it first")
	
	@commands.command()
	@commands.guild_only()
	@checks.not_forbidden()
	@checks.is_voice_connected()
	async def files(self, ctx):
		'''List existing audio files'''
		await ctx.embed_reply(self.players[ctx.guild.id].list_files())
	
	@commands.group(invoke_without_command = True)
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def library(self, ctx):
		'''Start/stop playing songs from my library'''
		if self.players[ctx.guild.id].library_flag:
			self.players[ctx.guild.id].stop_library()
			await ctx.embed_reply(":stop_sign: Stopped playing songs from my library")
		elif not (await self.players[ctx.guild.id].play_library(ctx.author, ctx.message.created_at)):
			await ctx.embed_reply(":warning: Something else is already playing\nPlease stop it first", footer_text = "In response to: {}".format(ctx.message.content))
	
	@library.command(name = "play", aliases = ["start"])
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def library_play(self, ctx):
		'''Start playing songs from my library'''
		if self.players[ctx.guild.id].library_flag:
			await ctx.embed_reply(":no_entry: I'm already playing songs from my library")
		elif not (await self.players[ctx.guild.id].play_library(ctx.author, ctx.message.created_at)):
			await ctx.embed_reply(":warning: Something else is already playing\nPlease stop it first")
	
	@library.command(name = "stop")
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def library_stop(self, ctx):
		'''Stop playing songs from my library'''
		if self.players[ctx.guild.id].library_flag:
			self.players[ctx.guild.id].stop_library()
			await ctx.embed_reply(":stop_sign: Stopped playing songs from my library")
		else:
			await ctx.embed_reply(":no_entry: Not currently playing songs from my library", footer_text = "In response to: {}".format(ctx.message.content))
	
	@library.command(name = "song")
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def library_song(self, ctx, *, filename : str = ""):
		'''Play a song from my library'''
		if not (await self.players[ctx.guild.id].play_from_library(filename, ctx.author, ctx.message.created_at)):
			await ctx.embed_reply(":warning: Something else is already playing\nPlease stop it first")
	
	@library.command(name = "files")
	@commands.guild_only() # enable for DMs?
	@checks.not_forbidden()
	@checks.is_voice_connected()
	async def library_files(self, ctx):
		'''List song files in the library'''
		if not isinstance(ctx.channel, discord.DMChannel):
			await ctx.embed_reply("Check your DMs")
		output = "```"
		for filename in self.players[ctx.guild.id].library_files:
			if len(output) + len(filename) > 1997: # 2000 - 3
				await self.bot.whisper(output[:-2] + "```")
				output = "```" + filename + ", "
			else:
				output += filename + ", "
	
	@library.command(name = "search")
	@commands.guild_only()
	@checks.not_forbidden()
	@checks.is_voice_connected()
	async def library_search(self, ctx, *, search : str):
		'''Search songs in the library'''
		results = [filename for filename in self.players[ctx.guild.id].library_files if search.lower() in filename.lower()]
		if not results:
			await ctx.embed_reply(":no_entry: No songs matching that search found")
			return
		try:
			await ctx.embed_reply("```\n{}\n```".format(", ".join(results)))
		except discord.HTTPException:
			# TODO: use textwrap/paginate
			await ctx.embed_reply(":no_entry: Too many results\nTry a more specific search")
	
	@commands.group(invoke_without_command = True)
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def volume(self, ctx, *, volume_setting : float = None):
		'''
		Change the volume of the current song
		volume_setting: 0 - 2000
		'''
		if volume_setting is None:
			try:
				await ctx.embed_reply(":sound: Current volume: {:g}".format(self.players[ctx.guild.id].get_volume()))
			except errors.AudioNotPlaying:
				await ctx.embed_reply(":no_entry: There's nothing playing right now", footer_text = "In response to: {}".format(ctx.message.content))
		else:
			try:
				self.players[ctx.guild.id].set_volume(volume_setting)
			except errors.AudioNotPlaying:
				await ctx.embed_reply(":no_entry: Couldn't change volume\nThere's nothing playing right now", footer_text = "In response to: {}".format(ctx.message.content))
			else:
				if volume_setting > 2000: volume_setting = 2000
				elif volume_setting < 0: volume_setting = 0
				await ctx.embed_reply(":sound: Set volume to {:g}".format(volume_setting))
	
	@volume.command(name = "default")
	@commands.guild_only()
	@checks.is_permitted()
	@checks.is_voice_connected()
	async def volume_default(self, ctx, *, volume_setting : float = None):
		'''
		Change the default volume for the current player
		volume_setting: 0 - 2000
		'''
		if volume_setting is None:
			await ctx.embed_reply(":sound: Current default volume: {:g}".format(self.players[ctx.guild.id].default_volume))
		else:
			if volume_setting > 2000: volume_setting = 2000
			elif volume_setting < 0: volume_setting = 0
			self.players[ctx.guild.id].default_volume = volume_setting
			await ctx.embed_reply(":sound: Set default volume to {:g}".format(volume_setting))
	
	@commands.group(aliases = ["current"], invoke_without_command = True)
	@commands.guild_only()
	@checks.is_voice_connected()
	@checks.not_forbidden()
	async def playing(self, ctx):
		'''See the currently playing song'''
		try:
			embed = self.players[ctx.guild.id].current_embed()
		except errors.AudioNotPlaying:
			await ctx.embed_reply(":speaker: There is no song currently playing")
		else:
			embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url or ctx.author.default_avatar_url)
			await self.bot.say(embed = embed)
		await self.bot.attempt_delete_message(ctx.message)
	
	@commands.command()
	@commands.guild_only()
	@checks.is_voice_connected()
	@checks.not_forbidden()
	async def queue(self, ctx):
		'''See the current queue'''
		embed = self.players[ctx.guild.id].queue_embed()
		embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url)
		await ctx.send(embed = embed)
		await self.bot.attempt_delete_message(ctx.message)
	
	# Voice Input
	
	@commands.group(invoke_without_command = True, hidden = True)
	@checks.is_voice_connected()
	@checks.is_permitted()
	async def listen(self, ctx):
		if self.players[ctx.guild.id].listener:
			await self.players[ctx.guild.id].stop_listening()
		elif not (await self.players[ctx.guild.id].start_listening()):
			await ctx.embed_reply(":warning: Something else is already playing. Please stop it first.")
	
	@listen.command(name = "start", aliases = ["on"])
	@checks.is_voice_connected()
	@checks.is_permitted()
	async def listen_start(self, ctx):
		if self.players[ctx.guild.id].listener:
			await ctx.embed_reply(":no_entry: I'm already listening")
		elif not (await self.players[ctx.guild.id].start_listening()):
			await ctx.embed_reply(":warning: Something else is already playing. Please stop it first.")
	
	@listen.command(name = "stop", aliases = ["off"])
	@checks.is_voice_connected()
	@checks.is_permitted()
	async def listen_stop(self, ctx):
		if self.players[ctx.guild.id].listener:
			await self.players[ctx.guild.id].stop_listening()
		else:
			await ctx.embed_reply(":no_entry: I'm not listening")
	
	@listen.command(name = "once")
	@checks.is_voice_connected()
	@checks.is_permitted()
	async def listen_once(self, ctx):
		if self.players[ctx.guild.id].listener:
			await ctx.embed_reply(":no_entry: I'm already listening")
		elif (await self.players[ctx.guild.id].listen_once()) is False:
			await ctx.embed_reply(":warning: Something else is already playing. Please stop it first.")
	
	@listen.command(name = "finish")
	@checks.is_voice_connected()
	@checks.is_permitted()
	async def listen_finish(self, ctx):
		if self.players[ctx.guild.id].listener:
			await self.players[ctx.guild.id].finish_listening()
		else:
			await ctx.embed_reply(":no_entry: I'm not listening")
	
	@listen.command(name = "process")
	@checks.is_voice_connected()
	@checks.is_permitted()
	async def listen_process(self, ctx):
		await self.players[ctx.guild.id].process_listen()
	
	# Utility

	async def spotify_to_youtube(self, link):
		path = urllib.parse.urlparse(link).path
		if path[:7] != "/track/":
			return False
		url = "https://api.spotify.com/v1/tracks/{}".format(path[7:])
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json()
		if "name" not in data:
			return False
		songname = '+'.join(data["name"].split())
		artistname = '+'.join(data["artists"][0]["name"].split())
		url = "https://www.googleapis.com/youtube/v3/search?part=snippet&q={}+by+{}&key={}".format(songname, artistname, self.bot.GOOGLE_API_KEY)
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json()
		data = data["items"][0]
		if "videoId" not in data["id"]:
			async with clients.aiohttp_session.get(url) as resp:
				data = await resp.json()
			data = data["items"][1]
		link = "https://www.youtube.com/watch?v=" + data["id"]["videoId"]
		return link
	
	async def get_spotify_access_token(self):
		url = "https://accounts.spotify.com/api/token"
		params = {"grant_type": "client_credentials"}
		authorization = f"{self.bot.SPOTIFY_CLIENT_ID}:{self.bot.SPOTIFY_CLIENT_SECRET_KEY}"
		authorization = base64.b64encode(authorization.encode()).decode()
		headers = {"Authorization": f"Basic {authorization}", 
					"Content-Type": "application/x-www-form-urlencoded"}
		async with clients.aiohttp_session.post(url, params = params, headers = headers) as resp:
			data = await resp.json()
		return data["access_token"]
	
	# Termination
	
	def cancel_all_tasks(self):
		for player in self.players.values():
			player.player.cancel()
	
	def save_voice_channels(self):
		return [[voice_client.channel.id, self.players[voice_client.guild.id].text_channel.id] for voice_client in self.bot.voice_clients]

