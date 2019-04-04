
from twitchio.ext import commands

@commands.cog()
class Location:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command()
	async def location(self, ctx, *, location = ""):
		# TODO: Document
		# TODO: Add ability to reset
		# TODO: Add custom location ability for any viewer
		if ctx.author.name == ctx.channel.name and location:
			await self.bot.db.execute(
				"""
				INSERT INTO twitch.locations (channel, location)
				VALUES ($1, $2)
				ON CONFLICT (channel) DO
				UPDATE SET location = $2
				""", 
				ctx.channel.name, location
			)
			return await ctx.send(f"Location set to {location}")
		location = await self.bot.db.fetchval("SELECT location FROM twitch.locations WHERE channel = $1", ctx.channel.name)
		if not location:
			return await ctx.send(f"Error: Location not specified")
		await ctx.send(location)

