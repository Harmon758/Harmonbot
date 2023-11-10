
from discord.ext import commands

import datetime
import os

from utilities import checks


BATTLE_NET_API_KEY = BLIZZARD_API_KEY = (
    os.getenv("BATTLE_NET_API_KEY") or os.getenv("BLIZZARD_API_KEY")
)


async def setup(bot):
    await bot.add_cog(WoW())

class WoW(commands.Cog):

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.group(
        aliases = ["worldofwarcraft", "world_of_warcraft"],
        invoke_without_command = True, case_insensitive = True
    )
    async def wow(self, ctx):
        '''World of Warcraft'''
        await ctx.send_help(ctx.command)

    @wow.command()
    async def character(self, ctx, character: str, *, realm: str):
        '''WIP'''
        async with ctx.bot.aiohttp_session.get(
            "https://us.api.battle.net/wow/data/character/classes",
            params = {"apikey": BATTLE_NET_API_KEY}
        ) as resp:
            data = await resp.json()

        classes = {
            wow_class["id"]: wow_class["name"] for wow_class in data["classes"]
        }

        async with ctx.bot.aiohttp_session.get(
            "https://us.api.battle.net/wow/data/character/races",
            params = {"apikey": BATTLE_NET_API_KEY}
        ) as resp:
            data = await resp.json()

        races = {
            wow_race["id"]: wow_race["name"] for wow_race in data["races"]
        }

        # TODO: Add side/faction?

        async with ctx.bot.aiohttp_session.get(
            f"https://us.api.battle.net/wow/character/{realm}/{character}",
            params = {"apikey": BATTLE_NET_API_KEY}
        ) as resp:
            data = await resp.json()
            if resp.status != 200:
                await ctx.embed_reply(
                    f"{ctx.bot.error_emoji} Error: {data['reason']}"
                )
                return

        await ctx.embed_reply(
            title = data["name"],
            title_url = f"https://worldofwarcraft.com/en-us/character/{data['realm'].replace(' ', '-')}/{data['name']}",
            thumbnail_url = f"https://render-us.worldofwarcraft.com/character/{data['thumbnail']}",
            description = f"{data['realm']} ({data['battlegroup']})",
            fields = [
                ("Level", data["level"]),
                ("Achievement Points", data["achievementPoints"]),
                ("Class", f"{classes.get(data['class'], 'Unknown')}"),
                ("Race", races.get(data["race"], "Unknown")),
                (
                    "Gender",
                    {0: "Male", 1: "Female"}.get(data["gender"], "Unknown")
                )
            ],
            footer_text = "Last seen",
            timestamp = datetime.datetime.utcfromtimestamp(
                data["lastModified"] / 1000.0
            )
        )
        # TODO: faction and total honorable kills?

    @wow.command()
    async def statistics(self, ctx, character: str, *, realm: str):
        '''WIP'''
        async with ctx.bot.aiohttp_session.get(
            f"https://us.api.battle.net/wow/character/{realm}/{character}",
            params = {
                "fields": "statistics", "apikey": BATTLE_NET_API_KEY
            }
        ) as resp:
            data = await resp.json()
        statistics = data["statistics"]
        title_url = f"https://worldofwarcraft.com/en-us/character/{data['realm'].replace(' ', '-')}/{data['name']}/"
        # await ctx.embed_reply(
        #     f"{data['realm']} ({data['battlegroup']})",
        #     title = data["name"], title_url = title_url
        # )

