
import discord
from discord import app_commands
from discord.ext import commands

from enum import Enum

from utilities import checks
from utilities.transformers import PartialEmojiTransformer


class EMOJI(Enum):
    bird = '\N{BIRD}'
    cow = '\N{COW}'
    cucumber = '\N{CUCUMBER}'
    dragon = '\N{DRAGON}'
    eagle = '\N{EAGLE}'
    eggplant = '\N{AUBERGINE}'
    frog = '\N{FROG FACE}'
    gun = '\N{PISTOL}'
    horse = '\N{HORSE FACE}'
    lizard = '\N{LIZARD}'
    minidisc = '\N{MINIDISC}'
    panda = '\N{PANDA FACE}'
    penguin = '\N{PENGUIN}'
    tomato = '\N{TOMATO}'
    turtle = '\N{TURTLE}'


def emoji_command_wrapper(emoji):
    async def emoji_command(self, ctx):
        await ctx.embed_reply(emoji.value)
    return emoji_command

class EmojiCommand(commands.Command):

    def __init__(self, *args, emoji = None):
        super().__init__(
            emoji_command_wrapper(emoji),
            name = emoji.name,
            help = emoji.name.capitalize() + " emoji",
            checks = [checks.not_forbidden().predicate]
        )
        self.params = {}


async def setup(bot):

    for emoji in EMOJI:
        command = EmojiCommand(emoji = emoji)
        setattr(EmojiCog, emoji.name, command)
        EmojiCog.__cog_commands__.append(command)

    await bot.add_cog(EmojiCog())

class EmojiCog(commands.GroupCog, group_name = "emoji", name = "Emoji"):

    @commands.command(aliases = ["bigmote"])
    async def bigmoji(self, ctx, emoji: discord.PartialEmoji):
        """Enlarge custom emoji"""
        await ctx.embed_reply(image_url = emoji.url)

    @commands.command(aliases = ["emotify"])
    async def emojify(self, ctx, *, text: str):
        """Emojify text"""
        output = ""
        for character in text:
            if 'a' <= character.lower() <= 'z':
                output += chr(ord(character.lower()) + 127365) + ' '
                # ord('🇦') - ord('a') = 127365
            elif '0' <= character <= '9':
                output += (
                    character +
                    "\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP} "
                )
            else:
                output += character
        try:
            await ctx.embed_reply(output)
        except discord.HTTPException:
            # TODO: use textwrap/paginate
            await ctx.embed_reply(f"{ctx.bot.error_emoji} Error")

    @app_commands.command()
    async def enlarge(
        self, interaction, *,
        emoji: app_commands.Transform[
            discord.PartialEmoji, PartialEmojiTransformer
        ]
    ):
        """
        Enlarge custom emoji

        Parameters
        ----------
        emoji
            Custom emoji to enlarge
        """
        ctx = await interaction.client.get_context(interaction)
        await self.bigmoji(ctx, emoji = emoji)

    @app_commands.command()
    async def send(self, interaction, *, emoji: EMOJI):
        """
        Send emoji

        Parameters
        ----------
        emoji
            Emoji to send
        """
        ctx = await interaction.client.get_context(interaction)
        await ctx.embed_reply(emoji.value)

