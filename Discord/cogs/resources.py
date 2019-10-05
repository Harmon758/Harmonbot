
import discord
from discord.ext import commands

import asyncio
import datetime
import json
import unicodedata

import dateutil
# import spotipy

from modules import utilities
from utilities import checks

def setup(bot):
	bot.add_cog(Resources(bot))

class Resources(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		# spotify = spotipy.Spotify()
	
	@commands.group(aliases = ["blizzard", "battle.net"], invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def battlenet(self, ctx):
		'''Battle.net'''
		await ctx.send_help(ctx.command)
	
	@battlenet.command(name = "run", aliases = ["launch"])
	@checks.not_forbidden()
	async def battlenet_run(self, ctx, *, game : str):
		'''
		Generate a Battle.net link to launch a game
		You must have the Battle.net launcher open for the link to work
		'''
		abbreviations = {"world of warcraft": "WoW", "wow": "WoW", "diablo 3": "D3", 
						"starcraft 2": "S2", "hearthstone": "WTCG", "heroes of the storm": "Hero", 
						"hots": "Hero", "overwatch": "Pro"}
		abbreviation = abbreviations.get(game.lower())
		if not abbreviation:
			await ctx.embed_reply(":no_entry: Game not found")
			return
		await ctx.embed_reply(f"[Launch {game}](battlenet://{abbreviation})")
	
	@commands.group(aliases = ["colour"], invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def color(self, ctx, *, color : str):
		'''
		Information on colors
		Accepts hex color codes and search by keyword
		'''
		color = color.strip('#')
		if utilities.is_hex(color) and len(color) == 6:
			url = "http://www.colourlovers.com/api/color/" + color
			params = {}
		else:
			url = "http://www.colourlovers.com/api/colors"
			params = {"numResult": 1, "keywords": color}
		await self.process_color(ctx, url, params)
	
	async def process_color(self, ctx, url, params = None):
		if params is None:
			params = {}
		params["format"] = "json"
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if not data:
			await ctx.embed_reply(":no_entry: Error")
			return
		data = data[0]
		fields = (("RGB", f"{data['rgb']['red']}, {data['rgb']['green']}, {data['rgb']['blue']}"), 
					("HSV", f"{data['hsv']['hue']}°, {data['hsv']['saturation']}%, {data['hsv']['value']}%"))
		await ctx.embed_reply(f"#{data['hex']}", title = data["title"].capitalize(), 
								image_url = data["imageUrl"], fields = fields)
	
	@commands.command()
	@checks.not_forbidden()
	async def cve(self, ctx, identifier_number : str):
		identifier_number = identifier_number.lower().lstrip('-')
		if not identifier_number.startswith("cve-"):
			identifier_number = "cve-" + identifier_number
		url = f"http://cve.circl.lu/api/cve/{identifier_number}"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		if not data:
			return await ctx.embed_reply(":no_entry: Error: Not found")
		await ctx.embed_reply(data["summary"], title = data["id"], fields = (("CVSS", data["cvss"]),), 
								footer_text = "Published", timestamp = dateutil.parser.parse(data["Published"]))
	
	@commands.command()
	@checks.not_forbidden()
	async def gender(self, ctx, name : str):
		'''Gender of a name'''
		# TODO: add localization options?
		url = "https://api.genderize.io/"
		async with ctx.bot.aiohttp_session.get(url, params = {"name": name}) as resp:
			# TODO: check status code
			data = await resp.json()
		if not data["gender"]:
			await ctx.embed_reply("Gender: Unknown", title = data["name"].capitalize())
		else:
			probability = int(data["probability"] * 100)
			footer_text = f"Probability: {probability}% ({data['count']} data entries examined)"
			await ctx.embed_reply(f"Gender: {data['gender']}", title = data["name"].capitalize(), 
									footer_text = footer_text)
	
	@commands.command()
	@checks.not_forbidden()
	async def hastebin(self, ctx, *, contents : str):
		'''Hastebin'''
		url = "https://hastebin.com/documents"
		async with ctx.bot.aiohttp_session.post(url, data = contents) as resp:
			if resp.status == 503:
				return await ctx.embed_reply(f":no_entry: Error: {resp.reason}")
			data = await resp.json()
		await ctx.embed_reply("https://hastebin.com/" + data["key"])
	
	@commands.command(aliases = ["hibp"])
	@checks.not_forbidden()
	async def haveibeenpwned(self, ctx, name: str):
		'''Check if your account has been breached'''
		url = "https://haveibeenpwned.com/api/v2/breachedaccount/" + name
		params = {"truncateResponse": "true"}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			if resp.status in (400, 404):
				breachedaccounts = "None"
			else:
				data = await resp.json()
				breachedaccounts = ", ".join(acc["Name"] for acc in data)
		url = "https://haveibeenpwned.com/api/v2/pasteaccount/" + name
		async with ctx.bot.aiohttp_session.get(url) as resp:
			if resp.status in (400, 404):
				pastedaccounts = "None"
			else:
				data = await resp.json()
				pastedaccounts = ", ".join(f"{acc['Source']} ({acc['Id']})" for acc in data)
		await ctx.embed_reply(f"Breached accounts: {breachedaccounts}\nPastes: {pastedaccounts}")
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def horoscope(self, ctx, sign : str):
		'''Horoscope'''
		await self.process_horoscope(ctx, sign, "today")
	
	@horoscope.command(name = "signs", aliases = ["sun_signs", "sunsigns"])
	@checks.not_forbidden()
	async def horoscope_signs(self, ctx):
		'''Sun signs'''
		async with ctx.bot.aiohttp_session.get("http://sandipbgt.com/theastrologer/api/sunsigns") as resp:
			data = await resp.json(content_type = "text/html")
		await ctx.embed_reply(", ".join(data))
	
	@horoscope.command(name = "today")
	@checks.not_forbidden()
	async def horoscope_today(self, ctx, sign):
		'''Today's horoscope'''
		await self.process_horoscope(ctx, sign, "today")
	
	@horoscope.command(name = "tomorrow")
	@checks.not_forbidden()
	async def horoscope_tomorrow(self, ctx, sign):
		'''Tomorrow's horoscope'''
		await self.process_horoscope(ctx, sign, "tomorrow")
	
	@horoscope.command(name = "yesterday")
	@checks.not_forbidden()
	async def horoscope_yesterday(self, ctx, sign):
		'''Yesterday's horoscope'''
		await self.process_horoscope(ctx, sign, "yesterday")
	
	async def process_horoscope(self, ctx, sign, day):
		# https://github.com/sandipbgt/theastrologer-api/issues/13
		if len(sign) == 1:
			sign = unicodedata.name(sign)
		sign = sign.lower()
		# url = f"http://sandipbgt.com/theastrologer/api/horoscope/{sign}/{day}/"
		url = f"http://theastrologer-api.herokuapp.com/api/horoscope/{sign}/{day}"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			if resp.status in (404, 503):
				return await ctx.embed_reply(":no_entry: Error")
			# data = await resp.json(content_type = "text/html")
			data = await resp.json()
			if resp.status == 400:
				return await ctx.embed_reply(f":no_entry: Error: {data.get('message')}")
		fields = sorted((k.capitalize(), v) for k, v in data["meta"].items())
		date = [int(d) for d in data["date"].split('-')]
		timestamp = datetime.datetime(date[0], date[1], date[2])
		# await ctx.embed_reply(data["horoscope"].replace(data["credit"], ""), 
		await ctx.embed_reply(data["horoscope"], 
								title = data["sunsign"], fields = fields, 
		#						footer_text = data["credit"], timestamp = timestamp)
								timestamp = timestamp)
	
	@commands.command(aliases = ["movie"])
	@checks.not_forbidden()
	async def imdb(self, ctx, *, search : str):
		'''IMDb Information'''
		url = "http://www.omdbapi.com/"
		params = {'t': search, "plot": "short", "apikey": ctx.bot.OMDB_API_KEY}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if data["Response"] == "False":
			return await ctx.embed_reply(f":no_entry: Error: {data['Error']}")
		fields = [("IMDb Rating", data["imdbRating"]), ("Runtime", data["Runtime"]), 
					("Genre(s)", data["Genre"]), ("Director", data["Director"]), 
					("Writer", data["Writer"]), ("Cast", data["Actors"]), 
					("Language", data["Language"]), ("Country", data["Country"]), 
					("Awards", data["Awards"])]
		if "totalSeasons" in data:
			fields.append(("Total Seasons", data["totalSeasons"]))
		fields.append(("Plot", data["Plot"], False))
		thumbnail_url = None
		if data["Poster"] != "N/A":
			thumbnail_url = data["Poster"]
		await ctx.embed_reply(f"{data['Year']} {data['Type']}", title = data["Title"], 
								title_url = f"http://www.imdb.com/title/{data['imdbID']}", 
								fields = fields, thumbnail_url = thumbnail_url)
	
	@commands.command()
	@checks.not_forbidden()
	async def latex(self, ctx, *, input : str):
		r'''
		Render LaTeX
		"The server is currently running TeX Live 2016 with most* popular packages installed."
		"Potential security flaws such as \write18 and \input have been disabled."
		"There is a rendering time limit of 8 seconds."
		'''
		# http://rtex.probablyaweb.site/docs
		url = "http://rtex.probablyaweb.site/api/v2"
		data = {"code": input, "format": "png"}
		# TODO: Add jpg + pdf format options
		async with ctx.bot.aiohttp_session.post(url, data = data) as resp:
			if resp.status == 500:
				return await ctx.embed_reply(":no_entry: Error")
			data = await resp.json()
		if data["status"] == "error":
			return await ctx.embed_reply(f":no_entry: Error: {data['description']}")
			# TODO: Include log?
		await ctx.embed_reply(image_url = f"{url}/{data['filename']}")
	
	@commands.command()
	@checks.not_forbidden()
	async def longurl(self, ctx, url : str):
		'''Expand a short goo.gl url'''
		url = "https://www.googleapis.com/urlshortener/v1/url"
		params = {"shortUrl": url, "key": ctx.bot.GOOGLE_API_KEY}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			if resp.status == 400:
				await ctx.embed_reply(":no_entry: Error")
				return
			data = await resp.json()
		await ctx.embed_reply(data["longUrl"])
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def news(self, ctx, source : str):
		'''
		News
		Powered by NewsAPI.org
		'''
		url = "https://newsapi.org/v1/articles"
		params = {"source": source, "apiKey": ctx.bot.NEWSAPI_ORG_API_KEY}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if data["status"] != "ok":
			return await ctx.embed_reply(f":no_entry: Error: {data['message']}")
		'''
		paginator = commands.formatter.Paginator(prefix = ctx.author.display_name + ':', suffix = "")
		for article in data["articles"]:
			paginator.add_line(f"**{article['title']}** ({article['publishedAt'].replace('T', ' ').replace('Z', '')})")
			paginator.add_line(article["description"])
			paginator.add_line(f"<{article['url']}>")
			# output += f"\n{article['urlToImage']}"
		for page in paginator.pages:
			await ctx.send(page)
		'''
		response = await ctx.reply("React with a number from 1 to 10 to view each news article")
		numbers = {'\N{KEYCAP TEN}': 10}
		for number in range(1, 10):
			numbers[f"{number}\N{COMBINING ENCLOSING KEYCAP}"] = number
		for number_emote in sorted(numbers.keys()):
			await response.add_reaction(number_emote)
		while True:
			emoji_response = await self.bot.wait_for_reaction(user = ctx.author, message = response, emoji = numbers.keys())
			reaction = emoji_response.reaction
			number = numbers[reaction.emoji]
			article = data["articles"][number - 1]
			output = f"Article {number}:"
			output += f"\n**{article['title']}**"
			if article.get("publishedAt"):
				output += f" ({article.get('publishedAt').replace('T', ' ').replace('Z', '')})"
			# output += f"\n{article['description']}"
			# output += f"\n<{article['url']}>"
			output += f"\n{article['url']}"
			output += "\nSelect a different number for another article"
			await response.edit(content = f"{ctx.author.display_name}: {output}")
	
	@news.command(name = "sources")
	@checks.not_forbidden()
	async def news_sources(self, ctx):
		'''
		News sources
		https://newsapi.org/sources
		'''
		async with ctx.bot.aiohttp_session.get("https://newsapi.org/v1/sources") as resp:
			data = await resp.json()
		if data["status"] != "ok":
			await ctx.embed_reply(":no_entry: Error")
			return
		# for source in data["sources"]:
		await ctx.reply("<https://newsapi.org/sources>\n{}".format(", ".join([source["id"] for source in data["sources"]])))
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def oeis(self, ctx, *, search : str):
		'''The On-Line Encyclopedia of Integer Sequences'''
		url = "http://oeis.org/search"
		params = {"fmt": "json", 'q': search.replace(' ', "")}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if data["results"]:
			await ctx.embed_reply(data["results"][0]["data"], title = data["results"][0]["name"])
		elif data["count"]:
			await ctx.embed_reply(":no_entry: Too many sequences found")
		else:
			await ctx.embed_reply(":no_entry: Sequence not found")
	
	@oeis.command(name = "graph")
	@checks.not_forbidden()
	async def oeis_graph(self, ctx, *, search : str):
		'''Graphs from The On-Line Encyclopedia of Integer Sequences'''
		url = "http://oeis.org/search"
		params = {"fmt": "json", 'q': search.replace(' ', "")}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if data["results"]:
			# TODO: Handle no graph
			await ctx.embed_reply(image_url = f"https://oeis.org/A{data['results'][0]['number']:06d}/graph?png=1")
		elif data["count"]:
			await ctx.embed_reply(":no_entry: Too many sequences found")
		else:
			await ctx.embed_reply(":no_entry: Sequence not found")
	
	@commands.command()
	@checks.not_forbidden()
	async def phone(self, ctx, *, phone : str): # add reactions version
		'''Get phone specifications'''
		async with ctx.bot.aiohttp_session.get("https://fonoapi.freshpixl.com/v1/getdevice?device={}&position=0&token={}".format(phone.replace(' ', '+'), ctx.bot.FONO_API_TOKEN)) as resp:
			data = await resp.json()
		if "status" in data and data["status"] == "error":
			await ctx.embed_reply(":no_entry: Error: {}".format(data["message"]))
			return
		data = data[0]
		embed = discord.Embed(title = data["DeviceName"], color = ctx.bot.bot_color)
		embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url)
		# Brand
		if "Brand" in data: embed.add_field(name = "Brand", value = data["Brand"])
		# Network (network_c?)
		network_info = []
		if "technology" in data: network_info.append("Technology: " + data["technology"])
		if "_2g_bands" in data: network_info.append("2G bands: " + data["_2g_bands"])
		if "_3g_bands" in data: network_info.append("3G Network: " + data["_3g_bands"])
		if "_4g_bands" in data: network_info.append("4G Network: " + data["_4g_bands"])
		if "speed" in data: network_info.append("Speed: " + data["speed"])
		if "gprs" in data: network_info.append("GPRS: " + data["gprs"])
		if "edge" in data: network_info.append("EDGE: " + data["edge"])
		if network_info: embed.add_field(name = "Network", value = '\n'.join(network_info), inline = False)
		# Launch
		launch_info = []
		if "announced" in data: launch_info.append("Announced: " + data["announced"])
		if "status" in data: launch_info.append("Status: " + data["status"])
		if launch_info: embed.add_field(name = "Launch", value = '\n'.join(launch_info), inline = False)
		# Body
		body_info = []
		if "dimensions" in data: body_info.append("Dimensions: " + data["dimensions"])
		if "weight" in data: body_info.append("Weight: " + data["weight"])
		if "keyboard" in data: body_info.append("Keyboard: " + data["keyboard"])
		if "build" in data: body_info.append("Build: " + data["build"])
		if "sim" in data: body_info.append("SIM: " + data["sim"])
		if "body_c" in data: body_info.append(data["body_c"])
		if body_info: embed.add_field(name = "Body", value = '\n'.join(body_info), inline = False)
		# Display
		display_info = []
		if "type" in data: display_info.append("Type: " + data["type"])
		if "size" in data: display_info.append("Size: " + data["size"])
		if "resolution" in data: display_info.append("Resolution: " + data["resolution"])
		if "multitouch" in data: display_info.append("Multitouch: " + data["multitouch"])
		if "protection" in data: display_info.append("Protection: " + data["protection"])
		if "display_c" in data: display_info.append(data["display_c"])
		if display_info: embed.add_field(name = "Display", value = '\n'.join(display_info), inline = False)
		# Platform
		platform_info = []
		if "os" in data: platform_info.append("OS: " + data["os"])
		if "chipset" in data: platform_info.append("Chipset: " + data["chipset"])
		if "cpu" in data: platform_info.append("CPU: " + data["cpu"])
		if "gpu" in data: platform_info.append("GPU: " + data["gpu"])
		if platform_info: embed.add_field(name = "Platform", value = '\n'.join(platform_info), inline = False)
		# Memory
		memory_info = []
		if "card_slot" in data: memory_info.append("Card slot: " + data["card_slot"])
		if "phonebook" in data: memory_info.append("Phonebook: " + data["phonebook"])
		if "call_records" in data: memory_info.append("Call records: " + data["call_records"])
		if "internal" in data: memory_info.append("Internal: " + data["internal"])
		if "memory_c" in data: memory_info.append(data["memory_c"])
		if memory_info: embed.add_field(name = "Memory", value = '\n'.join(memory_info), inline = False)
		# Camera
		camera_info = []
		if "primary_" in data: camera_info.append("Primary: " + data["primary_"])
		if "features" in data: camera_info.append("Features: " + data["features"])
		if "video" in data: camera_info.append("Video: " + data["video"])
		if "secondary" in data: camera_info.append("Secondary: " + data["secondary"])
		if "camera_c" in data: camera_info.append(data["camera_c"])
		if camera_info: embed.add_field(name = "Camera", value = '\n'.join(camera_info), inline = False)
		# Sound
		sound_info = []
		if "alert_types" in data: sound_info.append("Alert types: " + data["alert_types"])
		if "loudspeaker_" in data: sound_info.append("Loudspeaker: " + data["loudspeaker_"])
		if "_3_5mm_jack_" in data: sound_info.append("3.5mm jack: " + data["_3_5mm_jack_"])
		if "sound_c" in data: sound_info.append(data["sound_c"])
		if sound_info: embed.add_field(name = "Sound", value = '\n'.join(sound_info), inline = False)
		# Comms
		comms_info = []
		if "wlan" in data: comms_info.append("WLAN: " + data["wlan"])
		if "bluetooth" in data: comms_info.append("Bluetooth: " + data["bluetooth"])
		if "gps" in data: comms_info.append("GPS: " + data["gps"])
		if "nfc" in data: comms_info.append("NFC: " + data["nfc"])
		if "infrared_port" in data: comms_info.append("Infrared port: " + data["infrared_port"])
		if "radio" in data: comms_info.append("Radio: " + data["radio"])
		if "usb" in data: comms_info.append("USB: " + data["usb"])
		if comms_info: embed.add_field(name = "Comms", value = '\n'.join(comms_info), inline = False)
		# Features
		features_info = []
		if "sensors" in data: features_info.append("Sensors: " + data["sensors"])
		if "messaging" in data: features_info.append("Messaging: " + data["messaging"])
		if "browser" in data: features_info.append("Browser: " + data["browser"])
		if "clock" in data: features_info.append("Clock: " + data["clock"])
		if "alarm" in data: features_info.append("Alarm: " + data["alarm"])
		if "games" in data: features_info.append("Games: " + data["games"])
		if "languages" in data: features_info.append("Languages: " + data["languages"])
		if "java" in data: features_info.append("Java: " + data["java"])
		if "features_c" in data: features_info.append(data["features_c"])
		if features_info: embed.add_field(name = "Features", value = '\n'.join(features_info), inline = False)
		# Battery
		battery_info = []
		if "battery_c" in data: battery_info.append(data["battery_c"])
		if "stand_by" in data: battery_info.append("Stand-by: " + data["stand_by"])
		if "talk_time" in data: battery_info.append("Talk time: " + data["talk_time"])
		if "music_play" in data: battery_info.append("Music play: " + data["music_play"])
		if battery_info: embed.add_field(name = "Battery", value = '\n'.join(battery_info), inline = False)
		# Misc
		misc_info = []
		if "colors" in data: misc_info.append("Colors: " + data["colors"])
		if misc_info: embed.add_field(name = "Misc", value = '\n'.join(misc_info), inline = False)
		# Tests
		tests_info = []
		if "performance" in data: tests_info.append("Performance: " + data["performance"])
		if "display" in data: tests_info.append("Display: " + data["display"])
		if "camera" in data: tests_info.append("Camera: " + data["camera"])
		if "loudspeaker" in data: tests_info.append("Loudspeaker: " + data["loudspeaker"])
		if "audio_quality" in data: tests_info.append("Audio quality: " + data["audio_quality"])
		if "battery_life" in data: tests_info.append("Battery_life: " + data["battery_life"])
		if tests_info: embed.add_field(name = "Tests", value = '\n'.join(tests_info), inline = False)
		# send
		await ctx.send(embed = embed)
	
	@commands.command(hidden = True)
	@checks.not_forbidden()
	async def redditsearch(self, ctx):
		'''WIP'''
		return
	
	@commands.command()
	@checks.not_forbidden()
	async def shorturl(self, ctx, url : str):
		'''Generate a short goo.gl url for your link'''
		short_url = await self._shorturl(url)
		await ctx.embed_reply(short_url)
	
	async def _shorturl(self, url):
		async with self.bot.aiohttp_session.post("https://www.googleapis.com/urlshortener/v1/url?key={}".format(self.bot.GOOGLE_API_KEY), headers = {'Content-Type': 'application/json'}, data = '{"longUrl": "' + url + '"}') as resp:
			data = await resp.json()
		return data["id"]
	
	@commands.command(aliases = ["sptoyt", "spotify_to_youtube", "sp_to_yt"])
	@checks.not_forbidden()
	async def spotifytoyoutube(self, ctx, url : str):
		'''Find a Spotify track on YouTube'''
		link = await self.bot.cogs["Audio"].spotify_to_youtube(url)
		if link:
			await ctx.reply(link)
		else:
			await ctx.embed_reply(":no_entry: Error")
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def steam(self, ctx):
		'''Steam Information'''
		return
	
	@steam.command(name = "appid")
	@checks.not_forbidden()
	async def steam_appid(self, ctx, *, app: str):
		'''Get the AppID'''
		url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		apps = data["applist"]["apps"]
		appid = 0
		for app_info in apps:
			if app_info["name"].lower() == app.lower():
				appid = app_info["appid"]
				break
		await ctx.embed_reply(appid)
	
	@steam.command(name = "gamecount", aliases = ["game_count"])
	@checks.not_forbidden()
	async def steam_gamecount(self, ctx, vanity_name : str):
		'''Find how many games someone has'''
		url = "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/"
		params = {"key": ctx.bot.STEAM_WEB_API_KEY, "vanityurl": vanity_name}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if data["response"]["success"] == 42:  # NoMatch, https://partner.steamgames.com/doc/api/steam_api#EResult
			return await ctx.embed_reply(":no_entry: Error: User not found")
		url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
		params = {"key": ctx.bot.STEAM_WEB_API_KEY, "steamid": data["response"]["steamid"]}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		gamecount = data["response"]["game_count"]
		await ctx.embed_reply(f"{vanity_name} has {gamecount} games")
	
	@steam.command(name = "gameinfo", aliases = ["game_info"])
	@checks.not_forbidden()
	async def steam_gameinfo(self, ctx, *, game: str):
		'''Information about a game'''
		url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		app = discord.utils.find(lambda app: app["name"].lower() == game.lower(), data["applist"]["apps"])
		if not app:
			return await ctx.embed_reply(":no_entry: Game not found")
		appid = str(app["appid"])
		url = "http://store.steampowered.com/api/appdetails/"
		params = {"appids": appid}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		data = data[appid]["data"]
		await ctx.embed_reply(data["short_description"], 
								title = data["name"], title_url = data["website"], 
								fields = (("Release Date", data["release_date"]["date"]), 
											("Free", "Yes" if data["is_free"] else "No"), 
											("App ID", data["steam_appid"])), 
								image_url = data["header_image"])
	
	@steam.command(name = "run", aliases = ["launch"])
	@checks.not_forbidden()
	async def steam_run(self, ctx, *, game : str):
		'''Generate a steam link to launch a game'''
		url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		app = discord.utils.find(lambda app: app["name"].lower() == game.lower(), data["applist"]["apps"])
		if not app:
			return await ctx.embed_reply(":no_entry: Game not found")
		await ctx.embed_reply(f"steam://run/{app['appid']}", title = f"Launch {app['name']}")
	
	@commands.command()
	@checks.not_forbidden()
	async def strawpoll(self, ctx, question : str, *options : str):
		'''
		Generate a strawpoll link
		Use qoutes for spaces in the question or options
		'''
		url = "https://www.strawpoll.me/api/v2/polls"
		data = json.dumps({"title" : question, "options" : options})
		async with ctx.bot.aiohttp_session.post(url, data = data) as resp:
			poll = await resp.json()
			if resp.status == 400 or "errorCode" in poll:
				return await ctx.embed_reply(f":no_entry: Error: {poll['errorMessage']}")
		await ctx.reply("http://strawpoll.me/" + str(poll["id"]))
	
	@commands.command(aliases = ["urband", "urban_dictionary", "urbandefine", "urban_define"])
	@checks.not_forbidden()
	async def urbandictionary(self, ctx, *, term : str):
		'''Urban Dictionary'''
		# TODO: Integrate into reactions system; Return first definition instead for non-reaction version
		# TODO: Convert to define/dictionary subcommand urban and add urband etc. as command aliases
		url = "http://api.urbandictionary.com/v0/define"
		params = {"term": term}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if not data.get("list"):
			return await ctx.embed_reply(":no_entry: No results found")
		num_results = len(data["list"])
		# TODO: Handle if one definition
		if num_results > 10: num_results = 10  # necessary?
		response = await ctx.embed_reply(f"React with a number from 1 to {num_results} to view each definition")
		embed = response.embeds[0]
		numbers = {"1⃣": 1, "2⃣": 2, "3⃣": 3, "4⃣": 4, "5⃣": 5, "6⃣": 6, "7⃣": 7, "8⃣": 8, "9⃣": 9, "🔟" : 10}
		for number_emote in sorted(numbers.keys())[:num_results]:
			await response.add_reaction(number_emote)
		while True:
			reaction, user = await self.bot.wait_for("reaction_add", check = lambda reaction, user: user == ctx.author and reaction.message.id == response.id and str(reaction.emoji) in sorted(numbers.keys())[:num_results])
			number = numbers[reaction.emoji]
			definition = data["list"][number - 1]
			embed.clear_fields()
			embed.title = definition["word"]
			embed.url = definition["permalink"]
			embed.description = definition["definition"]
			# TODO: Check description/definition length?
			embed.add_field(name = "Example", value = "{0[example]}\n\n:thumbsup::skin-tone-2: {0[thumbs_up]} :thumbsdown::skin-tone-2: {0[thumbs_down]}".format(definition))
			embed.set_footer(text = "Select a different number for another definition")
			await response.edit(embed = embed)
	
	@commands.command()
	@checks.not_forbidden()
	async def websitescreenshot(self, ctx, url : str):
		'''Take a screenshot of a website'''
		response = None
		api_url = "http://api.page2images.com/restfullink"
		params = {"p2i_url": url, "p2i_screen": "1280x1024", "p2i_size": "1280x0", 
					"p2i_fullpage": 1, "p2i_key": ctx.bot.PAGE2IMAGES_REST_API_KEY}
		while True:
			async with ctx.bot.aiohttp_session.get(api_url, params = params) as resp:
				data = await resp.json(content_type = "text/html")
			if data["status"] == "processing":
				wait_time = int(data["estimated_need_time"])
				if response:
					embed = response.embeds[0]
					embed.description = "Processing {}\nEstimated wait time: {} sec".format(url, wait_time)
					await response.edit(embed = embed)
				else:
					response = await ctx.embed_reply("Processing {}\nEstimated wait time: {} sec".format(url, wait_time))
				await asyncio.sleep(wait_time)
			elif data["status"] == "finished":
				await ctx.embed_reply("Your screenshot of {}:".format(url), image_url = data["image_url"])
				return
			elif data["status"] == "error":
				await ctx.embed_reply(":no_entry: Error: {}".format(data["msg"]))
				return
	
	@commands.command(aliases = ["whatare"])
	@checks.not_forbidden()
	async def whatis(self, ctx, *search : str):
		'''WIP'''
		if not search:
			await ctx.embed_reply("What is what?")
		else:
			url = "https://kgsearch.googleapis.com/v1/entities:search?limit=1&query={}&key={}".format('+'.join(search), ctx.bot.GOOGLE_API_KEY)
			async with ctx.bot.aiohttp_session.get(url) as resp:
				data = await resp.json()
			if data.get("itemListElement") and data["itemListElement"][0].get("result", {}).get("detailedDescription", {}).get("articleBody", {}):
				await ctx.embed_reply(data["itemListElement"][0]["result"]["detailedDescription"]["articleBody"])
			else:
				await ctx.embed_reply("I don't know what that is")
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def xkcd(self, ctx, number : int = 0):
		'''Find xkcd's'''
		if not number:
			url = "http://xkcd.com/info.0.json" # http://dynamic.xkcd.com/api-0/jsonp/comic/
		else:
			url = "http://xkcd.com/{0}/info.0.json".format(number) # http://dynamic.xkcd.com/api-0/jsonp/comic/#
		await self.process_xkcd(ctx, url)
	
	async def process_xkcd(self, ctx, url):
		async with ctx.bot.aiohttp_session.get(url) as resp:
			if resp.status == 404:
				await ctx.embed_reply(":no_entry: Error")
				return
			data = await resp.json()
		await ctx.embed_reply(title = data["title"], title_url = "http://xkcd.com/{}".format(data["num"]), image_url = data["img"], footer_text = data["alt"], timestamp = datetime.datetime(int(data["year"]), int(data["month"]), int(data["day"])))

