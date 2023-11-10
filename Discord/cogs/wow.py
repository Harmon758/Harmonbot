
from discord.ext import commands

import datetime
import os

import aiohttp

from utilities import checks


BATTLE_NET_CLIENT_ID = BLIZZARD_CLIENT_ID = (
    os.getenv("BATTLE_NET_CLIENT_ID") or os.getenv("BLIZZARD_CLIENT_ID")
)
BATTLE_NET_CLIENT_SECRET = BLIZZARD_CLIENT_SECRET = (
    os.getenv("BATTLE_NET_CLIENT_SECRET") or
    os.getenv("BLIZZARD_CLIENT_SECRET")
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

    # TODO: Subcommands: classes, races

    @wow.command()
    async def character(self, ctx, character: str, *, realm: str):
        '''WIP'''
        async with ctx.bot.aiohttp_session.post(
            "https://oauth.battle.net/token",
            auth = aiohttp.BasicAuth(
                BATTLE_NET_CLIENT_ID, BATTLE_NET_CLIENT_SECRET
            ),
            data = {"grant_type": "client_credentials"}
        ) as resp:
            data = await resp.json()

        access_token = data["access_token"]

        async with ctx.bot.aiohttp_session.get(
            f"https://us.api.blizzard.com/profile/wow/character/{realm}/{character}",
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Battlenet-Namespace": "profile-us"
            }
        ) as resp:
            data = await resp.json()

            if resp.status == 404:
                await ctx.embed_reply(
                    f"{ctx.bot.error_emoji} Error: {data['detail']}"
                )
                return

        await ctx.embed_reply(
            title = data["name"],
            title_url = f"https://worldofwarcraft.com/en-us/character/{data['realm']['slug']}/{data['name']}",
            # thumbnail_url = f"https://render-us.worldofwarcraft.com/character/{data['thumbnail']}",
            # description = f"{data['realm']['name']['en_US']} ({data['battlegroup']})",
            description = data["realm"]["name"]["en_US"],
            fields = [
                ("Level", data["level"]),
                ("Achievement Points", data["achievement_points"]),
                ("Class", data["character_class"]["name"]["en_US"]),
                ("Race", data["race"]["name"]["en_US"]),
                ("Gender", data["gender"]["name"]["en_US"])
            ],
            footer_text = "Last login",
            timestamp = datetime.datetime.utcfromtimestamp(
                data["last_login_timestamp"] / 1000.0
            )
        )
        # TODO: Add faction

    @wow.command()
    async def statistics(self, ctx, character: str, *, realm: str):
        '''WIP'''
        async with ctx.bot.aiohttp_session.post(
            "https://oauth.battle.net/token",
            auth = aiohttp.BasicAuth(
                BATTLE_NET_CLIENT_ID, BATTLE_NET_CLIENT_SECRET
            ),
            data = {"grant_type": "client_credentials"}
        ) as resp:
            data = await resp.json()

        access_token = data["access_token"]

        async with ctx.bot.aiohttp_session.get(
            f"https://us.api.blizzard.com/profile/wow/character/{realm}/{character}/statistics",
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Battlenet-Namespace": "profile-us"
            }
        ) as resp:
            data = await resp.json()

        title_url = f"https://worldofwarcraft.com/en-us/character/{data['character']['realm']['slug']}/{data['name']}/"
        # await ctx.embed_reply(
        #     f"{data['realm']} ({data['battlegroup']})",
        #     title = data["name"], title_url = title_url
        # )

