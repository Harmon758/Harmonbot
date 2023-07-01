
import discord
from discord.ext import commands

from operator import attrgetter
from typing import Union


Me = commands.parameter(
    converter = Union[discord.Member, discord.User],
    default = attrgetter("me"),
    displayed_default = "<me>",
)

def default_voice_channel(
    ctx: commands.Context
) -> discord.VoiceChannel | None:
    if isinstance(ctx.channel, discord.VoiceChannel):
        return ctx.channel
    if ctx.author.voice:
        return ctx.author.voice.channel

CurrentVoiceChannel = commands.parameter(
    converter = commands.VoiceChannelConverter,
    default = default_voice_channel,
    displayed_default = "<your current voice channel>",
)
