
from discord.ext import commands


# https://developer.valvesoftware.com/wiki/SteamID
STEAM_ID_64_BASE = int("0x110000100000000", 16)  # Assuming Public Individual user account

class SteamID32(commands.Converter):
	async def convert(self, ctx, argument):
		return await SteamID64().convert(ctx, argument) - STEAM_ID_64_BASE

class SteamID64(commands.Converter):
	async def convert(self, ctx, argument):
		try:
			return int(argument)
		except ValueError:
			url = "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/"
			params = {"vanityurl": argument, "key": ctx.bot.STEAM_WEB_API_KEY}
			async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
				# TODO: Handle 429?
				data = await resp.json()
			if data["response"]["success"] == 42:  # NoMatch, https://partner.steamgames.com/doc/api/steam_api#EResult
				raise commands.BadArgument("Account not found")
			return int(data['response']['steamid'])

class SteamProfile(commands.Converter):
	async def convert(self, ctx, argument):
		async with ctx.bot.aiohttp_session.get(
			"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/",
			params = {
				"steamids": await SteamID64().convert(ctx, argument),
				"key": ctx.bot.STEAM_WEB_API_KEY
			}
		) as resp:
			return (await resp.json())["response"]["players"][0]

