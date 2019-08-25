
from discord.ext import commands

from utilities import checks

def setup(bot):
	bot.add_cog(DotA())

class DotA(commands.Cog):
	
	def cog_check(self, ctx):
		return checks.not_forbidden_predicate(ctx)
	
	@commands.group(aliases = ["dota2"], invoke_without_command = True, case_insensitive = True)
	async def dota(self, ctx):
		'''Defense of the Ancients 2'''
		await ctx.send_help(ctx.command)
	
	# TODO: Add dota buff subcommand alias
	@commands.command()
	async def dotabuff(self, ctx, account : str):
		'''Get Dotabuff link'''
		try:
			url = f"https://www.dotabuff.com/players/{int(account) - 76561197960265728}"
		except ValueError:
			url = "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/"
			params = {"key": ctx.bot.STEAM_WEB_API_KEY, "vanityurl": account}
			async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			url = f"https://www.dotabuff.com/players/{int(data['response']['steamid']) - 76561197960265728}"
		await ctx.embed_reply(title = f"{account}'s Dotabuff profile", title_url = url)

