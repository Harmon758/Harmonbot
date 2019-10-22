
from twitchio.ext import commands

import datetime
import sys

import dateutil.parser

sys.path.insert(0, "..")
from units.time import duration_to_string
sys.path.pop(0)

@commands.cog()
class Twitch:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command()
	async def averagefps(self, ctx):
		users = await self.bot.get_users(ctx.channel.name)
		url = "https://api.twitch.tv/kraken/streams/" + users[0].id
		params = {"client_id": self.bot.http.client_id}
		headers = {"Accept": "application/vnd.twitchtv.v5+json"}
		async with self.bot.aiohttp_session.get(url, params = params, headers = headers) as resp:
			data = await resp.json()
		stream = data.get("stream")
		if not stream:
			return await ctx.send("Average FPS not found.")
		await ctx.send(f"Average FPS: {stream['average_fps']}")
	
	@commands.command(aliases = ("followed", "howlong"))
	async def followage(self, ctx):
		users = await self.bot.get_users(ctx.channel.name)
		follow = await self.bot.get_follow(ctx.author.id, users[0].id)
		if not follow:
			return await ctx.send(f"{ctx.author.name.capitalize()}, you haven't followed yet!")
		followed_at = dateutil.parser.parse(follow["followed_at"])
		ago = duration_to_string(datetime.datetime.now(datetime.timezone.utc) - followed_at)
		await ctx.send(f"{ctx.author.name.capitalize()} followed on {followed_at.strftime('%B %#d %Y')}, {ago} ago")
		# %#d for removal of leading zero on Windows with native Python executable
	
	@commands.command()
	async def followers(self, ctx):
		# Waiting for Get Users endpoint to include follower count
		# https://discuss.dev.twitch.tv/t/new-twitch-api-get-total-followers-count/12489
		# https://discuss.dev.twitch.tv/t/regarding-data-in-kraken-not-present-in-new-twitch-api/13045
		# https://discuss.dev.twitch.tv/t/helix-get-user-missing-total-followers/15449
		users = await self.bot.get_users(ctx.channel.name)
		count = await self.bot.get_followers(users[0].id, count = True)
		await ctx.send(f"There are currently {count:,} people following {ctx.channel.name.capitalize()}.")
	
	@commands.command(aliases = ("shout",))
	async def shoutout(self, ctx, channel = None):
		if not channel:
			return await ctx.send('\N{SPEAKING HEAD IN SILHOUETTE}')
		await ctx.send("https://www.twitch.tv/" + channel)
	
	@commands.command()
	async def title(self, ctx):
		stream = await ctx.get_stream()
		if not stream or not stream.get("title"):
			return await ctx.send("Title not found.")
		await ctx.send(stream["title"])
	
	@commands.command()
	async def uptime(self, ctx):
		stream = await ctx.get_stream()
		if not stream:
			return await ctx.send("Uptime not found.")
		duration = datetime.datetime.now(datetime.timezone.utc) - dateutil.parser.parse(stream["started_at"])
		await ctx.send(duration_to_string(duration))
	
	@commands.command()
	async def viewers(self, ctx):
		stream = await ctx.get_stream()
		if not stream:
			return await ctx.send("Stream is offline.")
		await ctx.send(f"{stream['viewer_count']} viewers watching now.")
		# TODO: Handle single viewer
		# TODO: Handle no viewers: No one is watching right now :-/
	
	# TODO: views command

