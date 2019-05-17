
from discord.ext import commands

import sys

import datetime
import pyowm.exceptions

from utilities import checks

sys.path.insert(0, "..")
from units.location import get_geocode_data, get_timezone_data, wind_degrees_to_direction, UnitOutputError
sys.path.pop(0)

def setup(bot):
	bot.add_cog(Location(bot))

class Location(commands.Cog):
	
	'''
	Commands regarding locations
	Also see Random cog for random location commands
	'''
	
	def __init__(self, bot):
		self.bot = bot
	
	# TODO: handle random location command
	
	@commands.command()
	@checks.not_forbidden()
	async def country(self, ctx, *, country : str):
		'''Information about a country'''
		# TODO: subcommands for other options to search by (e.g. capital)
		url = "https://restcountries.eu/rest/v2/name/" + country
		async with ctx.bot.aiohttp_session.get(url) as resp:
			if resp.status == 400:
				await ctx.embed_reply(":no_entry: Error")
				return
			data = await resp.json()
			if resp.status == 404:
				error_message = ":no_entry: Error"
				if "message" in data:
					error_message += ": " + data["message"]
				await ctx.embed_reply(error_message)
				return
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
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def geocode(self, ctx, *, address : str):
		'''Convert addresses to geographic coordinates'''
		try:
			data = await get_geocode_data(address, aiohttp_session = ctx.bot.aiohttp_session)
		except UnitOutputError as e:
			await ctx.embed_reply(f":no_entry: Error: {e}")
			return
		title = "Geographic Coordinates for " + data["formatted_address"]
		fields = (("Latitude", data["geometry"]["location"]["lat"]), 
					("Longitude", data["geometry"]["location"]["lng"]))
		await ctx.embed_reply(title = title, fields = fields)
	
	@geocode.command(name = "reverse")
	@checks.not_forbidden()
	async def geocode_reverse(self, ctx, latitude : float, longitude : float):
		'''Convert geographic coordinates to addresses'''
		url = "https://maps.googleapis.com/maps/api/geocode/json"
		params = {"latlng": f"{latitude},{longitude}", "key": ctx.bot.GOOGLE_API_KEY}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if data["status"] == "ZERO_RESULTS":
			await ctx.embed_reply(":no_entry: Address/Location not found")
			return
		if data["status"] != "OK":
			await ctx.embed_reply(":no_entry: Error")
			return
		data = data["results"][0]
		await ctx.embed_reply(data["formatted_address"], title = f"Address for {latitude}, {longitude}")
	
	# TODO: random address command?
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def map(self, ctx, *, location : str):
		'''See map of location'''
		location = location.replace(' ', '+')
		map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={location}&zoom=13&size=640x640"
		await ctx.embed_reply(f"[:map:]({map_url})", image_url = map_url)
	
	@map.command(name = "options")
	@checks.not_forbidden()
	async def map_options(self, ctx, zoom : int, maptype : str, *, location : str):
		'''
		More customized map of a location
		Zoom: 0 - 21+ (Default: 13)
		Map Types: roadmap, satellite, hybrid, terrain (Default: roadmap)
		'''
		location = location.replace(' ', '+')
		map_url = ("https://maps.googleapis.com/maps/api/staticmap"
			f"?center={location}&zoom={zoom}&maptype={maptype}&size=640x640")
		await ctx.embed_reply(f"[:map:]({map_url})", image_url = map_url)
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def streetview(self, ctx, *, location : str):
		'''Generate street view of a location'''
		location = location.replace(' ', '+')
		image_url = f"https://maps.googleapis.com/maps/api/streetview?size=400x400&location={location}"
		await ctx.embed_reply(image_url = image_url)
	
	@commands.group(aliases = ["timezone"], invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def time(self, ctx, *, location : str):
		'''Current time of a location'''
		try:
			geocode_data = await get_geocode_data(location, aiohttp_session = ctx.bot.aiohttp_session)
			latitude = geocode_data["geometry"]["location"]["lat"]
			longitude = geocode_data["geometry"]["location"]["lng"]
			timezone_data = await get_timezone_data(latitude = latitude, longitude = longitude, 
													aiohttp_session = ctx.bot.aiohttp_session)
		except UnitOutputError as e:
			await ctx.embed_reply(f":no_entry: Error: {e}")
			return
		location_time = datetime.datetime.fromtimestamp(datetime.datetime.utcnow().timestamp() + 
														timezone_data["dstOffset"] + timezone_data["rawOffset"])
		title = "Time at " + geocode_data["formatted_address"]
		description = (f"{location_time.strftime('%I:%M:%S %p').lstrip('0')}\n"
						f"{location_time.strftime('%Y-%m-%d %A')}")
		fields = (("Timezone", f"{timezone_data['timeZoneName']}\n{timezone_data['timeZoneId']}"),)
		await ctx.embed_reply(description, title = title, fields = fields)
	
	@commands.command()
	@checks.not_forbidden()
	async def weather(self, ctx, *, location : str):
		'''Weather'''
		try:
			observation = self.bot.owm_client.weather_at_place(location)
		except (pyowm.exceptions.api_response_error.NotFoundError, 
				pyowm.exceptions.api_call_error.BadGatewayError) as e:
			# TODO: Catch base exceptions?
			return await ctx.embed_reply(f":no_entry: Error: {e}")
		location = observation.get_location()
		description = f"**__{location.get_name()}, {location.get_country()}__**"
		weather = observation.get_weather()
		condition = weather.get_status()
		condition_emotes = {"Clear": ":sunny:", "Clouds": ":cloud:", "Fog": ":foggy:", 
							"Rain": ":cloud_rain:", "Snow": ":cloud_snow:"}
		# Emotes for Haze?, Mist?
		emote = ' '
		emote += condition_emotes.get(condition, "")
		fields = [("Conditions", f"{condition}{emote}")]
		temperature_c = weather.get_temperature(unit = "celsius")["temp"]
		temperature_f = weather.get_temperature(unit = "fahrenheit")["temp"]
		fields.append(("Temperature", f"{temperature_c}°C\n{temperature_f}°F"))
		wind = weather.get_wind()
		wind_direction = wind.get("deg", "")
		if wind_direction:
			wind_direction = wind_degrees_to_direction(wind_direction)
		fields.append(("Wind", f"{wind_direction} {wind['speed'] * 3.6:.2f} km/h\n"
								f"{wind_direction} {wind['speed'] * 2.236936:.2f} mi/h"))
		fields.append(("Humidity", f"{weather.get_humidity()}%"))
		pressure = weather.get_pressure()["press"]
		fields.append(("Pressure", f"{pressure} mb (hPa)\n"
									f"{pressure * 0.0295299830714:.2f} inHg"))
		visibility = weather.get_visibility_distance()
		if visibility:
			fields.append(("Visibility", f"{visibility / 1000:.2f} km\n"
											f"{visibility * 0.000621371192237:.2f} mi"))
		timestamp = weather.get_reference_time(timeformat = "date").replace(tzinfo = None)
		await ctx.embed_reply(description, fields = fields, timestamp = timestamp)

