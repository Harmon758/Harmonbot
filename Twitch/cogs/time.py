
from twitchio.ext import commands

import datetime
import sys

sys.path.insert(0, "..")
from units.location import get_geocode_data, get_timezone_data, UnitOutputError
sys.path.pop(0)

@commands.cog()
class Time:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command()
	async def time(self, ctx, *, location = ""):
		# TODO: Document
		# TODO: Add ability to reset
		if ctx.author.name == ctx.channel.name and location.lower().startswith(ctx.channel.name + ' '):
			location = location[len(ctx.channel.name) + 1:]
			await self.bot.db.execute(
				"""
				INSERT INTO twitch.timezones (channel, location)
				VALUES ($1, $2)
				ON CONFLICT (channel) DO
				UPDATE SET location = $2
				""", 
				ctx.channel.name, location
			)
			await ctx.send(f"Timezone location set to {location}")
		else:
			if not location or location.lower() == ctx.channel.name:
				location = await self.bot.db.fetchval("SELECT location FROM twitch.timezones WHERE channel = $1", ctx.channel.name)
				if not location:
					await ctx.send(f"Error: Location not specified")
					return
			try:
				geocode_data = await get_geocode_data(location, aiohttp_session = self.bot.aiohttp_session)
				latitude = geocode_data["geometry"]["location"]["lat"]
				longitude = geocode_data["geometry"]["location"]["lng"]
				timezone_data = await get_timezone_data(latitude = latitude, longitude = longitude, 
														aiohttp_session = self.bot.aiohttp_session)
			except UnitOutputError as e:
				await ctx.send(f"Error: {e}")
				return
			location_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(
							seconds = timezone_data["dstOffset"] + timezone_data["rawOffset"])))
			# TODO: Use method for Discord time command
			time_string = location_time.strftime(f"%#I:%M %p on %b. %#d (%a.) in {geocode_data['formatted_address']} (%Z)")
			await ctx.send(f"It is currently {time_string}.")
			# %#I and %#d for removal of leading zero on Windows with native Python executable

