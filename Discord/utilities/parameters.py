
import discord
from discord.ext import commands

from typing import Union


def default_voice_channel(
    ctx: commands.Context
) -> Union[discord.VoiceChannel, None]:  # TODO: Use | with Python 3.10
    if isinstance(ctx.channel, discord.VoiceChannel):
        return ctx.channel
    if ctx.author.voice:
        return ctx.author.voice.channel

CurrentVoiceChannel = commands.parameter(
    converter = commands.VoiceChannelConverter,
    default = default_voice_channel,
    displayed_default = "<your current voice channel>",
)
