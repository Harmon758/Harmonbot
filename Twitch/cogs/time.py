
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
	
	@commands.command(aliases = ("bday",))
	async def birthday(self, ctx, month : int = None, day : int = None):
		# TODO: Document
		# TODO: Add ability to reset
		# TODO: Handle leap day
		# TODO: Add custom birthday ability for any viewer
		now = datetime.datetime.utcnow()
		if ctx.author.name == ctx.channel.name and month and day:
			try:
				date = datetime.date(year = now.year, month = month, day = day)
			except ValueError as e:
				return await ctx.send(f"Error: {e}")
			await self.bot.db.execute(
				"""
				INSERT INTO twitch.birthdays (channel, month, day)
				VALUES ($1, $2, $3)
				ON CONFLICT (channel) DO
				UPDATE SET month = $2, day = $3
				""", 
				ctx.channel.name, month, day
			)
			return await ctx.send(f"Birthday set to {date.strftime('%B %#d')}")
			# %#d for removal of leading zero on Windows with native Python executable
		record = await self.bot.db.fetchrow("SELECT month, day FROM twitch.birthdays WHERE channel = $1", ctx.channel.name)
		if not record or not record["month"] or not record["day"]:
			return await ctx.send(f"Error: Birthday not set")
		location = await self.bot.db.fetchval("SELECT location FROM twitch.timezones WHERE channel = $1", ctx.channel.name)
		if location:
			try:
				timezone_data = await get_timezone_data(location = location, aiohttp_session = self.aiohttp_session)
			except UnitOutputError as e:
				return await ctx.send(f"Error: {e}")
			now = datetime.datetime.fromtimestamp(datetime.datetime.utcnow().timestamp() + 
													timezone_data["dstOffset"] + timezone_data["rawOffset"])
		birthday = datetime.datetime(now.year, record["month"], record["day"])
		if now > birthday:
			birthday = birthday.replace(year = birthday.year + 1)
		seconds = int((birthday - now).total_seconds())
		await ctx.send(f"{self.secs_to_duration(seconds)} until {ctx.channel.name.capitalize()}'s birthday!")
	
	@commands.command()
	async def time(self, ctx, *, location = ""):
		# TODO: Document
		# TODO: Add ability to reset
		# TODO: Add custom location ability for any viewer
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
			return await ctx.send(f"Timezone location set to {location}")
		if not location or location.lower() == ctx.channel.name:
			location = await self.bot.db.fetchval("SELECT location FROM twitch.timezones WHERE channel = $1", ctx.channel.name)
			if not location:
				return await ctx.send(f"Error: Location not specified")
		try:
			geocode_data = await get_geocode_data(location, aiohttp_session = self.bot.aiohttp_session)
			latitude = geocode_data["geometry"]["location"]["lat"]
			longitude = geocode_data["geometry"]["location"]["lng"]
			timezone_data = await get_timezone_data(latitude = latitude, longitude = longitude, 
													aiohttp_session = self.bot.aiohttp_session)
		except UnitOutputError as e:
			return await ctx.send(f"Error: {e}")
		location_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(
						seconds = timezone_data["dstOffset"] + timezone_data["rawOffset"])))
		# TODO: Use method for Discord time command
		time_string = location_time.strftime(f"%#I:%M %p on %b. %#d (%a.) in {geocode_data['formatted_address']} (%Z)")
		# %#I and %#d for removal of leading zero on Windows with native Python executable
		await ctx.send(f"It is currently {time_string}.")
	
	@staticmethod
	def secs_to_duration(secs):
		# TODO: Generalize/Improve
		# TODO: Move to units
		output = ""
		for dur_name, dur_in_secs in (("year", 31536000), ("week", 604800), ("day", 86400), ("hour", 3600), ("minute", 60)):
			if secs >= dur_in_secs:
				num_dur = int(secs / dur_in_secs)
				output += f" {num_dur} {dur_name}"
				if (num_dur > 1): output += 's'
				secs -= num_dur * dur_in_secs
		if secs != 0:
			output += f" {secs} second"
			if (secs != 1): output += 's'
		return output[1:] if output else f"{secs} seconds"

