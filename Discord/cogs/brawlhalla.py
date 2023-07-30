
from discord import app_commands
from discord.ext import commands

import sys
from typing import Optional

from utilities import checks
from utilities.converters import SteamID64

sys.path.insert(0, "..")
from units.cache import async_cache
sys.path.pop(0)


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

    @brawlhalla.command()
    async def player(self, ctx, name: SteamID64, legend: Optional[str] = None):
        """
        Show information about a Brawlhalla player

        Parameters
        ----------
        name
            Name of player to show information about
        legend
            Specific legend to show player information about
        """
        brawlhalla_id = await self.brawlhalla_id(name)
        async with self.bot.aiohttp_session.get(
            f"https://api.brawlhalla.com/player/{brawlhalla_id}/stats",
            params = {"api_key": self.bot.BRAWLHALLA_API_KEY}
        ) as resp:
            stats = await resp.json()

        if legend:
            for legend_stats in stats["legends"]:
                if legend_stats["legend_name_key"] == legend.lower():
                    await ctx.embed_reply(
                        title = stats["name"],
                        fields = (
                            ("Level", legend_stats["level"]),
                        )
                    )
                    return
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} {legend} information for {stats['name']} not found"
            )
        else:
            await ctx.embed_reply(
                title = stats["name"],
                fields = (
                    ("Level", stats["level"]),
                    ("XP", format(stats["xp"], ',')),
                    (
                        "Wins",
                        f"{stats['wins']} / {stats['games']} "
                        f"({stats['wins'] / stats['games'] * 100:.2f}%)"
                    ),
                    ("Clan", stats["clan"]["clan_name"])
                )
            )

    @async_cache
    async def brawlhalla_id(self, steam_id):
        async with self.bot.aiohttp_session.get(
            "https://api.brawlhalla.com/search",
            params = {
                "steamid": steam_id, "api_key": self.bot.BRAWLHALLA_API_KEY
            }
        ) as resp:
            return (await resp.json())["brawlhalla_id"]

