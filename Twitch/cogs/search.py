
from twitchio.ext import commands

@commands.cog()
class Search:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command()
	async def google(self, ctx, *search):
		await ctx.send("https://google.com/search?q=" + '+'.join(search))

