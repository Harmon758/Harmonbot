
from twitchio.ext import commands

import pyowm

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
	
	@commands.command()
	async def weather(self, ctx, *, location = ""):
		if not location or location.lower() == ctx.channel.name:
			location = await self.bot.db.fetchval("SELECT location FROM twitch.locations WHERE channel = $1", ctx.channel.name)
			if not location:
				return await ctx.send(f"Error: Location not specified")
		try:
			observation = self.bot.owm_client.weather_at_place(location)
		except (pyowm.exceptions.api_response_error.NotFoundError, 
				pyowm.exceptions.api_call_error.BadGatewayError) as e:
			# TODO: Catch base exceptions?
			return await ctx.send(f"Error: {e}")
		location = observation.get_location()
		weather = observation.get_weather()
		condition = weather.get_status()
		temperature_c = weather.get_temperature(unit = "celsius")["temp"]
		temperature_f = weather.get_temperature(unit = "fahrenheit")["temp"]
		await ctx.send(f"{location.get_name()}, {location.get_country()}: {condition} and {temperature_c}°C/{temperature_f}°F")

