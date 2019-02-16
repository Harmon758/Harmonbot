
from twitchio.ext import commands

@commands.cog()
class Twitch:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command()
	async def followers(self, ctx):
		url = f"https://api.twitch.tv/kraken/channels/{ctx.channel.name}/follows"
		params = {"client_id": self.bot.http.client_id}
		async with self.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		await ctx.send(f"There are currently {data['_total']} people following {ctx.channel.name.capitalize()}.")

