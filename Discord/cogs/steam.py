
import discord
from discord.ext import commands

from utilities import checks
from utilities.converters import SteamProfile


def setup(bot):
    bot.add_cog(Steam())

class Steam(commands.Cog):

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.group(case_insensitive = True, invoke_without_command = True)
    async def steam(self, ctx):
        '''Steam Information'''
        await ctx.send_help(ctx.command)

    # https://developer.valvesoftware.com/wiki/Steam_Web_API
    # TODO: profile command, merge gameinfo command into?, games subcommand?, games recent subcommand?
    # TODO: profile friends?, achievements (with optional game parameter) commands
    # TODO: game parent command, alias app, make id + info subcommands
    # TODO: game news, achievements?, stats commands
    # TODO: alias steam as info subcommand?

    @steam.command()
    async def appid(self, ctx, *, app: str):
        '''Get the AppID'''
        url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/"
        async with ctx.bot.aiohttp_session.get(url) as resp:
            data = await resp.json()
        apps = data["applist"]["apps"]
        appid = 0
        for app_info in apps:
            if app_info["name"].lower() == app.lower():
                appid = app_info["appid"]
                break
        await ctx.embed_reply(appid)

    @steam.command(aliases = ["game_count"])
    async def gamecount(self, ctx, account: SteamProfile):
        '''Find how many games someone has'''
        url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
        params = {
            "key": ctx.bot.STEAM_WEB_API_KEY, "steamid": account["steamid"]
        }
        async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
            data = await resp.json()
        gamecount = data["response"]["game_count"]
        await ctx.embed_reply(
            f"[{account['personaname']}]({account['profileurl']}) has {gamecount} games",
            thumbnail_url = account["avatarfull"]
        )

    @steam.command(aliases = ["game_info"])
    async def gameinfo(self, ctx, *, game: str):
        '''Information about a game'''
        url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/"
        async with ctx.bot.aiohttp_session.get(url) as resp:
            data = await resp.json()

        if not (
            app := discord.utils.find(
                lambda app: app["name"].lower() == game.lower(),
                data["applist"]["apps"]
            )
        ):
            await ctx.embed_reply(f"{ctx.bot.error_emoji} Game not found")
            return

        appid = str(app["appid"])

        url = "http://store.steampowered.com/api/appdetails/"
        params = {"appids": appid}
        async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
            data = await resp.json()

        data = data[appid]["data"]
        await ctx.embed_reply(
            title = data["name"], title_url = data["website"],
            description = data["short_description"],
            fields = (
                ("Release Date", data["release_date"]["date"]),
                ("Free", "Yes" if data["is_free"] else "No"),
                ("App ID", data["steam_appid"])
            ), image_url = data["header_image"]
        )

    @steam.command(aliases = ["launch"])
    async def run(self, ctx, *, game: str):
        '''Generate a steam link to launch a game'''
        url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/"
        async with ctx.bot.aiohttp_session.get(url) as resp:
            data = await resp.json()

        if not (
            app := discord.utils.find(
                lambda app: app["name"].lower() == game.lower(),
                data["applist"]["apps"]
            )
        ):
            await ctx.embed_reply(f"{ctx.bot.error_emoji} Game not found")
            return

        await ctx.embed_reply(
            title = f"Launch {app['name']}",
            description = f"steam://run/{app['appid']}"
        )

