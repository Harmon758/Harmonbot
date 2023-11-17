
import discord

import functools
import logging
import subprocess
import os


class ModifiedFFmpegPCMAudio(discord.FFmpegPCMAudio):

    '''
    Modified discord.FFmpegPCMAudio
    To use ffmpeg log as stderr
    '''

    def __init__(self, ctx, source, before_options = None):
        self.ctx = ctx
        self.source = source  # Unnecessary?
        self.bot = ctx.bot
        with open(self.bot.data_path + "/logs/ffmpeg.log", 'a') as ffmpeg_log:
            super().__init__(
                source, executable = "bin/ffmpeg", stderr = ffmpeg_log,
                before_options = before_options
            )


class ModifiedPCMVolumeTransformer(discord.PCMVolumeTransformer):

    '''
    Modified discord.PCMVolumeTransformer
    To use volume range of 0 - 2000, instead of 0 - 2
    and default volume of 100 (0.1), instead of 1000 (1)
    '''

    def __init__(self, original, volume = 100.0):
        super().__init__(original, volume = volume)

    @property
    def volume(self):
        return self._volume * 1000

    @volume.setter
    def volume(self, value):
        self._volume = max(value / 1000, 0.0)


class FileSource(ModifiedPCMVolumeTransformer):

    def __init__(self, ctx, filename, volume, title_prefix = ""):
        self.ctx = ctx
        self.requester = ctx.author
        self.timestamp = ctx.message.created_at
        self.filename = filename
        self.volume = volume
        self.title_prefix = title_prefix
        self.title = f"{title_prefix}`{os.path.basename(self.filename)}`"
        super().__init__(ModifiedFFmpegPCMAudio(ctx, filename), volume)

    @classmethod
    async def replay(cls, original):
        return cls(
            original.ctx, original.filename, original.volume,
            original.title_prefix
        )


class TTSSource(ModifiedPCMVolumeTransformer):

    '''
    Text-To-Speech Audio Source
    generate_file and initialize_source must be called before usage
    '''

    def __init__(
        self, ctx, message, *, amplitude = 100, pitch = 50, speed = 150,
        word_gap = 0, voice = "en-us+f1"
    ):
        self.ctx = ctx
        self.bot = ctx.bot
        self.requester = ctx.author
        self.timestamp = ctx.message.created_at
        self.message = message
        self.amplitude = amplitude
        self.pitch = pitch
        self.speed = speed
        self.word_gap = word_gap
        self.voice = voice

        self.initialized = False
        self.title = f"TTS Message: `{self.message}`"

    async def generate_file(self):
        func = functools.partial(
            subprocess.run,
            [
                "bin/eSpeak NG/espeak-ng", "--path=bin/eSpeak NG",
                f"-a {self.amplitude}", f"-p {self.pitch}", f"-s {self.speed}",
                f"-g {self.word_gap}", f"-v{self.voice}",
                f"-w {self.bot.data_path}/temp/tts.wav", self.message
            ],
            creationflags = subprocess.CREATE_NO_WINDOW
        )
        await self.bot.loop.run_in_executor(None, func)

    def initialize_source(self, volume):
        super().__init__(
            ModifiedFFmpegPCMAudio(
                self.ctx, self.bot.data_path + "/temp/tts.wav"
            ),
            volume
        )
        self.initialized = True

    @classmethod
    async def replay(cls, original):
        source = cls(
            original.ctx, original.message, amplitude = original.amplitude,
            pitch = original.pitch, speed = original.speed,
            word_gap = original.word_gap, voice = original.voice
        )
        if not os.path.exists(original.bot.data_path + "/temp/tts.wav"):
            await source.generate_file()
        source.initialize_source(original.volume)
        return source

    def cleanup(self):
        if self.initialized:
            super().cleanup()
        '''
        if os.path.exists(self.bot.data_path + "/temp/tts.wav"):
            try:
                os.remove(self.bot.data_path + "/temp/tts.wav")
            except PermissionError:
                pass
        '''


class YTDLSource(ModifiedPCMVolumeTransformer):

    '''
    YouTube Audio Source
    get_info/set_info and initialize_source must be called before usage
    '''

    def __init__(self, ctx, url, stream = False, title_prefix = ""):
        self.ctx = ctx
        self.bot = ctx.bot
        self.requester = ctx.author
        self.timestamp = ctx.message.created_at
        self.url = url
        self.stream = stream
        self.title_prefix = title_prefix
        self.title = title_prefix

        self.initialized = False
        self.filename = None
        self.previous_played_time = 0

    async def get_info(self):
        func = functools.partial(self.bot.ytdl_info.extract_info, self.url, download = False)
        info = await self.bot.loop.run_in_executor(None, func)
        self.set_info(info)

    def set_info(self, info):
        self.info = next(iter(info.get("entries", [])), info)
        logging.getLogger("discord").info(f"playing URL {self.url}")

        self.stream = self.info.get("is_live") or self.stream
        if "title" in self.info:
            self.title += f"`{self.info['title']}`"

    async def initialize_source(self, volume):
        if self.stream:
            super().__init__(ModifiedFFmpegPCMAudio(self.ctx, self.info["url"]), volume)
        else:
            func = functools.partial(self.bot.ytdl_download.extract_info, self.info["webpage_url"], download = True)
            info = await self.bot.loop.run_in_executor(None, func)
            self.filename = self.bot.ytdl_download.prepare_filename(info)

            before_options = f"-ss {self.info['start_time']}" if self.info.get("start_time") else None
            self.previous_played_time = self.info.get("start_time") if self.info.get("start_time") else 0
            super().__init__(ModifiedFFmpegPCMAudio(self.ctx, self.filename, before_options = before_options), volume)
        self.initialized = True

    @classmethod
    async def replay(cls, original):
        source = cls(original.ctx, original.url, original.stream, original.title_prefix)
        source.info, source.stream, source.title = original.info, original.stream, original.title
        await source.initialize_source(original.volume)
        return source

    def cleanup(self):
        if self.initialized:
            super().cleanup()
        if self.filename and os.path.exists(self.filename):
            try:
                os.remove(self.filename)
            except PermissionError as e:  # TODO: Fix
                print(str(e))

