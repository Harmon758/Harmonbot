
from discord.ext import commands

from utilities import checks


async def setup(bot):
    await bot.add_cog(Duelyst())


class Duelyst(commands.Cog):

    """
    This is deprecated now that Duelyst is closed/shut down:
    https://duelyst.com/news/farewell-duelyst
    https://web.archive.org/web/20200126025952/https://duelyst.com/news/farewell-duelyst
    https://steamcommunity.com/games/291410/announcements/detail/1688222120329073284
    https://twitter.com/PlayDuelyst/status/1220802596081811456
    and now that the duelyststats.info domain being used for its API has a different owner and website
    """

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.group(
        hidden = True, case_insensitive = True, invoke_without_command = True
    )
    async def duelyst(self, ctx):
        """
        This command is deprecated now that Duelyst is closed/shut down:
        https://duelyst.com/news/farewell-duelyst
        https://web.archive.org/web/20200126025952/https://duelyst.com/news/farewell-duelyst
        https://steamcommunity.com/games/291410/announcements/detail/1688222120329073284
        https://twitter.com/PlayDuelyst/status/1220802596081811456
        and now that the duelyststats.info domain being used for its API has a different owner and website
        """
        await ctx.send_help(ctx.command)

    @duelyst.group(hidden = True, case_insensitive = True)
    async def card(self, ctx, *, name: str):
        """
        This command is deprecated now that Duelyst is closed/shut down:
        https://duelyst.com/news/farewell-duelyst
        https://web.archive.org/web/20200126025952/https://duelyst.com/news/farewell-duelyst
        https://steamcommunity.com/games/291410/announcements/detail/1688222120329073284
        https://twitter.com/PlayDuelyst/status/1220802596081811456
        and now that the duelyststats.info domain being used for its API has a different owner and website
        """
        await ctx.send_help(ctx.command)

    @card.command(hidden = True)
    async def card_random(self, ctx):
        """
        This command is deprecated now that Duelyst is closed/shut down:
        https://duelyst.com/news/farewell-duelyst
        https://web.archive.org/web/20200126025952/https://duelyst.com/news/farewell-duelyst
        https://steamcommunity.com/games/291410/announcements/detail/1688222120329073284
        https://twitter.com/PlayDuelyst/status/1220802596081811456
        and now that the duelyststats.info domain being used for its API has a different owner and website
        """
        await ctx.send_help(ctx.command)

