
from discord.ext import commands

import clients
from utilities import checks

def setup(bot):
	bot.add_cog(Duelyst(bot))

class Duelyst:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def duelyst(self, ctx):
		'''Duelyst'''
		await ctx.invoke(ctx.bot.get_command("help"), ctx.invoked_with)
	
	@duelyst.group()
	@checks.not_forbidden()
	async def card(self, ctx, *, name : str):
		'''Details of a specific card'''
		async with clients.aiohttp_session.get(
		"https://duelyststats.info/scripts/carddata/get.php?cardName=" + name) as resp:
			data = await resp.text()
		await ctx.embed_reply(data)
	
	@card.command()
	@checks.not_forbidden()
	async def card_random(self, ctx):
		'''Details of a random card'''
		async with clients.aiohttp_session.get(
		"https://duelyststats.info/scripts/carddata/get.php?random=1") as resp:
			data = await resp.text()
		await ctx.embed_reply(data)

