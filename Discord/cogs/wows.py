
from discord.ext import commands

import datetime

from utilities import checks

def setup(bot):
	bot.add_cog(WoWS(bot))

class WoWS(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.api_urls = {"asia": "https://api.worldofwarships.asia/wows/", 
							"eu": "https://api.worldofwarships.eu/wows/", 
							"na": "https://api.worldofwarships.com/wows/", 
							"ru": "https://api.worldofwarships.ru/wows/"}
	
	@commands.group(aliases = ["worldofwarships", "world_of_warships"], 
					invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def wows(self, ctx):
		'''
		World of Warships
		Realms/Regions: Asia, EU, NA, RU (Default: NA)
		'''
		await ctx.send_help(ctx.command)
	
	@wows.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def player(self, ctx, player : str, region : str = "NA"):
		'''Player details'''
		api_url = self.api_urls.get(region.lower(), "na")
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
		# TODO: handle hidden profile?
		fields = [("ID", account_id), ("Account Level", data["leveling_tier"])]
		fields.append(("Account XP", f"{data['leveling_points']:,}"))
		fields.append(("Battles Fought", data["statistics"]["battles"]))
		fields.append(("Miles Travelled", data["statistics"]["distance"]))
		created_at = datetime.datetime.utcfromtimestamp(data["created_at"])
		await ctx.embed_reply(title = data["nickname"], fields = fields, 
								footer_text = "Account Created", timestamp = created_at)

