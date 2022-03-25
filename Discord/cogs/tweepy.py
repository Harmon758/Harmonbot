
from discord import app_commands
from discord.ext import commands


async def setup(bot):
    await bot.add_cog(Tweepy())


class Tweepy(commands.Cog, app_commands.Group):
    """Tweepy"""
