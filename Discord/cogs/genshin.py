
from discord.ext import commands

from utilities import checks


async def setup(bot):
    await bot.add_cog(GenshinImpact())


class GenshinImpact(commands.Cog, name = "Genshin Impact"):
    """Genshin Impact"""

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.hybrid_group(aliases = ["genshin"], case_insensitive = True)
    async def genshin_impact(self, ctx):
        """Genshin Impact"""
        await ctx.send_help(ctx.command)

    @genshin_impact.command(aliases = ["fandom", "wikia", "wikicities"])
    async def wiki(self, ctx, *, query: str):
        """
        Search for an article on the Genshin Impact wiki

        Parameters
        ----------
        query
            Search query
        """
        await ctx.defer()

        if command := ctx.bot.get_command("search fandom"):
            await ctx.invoke(command, wiki = "Genshin Impact", query = query)
        else:
            raise RuntimeError(
                "search fandom command not found "
                "when genshin_impact wiki command invoked"
            )

