
import discord
from discord import app_commands, ui
from discord.ext import commands

from decimal import Decimal
import io
import sys
from typing import Optional

import datetime
import pyowm.commons.exceptions

from utilities import checks
from utilities.converters import Maptype

sys.path.insert(0, "..")
from units.location import get_geocode_data, get_timezone_data, wind_degrees_to_direction, UnitOutputError
sys.path.pop(0)

async def setup(bot):
	await bot.add_cog(Location(bot))

class Location(commands.Cog):
	
	'''
	Commands regarding locations
	Also see Random cog for random location commands
	'''
	
	def __init__(self, bot):
		self.bot = bot
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	# TODO: handle random location command
	
	@commands.command()
	async def country(self, ctx, *, country: str):
		'''Information about a country'''
		# TODO: subcommands for other options to search by (e.g. capital)
		url = "https://restcountries.eu/rest/v2/name/" + country
		async with ctx.bot.aiohttp_session.get(url) as resp:
			if resp.status == 400:
				return await ctx.embed_reply(":no_entry: Error")
			data = await resp.json()
			if resp.status == 404:
				error_message = ":no_entry: Error"
				if "message" in data:
					error_message += ": " + data["message"]
				return await ctx.embed_reply(error_message)
		country_data = {}
		for c in data:
			if c["name"].lower() == country.lower() or country.lower() in [n.lower() for n in c["altSpellings"]]:
				country_data = c
				break
		if not country_data:
			country_data = data[0]
		# Flag, Population
		fields = [("Flag", f"[:flag_{country_data['alpha2Code'].lower()}:]({country_data['flag']})"), 
					("Population", f"{country_data['population']:,}")]
		# Area
		if country_data["area"]:
			fields.append(("Area", f"{country_data['area']:,} sq km"))
		# Capital
		if country_data["capital"]:
			fields.append(("Capital", country_data["capital"]))
		# Languages
		languages = []
		for language in country_data["languages"]:
			language_name = language["name"]
			if language["nativeName"] != language["name"]:
				language_name += f"\n({language['nativeName']})"
			languages.append(language_name)
		if len(languages) == 1 and len(languages[0]) > 22:  # 22: embed field value limit without offset
			languages = languages[0]
		else:
			languages = '\n'.join(l.replace('\n', ' ') for l in languages)
		field_title = ctx.bot.inflect_engine.plural("Language", len(country_data["languages"]))
		fields.append((field_title, languages))
		# Currencies
		currencies = []
		for currency in country_data["currencies"]:
			currency_name = f"{currency['name']}\n({currency['code']}"
			if currency["symbol"]:
				currency_name += ", " + currency["symbol"]
			currency_name += ')'
			currencies.append(currency_name)
		if len(currencies) == 1 and len(currencies[0]) > 22:  # 22: embed field value limit without offset
			currencies = currencies[0]
		else:
			currencies = '\n'.join(c.replace('\n', ' ') for c in currencies)
		field_title = ctx.bot.inflect_engine.plural("currency", len(country_data["currencies"]))
		field_title = field_title.capitalize()
		fields.append((field_title, currencies))
		# Regions/Subregions
		if country_data["subregion"]:
			fields.append(("Region: Subregion", f"{country_data['region']}:\n{country_data['subregion']}"))
		else:
			fields.append(("Region", country_data["region"]))
		# Regional Blocs
		if country_data["regionalBlocs"]:
			regional_blocs = [f"{rb['name']}\n({rb['acronym']})" for rb in country_data["regionalBlocs"]]
			if len(regional_blocs) == 1:
				regional_blocs = regional_blocs[0]
			else:
				regional_blocs = '\n'.join(rb.replace('\n', ' ') for rb in regional_blocs)
			field_title = ctx.bot.inflect_engine.plural("Regional Bloc", len(country_data["regionalBlocs"]))
			fields.append((field_title, regional_blocs))
		# Borders
		if country_data["borders"]:
			field_title = ctx.bot.inflect_engine.plural("Border", len(country_data["borders"]))
			fields.append((field_title, '\n'.join(", ".join(country_data["borders"][i:i + 4]) for i in range(0, len(country_data["borders"]), 4))))
		# Timezones
		field_title = ctx.bot.inflect_engine.plural("Timezone", len(country_data["timezones"]))
		fields.append((field_title, '\n'.join(", ".join(country_data["timezones"][i:i + 2]) for i in range(0, len(country_data["timezones"]), 2))))
		# Demonym
		if country_data["demonym"]:
			fields.append(("Demonym", country_data["demonym"]))
		# Top-Level Domains
		if country_data["topLevelDomain"][0]:
			field_title = ctx.bot.inflect_engine.plural("Top-Level Domain", len(country_data["topLevelDomain"]))
			fields.append((field_title, ", ".join(country_data["topLevelDomain"])))
		# Calling Codes
		if country_data["callingCodes"] and country_data["callingCodes"][0]:
			field_title = ctx.bot.inflect_engine.plural("Calling Code", len(country_data["callingCodes"]))
			fields.append((field_title, ", ".join('+' + cc for cc in country_data["callingCodes"])))
		# Name
		country_name = country_data["name"]
		if country_data["nativeName"] not in country_data["name"]:
			country_name += f" ({country_data['nativeName']})"
		await ctx.embed_reply(title = country_name, fields = fields)
	
	@commands.group(case_insensitive = True, invoke_without_command = True)
	async def geocode(self, ctx, *, address: str):
		'''Convert addresses to geographic coordinates'''
		try:
			data = await get_geocode_data(
				address, aiohttp_session = ctx.bot.aiohttp_session
			)
		except UnitOutputError as e:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")
			return
		
		await ctx.embed_reply(
			title = "Geographic Coordinates for " + data["formatted_address"],
			fields = (
				("Latitude", data["geometry"]["location"]["lat"]),
				("Longitude", data["geometry"]["location"]["lng"])
			)
		)
	
	@geocode.command(name = "reverse")
	async def geocode_reverse(self, ctx, latitude: float, longitude: float):
		'''Convert geographic coordinates to addresses'''
		url = "https://maps.googleapis.com/maps/api/geocode/json"
		params = {"latlng": f"{latitude},{longitude}", "key": ctx.bot.GOOGLE_API_KEY}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if data["status"] == "ZERO_RESULTS":
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Address/Location not found")
		if data["status"] != "OK":
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error")
		data = data["results"][0]
		await ctx.embed_reply(data["formatted_address"], title = f"Address for {latitude}, {longitude}")
	
	# TODO: random address command?
	
	@commands.group(case_insensitive = True, invoke_without_command = True)
	async def map(
		self, ctx, zoom: Optional[int] = 13,
		maptype: Optional[Maptype] = "roadmap", *, location: str
	):
		'''
		See map of location
		Zoom: 0 - 21+
		Map Types: roadmap, satellite, hybrid, terrain
		'''
		url = "https://maps.googleapis.com/maps/api/staticmap"
		params = {
			"center": location, "zoom": zoom, "maptype": maptype,
			"size": "640x640", "key": ctx.bot.GOOGLE_API_KEY
		}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.read()
		await ctx.embed_reply(
			image_url = "attachment://map.png",
			file = discord.File(io.BytesIO(data), filename = "map.png")
		)
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	async def streetview(self, ctx, pitch: Optional[int] = 0, heading: Optional[int] = None, *, location: str):
		'''
		Generate street view of a location
		`pitch`: specifies the up or down angle of the camera relative to the Street View vehicle.
		This is often, but not always, flat horizontal.
		Positive values angle the camera up (with `90` degrees indicating straight up);
		negative values angle the camera down (with `-90` indicating straight down).
		`heading`: indicates the compass heading of the camera.
		Accepted values are from `0` to `360` (both values indicating North, with `90` indicating East, and `180` South).
		If no heading is specified, a value will be calculated that directs the camera towards the specified `location`, from the point at which the closest photograph was taken.
		'''
		url = "https://maps.googleapis.com/maps/api/streetview"
		params = {"location": location, "size": "640x640", "fov": 120, "pitch": pitch, 
					"key": ctx.bot.GOOGLE_API_KEY}
		if heading is not None:
			params["heading"] = heading
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.read()
		await ctx.embed_reply(image_url = "attachment://streetview.png", 
								file = discord.File(io.BytesIO(data), filename = "streetview.png"))
	
	@commands.group(
		aliases = ["timezone"],
		case_insensitive = True, invoke_without_command = True
	)
	async def time(self, ctx, *, location: str):
		'''Current time of a location'''
		try:
			geocode_data = await get_geocode_data(
				location, aiohttp_session = ctx.bot.aiohttp_session
			)
			latitude = geocode_data["geometry"]["location"]["lat"]
			longitude = geocode_data["geometry"]["location"]["lng"]
			timezone_data = await get_timezone_data(
				latitude = latitude, longitude = longitude,
				aiohttp_session = ctx.bot.aiohttp_session
			)
		except UnitOutputError as e:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")
			return
		
		location_time = datetime.datetime.fromtimestamp(
			datetime.datetime.utcnow().timestamp() +
			timezone_data["dstOffset"] + timezone_data["rawOffset"]
		)
		
		await ctx.embed_reply(
			title = "Time at " + geocode_data["formatted_address"],
			description = (
				f"{location_time.strftime('%I:%M:%S %p').lstrip('0')}\n"
				f"{location_time.strftime('%Y-%m-%d %A')}"
			),
			fields = ((
				"Timezone",
				(
					f"{timezone_data['timeZoneName']}\n"
					f"{timezone_data['timeZoneId']}"
				)
			),)
		)
	
	@commands.command()
	async def weather(self, ctx, *, location: str):
		'''Weather'''
		try:
			observation = self.bot.weather_manager.weather_at_place(location)
		except (
			pyowm.commons.exceptions.NotFoundError,
			pyowm.commons.exceptions.BadGatewayError
		) as e:  # TODO: Catch base exceptions?
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")
			return
		
		embed = format_weather_embed(ctx, observation.weather)
		embed.title = (
			f"{observation.location.name}, {observation.location.country}"
		)
		
		await ctx.send(embed = embed)
		await self.bot.attempt_delete_message(ctx.message)
	
	@app_commands.command(name = "weather")
	async def slash_weather(self, interaction, location: str):
		"""
		Weather
		
		Parameters
		----------
		location
			Location to query
		"""
		try:
			geocode_data = await get_geocode_data(
				location, aiohttp_session = interaction.client.aiohttp_session
			)
			lat = geocode_data["geometry"]["location"]["lat"]
			lon = geocode_data["geometry"]["location"]["lng"]
		except UnitOutputError:
			locations = interaction.client.geocoding_manager.geocode(
				location, limit = 1
			)
			
			if not locations:
				await interaction.response.send_message(
					"Error: Location not found", ephemeral = True
				)
				return
			
			lat = locations[0].lat
			lon = locations[0].lon
		
		one_call = interaction.client.weather_manager.one_call(
			lat = lat, lon = lon
		)
		
		embed = format_weather_embed(interaction, one_call.current)
		embed.title = geocode_data['formatted_address']
		
		view = WeatherView(
			interaction.client, geocode_data['formatted_address'], one_call,
			interaction.user
		)
		await interaction.response.send_message(
			embed = embed,
			view = view
		)
		message = await interaction.original_message()
        # Fetch Message, as InteractionMessage token expires after 15 min.
		view.message = await message.fetch()
		interaction.client.views.append(view)

class WeatherView(ui.View):  # TODO: Use ButtonPaginator?
	
	def __init__(self, bot, location, one_call, user):
		super().__init__(timeout = None)
		
		self.bot = bot
		self.location = location
		self.one_call = one_call
		self.user = user
		
		self.forecast_index = 0
		self.forecast_precision = "daily"
		self.message = None
	
	@ui.button(
		emoji = (
			'\N{LEFTWARDS BLACK ARROW}'
			'\N{VARIATION SELECTOR-16}'
		),
		disabled = True
	)
	async def previous_button(self, interaction, button):
		self.forecast_index -= 1
		forecasts = getattr(
			self.one_call,
			f"forecast_{self.forecast_precision}"
		)
		weather = forecasts[self.forecast_index]
		embed = format_weather_embed(interaction, weather)
		embed.title = self.location
		
		if not self.forecast_index:
			button.disabled = True
		self.next_button.disabled = False
		
		await interaction.response.edit_message(embed = embed, view = self)
	
	@ui.button(label = "Current")
	async def current_button(self, interaction, button):
		embed = format_weather_embed(interaction, self.one_call.current)
		embed.title = self.location
		
		self.previous_button.disabled = True
		self.forecast_index = 0
		self.next_button.disabled = False
		
		await interaction.response.edit_message(embed = embed, view = self)
	
	@ui.button(
		emoji = (
			'\N{BLACK RIGHTWARDS ARROW}'
			'\N{VARIATION SELECTOR-16}'
		)
	)
	async def next_button(self, interaction, button):
		self.forecast_index += 1
		forecasts = getattr(
			self.one_call,
			f"forecast_{self.forecast_precision}"
		)
		weather = forecasts[self.forecast_index]
		embed = format_weather_embed(
			interaction, weather,
			humidity = self.forecast_precision != "minutely"
		)
		embed.title = self.location
		
		self.previous_button.disabled = False
		if len(forecasts) == self.forecast_index + 1:
			button.disabled = True
		
		await interaction.response.edit_message(embed = embed, view = self)
	
	@ui.select(
		options = [
			discord.SelectOption(label = "Daily Forecast", default = True),
			discord.SelectOption(label = "Hourly Forecast"),
			discord.SelectOption(label = "Minutely Forecast")
		]
	)
	async def forecast_precision_select(self, interaction, select):
		precision = select.values[0].split()[0].lower()
		forecasts = getattr(self.one_call, f"forecast_{precision}")
		
		if not forecasts:
			await interaction.response.send_message(
				select.values[0] + " not available for this location.",
				ephemeral = True
			)
			await interaction.message.edit(view = self)
			return
		
		self.forecast_precision = precision
		self.forecast_index = 0
		weather = forecasts[self.forecast_index]
		embed = format_weather_embed(
			interaction, weather,
			humidity = self.forecast_precision != "minutely"
		)
		embed.title = self.location
		
		for option in select.options:
			option.default = option.label == select.values[0]
		self.previous_button.disabled = True
		self.next_button.disabled = False
		
		await interaction.response.edit_message(embed = embed, view = self)
	
	@ui.button(label = "Alerts", row = 2)
	async def alerts_button(self, interaction, button):
		embed = discord.Embed(
			color = interaction.client.bot_color,
			title = self.location
		)
		if not self.one_call.national_weather_alerts:
			embed.description = "No national weather alerts"
		else:
			for alert in self.one_call.national_weather_alerts:
				embed.add_field(
					name = f"{alert.title} - {alert.sender}",
					value = alert.description,
					inline = False
				)
		
		self.previous_button.disabled = True
		self.next_button.disabled = True
		
		await interaction.response.edit_message(embed = embed, view = self)
	
	@ui.button(
		style = discord.ButtonStyle.red,
		emoji = '\N{OCTAGONAL SIGN}',
		row = 2
	)
	async def stop_button(self, interaction, button):
		await self.stop(interaction = interaction)
	
	async def interaction_check(self, interaction):
		if interaction.user.id not in (
			self.user.id, interaction.client.owner_id
		):
			await interaction.response.send_message(
				"You didn't invoke this command.", ephemeral = True
			)
			return False
		return True
	
	async def stop(self, interaction = None):
		self.previous_button.disabled = True
		self.forecast_precision_select.disabled = True
		self.next_button.disabled = True
		self.current_button.disabled = True
		self.alerts_button.disabled = True
		self.remove_item(self.stop_button)
		
		if interaction:
			await interaction.response.edit_message(view = self)
		elif self.message:
			await self.bot.attempt_edit_message(
				self.message, view = self
			)

def format_weather_embed(ctx_or_interaction, weather, humidity = True):
	embed = discord.Embed(
		timestamp = weather.reference_time(timeformat = "date")
	).set_thumbnail(
		url = weather.weather_icon_url()
	)
	if weather.status:
		embed.add_field(
			name = "Conditions",
			value = weather.status
		)
	if "temp" in weather.temp:
		embed.add_field(
			name = "Temperature",
			value = (
				f"{weather.temperature(unit = 'celsius')['temp']}°C\n"
				f"{weather.temperature(unit = 'fahrenheit')['temp']}°F"
			)
		)
	elif "min" in weather.temp and "max" in weather.temp:
		embed.add_field(
			name = "Minimum Temperature",
			value = (
				f"{weather.temperature(unit = 'celsius')['min']}°C\n"
				f"{weather.temperature(unit = 'fahrenheit')['min']}°F"
			)
		)
		embed.add_field(
			name = "Maximum Temperature",
			value = (
				f"{weather.temperature(unit = 'celsius')['max']}°C\n"
				f"{weather.temperature(unit = 'fahrenheit')['max']}°F"
			)
		)
	if wind_direction := weather.wnd.get("deg", ""):
		wind_direction = wind_degrees_to_direction(wind_direction)
	if weather.wnd:
		embed.add_field(
			name = "Wind",
			value = (
				f"{wind_direction} {weather.wind(unit = 'km_hour')['speed']:.2f} km/h\n"
				f"{wind_direction} {weather.wind(unit = 'miles_hour')['speed']:.2f} mi/h"
			)
		)
	if humidity:
		embed.add_field(
			name = "Humidity",
			value = f"{weather.humidity}%"
		)
	if pressure := weather.pressure["press"]:
		embed.add_field(
			name = "Pressure",
			value = (
				f"{pressure} mb (hPa)\n"
				f"{pressure * 0.0295299830714:.2f} inHg"
			)
		)
	if visibility := weather.visibility_distance:
		embed.add_field(
			name = "Visibility",
			value = (
				f"{visibility / 1000:.2f} km\n"
				f"{visibility * 0.000621371192237:.2f} mi"
			)
		)
	if weather.precipitation_probability:
		embed.add_field(
			name = "Precipitation",
			value = f"{Decimal(str(weather.precipitation_probability)):%}"
		)
	elif "all" in weather.rain:
		embed.add_field(
			name = "Precipitation",
			value = f"{weather.rain['all'] * 100}%"
		)
	
	if isinstance(ctx_or_interaction, commands.Context):
		embed.color = ctx_or_interaction.bot.bot_color
		embed.set_author(
			name = ctx_or_interaction.author.display_name,
			icon_url = ctx_or_interaction.author.display_avatar.url
		)
		embed.set_footer(text = (
			"In response to: " +
			ctx_or_interaction.message.clean_content
		))
	elif isinstance(ctx_or_interaction, discord.Interaction):
		embed.color = ctx_or_interaction.client.bot_color
	else:
		raise RuntimeError(
			"format_weather_embed passed neither Context nor Interaction"
		)
	
	return embed

