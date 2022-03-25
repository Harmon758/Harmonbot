
import discord
from discord.ext import commands

import base64
import concurrent.futures
import inspect
import random
import sys
from typing import Optional
import urllib

from modules import utilities
from utilities.audio_player import AudioPlayer
from utilities import audio_sources
from utilities import checks
from utilities import errors

sys.path.insert(0, "..")
from units.files import create_folder
sys.path.pop(0)

async def setup(bot):
	await bot.add_cog(Audio(bot))

class Audio(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.players = {}
		for name, command in inspect.getmembers(self):
			if isinstance(command, commands.Command) and command.parent is None and name != "audio":
				self.bot.add_command(command)
				self.audio.add_command(command)
		create_folder(self.bot.data_path + "/audio_cache")
		create_folder(self.bot.data_path + "/audio_files")
	
	def cog_unload(self):
		# TODO: Leave voice channels?
		for player in self.players.values():
			player.player.cancel()
	
	async def cog_check(self, ctx):
		return await commands.guild_only().predicate(ctx)
	
	@commands.group(aliases = ["yt", "youtube", "soundcloud", "voice", "stream", "play", 
								"playlist", "spotify", "budio", "music", "download"], 
					description = "Supports [these sites](https://rg3.github.io/youtube-dl/supportedsites.html) and Spotify", 
					invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def audio(self, ctx, *, song: Optional[str]):  #elif options[0] == "full":
		'''
		Audio System - play a song
		All audio subcommands are also commands
		For cleanup of audio commands, the Manage Messages permission is required
		'''
		if song and song.lower().startswith("info "):
			if ctx.invoked_with.lower() == "spotify":
				return await ctx.invoke(self.bot.cogs["Info"].spotify, song.lstrip(song.split()[0]).lstrip())
			elif ctx.invoked_with.lower() in ("yt", "youtube"):
				return await ctx.invoke(self.bot.cogs["Info"].youtube, song.lstrip(song.split()[0]).lstrip())
		if not ctx.guild.voice_client:
			if ctx.guild.id not in self.players:
				self.players[ctx.guild.id] = AudioPlayer.from_context(ctx)
			try:
				is_guild_owner = await checks.is_guild_owner().predicate(ctx)
			except errors.NotGuildOwner:
				is_guild_owner = False
			if is_guild_owner or await ctx.get_permission("join", user = ctx.author):
				if ctx.author.voice and ctx.author.voice.channel:
					await ctx.author.voice.channel.connect()
					await ctx.embed_reply(":headphones: I've joined the voice channel")
				else:
					raise errors.PermittedVoiceNotConnected
			else:
				raise errors.NotPermittedVoiceNotConnected
		if not song:
			return await ctx.embed_reply(":grey_question: What would you like to play?")
		if "playlist" in song:
			return await self.players[ctx.guild.id].add_playlist(ctx, song)
		if "spotify" in song:
			if not (song := await self.spotify_to_youtube(song)):
				return await ctx.embed_reply(":warning: Error")
		response = await ctx.embed_reply(":cd: Loading..")
		# TODO: Handle no embed permission
		embed = response.embeds[0]
		try:
			source = await self.players[ctx.guild.id].add_song(ctx, song, stream = ctx.invoked_with == "stream")
		except Exception as e:
			embed.description = f":warning: Error loading `{song}`\n`{type(e).__name__}: {e}`"
			if len(embed.description) > ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT:
				embed.description = embed.description[:ctx.bot.EDCL - 4] + "...`"
				# EDCL: Embed Description Character Limit
		else:
			if source.info["webpage_url"] != "ytsearch:" + song:
				embed.title = source.info["title"]
				embed.url = source.info["webpage_url"]
				embed.description = f":ballot_box_with_check: Successfully added `{song}` to the queue"
			else:
				embed.description = f"{ctx.bot.error_emoji} Video not found"
		finally:
			await response.edit(embed = embed)
	
	@commands.command(aliases = ["summon", "move"])
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def join(self, ctx, *, channel: Optional[discord.VoiceChannel]):
		'''Get me to join a voice channel'''
		# TODO: Permit all when not in voice channel?
		if ctx.guild.id not in self.players:
			self.players[ctx.guild.id] = AudioPlayer.from_context(ctx)
		if not channel and (not ctx.author.voice or not (channel := ctx.author.voice.channel)):
			return await ctx.embed_reply(":no_entry: Voice channel not found")
		try:
			if ctx.guild.voice_client:
				await ctx.guild.voice_client.move_to(channel)
				await ctx.embed_reply(":arrow_right_hook: I've moved to the voice channel")
			else:
				await channel.connect()
				await ctx.embed_reply(":headphones: I've joined the voice channel")
		except concurrent.futures.TimeoutError:
			await ctx.embed_reply(":no_entry: Error joining the voice channel\n"
									"Please check that I'm permitted to join")
	
	@commands.command()
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def leave(self, ctx):
		'''Tell me to leave the voice channel'''
		if (await self.players[ctx.guild.id].leave_channel()):
			await ctx.embed_reply(":door: I've left the voice channel")
		del self.players[ctx.guild.id]
		await self.bot.attempt_delete_message(ctx.message)
	
	@commands.command(aliases = ["stop"])
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def pause(self, ctx):
		'''Pause the current song'''
		if ctx.guild.voice_client.is_playing():
			ctx.guild.voice_client.pause()
			await ctx.embed_reply(":pause_button: Paused song")
		elif ctx.guild.voice_client.is_paused():
			await ctx.embed_reply(":no_entry: The song is already paused")
		else:
			await ctx.embed_reply(":no_entry: There is no song to pause")
	
	@commands.command(aliases = ["start"])
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def resume(self, ctx):
		'''Resume the current song'''
		if ctx.guild.voice_client.is_paused():
			ctx.guild.voice_client.source.previous_played_time += ctx.guild.voice_client._player.DELAY * ctx.guild.voice_client._player.loops
			ctx.guild.voice_client.resume()
			await ctx.embed_reply(":play_pause: Resumed song")
		elif ctx.guild.voice_client.is_playing():
			await ctx.embed_reply(":no_entry: The song is already playing")
		else:
			await ctx.embed_reply(":no_entry: There is no song to resume")
	
	@commands.group(aliases = ["next", "remove"], invoke_without_command = True, case_insensitive = True)
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
		try:
			await commands.check_any(checks.is_permitted(), checks.is_guild_owner()).predicate(ctx)
		except commands.CheckAnyFailure:
			if ctx.author in ctx.guild.voice_client.channel.members or ctx.author.id in ctx.guild.voice_client.channel.voice_states:
				if not ctx.guild.voice_client.is_playing() and not ctx.guild.voice_client.is_paused():
					await ctx.embed_reply(":no_entry: There is no song to skip")
				elif ctx.author.id in player.skip_votes:
					await ctx.embed_reply(":no_entry: You've already voted to skip. Skips: {}/{}".format(len(player.skip_votes), player.skip_votes_required))
				else:
					vote = player.vote_skip(ctx.author)
					await ctx.embed_reply(":white_check_mark: You voted to skip the current song\n{}".format("Skips: {}/{}".format(vote, player.skip_votes_required) if vote else ":next_track: Song skipped"))
			else:
				await ctx.embed_reply(":no_entry: You're not even listening!")
		else:
			if number:
				try:
					song = await player.skip_specific(number)
				except errors.AudioError as e:
					await ctx.embed_reply(":no_entry: {}".format(e))
				else:
					await ctx.embed_reply(":put_litter_in_its_place: Skipped #{} in the queue: `{}`".format(number, song.info["title"]))
					del song
			else:
				if self.players[ctx.guild.id].skip():
					await ctx.embed_reply(":next_track: Song skipped")
					# TODO: Include title of skipped song
				else:
					await ctx.embed_reply(":no_entry: There is no song to skip")
	
	@skip.command(name = "to")
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def skip_to(self, ctx, number : int):
		'''
		Skip to a song in the queue
		Skips every song before number
		'''
		try:
			songs = await self.players[ctx.guild.id].skip_to_song(number)
		except errors.AudioError as e:
			await ctx.embed_reply(":no_entry: {}".format(e))
		else:
			await ctx.embed_reply(":put_litter_in_its_place: Skipped to #{} in the queue".format(number))
			del songs
	
	@commands.command(aliases = ["repeat"])
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def replay(self, ctx):
		'''Repeat the current song'''
		# TODO: Add restart alias?
		response = await ctx.embed_reply(":repeat_one: Restarting song..")
		embed = response.embeds[0]
		try:
			await self.players[ctx.guild.id].replay()
		except errors.AudioError as e:
			embed.description = ":no_entry: {}".format(e)
		else:
			embed.description = ":repeat_one: Restarted song"
		finally:
			await response.edit(embed = embed)
	
	@commands.command()
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
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
			source = await self.players[ctx.guild.id].insert_song(ctx, song, position_number)
		except Exception as e:
			embed.description = ":warning: Error loading `{}`\n`{}: {}`".format(song, type(e).__name__, e)
			if len(embed.description) > ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT:
				embed.description = embed.description[:ctx.bot.EDCL - 4] + "...`"
				# EDCL: Embed Description Character Limit
		else:
			embed.description = ":ballot_box_with_check: `{}` has been inserted into position #{} in the queue".format(source.title, position_number)
		finally:
			await response.edit(embed = embed)
	
	@commands.command(aliases = ["clear"])
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def empty(self, ctx):
		'''Empty the queue'''
		await self.players[ctx.guild.id].empty_queue()
		await ctx.embed_reply(":wastebasket: Emptied queue")
	
	@commands.command()
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def shuffle(self, ctx):
		'''Shuffle the queue'''
		response = await ctx.embed_reply(":twisted_rightwards_arrows: Shuffling..")
		embed = response.embeds[0]
		await self.players[ctx.guild.id].shuffle_queue()
		embed.description = ":twisted_rightwards_arrows: Shuffled songs"
		await response.edit(embed = embed)
	
	@audio.command(name = "random", aliases = ["top"])
	@checks.not_forbidden()
	@checks.is_voice_connected()
	async def audio_random(self, ctx):
		'''Play a random song from YouTube's top 50'''
		url = "https://www.googleapis.com/youtube/v3/videos?part=id&chart=mostPopular&maxResults=50&videoCategoryId=10&key={}".format(ctx.bot.GOOGLE_API_KEY)
		async with ctx.bot.aiohttp_session.get(url) as resp:
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
			await response.edit(embed = embed)
		except discord.HTTPException:  # Necessary?
			embed.description = ":warning: Error loading `{}`".format(song)
			await response.edit(embed = embed)
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def radio(self, ctx):
		'''
		Radio station based on the current song
		No input to turn on/off
		'''
		if self.players[ctx.guild.id].radio_flag:
			self.players[ctx.guild.id].radio_off()
			await ctx.embed_reply(":stop_sign: Turned radio off")
		elif (await self.players[ctx.guild.id].radio_on(ctx)) is False:
			await ctx.embed_reply(":warning: Something else is already playing\nPlease stop it first")
	
	@radio.command(name = "on", aliases = ["start"])
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def radio_on(self, ctx):
		'''Turn radio on'''
		if self.players[ctx.guild.id].radio_flag:
			await ctx.embed_reply(":no_entry: Radio is already on")
		elif (await self.players[ctx.guild.id].radio_on(ctx)) is False:
			await ctx.embed_reply(":warning: Something else is already playing\nPlease stop it first")
	
	@radio.command(name = "off", aliases = ["stop"])
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def radio_off(self, ctx):
		'''Turn radio off'''
		if self.players[ctx.guild.id].radio_flag:
			self.players[ctx.guild.id].radio_off()
			await ctx.embed_reply(":stop_sign: Turned radio off")
		else:
			await ctx.embed_reply(":no_entry: Radio is already off")
	
	@commands.command(aliases = ["set_text"])
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def settext(self, ctx):
		'''Set text channel for messages'''
		self.players[ctx.guild.id].text_channel = ctx.channel
		await ctx.embed_reply(f":writing_hand:{ctx.bot.emoji_skin_tone} Changed text channel")
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def tts(self, ctx, *, message : str):
		'''Text to speech'''
		if not (await self.players[ctx.guild.id].play_tts(ctx, message)):
			await ctx.embed_reply(":warning: Something else is already playing\nPlease stop it first")
	
	@tts.command(name = "options")
	@checks.not_forbidden()
	@checks.is_voice_connected()
	async def tts_options(self, ctx, amplitude: int, pitch: int, speed: int, word_gap: int, voice: str, *, message : str):
		'''
		Text to speech with options
		amplitude, pitch, speed, word_gap, voice
		defaults: 100, 50, 150, 0, en-us+f1 (input -1 for defaults)
		limits: 0-1000, 0-99, 80-9000, 0-1000, valid voice
		word_gap: length of pause between words, in units of 10 ms
		voice:
		http://espeak.sourceforge.net/languages.html
		https://github.com/espeak-ng/espeak-ng/blob/master/docs/languages.md#languages
		https://github.com/espeak-ng/espeak-ng/tree/master/espeak-ng-data/voices/!v
		'''
		if amplitude == -1: amplitude = 100
		if pitch == -1: pitch = 50
		if speed == -1: speed = 150
		if word_gap == -1: word_gap = 0
		if voice == "-1": voice = "en-us+f1"
		if amplitude > 1000: amplitude = 1000
		if speed > 9000: speed = 9000
		if word_gap > 1000: word_gap = 1000
		if not (await self.players[ctx.guild.id].play_tts(ctx, message, amplitude = amplitude, pitch = pitch, speed = speed, word_gap = word_gap, voice = voice)):
			await ctx.embed_reply(":warning: Something else is already playing\nPlease stop it first")
	
	@commands.command()
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def file(self, ctx, *, filename : str = ""):
		'''Play an audio file'''
		if not (await self.players[ctx.guild.id].play_file(ctx, filename)):
			await ctx.embed_reply(":warning: Something else is already playing\nPlease stop it first")
	
	@commands.command()
	@checks.not_forbidden()
	@checks.is_voice_connected()
	async def files(self, ctx):
		'''List existing audio files'''
		await ctx.embed_reply(self.players[ctx.guild.id].list_files())
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def library(self, ctx):
		'''Start/stop playing songs from my library'''
		if self.players[ctx.guild.id].library_flag:
			self.players[ctx.guild.id].stop_library()
			await ctx.embed_reply(":stop_sign: Stopped playing songs from my library")
		elif not (await self.players[ctx.guild.id].play_library(ctx)):
			await ctx.embed_reply(":warning: Something else is already playing\nPlease stop it first")
	
	@library.command(name = "play", aliases = ["start"])
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def library_play(self, ctx):
		'''Start playing songs from my library'''
		if self.players[ctx.guild.id].library_flag:
			await ctx.embed_reply(":no_entry: I'm already playing songs from my library")
		elif not (await self.players[ctx.guild.id].play_library(ctx)):
			await ctx.embed_reply(":warning: Something else is already playing\nPlease stop it first")
	
	@library.command(name = "stop")
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def library_stop(self, ctx):
		'''Stop playing songs from my library'''
		if self.players[ctx.guild.id].library_flag:
			self.players[ctx.guild.id].stop_library()
			await ctx.embed_reply(":stop_sign: Stopped playing songs from my library")
		else:
			await ctx.embed_reply(":no_entry: Not currently playing songs from my library")
	
	@library.command(name = "song")
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def library_song(self, ctx, *, filename : str = ""):
		'''Play a song from my library'''
		if not (await self.players[ctx.guild.id].play_from_library(ctx, filename = filename)):
			await ctx.embed_reply(":warning: Something else is already playing\nPlease stop it first")
	
	@library.command(name = "files")  # enable for DMs?
	@checks.not_forbidden()
	@checks.is_voice_connected()  # don't require
	async def library_files(self, ctx):
		'''List song files in the library'''
		# TODO: Better pagination method
		if ctx.channel.type is not discord.ChannelType.private:
			await ctx.embed_reply("Check your DMs")
		output = "```"
		for filename in self.players[ctx.guild.id].library_files:
			if len(output) + len(filename) > 1997:  # 2000 - 3
				await ctx.whisper(output[:-2] + "```")
				output = "```" + filename + ", "
			else:
				output += filename + ", "
	
	@library.command(name = "search")
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
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def volume(self, ctx, *, volume_setting : float = None):
		'''
		Change the volume of the current song
		volume_setting: 0 - 2000
		'''
		if volume_setting is None:
			if ctx.guild.voice_client.is_playing():
				await ctx.embed_reply(":sound: Current volume: {:g}".format(ctx.guild.voice_client.source.volume))
			else:
				await ctx.embed_reply(":no_entry: There's nothing playing right now")
		else:
			if ctx.guild.voice_client.is_playing():
				ctx.guild.voice_client.source.volume = volume_setting
				volume_setting = min(max(0, volume_setting), 2000)
				await ctx.embed_reply(":sound: Set volume to {:g}".format(volume_setting))
			else:
				await ctx.embed_reply(":no_entry: Couldn't change volume\nThere's nothing playing right now")
	
	@volume.command(name = "default")
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def volume_default(self, ctx, *, volume_setting : float = None):
		'''
		Change the default volume for the current player
		volume_setting: 0 - 2000
		'''
		if volume_setting is None:
			await ctx.embed_reply(":sound: Current default volume: {:g}".format(self.players[ctx.guild.id].default_volume))
		else:
			volume_setting = min(max(0, volume_setting), 2000)
			self.players[ctx.guild.id].default_volume = volume_setting
			await ctx.embed_reply(":sound: Set default volume to {:g}".format(volume_setting))
	
	@commands.group(aliases = ["current"], invoke_without_command = True, case_insensitive = True)
	@checks.is_voice_connected()
	@checks.not_forbidden()
	async def playing(self, ctx):
		'''See the currently playing song'''
		if ctx.guild.voice_client.is_playing():
			requester = ctx.guild.voice_client.source.requester
			# Description
			if self.players[ctx.guild.id].radio_flag:
				description = ":radio: Radio is currently playing"
			elif self.players[ctx.guild.id].library_flag:
				description = ":notes: Playing song from my library"
			elif isinstance(ctx.guild.voice_client.source, audio_sources.FileSource):
				description = ":floppy_disk: Playing audio file"
			elif isinstance(ctx.guild.voice_client.source, audio_sources.TTSSource):
				description = ":speaking_head: Playing TTS Message"
			else:
				description = ":musical_note: Currently playing"
				played_duration = ctx.guild.voice_client.source.previous_played_time + ctx.guild.voice_client._player.DELAY * ctx.guild.voice_client._player.loops
				total_duration = ctx.guild.voice_client.source.info.get("duration")
				if total_duration:
					playing_bar = "▬" * 10
					button_spot = int(played_duration / (total_duration / 10))
					playing_bar = playing_bar[:button_spot] + ":radio_button: " + playing_bar[button_spot + 1:]
					played_duration = utilities.secs_to_colon_format(played_duration)
					total_duration = utilities.secs_to_colon_format(total_duration)
					description = ":arrow_forward: {}`[{}/{}]`".format(playing_bar, played_duration, total_duration)  # Add :sound:?
				views = ctx.guild.voice_client.source.info.get("view_count")
				likes = ctx.guild.voice_client.source.info.get("like_count")
				dislikes = ctx.guild.voice_client.source.info.get("dislike_count")
				description += '\n' if views or likes or dislikes else ""
				description += f"{views:,} :eye:" if views else ""
				description += " | " if views and (likes or dislikes) else ""
				description += f"{likes:,} :thumbsup::skin-tone-2:" if likes else ""
				description += " | " if likes and dislikes else ""
				description += f"{dislikes:,} :thumbsdown::skin-tone-2:" if dislikes else ""
			if hasattr(ctx.guild.voice_client.source, "info"):
				title = ctx.guild.voice_client.source.info.get("title")
				title_url = ctx.guild.voice_client.source.info.get("webpage_url")
			else:
				title = ctx.guild.voice_client.source.title
				title_url = discord.Embed.Empty
			return await ctx.embed_reply(description, title = title, title_url = title_url, footer_text = "Added by " + requester.display_name, footer_icon_url = requester.display_avatar.url, timestamp = ctx.guild.voice_client.source.timestamp)
		else:
			return await ctx.embed_reply(":speaker: There is no song currently playing")
	
	@commands.command()
	@checks.is_voice_connected()
	@checks.not_forbidden()
	async def queue(self, ctx):
		'''See the current queue'''
		embed = self.players[ctx.guild.id].queue_embed()
		embed.set_author(
			name = ctx.author.display_name,
			icon_url = ctx.author.display_avatar.url
		)
		await ctx.send(embed = embed)
		await self.bot.attempt_delete_message(ctx.message)
	
	# Meta

	@audio.group(invoke_without_command = True, case_insensitive = True)
	@checks.is_voice_connected()
	@checks.not_forbidden()
	async def latency(self, ctx):
		'''Latency between a HEARTBEAT and its HEARTBEAT_ACK in seconds'''
		await ctx.embed_reply(f"{ctx.guild.voice_client.latency}s")
	
	@latency.command()
	@checks.is_voice_connected()
	@checks.not_forbidden()
	async def average(self, ctx):
		'''Average of last 20 HEARTBEAT latencies'''
		await ctx.embed_reply(f"{ctx.guild.voice_client.average_latency}s")
	
	# Discord Control

	@commands.command()
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def deafen(self, ctx):
		'''Deafen'''
		if ctx.guild.me.voice.self_deaf:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} I'm already deafened")
		await ctx.guild.change_voice_state(channel = ctx.guild.voice_client.channel, self_deaf = True, self_mute = ctx.guild.me.voice.self_mute)
		await ctx.embed_reply("I've deafened myself")
	
	@commands.command()
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def mute(self, ctx):
		'''Mute'''
		if ctx.guild.me.voice.self_mute:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} I'm already muted")
		await ctx.guild.change_voice_state(channel = ctx.guild.voice_client.channel, self_mute = True, self_deaf = ctx.guild.me.voice.self_deaf)
		await ctx.embed_reply("I've muted myself")
	
	@commands.command()
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def undeafen(self, ctx):
		'''Undeafen'''
		if not ctx.guild.me.voice.self_deaf:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} I'm not deafened")
		await ctx.guild.change_voice_state(channel = ctx.guild.voice_client.channel, self_deaf = False, self_mute = ctx.guild.me.voice.self_mute)
		await ctx.embed_reply("I've undeafened myself")
	
	@commands.command()
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def unmute(self, ctx):
		'''Unmute'''
		if not ctx.guild.me.voice.self_mute:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} I'm not muted")
		await ctx.guild.change_voice_state(channel = ctx.guild.voice_client.channel, self_mute = False, self_deaf = ctx.guild.me.voice.self_deaf)
		await ctx.embed_reply("I've unmuted myself")
	
	# Voice Input
	
	@commands.group(invoke_without_command = True, case_insensitive = True, hidden = True)
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def listen(self, ctx):
		if self.players[ctx.guild.id].listener:
			await self.players[ctx.guild.id].stop_listening()
		elif not (await self.players[ctx.guild.id].start_listening()):
			await ctx.embed_reply(":warning: Something else is already playing. Please stop it first.")
	
	@listen.command(name = "start", aliases = ["on"])
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def listen_start(self, ctx):
		if self.players[ctx.guild.id].listener:
			await ctx.embed_reply(":no_entry: I'm already listening")
		elif not (await self.players[ctx.guild.id].start_listening()):
			await ctx.embed_reply(":warning: Something else is already playing. Please stop it first.")
	
	@listen.command(name = "stop", aliases = ["off"])
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def listen_stop(self, ctx):
		if self.players[ctx.guild.id].listener:
			await self.players[ctx.guild.id].stop_listening()
		else:
			await ctx.embed_reply(":no_entry: I'm not listening")
	
	@listen.command(name = "once")
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def listen_once(self, ctx):
		if self.players[ctx.guild.id].listener:
			await ctx.embed_reply(":no_entry: I'm already listening")
		elif (await self.players[ctx.guild.id].listen_once()) is False:
			await ctx.embed_reply(":warning: Something else is already playing. Please stop it first.")
	
	@listen.command(name = "finish")
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def listen_finish(self, ctx):
		if self.players[ctx.guild.id].listener:
			await self.players[ctx.guild.id].finish_listening()
		else:
			await ctx.embed_reply(":no_entry: I'm not listening")
	
	@listen.command(name = "process")
	@checks.is_voice_connected()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def listen_process(self, ctx):
		await self.players[ctx.guild.id].process_listen()
	
	# Utility

	async def spotify_to_youtube(self, link):
		path = urllib.parse.urlparse(link).path
		if path[:7] != "/track/":
			return False
		spotify_access_token = await self.get_spotify_access_token()
		url = f"https://api.spotify.com/v1/tracks/{path[7:]}"
		headers = {"Authorization": f"Bearer {spotify_access_token}"}
		async with self.bot.aiohttp_session.get(url, headers = headers) as resp:
			data = await resp.json()
		if "name" not in data:
			return False
		url = "https://www.googleapis.com/youtube/v3/search"
		params = {"part": "snippet", "key": self.bot.GOOGLE_API_KEY, 
					'q': f"{data['artists'][0]['name']} - {data['name']}"}
		async with self.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		for item in data["items"]:
			if "videoId" in item["id"]:
				return "https://www.youtube.com/watch?v=" + item["id"]["videoId"]
	
	async def get_spotify_access_token(self):
		url = "https://accounts.spotify.com/api/token"
		params = {"grant_type": "client_credentials"}
		authorization = f"{self.bot.SPOTIFY_CLIENT_ID}:{self.bot.SPOTIFY_CLIENT_SECRET_KEY}"
		authorization = base64.b64encode(authorization.encode()).decode()
		headers = {"Authorization": f"Basic {authorization}", 
					"Content-Type": "application/x-www-form-urlencoded"}
		async with self.bot.aiohttp_session.post(url, params = params, headers = headers) as resp:
			data = await resp.json()
		return data["access_token"]

