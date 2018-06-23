
import discord
from discord.ext import commands

import datetime
import pyowm.exceptions

import clients
import credentials
from utilities import checks

def setup(bot):
	bot.add_cog(Location(bot))

class Location:
	
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
		async with clients.aiohttp_session.get("https://restcountries.eu/rest/v2/name/{}".format(country)) as resp:
			if resp.status == 400:
				await ctx.embed_reply(":no_entry: Error")
				return
			data = await resp.json()
			if resp.status == 404:
				await ctx.embed_reply(":no_entry: Error: {}".format(data.get("message")))
				return
		country_data = {}
		for _country in data:
			if _country["name"].lower() == country.lower() or country.lower() in [n.lower() for n in _country["altSpellings"]]:
				country_data = _country
				break
		if not country_data:
			country_data = data[0]
		# Flag, Population
		fields = [("Flag", "[:flag_{}:]({})".format(country_data["alpha2Code"].lower(), country_data["flag"])), 
					("Population", "{:,}".format(country_data["population"]))]
		# Area
		if country_data["area"]:
			fields.append(("Area", "{:,} sq km".format(country_data["area"])))
		# Capital
		if country_data["capital"]:
			fields.append(("Capital", country_data["capital"]))
		# Languages
		languages = ["{}\n{}".format(l["name"], "({})".format(l["nativeName"]) if l["nativeName"] != l["name"] else "") for l in country_data["languages"]]
		if len(languages) == 1 and len(languages[0]) > 22:  # 22: embed field value limit without offset
			languages = languages[0]
		else:
			languages = '\n'.join(l.replace('\n', ' ') for l in languages)
		fields.append((clients.inflect_engine.plural("Language", len(country_data["languages"])), languages))
		# Currencies
		currencies = ["{0[name]}\n({0[code]}{1})".format(c, ", " + c["symbol"] if c["symbol"] else "") for c in country_data["currencies"]]
		if len(currencies) == 1 and len(currencies[0]) > 22:  # 22: embed field value limit without offset
			currencies = currencies[0]
		else:
			currencies = '\n'.join(c.replace('\n', ' ') for c in currencies)
		fields.append((clients.inflect_engine.plural("currency", len(country_data["currencies"])).capitalize(), currencies))
		# Regions/Subregions
		if country_data["subregion"]:
			fields.append(("Region: Subregion", "{0[region]}:\n{0[subregion]}".format(country_data)))
		else:
			fields.append(("Region", country_data["region"]))
		# Regional Blocs
		if country_data["regionalBlocs"]:
			regional_blocs = ["{0[name]}\n({0[acronym]})".format(rb) for rb in country_data["regionalBlocs"]]
			if len(regional_blocs) == 1:
				regional_blocs = regional_blocs[0]
			else:
				regional_blocs = '\n'.join(rb.replace('\n', ' ') for rb in regional_blocs)
			fields.append((clients.inflect_engine.plural("Regional Bloc", len(country_data["regionalBlocs"])), regional_blocs))
		# Borders
		if country_data["borders"]:
			fields.append((clients.inflect_engine.plural("Border", len(country_data["borders"])), '\n'.join(", ".join(country_data["borders"][i:i + 4]) for i in range(0, len(country_data["borders"]), 4))))
		# Timezones
		fields.append((clients.inflect_engine.plural("Timezone", len(country_data["timezones"])), '\n'.join(", ".join(country_data["timezones"][i:i + 2]) for i in range(0, len(country_data["timezones"]), 2))))
		# Demonym
		if country_data["demonym"]:
			fields.append(("Demonym", country_data["demonym"]))
		# Top-Level Domains
		if country_data["topLevelDomain"][0]:
			fields.append((clients.inflect_engine.plural("Top-Level Domain", len(country_data["topLevelDomain"])), ", ".join(country_data["topLevelDomain"])))
		# Calling Codes
		if country_data["callingCodes"] and country_data["callingCodes"][0]:
			fields.append((clients.inflect_engine.plural("Calling Code", len(country_data["callingCodes"])), ", ".join('+' + cc for cc in country_data["callingCodes"])))
		await ctx.embed_reply(title = "{}{}".format(country_data["name"], " ({})".format(country_data["nativeName"]) if country_data["nativeName"] not in country_data["name"] else ""), fields = fields)
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def geocode(self, ctx, *, address : str):
		'''Convert addresses to geographic coordinates'''
		async with clients.aiohttp_session.get("https://maps.googleapis.com/maps/api/geocode/json", params = {"address": address, "key": credentials.google_apikey}) as resp:
			data = await resp.json()
		if data["status"] == "ZERO_RESULTS":
			await ctx.embed_reply(":no_entry: Address/Location not found")
			return
		if data["status"] != "OK":
			await ctx.embed_reply(":no_entry: Error")
			return
		data = data["results"][0]
		await ctx.embed_reply(title = "Geographic Coordinates for " + data["formatted_address"], fields = (("Latitude", data["geometry"]["location"]["lat"]), ("Longitude", data["geometry"]["location"]["lng"])))
	
	@geocode.command(name = "reverse")
	@checks.not_forbidden()
	async def geocode_reverse(self, ctx, latitude : float, longitude : float):
		'''Convert geographic coordinates to addresses'''
		async with clients.aiohttp_session.get("https://maps.googleapis.com/maps/api/geocode/json", params = {"latlng": "{},{}".format(latitude, longitude), "key": credentials.google_apikey}) as resp:
			data = await resp.json()
		if data["status"] == "ZERO_RESULTS":
			await ctx.embed_reply(":no_entry: Address/Location not found")
			return
		if data["status"] != "OK":
			await ctx.embed_reply(":no_entry: Error")
			return
		data = data["results"][0]
		await ctx.embed_reply(data["formatted_address"], title = "Address for {}, {}".format(latitude, longitude))
	
	# TODO: random address command?
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def map(self, ctx, *, location : str):
		'''See map of location'''
		map_url = "https://maps.googleapis.com/maps/api/staticmap?center={}&zoom=13&size=640x640".format(location.replace(' ', '+'))
		await ctx.embed_reply("[:map:]({})".format(map_url), image_url = map_url)
	
	@map.command(name = "options")
	@checks.not_forbidden()
	async def map_options(self, ctx, zoom : int, maptype : str, *, location : str):
		'''
		More customized map of a location
		Zoom: 0 - 21+ (Default: 13)
		Map Types: roadmap, satellite, hybrid, terrain (Default: roadmap)
		'''
		map_url = "https://maps.googleapis.com/maps/api/staticmap?center={}&zoom={}&maptype={}&size=640x640".format(location.replace(' ', '+'), zoom, maptype)
		await ctx.embed_reply("[:map:]({})".format(map_url), image_url = map_url)
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def streetview(self, ctx, *, location : str):
		'''Generate street view of a location'''
		image_url = "https://maps.googleapis.com/maps/api/streetview?size=400x400&location={}".format(location.replace(' ', '+'))
		await ctx.embed_reply(image_url = image_url)
	
	@commands.group(aliases = ["timezone"], invoke_without_command = True)
	@checks.not_forbidden()
	async def time(self, ctx, *, location : str):
		'''Current time of a location'''
		async with clients.aiohttp_session.get("https://maps.googleapis.com/maps/api/geocode/json", params = {"address": location, "key": credentials.google_apikey}) as resp:
			geocode_data = await resp.json()
		if geocode_data["status"] == "ZERO_RESULTS":
			await ctx.embed_reply(":no_entry: Address/Location not found")
			return
		if geocode_data["status"] != "OK":
			await ctx.embed_reply(":no_entry: Error")
			return
		geocode_data = geocode_data["results"][0]
		current_utc_timestamp = datetime.datetime.utcnow().timestamp()
		async with clients.aiohttp_session.get("https://maps.googleapis.com/maps/api/timezone/json", params = {"location": "{},{}".format(geocode_data["geometry"]["location"]["lat"], geocode_data["geometry"]["location"]["lng"]), "timestamp": str(current_utc_timestamp), "key": credentials.google_apikey}) as resp:
			timezone_data = await resp.json()
		if timezone_data["status"] == "ZERO_RESULTS":
			await ctx.embed_reply(":no_entry: Time not found")
			return
		if timezone_data["status"] != "OK":
			await ctx.embed_reply(":no_entry: Error: {}".format(timezone_data.get("errorMessage", timezone_data["status"])))
			return
		location_time = datetime.datetime.fromtimestamp(current_utc_timestamp + timezone_data["dstOffset"] + timezone_data["rawOffset"])
		await ctx.embed_reply("{}\n{}".format(location_time.strftime("%I:%M:%S %p").lstrip('0'), location_time.strftime("%Y-%m-%d %A")), title = "Time at " + geocode_data["formatted_address"], fields = (("Timezone", "{}\n{}".format(timezone_data["timeZoneName"], timezone_data["timeZoneId"])),))
	
	# TODO: error descriptions?
	# TODO: process_geocode function?
	
	@commands.command()
	@checks.not_forbidden()
	async def weather(self, ctx, *, location : str):
		'''Weather'''
		# wunderground?
		try:
			observation = self.bot.owm_client.weather_at_place(location)
		except (pyowm.exceptions.not_found_error.NotFoundError, pyowm.exceptions.api_call_error.BadGatewayError) as e:
			await ctx.embed_reply(":no_entry: Error: {}".format(e))
			return
		location = observation.get_location()
		weather = observation.get_weather()
		condition = weather.get_status()
		if condition == "Clear": emote = " :sunny:"
		elif condition == "Clouds": emote = " :cloud:"
		elif condition == "Rain": emote = " :cloud_rain:"
		else: emote = ""
		wind = weather.get_wind()
		pressure = weather.get_pressure()["press"]
		visibility = weather.get_visibility_distance()
		embed = discord.Embed(description = "**__{}__**".format(location.get_name()), color = clients.bot_color, timestamp = weather.get_reference_time(timeformat = "date").replace(tzinfo = None))
		embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url)
		embed.add_field(name = "Conditions", value = "{}{}".format(condition, emote))
		embed.add_field(name = "Temperature", value = "{}°C\n{}°F".format(weather.get_temperature(unit = "celsius")["temp"], weather.get_temperature(unit = "fahrenheit")["temp"]))
		embed.add_field(name = "Wind", value = "{0} {1:.2f} km/h\n{0} {2:.2f} mi/h".format(self.wind_degrees_to_direction(wind["deg"]), wind["speed"] * 3.6, wind["speed"] * 2.236936))
		embed.add_field(name = "Humidity", value = "{}%".format(weather.get_humidity()))
		embed.add_field(name = "Pressure", value = "{} mb (hPa)\n{:.2f} inHg".format(pressure, pressure * 0.0295299830714))
		if visibility: embed.add_field(name = "Visibility", value = "{:.2f} km\n{:.2f} mi".format(visibility / 1000, visibility * 0.000621371192237))
		await ctx.send(embed = embed)
	
	def wind_degrees_to_direction(self, degrees):
		# http://climate.umn.edu/snow_fence/components/winddirectionanddegreeswithouttable3.htm
		if 0 <= degrees <= 11.25 or 348.75 <= degrees <= 360: return 'N'
		elif 11.25 <= degrees <= 33.75: return "NNE"
		elif 33.75 <= degrees <= 56.25: return "NE"
		elif 56.25 <= degrees <= 78.75: return "ENE"
		elif 78.75 <= degrees <= 101.25: return 'E'
		elif 101.25 <= degrees <= 123.75: return "ESE"
		elif 123.75 <= degrees <= 146.25: return "SE"
		elif 146.25 <= degrees <= 168.75: return "SSE"
		elif 168.75 <= degrees <= 191.25: return 'S'
		elif 191.25 <= degrees <= 213.75: return "SSW"
		elif 213.75 <= degrees <= 236.25: return "SW"
		elif 236.25 <= degrees <= 258.75: return "WSW"
		elif 258.75 <= degrees <= 281.25: return 'W'
		elif 281.25 <= degrees <= 303.75: return "WNW"
		elif 303.75 <= degrees <= 326.25: return "NW"
		elif 326.25 <= degrees <= 348.75: return "NNW"
		else: return ""

