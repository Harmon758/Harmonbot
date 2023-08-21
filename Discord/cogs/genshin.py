
from discord import app_commands
from discord.ext import commands

import calendar
import sys

from utilities import checks

sys.path.insert(0, "..")
from units.genshin_impact import (
    API_BASE_URL, get_character, get_character_images, get_characters
)
sys.path.pop(0)


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

    @genshin_impact.command()
    async def character(self, ctx, name: str):
        """
        Show information about a Genshin Impact character

        Parameters
        ----------
        name
            Name of character to show information about
        """
        await ctx.defer()

        try:
            character = await get_character(
                name, aiohttp_session = ctx.bot.aiohttp_session
            )
        except ValueError as e:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} {e}")
            return

        images = await get_character_images(
            name, aiohttp_session = ctx.bot.aiohttp_session
        )

        # birth year is always 0000
        # pylint: disable-next=unused-variable
        birth_year, birth_month, birth_day = map(
            int, character.birthday.split('-')
        )

        await ctx.embed_reply(
            title = character.name,
            description = character.description,
            thumbnail_url = (
                f"{API_BASE_URL}/characters/{name.lower().replace(' ', '-')}/icon"
                if "icon" in images else None
            ),
            fields = (
                ("Title", character.title),
                ("Vision", character.vision),
                ("Weapon", character.weapon),
                ("Nation", character.nation),
                ("Affiliation", character.affiliation),
                ("Rarity", '\N{WHITE MEDIUM STAR}' * character.rarity),
                ("Constellation", character.constellation),
                (
                    "Birthday",
                    f"{calendar.month_name[birth_month]} {birth_day}"
                )
            )
            # TODO: combat talents, passive talents, constellations
            # TODO: other images
        )

    @character.autocomplete(name = "name")
    async def character_autocomplete(self, interaction, current):
        current = current.lower()

        characters = await get_characters(
            aiohttp_session = interaction.client.aiohttp_session
        )
        characters = [character.replace('-', ' ') for character in characters]

        primary_matches = set()
        secondary_matches = set()

        for character in characters:
            if character.startswith(current):
                primary_matches.add(character)
            elif current in character:
                secondary_matches.add(character)

        matches = sorted(primary_matches) + sorted(secondary_matches)

        return [
            app_commands.Choice(name = match.title(), value = match)
            for match in matches[:25]
        ]

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

