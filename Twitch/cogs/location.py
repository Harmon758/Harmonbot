
from twitchio.ext import commands

import datetime
import sys

import pyowm

sys.path.insert(0, "..")
from units.location import wind_degrees_to_direction
sys.path.pop(0)

@commands.cog()
class Location:
	
	def __init__(self, bot):
		self.bot = bot
	
	# TODO: almanac? - record highs and lows
	#       format: KTUL Airport: Normal High: 85°F/29°C, Normal Low: 64°F/17°C | Record High: 106°F/41°C in 1911, Record Low: 50°F/10°C in 1998
	#       error formats: Location Not Found. Try location near an airport.
	#                      {Location} Found. No data provided.
	# TODO: alert(s)? - weather alerts in area
	#       format: New York City: 2 Alerts: Winter Weather Advisory till 2:00 AM EST on March 04, 2015 | Winter Weather Advisory till 2:00 AM EST on March 04, 2015 | Use * !alertinfo * for alert details
	#               New York City: No Alerts
	# TODO: alert(s)info? - detailed report of alerts in area
	#       format: Jefferson City, Missouri: 1 Alerts | * Winter Weather Advisory * from 3:12 PM CST on December 17, 2014 till 10:00 AM CST on December 18, 2014 ...Winter Weather Advisory remains in effect from midnight tonight to 10 am CST Thursday... * timing...snow will spread across the area tonight and continue through mid-morning on Thursday. * Accumulations...1 to 2 inches of snow. * Winds...east 5 mph or less. * Impacts...the wintry precipitation will result in hazardous travel conditions on bridges...overpasses...and untreated roads. Parking lots and sidewalks will become slippery as well. Precautionary/preparedness actions... A Winter Weather Advisory is issued for a variety of winter weather conditions...such as snow...blowing snow...sleet...or freezing drizzle and rain. It only takes a small amount of wintry precipitation to make roads...bridges...sidewalks...and parking lots icy and dangerous. It is often difficult to tell when ice begins to form...so do not be caught off guard.
	#               Jefferson City, Missouri: No Alerts
	
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
	async def forecast(self, ctx, *, location = ""):
		# TODO: Detailed forecast option?
		if not location or location.lower() == ctx.channel.name:
			location = await self.bot.db.fetchval("SELECT location FROM twitch.locations WHERE channel = $1", ctx.channel.name)
			if not location:
				return await ctx.send(f"Error: Location not specified")
		try:
			forecaster = self.bot.owm_client.daily_forecast(location)
		except (pyowm.exceptions.api_response_error.NotFoundError, 
				pyowm.exceptions.api_call_error.BadGatewayError) as e:
			# TODO: Catch base exceptions?
			return await ctx.send(f"Error: {e}")
		forecast = forecaster.get_forecast()
		location = forecast.get_location()
		output = f"{location.get_name()}, {location.get_country()}"
		for weather in forecast:
			date = weather.get_reference_time(timeformat = "date")
			if datetime.datetime.now(datetime.timezone.utc) > date:
				continue
			temperature_c = weather.get_temperature(unit = "celsius")
			temperature_f = weather.get_temperature(unit = "fahrenheit")
			weather_output = (f" | {date.strftime('%A')}: {weather.get_status()}. "
								f"High: {temperature_c['max']}°C/{temperature_f['max']}°F, "
								f"Low: {temperature_c['min']}°C/{temperature_f['min']}°F")
			if len(output + weather_output) > self.bot.character_limit:
				break
			output += weather_output
		await ctx.send(output)
	
	@commands.command()
	async def weather(self, ctx, *, location = ""):
		if not location or location.lower() == ctx.channel.name:
			location = await self.bot.db.fetchval("SELECT location FROM twitch.locations WHERE channel = $1", ctx.channel.name)
			if not location:
				return await ctx.send(f"Error: Location not specified")
		try:
			observation = self.bot.weather_manager.weather_at_place(location)
		except (pyowm.commons.exceptions.NotFoundError, 
				pyowm.commons.exceptions.BadGatewayError) as e:
			# TODO: Catch base exceptions?
			return await ctx.send(f"Error: {e}")
		output = (f"{observation.location.name}, {observation.location.country}: "
					f"{observation.weather.status} and "
					f"{observation.weather.temperature(unit = 'celsius')['temp']}°C / "
					f"{observation.weather.temperature(unit = 'fahrenheit')['temp']}°F | Wind: ")
		if wind_degrees := observation.weather.wnd.get("deg", ""):
			output += f"{wind_degrees_to_direction(wind_degrees)} "
		output += (f"{observation.weather.wind(unit = 'km_hour')['speed']:.2f} km/h / "
					f"{observation.weather.wind(unit = 'miles_hour')['speed']:.2f} mi/h"
					f" | Humidity: {observation.weather.humidity}%")
		pressure = observation.weather.pressure["press"]
		output += f" | Pressure: {pressure} mb (hPa) / {pressure * 0.0295299830714:.2f} inHg"
		if visibility := observation.weather.visibility_distance:
			output += f" | Visibility: {visibility / 1000:.2f} km / {visibility * 0.000621371192237:.2f} mi"
		# TODO: Heat Index [°C/°F], not possible to get from weather.heat_index?
		# TODO: Windchill [°C/°F]?
		# TODO: Dew (point) [°C/°F]?
		await ctx.send(output)

