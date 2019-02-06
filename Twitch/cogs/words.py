
from twitchio.ext import commands

@commands.cog()
class Words:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command()
	async def audiodefine(self, ctx, word):
		url = f"http://api.wordnik.com:80/v4/word.json/{word}/audio"
		params = {"useCanonical": "false", "limit": 1, "api_key": self.bot.WORDNIK_API_KEY}
		async with self.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if data:
			await ctx.send(f"{data[0]['word'].capitalize()}: {data[0]['fileUrl']}")
		else:
			await ctx.send("Word or audio not found.")
	
	@commands.command()
	async def define(self, ctx, word):
		url = f"http://api.wordnik.com:80/v4/word.json/{word}/definitions"
		params = {"limit": 1, "includeRelated": "false", "useCanonical": "false", "includeTags": "false", 
					"api_key": self.bot.WORDNIK_API_KEY}
		async with self.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if data:
			await ctx.send(data[0]["word"].capitalize() + ": " + data[0]["text"])
		else:
			await ctx.send("Definition not found.")

