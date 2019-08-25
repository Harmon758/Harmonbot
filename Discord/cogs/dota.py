
from discord.ext import commands

from utilities import checks

def setup(bot):
	bot.add_cog(DotA())

class DotA(commands.Cog):
	
	def cog_check(self, ctx):
		return checks.not_forbidden_predicate(ctx)
	
	# TODO: Move to converters file
	class SteamAccount(commands.Converter):
		async def convert(self, ctx, argument):
			try:
				return int(argument) - 76561197960265728
			except ValueError:
				url = "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/"
				params = {"key": ctx.bot.STEAM_WEB_API_KEY, "vanityurl": argument}
				async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
					# TODO: Handle 429?
					data = await resp.json()
				return int(data['response']['steamid']) - 76561197960265728
	
	@commands.group(aliases = ["dota2"], invoke_without_command = True, case_insensitive = True)
	async def dota(self, ctx):
		'''Defense of the Ancients 2'''
		await ctx.send_help(ctx.command)
	
	# TODO: Add dota buff subcommand alias
	@commands.command()
	async def dotabuff(self, ctx, account: SteamAccount):
		'''Get Dotabuff link'''
		await ctx.embed_reply(f"https://www.dotabuff.com/players/{account}")

