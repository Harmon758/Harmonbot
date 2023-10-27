
from twitchio.ext import commands

import datetime

import dateutil.easter

from units.location import get_geocode_data, get_timezone_data
from units.time import duration_to_string

@commands.cog()
class Time:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command(aliases = ("bday",))
	async def birthday(self, ctx, month: int = None, day: int = None):
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
		location = await self.bot.db.fetchval("SELECT location FROM twitch.locations WHERE channel = $1", ctx.channel.name)
		if location:
			try:
				timezone_data = await get_timezone_data(location = location, aiohttp_session = self.bot.aiohttp_session)
			except ValueError as e:
				return await ctx.send(f"Error: {e}")
			now = datetime.datetime.fromtimestamp(datetime.datetime.utcnow().timestamp() + 
													timezone_data["dstOffset"] + timezone_data["rawOffset"])
		birthday = datetime.datetime(now.year, record["month"], record["day"])
		if now > birthday:
			birthday = birthday.replace(year = birthday.year + 1)
		await ctx.send(f"{duration_to_string(birthday - now)} until {ctx.channel.name.capitalize()}'s birthday!")
	
	@commands.command()
	async def christmas(self, ctx):
		# TODO: Use streamer timezone if available
		now = datetime.datetime.utcnow()
		christmas = datetime.datetime(now.year, 12, 25)
		if now > christmas:
			christmas = christmas.replace(year = christmas.year + 1)
		await ctx.send(f"{duration_to_string(christmas - now)} until Christmas!")
	
	@commands.command()
	async def easter(self, ctx):
		# TODO: Use streamer timezone if available
		now = datetime.datetime.utcnow()
		easter = datetime.datetime.combine(dateutil.easter.easter(now.year), datetime.time.min)
		if now > easter:
			easter = datetime.datetime.combine(dateutil.easter.easter(now.year + 1), datetime.time.min)
		await ctx.send(f"{duration_to_string(easter - now)} until Easter!")
	
	@commands.command()
	async def time(self, ctx, *, location = ""):
		if not location or location.lower() == ctx.channel.name:
			location = await self.bot.db.fetchval("SELECT location FROM twitch.locations WHERE channel = $1", ctx.channel.name)
			if not location:
				return await ctx.send(f"Error: Location not specified")
		try:
			geocode_data = await get_geocode_data(location, aiohttp_session = self.bot.aiohttp_session)
			latitude = geocode_data["geometry"]["location"]["lat"]
			longitude = geocode_data["geometry"]["location"]["lng"]
			timezone_data = await get_timezone_data(latitude = latitude, longitude = longitude, 
													aiohttp_session = self.bot.aiohttp_session)
		except ValueError as e:
			return await ctx.send(f"Error: {e}")
		location_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(
						seconds = timezone_data["dstOffset"] + timezone_data["rawOffset"])))
		# TODO: Use method for Discord time command
		time_string = location_time.strftime(f"%#I:%M %p on %b. %#d (%a.) in {geocode_data['formatted_address']} (%Z)")
		# %#I and %#d for removal of leading zero on Windows with native Python executable
		await ctx.send(f"It is currently {time_string}.")

