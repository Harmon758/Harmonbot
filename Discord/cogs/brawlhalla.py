
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
        try:
            legend = (await self.all_legends())[name.lower()]
        except KeyError:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} Legend not found")
            return

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

    @legend.autocomplete("name")
    async def legend_autocomplete(self, interaction, current):
        current = current.lower()
        legends = await self.all_legends()

        primary_matches = set()
        secondary_matches = set()

        for name, data in legends.items():
            if name.startswith(current):
                primary_matches.add(data["legend_name_key"])
            elif current in name:
                secondary_matches.add(data["legend_name_key"])

        matches = sorted(primary_matches) + sorted(secondary_matches)

        return [
            app_commands.Choice(
                name = legends[match]["bio_name"],
                value = match
            )
            for match in matches[:25]
        ]

    @async_cache
    async def all_legends(self):
        async with self.bot.aiohttp_session.get(
            "https://api.brawlhalla.com/legend/all",
            params = {"api_key": self.bot.BRAWLHALLA_API_KEY}
        ) as resp:
            data = await resp.json()

        legends = {}
        for legend_data in data:
            name_key = legend_data["legend_name_key"]
            legends[name_key] = legend_data
            if (bio_name := legend_data["bio_name"].lower()) != name_key:
                legends[bio_name] = legend_data

        return legends

