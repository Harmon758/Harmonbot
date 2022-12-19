
import discord
from discord.ext import commands

import contextlib
import difflib
import json

from utilities import checks


async def setup(bot):
    await bot.add_cog(LoR(bot))


class LoR(commands.Cog):

    """Legends of Runeterra"""

    def __init__(self, bot):
        self.cards = {}
        for set_bundle in (
            "set1-en_us", "set2-en_us", "set3-en_us", "set4-en_us",
            "set5-en_us", "set6-en_us", "set6cde-en_us"
        ):
            with contextlib.suppress(FileNotFoundError):
                with open(
                    f"{bot.data_path}/lor/{set_bundle}/en_us/data/{set_bundle}.json",
                    'r',
                    encoding = "UTF-8"
                ) as set_bundle_file:
                    data = json.load(set_bundle_file)

                for card in data:
                    self.cards[card["name"]] = (
                        self.cards.get(card["name"], []) + [card]
                    )

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.hybrid_group(case_insensitive = True)
    async def lor(self, ctx):
        """Legends of Runeterra"""
        await ctx.send_help(ctx.command)

    @lor.command()
    async def card(self, ctx, *, name: str):
        """
        Show a specified Legends of Runeterra card

        Parameters
        ----------
        name
            Name of card to show
        """
        close_match = difflib.get_close_matches(name, self.cards, n = 1)

        if not close_match:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} Card not found")
            return

        cards = self.cards[close_match[0]]

        await ctx.embed_reply(
            title = cards[0]["name"],
            image_url = cards[0]["assets"][0]["gameAbsolutePath"],
            footer_text = None,
            embeds = [
                discord.Embed(color = ctx.bot.bot_color).set_image(
                    url = card_data["assets"][0]["gameAbsolutePath"]
                ) for card_data in cards[1:]
            ]  # TODO: Paginate with show all button?
        )
        # TODO: Use ["assets"][0]["fullAbsolutePath"] ?

    # TODO: Random card?

