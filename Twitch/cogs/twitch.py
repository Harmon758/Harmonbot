
from twitchio.ext import commands

@commands.cog()
class Twitch:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command()
	async def followers(self, ctx):
		# Waiting for Get Users endpoint to include follower count
		# https://discuss.dev.twitch.tv/t/new-twitch-api-get-total-followers-count/12489
		# https://discuss.dev.twitch.tv/t/regarding-data-in-kraken-not-present-in-new-twitch-api/13045
		# https://discuss.dev.twitch.tv/t/helix-get-user-missing-total-followers/15449
		users = await self.bot.get_users(ctx.channel.name)
		count = await self.bot.get_followers(users[0].id, count = True)
		await ctx.send(f"There are currently {count} people following {ctx.channel.name.capitalize()}.")
	
	@commands.command(aliases = ("shout",))
	async def shoutout(self, ctx, channel = None):
		if not channel:
			return await ctx.send('\N{SPEAKING HEAD IN SILHOUETTE}')
		await ctx.send("https://www.twitch.tv/" + channel)
	
	# TODO: views command

