
from discord.ext import commands

from utilities import checks


EMOJI_MAPPING = {
    "frog": '\N{FROG FACE}',
    "turtle": '\N{TURTLE}',
    "gun": '\N{PISTOL}',
    "tomato": '\N{TOMATO}',
    "cucumber": '\N{CUCUMBER}',
    "eggplant": '\N{AUBERGINE}',
    "lizard": '\N{LIZARD}',
    "minidisc": '\N{MINIDISC}',
    "horse": '\N{HORSE FACE}',
    "penguin": '\N{PENGUIN}',
    "dragon": '\N{DRAGON}',
    "eagle": '\N{EAGLE}',
    "bird": '\N{BIRD}',
    "cow": '\N{COW}',
    "panda": '\N{PANDA FACE}'
}


def emoji_command_wrapper(emoji):
    async def emoji_command(self, ctx):
        await ctx.embed_reply(EMOJI_MAPPING[emoji])
    return emoji_command

class EmojiCommand(commands.Command):

    def __init__(self, *args, emoji = None):
        super().__init__(
            emoji_command_wrapper(emoji),
            name = emoji,
            help = emoji.capitalize() + " emoji",
            checks = [checks.not_forbidden().predicate]
        )
        self.params = {}


async def setup(bot):

    for emoji in EMOJI_MAPPING:
        command = EmojiCommand(emoji = emoji)
        setattr(Emoji, emoji, command)
        Emoji.__cog_commands__.append(command)

    await bot.add_cog(Emoji())

class Emoji(commands.Cog):

    ...

