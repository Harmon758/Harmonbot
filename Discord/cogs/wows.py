
from discord.ext import commands

import datetime

from utilities import checks

async def setup(bot):
	await bot.add_cog(WoWS())

API_URLS = {
	"asia": "https://api.worldofwarships.asia/wows/", 
	"eu": "https://api.worldofwarships.eu/wows/", 
	"na": "https://api.worldofwarships.com/wows/", 
	"ru": "https://api.worldofwarships.ru/wows/"
}

class WoWS(commands.Cog):
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.group(aliases = ["worldofwarships", "world_of_warships"], 
					invoke_without_command = True, case_insensitive = True)
	async def wows(self, ctx):
		'''
		World of Warships
		Realms/Regions: Asia, EU, NA, RU (Default: NA)
		'''
		await ctx.send_help(ctx.command)
	
	@wows.group(invoke_without_command = True, case_insensitive = True)
	async def player(self, ctx, player: str, region: str = "NA"):
		'''Player details'''
		api_url = API_URLS.get(region.lower(), API_URLS["na"])
		params = {"application_id": ctx.bot.WARGAMING_APPLICATION_ID, "search": player, "limit": 1}
		async with ctx.bot.aiohttp_session.get(api_url + "account/list/", params = params) as resp:
			data = await resp.json()
		if data["status"] == "error":
			return await ctx.embed_reply(f":no_entry: Error: {data['error']['message']}")
		if data["status"] != "ok":
			return await ctx.embed_reply(":no_entry: Error")
		if not data["meta"]["count"]:
			return await ctx.embed_reply(":no_entry: Error: Player not found")
		account_id = data["data"][0]["account_id"]
		params = {"application_id": ctx.bot.WARGAMING_APPLICATION_ID, "account_id": account_id}
		async with ctx.bot.aiohttp_session.get(api_url + "account/info/", params = params) as resp:
			data = await resp.json()
		if data["status"] == "error":
			return await ctx.embed_reply(f":no_entry: Error: {data['error']['message']}")
		if data["status"] != "ok":
			return await ctx.embed_reply(":no_entry: Error")
		data = data["data"][str(account_id)]
		# TODO: Handle hidden profile?
		await ctx.embed_reply(title = data["nickname"], 
								fields = (("ID", account_id), ("Account Level", data["leveling_tier"]), 
											("Account XP", f"{data['leveling_points']:,}"), 
											("Battles Fought", data["statistics"]["battles"]), 
											("Miles Travelled", data["statistics"]["distance"])), 
								footer_text = "Account Created", 
								timestamp = datetime.datetime.utcfromtimestamp(data["created_at"]))

