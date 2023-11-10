
from discord.ext import commands

import datetime

from units.battle_net import request_access_token
from utilities import checks


async def setup(bot):
    await bot.add_cog(WoW())

class WoW(commands.Cog):

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.group(
        aliases = ["worldofwarcraft", "world_of_warcraft"],
        case_insensitive = True, invoke_without_command = True
    )
    async def wow(self, ctx):
        '''World of Warcraft'''
        await ctx.send_help(ctx.command)

    # TODO: Subcommands: classes, races

    @wow.command()
    async def character(self, ctx, character: str, *, realm: str):
        '''WIP'''
        access_token = await request_access_token(
            aiohttp_session = ctx.bot.aiohttp_session
        )

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
        access_token = await request_access_token(
            aiohttp_session = ctx.bot.aiohttp_session
        )

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

