
from discord import app_commands
from discord.ext import commands

from async_lru import alru_cache

from utilities import checks


async_cache = alru_cache(maxsize=None)
# https://github.com/python/cpython/issues/90780


async def setup(bot):
    await bot.add_cog(Brawlhalla(bot))


class Brawlhalla(commands.Cog):

    """Brawlhalla"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.hybrid_group(case_insensitive = True)
    async def brawlhalla(self, ctx):
        """Brawlhalla"""
        await ctx.send_help(ctx.command)

    @brawlhalla.command()
    async def legend(self, ctx, *, name: str):
        """
        Show information about a Brawlhalla legend

        Parameters
        ----------
        name
            Name of legend to show information about
        """
        for legend in (await self.all_legends()):
            if name.lower() in (
                legend["legend_name_key"], legend["bio_name"].lower()
            ):
                await ctx.embed_reply(
                    title = legend["bio_name"],
                    description = legend["bio_aka"],
                    fields = (
                        (
                            "Weapons",
                            f"{legend['weapon_one']}, {legend['weapon_two']}"
                        ),
                        ("Strength", legend["strength"]),
                        ("Dexterity", legend["dexterity"]),
                        ("Defense", legend["defense"]),
                        ("Speed", legend["speed"])
                    )
                )
                return
        await ctx.embed_reply(f"{ctx.bot.error_emoji} Legend not found")

    @legend.autocomplete("name")
    async def legend_autocomplete(self, interaction, current):
        current = current.lower()
        matching = [
            app_commands.Choice(
                name = legend["bio_name"],
                value = legend["legend_name_key"]
            )
            for legend in (await self.all_legends())
            if (
                current in legend["legend_name_key"] or
                current in legend["bio_name"].lower()
            )
        ]
        return matching[:25]  # TODO: Use difflib?

    @async_cache
    async def all_legends(self):
        async with self.bot.aiohttp_session.get(
            "https://api.brawlhalla.com/legend/all",
            params = {"api_key": self.bot.BRAWLHALLA_API_KEY}
        ) as resp:
            return await resp.json()  # TODO: Return dictionary?

