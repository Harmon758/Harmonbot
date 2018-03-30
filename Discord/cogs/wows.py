
from discord.ext import commands

import datetime

import clients
import credentials
from utilities import checks

def setup(bot):
	bot.add_cog(WoWS(bot))

class WoWS:
	
	def __init__(self, bot):
		self.bot = bot
		self.api_urls = {"asia": "https://api.worldofwarships.asia/wows/", "eu": "https://api.worldofwarships.eu/wows/", "na": "https://api.worldofwarships.com/wows/", "ru": "https://api.worldofwarships.ru/wows/"}
	
	@commands.group(aliases = ["worldofwarships", "world_of_warships"], invoke_without_command = True)
	@checks.not_forbidden()
	async def wows(self, ctx):
		'''
		World of Warships
		Realms/Regions: Asia, EU, NA, RU (Default: NA)
		'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	@wows.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def player(self, ctx, player : str, region : str = "NA"):
		'''Player details'''
		api_url = self.api_urls.get(region.lower(), "na")
		async with clients.aiohttp_session.get(api_url + "account/list/", params = {"application_id": credentials.wargaming_application_id, "search": player, "limit": 1}) as resp:
			data = await resp.json()
		if data["status"] == "error":
			await ctx.embed_reply(":no_entry: Error: {}".format(data["error"]["message"]))
			return
		elif data["status"] != "ok":
			await ctx.embed_reply(":no_entry: Error")
			return
		account_id = data["data"][0]["account_id"]
		async with clients.aiohttp_session.get(api_url + "account/info/", params = {"application_id": credentials.wargaming_application_id, "account_id": account_id}) as resp:
			data = await resp.json()
		if data["status"] == "error":
			await ctx.embed_reply(":no_entry: Error: {}".format(data["error"]["message"]))
			return
		elif data["status"] != "ok":
			await ctx.embed_reply(":no_entry: Error")
			return
		data = data["data"][str(account_id)]
		# TODO: handle hidden profile?
		await ctx.embed_reply(title = data["nickname"], fields = (("ID", account_id),("Account Level", data["leveling_tier"]), ("Account XP", "{:,}".format(data["leveling_points"])), ("Battles Fought", data["statistics"]["battles"]), ("Miles Travelled", data["statistics"]["distance"]), ("Account Created", datetime.datetime.utcfromtimestamp(data["created_at"]).strftime("%Y-%m-%d @ %I:%M:%S %p (UTC)"))))
		

