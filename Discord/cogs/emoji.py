
import discord
from discord import app_commands
from discord.ext import commands

from enum import Enum
from operator import attrgetter

from utilities import checks
from utilities.transformers import PartialEmojiTransformer


class EMOJI(Enum):
    bear = '\N{BEAR FACE}'
    bird = '\N{BIRD}'
    chipmunk = '\N{CHIPMUNK}'
    cow = '\N{COW}'
    cucumber = '\N{CUCUMBER}'
    dragon = '\N{DRAGON}'
    eagle = '\N{EAGLE}'
    eggplant = '\N{AUBERGINE}'
    frog = '\N{FROG FACE}'
    gun = '\N{PISTOL}'
    horse = '\N{HORSE FACE}'
    lemon = '\N{LEMON}'
    lizard = '\N{LIZARD}'
    minidisc = '\N{MINIDISC}'
    panda = '\N{PANDA FACE}'
    penguin = '\N{PENGUIN}'
    tomato = '\N{TOMATO}'
    turtle = '\N{TURTLE}'


class EMOJI_ALIASES(Enum):
    squirrel = "chipmunk"
    # https://www.unicode.org/L2/L2017/17442-squirrel-emoji.pdf
    # https://www.unicode.org/L2/L2018/18024-emoji-recs12.pdf
    # https://unicode.org/emoji/proposals.html
    # https://www.unicode.org/mail-arch/unicode-ml/y2018-m08/0010.html


def emoji_command_wrapper(emoji):
    async def emoji_command(self, ctx):
        await ctx.embed_reply(emoji.value)
    return emoji_command

class EmojiCommand(commands.Command):

    def __init__(self, *args, emoji = None):
        super().__init__(
            emoji_command_wrapper(emoji),
            name = emoji.name,
            aliases = [
                alias.name
                for alias in EMOJI_ALIASES
                if alias.value == emoji.name
            ],
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
    """Emoji"""

    @commands.command(aliases = ["bigmote"])
    async def bigmoji(self, ctx, emoji: discord.PartialEmoji):
        """Enlarge custom emoji"""
        await ctx.embed_reply(
            title = emoji.name,
            title_url = emoji.url,
            image_url = emoji.url
        )

    @commands.command(aliases = ["emotify"])
    async def emojify(self, ctx, *, text: str):
        """
        Convert text to emoji
        Note: Discord currently only renders up to 199 emoji per message
        """
        output = ""
        for character in text:
            if 'a' <= character.lower() <= 'z':
                output += chr(ord(character.lower()) + 127365) + ' '
                # ord('🇦') - ord('a') = 127365
            elif '0' <= character <= '9':
                output += character + "\N{COMBINING ENCLOSING KEYCAP} "
            else:
                output += character
        try:
            await ctx.embed_reply(output)
        except discord.HTTPException:
            # TODO: Use textwrap/paginate
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
    @app_commands.choices(
        emoji = sorted(
            [
                app_commands.Choice(name = member.name, value = member.value)
                for member in EMOJI
            ] + [
                app_commands.Choice(
                    name = member.name, value = EMOJI[member.value].value
                )
                for member in EMOJI_ALIASES
            ],
            key = attrgetter("name")
        )
    )
    async def send(self, interaction, *, emoji: app_commands.Choice[str]):
        """
        Send emoji

        Parameters
        ----------
        emoji
            Emoji to send
        """
        ctx = await interaction.client.get_context(interaction)
        await ctx.embed_reply(emoji.value)

    @app_commands.command(name = "text")
    async def slash_text(self, interaction, *, text: str):
        """
        Convert text to emoji

        Parameters
        ----------
        text
            Text to convert to emoji
        """
        ctx = await interaction.client.get_context(interaction)
        await self.emojify(ctx, text = text)

