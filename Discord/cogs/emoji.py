
from discord.ext import commands

from utilities import checks


EMOJI_MAPPING = {
    "bird": '\N{BIRD}',
    "cow": '\N{COW}',
    "cucumber": '\N{CUCUMBER}',
    "dragon": '\N{DRAGON}',
    "eagle": '\N{EAGLE}',
    "eggplant": '\N{AUBERGINE}',
    "frog": '\N{FROG FACE}',
    "gun": '\N{PISTOL}',
    "horse": '\N{HORSE FACE}',
    "lizard": '\N{LIZARD}',
    "minidisc": '\N{MINIDISC}',
    "panda": '\N{PANDA FACE}',
    "penguin": '\N{PENGUIN}',
    "tomato": '\N{TOMATO}',
    "turtle": '\N{TURTLE}'
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
        setattr(EmojiCog, emoji, command)
        EmojiCog.__cog_commands__.append(command)

    await bot.add_cog(EmojiCog())

class EmojiCog(commands.Cog, name = "Emoji"):

    ...

