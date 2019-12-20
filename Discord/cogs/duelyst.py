
from discord.ext import commands

from utilities import checks

def setup(bot):
	bot.add_cog(Duelyst(bot))

class Duelyst(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	async def duelyst(self, ctx):
		'''Duelyst'''
		await ctx.send_help(ctx.command)
	
	@duelyst.group(case_insensitive = True)
	async def card(self, ctx, *, name: str):
		'''Details of a specific card'''
		url = "https://duelyststats.info/scripts/carddata/get.php"
		params = {"cardName": name}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.text()
		await ctx.embed_reply(data)
	
	@card.command()
	async def card_random(self, ctx):
		'''Details of a random card'''
		url = "https://duelyststats.info/scripts/carddata/get.php"
		params = {"random": 1}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.text()
		await ctx.embed_reply(data)

