
import discord
from discord.ext import commands

import base64
import concurrent.futures
import random
from typing import Optional
import urllib

from modules import utilities
from units.files import create_folder
from utilities.audio_player import AudioPlayer
from utilities import audio_sources, checks, errors, parameters


async def setup(bot):
    await bot.add_cog(Audio(bot))

class Audio(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.players = {}

        # TODO: Add back as audio subcommands:
        # library, library subcommands
        # listen, listen subcommands
        # playing?
        # radio
        # skip, merge skip subcommand?

        create_folder(self.bot.data_path + "/audio_cache")
        create_folder(self.bot.data_path + "/audio_files")

    def cog_unload(self):
        # TODO: Leave voice channels?
        for player in self.players.values():
            player.player.cancel()

    async def cog_check(self, ctx):
        return await commands.guild_only().predicate(ctx)

    @commands.hybrid_group(
        aliases = [
            "soundcloud", "voice", "stream", "play", "playlist", "budio",
            "music", "download"
        ],
        case_insensitive = True,
        fallback = "play"
    )
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def audio(self, ctx, *, query: str):
        '''
        Play audio

        All audio subcommands are also commands
        For cleanup of audio commands, the Manage Messages permission is required

        Supported sites:
        https://ytdl-org.github.io/youtube-dl/supportedsites.html
        Spotify

        Parameters
        ----------
        query
            Audio to play
        '''
        # Note: spotify command invokes this command
        # Note: youtube command invokes this command
        if not ctx.guild.voice_client:
            if command := ctx.bot.get_command("audio join"):
                joined = await ctx.invoke(
                    command, channel = parameters.default_voice_channel(ctx)
                )
                if not joined:
                    return
            else:
                raise RuntimeError(
                    "audo join command not found when audio command invoked"
                )
        if "playlist" in query:
            await self.players[ctx.guild.id].add_playlist(ctx, query)
            return
        if "spotify" in query:
            if not (query := await self.spotify_to_youtube(query)):
                await ctx.embed_reply(":warning: Error")
                return
        response = await ctx.embed_reply(":cd: Loading..")
        # TODO: Handle no embed permission
        embed = response.embeds[0]
        try:
            source = await self.players[ctx.guild.id].add_song(
                ctx, query, stream = ctx.invoked_with == "stream"
            )
        except Exception as e:
            embed.description = f":warning: Error loading `{query}`\n`{type(e).__name__}: {e}`"
            if len(embed.description) > ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT:
                embed.description = embed.description[:ctx.bot.EDCL - 4] + "...`"
                # EDCL: Embed Description Character Limit
        else:
            if source.info["webpage_url"] != "ytsearch:" + query:
                embed.title = source.info["title"]
                embed.url = source.info["webpage_url"]
                embed.description = f":ballot_box_with_check: Successfully added `{query}` to the queue"
            else:
                embed.description = f"{ctx.bot.error_emoji} Video not found"
        finally:
            await response.edit(embed = embed)

    @commands.group(case_insensitive = True, invoke_without_command = True)
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def spotify(self, ctx, *, query: str):
        '''
        Play audio

        All audio subcommands are also commands
        For cleanup of audio commands, the Manage Messages permission is required

        Supported sites:
        https://ytdl-org.github.io/youtube-dl/supportedsites.html
        Spotify

        Parameters
        ----------
        query
            Audio to play
        '''
        if command := ctx.bot.get_command("audio"):
            await ctx.invoke(command, query = query)
        else:
            raise RuntimeError(
                "audio command not found when spotify command invoked"
            )

    @spotify.command(name = "information", aliases = ["info"])
    @checks.not_forbidden()
    async def spotify_information(self, ctx, url: str):
        '''Information about a Spotify track'''
        if command := ctx.bot.get_command("information spotify"):
            await ctx.invoke(command, url = url)
        else:
            raise RuntimeError(
                "information spotify command not found "
                "when spotify information command invoked"
            )

    @commands.hybrid_group(
        aliases = ["yt"], case_insensitive = True, with_app_command = False
    )
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def youtube(self, ctx, *, query: str):
        '''
        Play audio

        All audio subcommands are also commands
        For cleanup of audio commands, the Manage Messages permission is required

        Supported sites:
        https://ytdl-org.github.io/youtube-dl/supportedsites.html
        Spotify

        Parameters
        ----------
        query
            Audio to play
        '''
        if command := ctx.bot.get_command("audio"):
            await ctx.invoke(command, query = query)
        else:
            raise RuntimeError(
                "audio command not found when youtube command invoked"
            )

    @youtube.command(
        name = "information", aliases = ["info"], with_app_command = False
    )
    @checks.not_forbidden()
    async def youtube_information(self, ctx, url: str):
        """
        Show information about a YouTube video
        
        Parameters
        ----------
        url
            YouTube video URL
        """
        if command := ctx.bot.get_command("information youtube"):
            await ctx.invoke(command, url = url)
        else:
            raise RuntimeError(
                "information youtube command not found "
                "when youtube information command invoked"
            )

    @youtube.command(name = "search", with_app_command = False)
    @checks.not_forbidden()
    async def youtube_search(self, ctx, *, search):
        '''Search for a YouTube video'''
        if command := ctx.bot.get_command("search youtube"):
            await ctx.invoke(command, search = search)
        else:
            raise RuntimeError(
                "search youtube command not found "
                "when youtube search command invoked"
            )

    # TODO: Other audio search commands?

    @audio.command(name = "join", aliases = ["summon", "move"])
    @commands.check_any(
        checks.is_permitted(),
        commands.has_guild_permissions(move_members = True)
        # TODO: Check channel-specific permission?
    )
    async def audio_join(
        self, ctx, *,
        channel: Optional[  # noqa: UP007 (non-pep604-annotation)
            discord.VoiceChannel
        ] = parameters.CurrentVoiceChannel
    ):
        '''
        Have me join a voice channel

        Parameters
        ----------
        channel
            Voice channel for me to join
            (Defaults to the/your current channel)
        '''
        # Note: audio command invokes this command
        # Note: join command invokes this command
        # TODO: Permit all when not in voice channel?
        if ctx.guild.id not in self.players:
            self.players[ctx.guild.id] = AudioPlayer.from_context(ctx)
        if not channel:
            await ctx.embed_reply(":no_entry: Voice channel not found")
            return False
        try:
            if ctx.guild.voice_client:
                await ctx.guild.voice_client.move_to(channel)
                await ctx.embed_reply(
                    ":arrow_right_hook: I've moved to the voice channel"
                )
            else:
                await channel.connect()
                await ctx.embed_reply(
                    ":headphones: I've joined the voice channel"
                )
            return True
        except concurrent.futures.TimeoutError:
            await ctx.embed_reply(
                ":no_entry: Error joining the voice channel\n"
                "Please check that I'm permitted to join"
            )
            return False

    @commands.command(aliases = ["summon", "move"])
    @commands.check_any(
        checks.is_permitted(),
        commands.has_guild_permissions(move_members = True)
    )
    async def join(
        self, ctx, *,
        channel: Optional[  # noqa: UP007 (non-pep604-annotation)
            discord.VoiceChannel
        ] = parameters.CurrentVoiceChannel
    ):
        '''
        Have me join a voice channel

        Parameters
        ----------
        channel
            Voice channel for me to join
            (Defaults to the/your current channel)
        '''
        if command := ctx.bot.get_command("audio join"):
            await ctx.invoke(command, channel = channel)
        else:
            raise RuntimeError(
                "audio join command not found when join command invoked"
            )

    @audio.command(name = "leave")
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(),
        commands.has_guild_permissions(move_members = True)
        # TODO: Check channel-specific permission?
    )
    async def audio_leave(self, ctx):
        '''Have me leave the voice channel'''
        # Note: leave command invokes this command
        if (await self.players[ctx.guild.id].leave_channel()):
            await ctx.embed_reply(":door: I've left the voice channel")
        del self.players[ctx.guild.id]
        await self.bot.attempt_delete_message(ctx.message)

    @commands.command()
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(),
        commands.has_guild_permissions(move_members = True)
    )
    async def leave(self, ctx):
        '''Have me leave the voice channel'''
        if command := ctx.bot.get_command("audio leave"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "audio leave command not found when leave command invoked"
            )

    @audio.command(name = "pause", aliases = ["stop"])
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def audio_pause(self, ctx):
        '''Pause the current song'''
        # Note: pause command invokes this command
        if ctx.guild.voice_client.is_playing():
            ctx.guild.voice_client.pause()
            await ctx.embed_reply(":pause_button: Paused song")
        elif ctx.guild.voice_client.is_paused():
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} The song is already paused"
            )
        else:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} There is no song to pause"
            )

    @commands.command(aliases = ["stop"])
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def pause(self, ctx):
        '''Pause the current song'''
        if command := ctx.bot.get_command("audio pause"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "audio pause command not found when pause command invoked"
            )

    @audio.command(name = "resume", aliases = ["start"])
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def audio_resume(self, ctx):
        '''Resume the current song'''
        # Note: resume command invokes this command
        if ctx.guild.voice_client.is_paused():
            ctx.guild.voice_client.source.previous_played_time += ctx.guild.voice_client._player.DELAY * ctx.guild.voice_client._player.loops
            ctx.guild.voice_client.resume()
            await ctx.embed_reply(":play_pause: Resumed song")
        elif ctx.guild.voice_client.is_playing():
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} The song is already playing"
            )
        else:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} There is no song to resume"
            )

    @commands.command(aliases = ["start"])
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def resume(self, ctx):
        '''Resume the current song'''
        if command := ctx.bot.get_command("audio resume"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "audio resume command not found when resume command invoked"
            )

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
                    await ctx.embed_reply(f":no_entry: You've already voted to skip. Skips: {len(player.skip_votes)}/{player.skip_votes_required}")
                else:
                    vote = player.vote_skip(ctx.author)
                    await ctx.embed_reply(":white_check_mark: You voted to skip the current song\n{}".format(f"Skips: {vote}/{player.skip_votes_required}" if vote else ":next_track: Song skipped"))
            else:
                await ctx.embed_reply(":no_entry: You're not even listening!")
        else:
            if number:
                try:
                    song = await player.skip_specific(number)
                except errors.AudioError as e:
                    await ctx.embed_reply(f":no_entry: {e}")
                else:
                    await ctx.embed_reply(f":put_litter_in_its_place: Skipped #{number} in the queue: `{song.info['title']}`")
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
            await ctx.embed_reply(f":no_entry: {e}")
        else:
            await ctx.embed_reply(f":put_litter_in_its_place: Skipped to #{number} in the queue")
            del songs

    @audio.command(
        name = "replay", aliases = ["repeat"], with_app_command = False
    )
    @checks.is_voice_connected()
    @commands.check_any(checks.is_permitted(), checks.is_guild_owner())
    async def audio_replay(self, ctx):
        '''Repeat the current song'''
        # Note: replay command invokes this command
        # TODO: Add restart alias?
        response = await ctx.embed_reply(":repeat_one: Restarting song..")
        embed = response.embeds[0]
        try:
            await self.players[ctx.guild.id].replay()
        except errors.AudioError as e:
            embed.description = f":no_entry: {e}"
        else:
            embed.description = ":repeat_one: Restarted song"
        finally:
            await response.edit(embed = embed)

    @commands.command(aliases = ["repeat"])
    @checks.is_voice_connected()
    @commands.check_any(checks.is_permitted(), checks.is_guild_owner())
    async def replay(self, ctx):
        '''Repeat the current song'''
        if command := ctx.bot.get_command("audio replay"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "audio replay command not found when replay command invoked"
            )

    @commands.command()
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def insert(self, ctx, position: int, *, query: str):
        '''
        Insert audio into the queue

        position
            Position number to insert the audio into the queue at
        query
            Audio to insert into the queue
        '''
        if command := ctx.bot.get_command("audio queue insert"):
            await ctx.invoke(
                command, position = position, query = query
            )
        else:
            raise RuntimeError(
                "audio queue insert command not found "
                "when insert command invoked"
            )

    @audio.command(name = "insert", with_app_command = False)
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def audio_insert(self, ctx, position: int, *, query: str):
        '''
        Insert audio into the queue

        position
            Position number to insert the audio into the queue at
        query
            Audio to insert into the queue
        '''
        if command := ctx.bot.get_command("audio queue insert"):
            await ctx.invoke(
                command, position = position, query = query
            )
        else:
            raise RuntimeError(
                "audio queue insert command not found "
                "when audio insert command invoked"
            )

    @audio.command(
        name = "empty", aliases = ["clear"], with_app_command = False
    )
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def audio_empty(self, ctx):
        '''Empty the queue'''
        if command := ctx.bot.get_command("audio queue empty"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "audio queue empty command not found "
                "when audio empty command invoked"
            )

    @commands.command(aliases = ["clear"])
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def empty(self, ctx):
        '''Empty the queue'''
        if command := ctx.bot.get_command("audio queue empty"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "audio queue empty command not found "
                "when empty command invoked"
            )

    @audio.command(name = "shuffle", with_app_command = False)
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def audio_shuffle(self, ctx):
        '''Shuffle the queue'''
        if command := ctx.bot.get_command("audio queue shuffle"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "audio queue shuffle command not found "
                "when audio shuffle command invoked"
            )

    @commands.command()
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def shuffle(self, ctx):
        '''Shuffle the queue'''
        if command := ctx.bot.get_command("audio queue shuffle"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "audio queue shuffle command not found "
                "when shuffle command invoked"
            )

    @audio.command(
        name = "random", aliases = ["top"], with_app_command = False
    )
    @checks.not_forbidden()
    @checks.is_voice_connected()
    async def audio_random(self, ctx):
        '''Play a random song from YouTube's top 50'''
        async with ctx.bot.aiohttp_session.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params = {
                "part": "id", "chart": "mostPopular", "maxResults": 50,
                "videoCategoryId": 10, "key": ctx.bot.GOOGLE_API_KEY
            }
        ) as resp:
            data = await resp.json()

        song = random.choice([video["id"] for video in data["items"]])

        response = await ctx.embed_reply(":cd: Loading..")
        embed = response.embeds[0]

        try:
            title, url = await self.players[ctx.guild.id].add_song(ctx, song)
        except Exception as e:
            embed.description = f":warning: Error loading `{song}`\n`{type(e).__name__}: {e}`"
        else:
            embed.title = title
            embed.url = url
            embed.description = f":ballot_box_with_check: Successfully added `{song}` to the queue"

        try:
            await response.edit(embed = embed)
        except discord.HTTPException:  # Necessary?
            embed.description = f":warning: Error loading `{song}`"
            await response.edit(embed = embed)

    @commands.command()
    @checks.is_voice_connected()
    @commands.check_any(checks.is_permitted(), checks.is_guild_owner())
    async def radio(
        self, ctx,
        setting: Optional[bool] = None  # noqa: UP007 (non-pep604-annotation)
    ):
        '''
        Radio station based on the current song

        Parameters
        ----------
        setting
            Whether to turn on radio
            (Defaults to None — toggle on/off)
        '''
        if setting:
            if self.players[ctx.guild.id].radio_flag:
                await ctx.embed_reply(
                    f"{ctx.bot.error_emoji} Radio is already on"
                )
            elif (await self.players[ctx.guild.id].radio_on(ctx)) is False:
                await ctx.embed_reply(
                    ":warning: Something else is already playing\n"
                    "Please stop it first"
                )
        elif setting is False:
            if self.players[ctx.guild.id].radio_flag:
                self.players[ctx.guild.id].radio_off()
                await ctx.embed_reply("\N{OCTAGONAL SIGN} Turned radio off")
            else:
                await ctx.embed_reply(
                    f"{ctx.bot.error_emoji} Radio is already off"
                )
        elif self.players[ctx.guild.id].radio_flag:
            self.players[ctx.guild.id].radio_off()
            await ctx.embed_reply("\N{OCTAGONAL SIGN} Turned radio off")
        elif (await self.players[ctx.guild.id].radio_on(ctx)) is False:
            await ctx.embed_reply(
                ":warning: Something else is already playing\n"
                "Please stop it first"
            )

    @audio.command(name = "text", with_app_command = False)
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def audio_text(
        self, ctx,
        channel: 
            discord.TextChannel | discord.VoiceChannel | discord.Thread |
            discord.StageChannel
        = commands.CurrentChannel
    ):
        '''Set text channel for messages'''
        self.players[ctx.guild.id].text_channel = channel
        await ctx.embed_reply(
            f"\N{WRITING HAND}{ctx.bot.emoji_skin_tone} "
            f"Changed text channel to {channel.mention}"
        )

    @audio.command(name = "tts")
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def audio_tts(
        self, ctx,
        amplitude: Optional[commands.Range[int, 0, 1000]] = 100,  # noqa: UP007 (non-pep604-annotation)
        pitch: Optional[commands.Range[int, 0, 99]] = 50,  # noqa: UP007 (non-pep604-annotation)
        speed: Optional[commands.Range[int, 80, 9000]] = 150,  # noqa: UP007 (non-pep604-annotation)
        word_gap: Optional[commands.Range[int, 0, 1000]] = 0,  # noqa: UP007 (non-pep604-annotation)
        voice: Optional[str] = "en-us+f1",  # noqa: UP007 (non-pep604-annotation)
        *, message: str
    ):
        '''
        Text to speech

        voices:
        http://espeak.sourceforge.net/languages.html
        https://github.com/espeak-ng/espeak-ng/blob/master/docs/languages.md#languages
        https://github.com/espeak-ng/espeak-ng/tree/master/espeak-ng-data/voices/!v

        Parameters
        ----------
        amplitude
            (0–1000, defaults to 100)
        pitch
            (0–99, defaults to 50)
        speed
            (80–9000, defaults to 150)
        word_gap
            Length of pause between words, in units of 10 ms
            (0–1000, defaults to 0)
        voice
            (defaults to en-us+f1)
        message
            Message to say
        '''  # noqa: RUF002 (ambiguous-unicode-character-docstring)
        # Note: tts command invokes this command
        await ctx.defer()

        if not (
            await self.players[ctx.guild.id].play_tts(
                ctx, message, amplitude = amplitude, pitch = pitch,
                speed = speed, word_gap = word_gap, voice = voice
            )
        ):
            await ctx.embed_reply(
                ":warning: Something else is already playing\n"
                "Please stop it first"
            )

    @commands.command()
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def tts(
        self, ctx,
        amplitude: Optional[commands.Range[int, 0, 1000]] = 100,  # noqa: UP007 (non-pep604-annotation)
        pitch: Optional[commands.Range[int, 0, 99]] = 50,  # noqa: UP007 (non-pep604-annotation)
        speed: Optional[commands.Range[int, 80, 9000]] = 150,  # noqa: UP007 (non-pep604-annotation)
        word_gap: Optional[commands.Range[int, 0, 1000]] = 0,  # noqa: UP007 (non-pep604-annotation)
        voice: Optional[str] = "en-us+f1",  # noqa: UP007 (non-pep604-annotation)
        *, message: str
    ):
        '''
        Text to speech

        voices:
        http://espeak.sourceforge.net/languages.html
        https://github.com/espeak-ng/espeak-ng/blob/master/docs/languages.md#languages
        https://github.com/espeak-ng/espeak-ng/tree/master/espeak-ng-data/voices/!v

        Parameters
        ----------
        amplitude
            (0–1000, defaults to 100)
        pitch
            (0–99, defaults to 50)
        speed
            (80–9000, defaults to 150)
        word_gap
            Length of pause between words, in units of 10 ms
            (0–1000, defaults to 0)
        voice
            (defaults to en-us+f1)
        message
            Message to say
        '''  # noqa: RUF002 (ambiguous-unicode-character-docstring)
        if command := ctx.bot.get_command("audio tts"):
            await ctx.invoke(
                command, amplitude = amplitude, pitch = pitch, speed = speed,
                word_gap = word_gap, voice = voice, message = message
            )
        else:
            raise RuntimeError(
                "audio tts command not found when tts command invoked"
            )

    @audio.command(name = "file", with_app_command = False)
    @checks.is_voice_connected()
    @commands.check_any(checks.is_permitted(), checks.is_guild_owner())
    async def audio_file(self, ctx, *, filename: str = ""):
        '''Play an audio file'''
        # Note: file command invokes this command
        if not (await self.players[ctx.guild.id].play_file(ctx, filename)):
            await ctx.embed_reply(
                ":warning: Something else is already playing\n"
                "Please stop it first"
            )

    @commands.command()
    @checks.is_voice_connected()
    @commands.check_any(checks.is_permitted(), checks.is_guild_owner())
    async def file(self, ctx, *, filename: str = ""):
        '''Play an audio file'''
        if command := ctx.bot.get_command("audio file"):
            await ctx.invoke(command, filename = filename)
        else:
            raise RuntimeError(
                "audio file command not found when file command invoked"
            )

    @audio.command(name = "files", with_app_command = False)
    @checks.not_forbidden()
    @checks.is_voice_connected()
    async def audio_files(self, ctx):
        '''List existing audio files'''
        # Note: files command invokes this command
        await ctx.embed_reply(self.players[ctx.guild.id].list_files())

    @commands.command()
    @checks.not_forbidden()
    @checks.is_voice_connected()
    async def files(self, ctx):
        '''List existing audio files'''
        if command := ctx.bot.get_command("audio files"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "audio files command not found when files command invoked"
            )

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

    @audio.command(name = "volume")
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def audio_volume(
        self, ctx,
        volume_setting: Optional[commands.Range[float, 0.0, 2000.0]] = None,  # noqa: UP007 (non-pep604-annotation)
        default: Optional[bool] = False  # noqa: UP007 (non-pep604-annotation)
    ):
        '''
        Change or show the volume of the current song or player

        Parameters
        ----------
        volume_setting
            Volume to change to
            (0–2000, defaults to None — show current volume)
        default
            Whether to change/show the default volume for the current player
            (Defaults to False — change/show the volume for the current song)
        '''  # noqa: RUF002 (ambiguous-unicode-character-docstring)
        # Note: volume command invokes this command
        # TODO: Use '\N{SPEAKER}' when volume/setting is 0
        if default:
            if volume_setting is None:
                await ctx.embed_reply(
                    f"\N{SPEAKER WITH ONE SOUND WAVE} Current default volume: {self.players[ctx.guild.id].default_volume:g}"
                )
            else:
                volume_setting = min(max(0, volume_setting), 2000)
                self.players[ctx.guild.id].default_volume = volume_setting
                await ctx.embed_reply(
                    f"\N{SPEAKER WITH ONE SOUND WAVE} Set default volume to {volume_setting:g}"
                )
        elif ctx.guild.voice_client.is_playing():
            if volume_setting is None:
                await ctx.embed_reply(
                    f"\N{SPEAKER WITH ONE SOUND WAVE} Current volume: {ctx.guild.voice_client.source.volume:g}"
                )
            else:
                ctx.guild.voice_client.source.volume = volume_setting
                volume_setting = min(max(0, volume_setting), 2000)
                await ctx.embed_reply(
                    f"\N{SPEAKER WITH ONE SOUND WAVE} Set volume to {volume_setting:g}"
                )
        else:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} There's nothing playing right now"
            )

    @commands.command()
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def volume(
        self, ctx,
        volume_setting: Optional[commands.Range[float, 0.0, 2000.0]] = None,  # noqa: UP007 (non-pep604-annotation)
        default: Optional[bool] = False  # noqa: UP007 (non-pep604-annotation)
    ):
        '''
        Change or show the volume of the current song or player

        Parameters
        ----------
        volume_setting
            Volume to change to
            (0–2000, defaults to None — show current volume)
        default
            Whether to change/show the default volume for the current player
            (Defaults to False — change/show the volume for the current song)
        '''  # noqa: RUF002 (ambiguous-unicode-character-docstring)
        if command := ctx.bot.get_command("audio volume"):
            await ctx.invoke(
                command, volume_setting = volume_setting, default = default
            )
        else:
            raise RuntimeError(
                "audio volume command not found when volume command invoked"
            )

    @commands.group(
        aliases = ["current"],
        invoke_without_command = True, case_insensitive = True
    )
    @checks.is_voice_connected()
    @checks.not_forbidden()
    async def playing(self, ctx):
        '''See the currently playing song'''
        if not ctx.guild.voice_client.is_playing():
            await ctx.embed_reply(":speaker: There is no song currently playing")
            return

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
            played_duration = (
                ctx.guild.voice_client.source.previous_played_time +
                ctx.guild.voice_client._player.DELAY * ctx.guild.voice_client._player.loops
            )
            total_duration = ctx.guild.voice_client.source.info.get("duration")
            if total_duration:
                playing_bar = "▬" * 10
                button_spot = int(played_duration / (total_duration / 10))
                playing_bar = playing_bar[:button_spot] + ":radio_button: " + playing_bar[button_spot + 1:]
                played_duration = utilities.secs_to_colon_format(played_duration)
                total_duration = utilities.secs_to_colon_format(total_duration)
                description = f":arrow_forward: {playing_bar}`[{played_duration}/{total_duration}]`"  # Add :sound:?
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
            title_url = None

        requester = ctx.guild.voice_client.source.requester

        await ctx.embed_reply(
            title = title,
            title_url = title_url,
            description = description,
            footer_text = "Added by " + requester.display_name,
            footer_icon_url = requester.display_avatar.url,
            timestamp = ctx.guild.voice_client.source.timestamp
        )

    @audio.group(name = "queue", fallback = "show")
    @checks.is_voice_connected()
    @checks.not_forbidden()
    async def audio_queue(self, ctx):
        '''Show the current queue'''
        # Note: queue command invokes this command
        embed = self.players[ctx.guild.id].queue_embed()
        embed.set_author(
            name = ctx.author.display_name,
            icon_url = ctx.author.display_avatar.url
        )
        await ctx.send(embed = embed)
        await self.bot.attempt_delete_message(ctx.message)

    @commands.group()
    @checks.is_voice_connected()
    @checks.not_forbidden()
    async def queue(self, ctx):
        '''Show the current queue'''
        if command := ctx.bot.get_command("audio queue"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "audio queue command not found when queue command invoked"
            )

    @audio_queue.command(name = "empty", aliases = ["clear"])
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def audio_queue_empty(self, ctx):
        '''Empty the queue'''
        # Note: audio empty command invokes this command
        # Note: empty command invokes this command
        # Note: queue empty command invokes this command
        await self.players[ctx.guild.id].empty_queue()
        await ctx.embed_reply(
            "\N{WASTEBASKET}\N{VARIATION SELECTOR-16} Emptied queue"
        )

    @queue.command(name = "empty", aliases = ["clear"])
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def queue_empty(self, ctx):
        '''Empty the queue'''
        if command := ctx.bot.get_command("audio queue empty"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "audio queue empty command not found "
                "when queue empty command invoked"
            )

    @audio_queue.command(name = "insert")
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def audio_queue_insert(self, ctx, position: int, *, query: str):
        '''
        Insert audio into the queue

        position
            Position number to insert the audio into the queue at
        query
            Audio to insert into the queue
        '''
        # audio insert command invokes this command
        # insert command invokes this command
        # queue insert command invokes this command
        if "spotify" in query:
            query = await self.spotify_to_youtube(query)
            if not query:
                await ctx.embed_reply(":warning: Error")
                return
        response = await ctx.embed_reply(":cd: Loading..")
        embed = response.embeds[0]
        try:
            source = await self.players[ctx.guild.id].insert_song(ctx, query, position)
        except Exception as e:
            embed.description = f":warning: Error loading `{query}`\n`{type(e).__name__}: {e}`"
            if len(embed.description) > ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT:
                embed.description = embed.description[:ctx.bot.EDCL - 4] + "...`"
                # EDCL: Embed Description Character Limit
        else:
            embed.description = f":ballot_box_with_check: `{source.title}` has been inserted into position #{position} in the queue"
        finally:
            await response.edit(embed = embed)

    @queue.command(name = "insert")
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def queue_insert(self, ctx, position: int, *, query: str):
        '''
        Insert audio into the queue

        position
            Position number to insert the audio into the queue at
        query
            Audio to insert into the queue
        '''
        if command := ctx.bot.get_command("audio queue insert"):
            await ctx.invoke(
                command, position = position, query = query
            )
        else:
            raise RuntimeError(
                "audio queue insert command not found "
                "when queue insert command invoked"
            )

    @audio_queue.command(name = "shuffle")
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def audio_queue_shuffle(self, ctx):
        '''Shuffle the queue'''
        # Note: audio shuffle command invokes this command
        # Note: queue shuffle command invokes this command
        # Note: shuffle command invokes this command
        response = await ctx.embed_reply(
            "\N{TWISTED RIGHTWARDS ARROWS} Shuffling.."
        )
        embed = response.embeds[0]
        await self.players[ctx.guild.id].shuffle_queue()
        embed.description = "\N{TWISTED RIGHTWARDS ARROWS} Shuffled songs"
        await response.edit(embed = embed)

    @queue.command(name = "shuffle")
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def queue_shuffle(self, ctx):
        '''Shuffle the queue'''
        if command := ctx.bot.get_command("audio queue shuffle"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "audio queue shuffle command not found "
                "when queue shuffle command invoked"
            )

    # Meta

    @audio.command(name = "latency")
    @checks.is_voice_connected()
    @checks.not_forbidden()
    async def audio_latency(
        self, ctx,
        average: Optional[bool] = False  # noqa: UP007 (non-pep604-annotation)
    ):
        '''
        Latency between a HEARTBEAT and its HEARTBEAT_ACK in seconds

        Parameters
        ----------
        average
            Whether to show the average of the last 20 HEARTBEAT latencies
            (Defaults to False — show the latest latency)
        '''
        if average:
            await ctx.embed_reply(f"{ctx.guild.voice_client.average_latency}s")
        else:
            await ctx.embed_reply(f"{ctx.guild.voice_client.latency}s")

    # Discord Control

    @audio.command(name = "deafen")
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def audio_deafen(self, ctx):
        '''Have me deafen myself'''
        # Note: deafen command invokes this command
        if ctx.guild.me.voice.self_deaf:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} I'm already deafened"
            )
            return
        await ctx.guild.change_voice_state(
            channel = ctx.guild.voice_client.channel, self_deaf = True,
            self_mute = ctx.guild.me.voice.self_mute
        )
        await ctx.embed_reply("I've deafened myself")

    @commands.command()
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def deafen(self, ctx):
        '''Have me deafen myself'''
        if command := ctx.bot.get_command("audio deafen"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "audio deafen command not found when deafen command invoked"
            )

    @audio.command(name = "mute")
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def audio_mute(self, ctx):
        '''Have me mute myself'''
        # Note: mute command invokes this command
        if ctx.guild.me.voice.self_mute:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} I'm already muted")
            return
        await ctx.guild.change_voice_state(
            channel = ctx.guild.voice_client.channel, self_mute = True,
            self_deaf = ctx.guild.me.voice.self_deaf
        )
        await ctx.embed_reply("I've muted myself")

    @commands.command()
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def mute(self, ctx):
        '''Have me mute myself'''
        if command := ctx.bot.get_command("audio mute"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "audio mute command not found when mute command invoked"
            )

    @audio.command(name = "undeafen")
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def audio_undeafen(self, ctx):
        '''Have me undeafen myself'''
        # Note: undeafen command invokes this command
        if not ctx.guild.me.voice.self_deaf:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} I'm not deafened")
            return
        await ctx.guild.change_voice_state(
            channel = ctx.guild.voice_client.channel, self_deaf = False,
            self_mute = ctx.guild.me.voice.self_mute
        )
        await ctx.embed_reply("I've undeafened myself")

    @commands.command()
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def undeafen(self, ctx):
        '''Have me undeafen myself'''
        if command := ctx.bot.get_command("audio undeafen"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "audio undeafen command not found "
                "when undeafen command invoked"
            )

    @audio.command(name = "unmute")
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def audio_unmute(self, ctx):
        '''Have me unmute myself'''
        # Note: unmute command invokes this command
        if not ctx.guild.me.voice.self_mute:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} I'm not muted")
            return
        await ctx.guild.change_voice_state(
            channel = ctx.guild.voice_client.channel, self_mute = False,
            self_deaf = ctx.guild.me.voice.self_deaf
        )
        await ctx.embed_reply("I've unmuted myself")

    @commands.command()
    @checks.is_voice_connected()
    @commands.check_any(
        checks.is_permitted(), commands.has_permissions(administrator = True),
        commands.is_owner()
    )
    async def unmute(self, ctx):
        '''Have me unmute myself'''
        if command := ctx.bot.get_command("audio unmute"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "audio unmute command not found when unmute command invoked"
            )

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
        async with self.bot.aiohttp_session.get(
            f"https://api.spotify.com/v1/tracks/{path[7:]}",
            headers = {"Authorization": f"Bearer {spotify_access_token}"}
        ) as resp:
            data = await resp.json()

        if "name" not in data:
            return False

        async with self.bot.aiohttp_session.get(
            "https://www.googleapis.com/youtube/v3/search",
            params = {
                "part": "snippet", "key": self.bot.GOOGLE_API_KEY,
                'q': f"{data['artists'][0]['name']} - {data['name']}"
            }
        ) as resp:
            data = await resp.json()

        for item in data["items"]:
            if "videoId" in item["id"]:
                return "https://www.youtube.com/watch?v=" + item["id"]["videoId"]

    async def get_spotify_access_token(self):
        authorization = f"{self.bot.SPOTIFY_CLIENT_ID}:{self.bot.SPOTIFY_CLIENT_SECRET_KEY}"
        authorization = base64.b64encode(authorization.encode()).decode()
        async with self.bot.aiohttp_session.post(
            "https://accounts.spotify.com/api/token",
            params = {"grant_type": "client_credentials"},
            headers = {
                "Authorization": f"Basic {authorization}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        ) as resp:
            data = await resp.json()

        return data["access_token"]

