
from discord.ext import commands

class Maptype(commands.Converter):
	
	'''
	For Google Maps Static API parameter
	https://developers.google.com/maps/documentation/maps-static/dev-guide
	'''

	async def convert(self, ctx, argument):
		if argument not in ("roadmap", "satellite", "hybrid", "terrain"):
			raise commands.BadArgument("Invalid map type")
		return argument

# https://developer.valvesoftware.com/wiki/SteamID
STEAM_ID_64_BASE = int("0x110000100000000", 16)  # Assuming Public Individual user account

# TODO: Use for steam gamecount command?
class SteamAccount(commands.Converter):
	async def convert(self, ctx, argument):
		try:
			return int(argument) - STEAM_ID_64_BASE
		except ValueError:
			url = "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/"
			params = {"key": ctx.bot.STEAM_WEB_API_KEY, "vanityurl": argument}
			async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
				# TODO: Handle 429?
				data = await resp.json()
			if data["response"]["success"] == 42:  # NoMatch, https://partner.steamgames.com/doc/api/steam_api#EResult
				raise commands.BadArgument("Account not found")
			return int(data['response']['steamid']) - STEAM_ID_64_BASE

