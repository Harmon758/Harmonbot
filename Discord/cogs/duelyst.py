
from discord.ext import commands

from utilities import checks


async def setup(bot):
    await bot.add_cog(Duelyst())


class Duelyst(commands.Cog):

    """
    Deprecated now that Duelyst is closed/shut down:
    https://duelyst.com/news/farewell-duelyst
    https://web.archive.org/web/20200126025952/https://duelyst.com/news/farewell-duelyst
    https://steamcommunity.com/games/291410/announcements/detail/1688222120329073284
    https://twitter.com/PlayDuelyst/status/1220802596081811456
    and now that the duelyststats.info domain being used for its API has a different owner and website
    """

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.group(
        hidden = True, invoke_without_command = True, case_insensitive = True
    )
    async def duelyst(self, ctx):
        """
        Duelyst
        Deprecated now that Duelyst is closed/shut down:
        https://duelyst.com/news/farewell-duelyst
        https://web.archive.org/web/20200126025952/https://duelyst.com/news/farewell-duelyst
        https://steamcommunity.com/games/291410/announcements/detail/1688222120329073284
        https://twitter.com/PlayDuelyst/status/1220802596081811456
        and now that the duelyststats.info domain being used for its API has a different owner and website
        """
        await ctx.send_help(ctx.command)

    @duelyst.group(enabled = False, hidden = True, case_insensitive = True)
    async def card(self, ctx, *, name: str):
        """Details of a specific card"""
        url = "https://duelyststats.info/scripts/carddata/get.php"
        params = {"cardName": name}
        async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
            data = await resp.text()
        await ctx.embed_reply(data)

    @card.command(enabled = False, hidden = True)
    async def card_random(self, ctx):
        """Details of a random card"""
        url = "https://duelyststats.info/scripts/carddata/get.php"
        params = {"random": 1}
        async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
            data = await resp.text()
        await ctx.embed_reply(data)

