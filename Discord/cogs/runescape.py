
from discord.ext import commands

import collections
import csv
import sys

from utilities import checks
from utilities.views import WikiArticlesView

sys.path.insert(0, "..")
from units.runescape import get_ge_data, get_item_id, get_monster_data
from units.wikis import search_wiki
sys.path.pop(0)

async def setup(bot):
    await bot.add_cog(RuneScape(bot))

class RuneScape(commands.Cog):
    """RuneScape"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.hybrid_group(aliases = ["rs"], case_insensitive = True)
    async def runescape(self, ctx):
        """RuneScape"""
        await ctx.send_help(ctx.command)

    @runescape.command(aliases = ["grandexchange", "grand_exchange"])
    async def ge(self, ctx, *, item: str):
        """
        Look up an item on the Grand Exchange

        Parameters
        ----------
        item
            Item to look up on the Grand Exchange
        """
        await ctx.defer()
        try:
            item_id = await get_item_id(
                item, aiohttp_session = ctx.bot.aiohttp_session
            )
            data = await get_ge_data(
                item, item_id = item_id,
                aiohttp_session = ctx.bot.aiohttp_session
            )
        except ValueError as e:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")
            return
        await ctx.embed_reply(
            title = data["name"],
            title_url = f"https://services.runescape.com/m=itemdb_rs/viewitem?obj={item_id}",
            thumbnail_url = data["icon_large"],
            description = data["description"],
            fields = (
                ("Current", data["current"]["price"]),
                ("Today", data["today"]["price"]),
                ("30 Day", data["day30"]["change"]),
                ("90 Day", data["day90"]["change"]),
                ("180 Day", data["day180"]["change"]),
                ("Category", data["type"])
            )
        )
        # TODO: Include id?, members

    @runescape.command(aliases = ["bestiary"], with_app_command = False)
    async def monster(self, ctx, *, monster: str):
        '''Bestiary'''
        try:
            data = await get_monster_data(
                monster, aiohttp_session = ctx.bot.aiohttp_session
            )
        except ValueError as e:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")
            return
        await ctx.embed_reply(
            title = data["name"],
            description = data["description"],
            fields = (
                ("Level", data["level"]), ("Weakness", data["weakness"]),
                ("XP/Kill", data["xp"]), ("Lifepoints", data["lifepoints"]),
                ("Members", "Yes" if data["members"] else "No"),
                ("Aggressive", "Yes" if data["aggressive"] else "No")
            )
        )
        # add other? - https://runescape.wiki/w/RuneScape_Bestiary#beastData

    @runescape.command(
        aliases = ["levels", "level", "xp", "ranks", "rank"],
        with_app_command = False
    )
    async def stats(self, ctx, *, username: str):
        """Stats"""
        async with ctx.bot.aiohttp_session.get(
            "http://services.runescape.com/m=hiscore/index_lite.ws",
            params = {"player": username}
        ) as resp:
            if resp.status == 404:
                await ctx.embed_reply(
                    f"{ctx.bot.error_emoji} Player not found"
                )
                return
            data = await resp.text()
        data = csv.DictReader(
            data.splitlines(), fieldnames = ("rank", "level", "xp")
        )
        stats = collections.OrderedDict()
        stats_names = (
            "Overall", "Attack", "Defence", "Strength", "Constitution",
            "Ranged", "Prayer", "Magic", "Cooking", "Woodcutting", "Fletching",
            "Fishing", "Firemaking", "Crafting", "Smithing", "Mining",
            "Herblore", "Agility", "Thieving", "Slayer", "Farming",
            "Runecrafting", "Hunter", "Construction", "Summoning",
            "Dungeoneering", "Divination", "Invention"
        )
        for stat in stats_names:
            stats[stat] = next(data)

        output = [f"`{name}`" for name in stats_names]
        fields = [("Skill", '\n'.join(output))]

        max_length = max(
            len(f"{int(values['rank']):,d}") for values in stats.values()
        )
        output = [
            f"""`| {f"{int(values['rank']):,d}".rjust(max_length)}`"""
            for values in stats.values()
        ]
        fields.append(("| Rank", '\n'.join(output)))

        max_length = max(
            len(f"{int(values['xp']):,d}") for values in stats.values()
        )
        output = [
            f"""`| {values["level"].rjust(4).ljust(5)}| {f"{int(values['xp']):,d}".rjust(max_length)}`"""
            for values in stats.values()
        ]
        fields.append(("| Level | Experience", '\n'.join(output)))

        await ctx.embed_reply(
            title = username,
            title_url = (
                "http://services.runescape.com/m=hiscore/compare?user1=" +
                username.replace(' ', '+')
            ),
            fields = fields
        )

    @runescape.command()
    async def wiki(self, ctx, *, query):
        """
        Search for an article on The RuneScape Wiki

        Parameters
        ----------
        query
            Search query
        """
        await ctx.defer()
        try:
            articles = await search_wiki(
                "https://runescape.wiki/", query,
                aiohttp_session = ctx.bot.aiohttp_session
            )
        except ValueError as e:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} {e}")
            return
        
        view = WikiArticlesView(articles)
        message = await ctx.reply(
            "",
            embed = view.initial_embed(ctx),
            view = view
        )
        
        if ctx.interaction:
            # Fetch Message, as InteractionMessage token expires after 15 min.
            message = await message.fetch()
        view.message = message
        ctx.bot.views.append(view)

    @runescape.command(hidden = True, with_app_command = False)
    async def zybez(self, ctx):
        """
        This command has been deprecated
        Zybez RuneScape Community was shut down on September 17th, 2018
        https://forums.zybez.net/topic/1783583-exit-post-the-end/
        """
        # Previously used
        # https://forums.zybez.net/runescape-2007-prices/api/?info
        await ctx.embed_reply(
            "See https://forums.zybez.net/topic/1783583-exit-post-the-end/"
        )

