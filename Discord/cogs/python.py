
from discord.ext import commands

from utilities import checks

def setup(bot):
	bot.add_cog(Python())

class Python(commands.Cog):
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.command()
	async def pypi(self, ctx, package: str):
		'''Information about a package on PyPI'''
		url = f"https://pypi.python.org/pypi/{package}/json"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		await ctx.embed_reply(title = data["info"]["name"], title_url = data["info"]["package_url"], 
								description = data["info"]["summary"], fields = (("Version", data["info"]["version"]),))

