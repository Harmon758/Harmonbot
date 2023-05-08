
import discord
from discord.ext import commands, menus

import asyncio
import datetime
import json
from typing import Optional
import unicodedata

import dateutil

from utilities import checks
from utilities.paginators import ButtonPaginator

async def setup(bot):
	await bot.add_cog(Resources(bot))

class Resources(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.group(
		aliases = ["blizzard", "battle.net"],
		case_insensitive = True, invoke_without_command = True
	)
	@checks.not_forbidden()
	async def battlenet(self, ctx):
		'''Battle.net'''
		await ctx.send_help(ctx.command)
	
	@battlenet.command(name = "run", aliases = ["launch"])
	@checks.not_forbidden()
	async def battlenet_run(self, ctx, *, game: str):
		'''
		Generate a Battle.net link to launch a game
		You must have the Battle.net launcher open for the link to work
		'''
		abbreviations = {
			"world of warcraft": "WoW", "wow": "WoW", "diablo 3": "D3",
			"starcraft 2": "S2", "hearthstone": "WTCG",
			"heroes of the storm": "Hero", "hots": "Hero", "overwatch": "Pro"
		}
		if not (abbreviation := abbreviations.get(game.lower())):
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Game not found")
			return
		await ctx.embed_reply(f"[Launch {game}](battlenet://{abbreviation})")
	
	@commands.group(aliases = ["colour"], case_insensitive = True, invoke_without_command = True)
	@checks.not_forbidden()
	async def color(self, ctx, *, color: discord.Color | str):
		'''
		Information on colors
		Accepts hex color codes and search by keyword
		'''
		if isinstance(color, discord.Color):
			url = f"http://www.colourlovers.com/api/color/{color.value:0>6X}"
			await self.process_color(ctx, url)
		else:
			url = "http://www.colourlovers.com/api/colors"
			params = {"numResult": 1, "keywords": color}
			await self.process_color(ctx, url, params)
		# TODO: Random color when no input
		# TODO: Allow explicit keyword search, to fix ambiguity for hex vs keyword, e.g. fab
	
	@color.command(name = "random")
	@checks.not_forbidden()
	async def color_random(self, ctx):
		'''Information on a random color'''
		# Note: random color command invokes this command
		url = "http://www.colourlovers.com/api/colors/random"
		params = {"numResults": 1}
		await self.process_color(ctx, url, params)
	
	async def process_color(self, ctx, url, params = None):
		if params is None:
			params = {}
		
		headers = {"User-Agent": ctx.bot.simple_user_agent}
		params["format"] = "json"
		async with ctx.bot.aiohttp_session.get(
			url, headers = headers, params = params
		) as resp:
			data = await resp.json()
		
		if not data:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error")
			return
		
		data = data[0]
		fields = (
			(
				"RGB",
				f"{data['rgb']['red']}, "
				f"{data['rgb']['green']}, "
				f"{data['rgb']['blue']}"
			),
			(
				"HSV",
				f"{data['hsv']['hue']}°, "
				f"{data['hsv']['saturation']}%, "
				f"{data['hsv']['value']}%"
			)
		)
		await ctx.embed_reply(
			title = data["title"].capitalize(),
			description = f"#{data['hex']}",
			image_url = data["imageUrl"],
			fields = fields
		)
	
	@commands.hybrid_command()
	@checks.not_forbidden()
	async def cve(self, ctx, identifier: str):
		"""
		Look up Common Vulnerabilities and Exposures
		
		Parameters
		----------
		identifier
			ID of CVE to look up
		"""
		await ctx.defer()
		
		identifier = identifier.lower().lstrip('-')
		if not identifier.startswith("cve-"):
			identifier = "cve-" + identifier
		
		url = f"http://cve.circl.lu/api/cve/{identifier}"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		
		if not data:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: Not found")
			return
		
		await ctx.embed_reply(
			title = data["id"],
			description = data["summary"],
			fields = (("CVSS", data["cvss"]),),
			footer_text = "Published",
			timestamp = dateutil.parser.parse(data["Published"])
		)
	
	@commands.command()
	@checks.not_forbidden()
	async def gender(self, ctx, name: str):
		'''Gender of a name'''
		# TODO: add localization options?
		url = "https://api.genderize.io/"
		async with ctx.bot.aiohttp_session.get(url, params = {"name": name}) as resp:
			# TODO: check status code
			data = await resp.json()
		if not data["gender"]:
			return await ctx.embed_reply("Gender: Unknown", title = data["name"].capitalize())
		await ctx.embed_reply(f"Gender: {data['gender']}", title = data["name"].capitalize(), 
								footer_text = f"Probability: {data['probability']:.0%} ({data['count']} data entries examined)")
	
	@commands.command()
	@checks.not_forbidden()
	async def hastebin(self, ctx, *, contents: str):
		'''Hastebin'''
		url = "https://hastebin.com/documents"
		async with ctx.bot.aiohttp_session.post(url, data = contents) as resp:
			if resp.status == 503:
				return await ctx.embed_reply(f":no_entry: Error: {resp.reason}")
			data = await resp.json()
		await ctx.embed_reply("https://hastebin.com/" + data["key"])
	
	# TODO: Pwned Passwords API?
	@commands.command(aliases = ["hibp"], enabled = False, hidden = True)
	async def haveibeenpwned(self, ctx, name: str):
		'''Deprecated, due to https://www.troyhunt.com/authentication-and-the-have-i-been-pwned-api/'''
		url = "https://haveibeenpwned.com/api/v2/breachedaccount/" + name
		headers = {"User-Agent": ctx.bot.user_agent}
		params = {"truncateResponse": "true"}
		async with ctx.bot.aiohttp_session.get(
			url, headers = headers, params = params
		) as resp:
			if resp.status in (400, 404):
				breachedaccounts = "None"
			else:
				data = await resp.json()
				breachedaccounts = ", ".join(acc["Name"] for acc in data)
		url = "https://haveibeenpwned.com/api/v2/pasteaccount/" + name
		async with ctx.bot.aiohttp_session.get(url, headers = headers) as resp:
			if resp.status in (400, 404):
				pastedaccounts = "None"
			else:
				data = await resp.json()
				pastedaccounts = ", ".join(
					f"{acc['Source']} ({acc['Id']})" for acc in data
				)
		await ctx.embed_reply(
			f"Breached accounts: {breachedaccounts}\nPastes: {pastedaccounts}"
		)
	
	@commands.group(case_insensitive = True, invoke_without_command = True)
	@checks.not_forbidden()
	async def horoscope(self, ctx, sign: str):
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
			if resp.status in (404, 500, 503):
				return await ctx.embed_reply(f"{ctx.bot.error_emoji} API Error: {resp.status} {resp.reason}")
			# data = await resp.json(content_type = "text/html")
			data = await resp.json()
			if resp.status == 400:
				return await ctx.embed_reply(f"{ctx.bot.error_emoji} API Error: {data.get('message')}")
		fields = sorted((k.capitalize(), v) for k, v in data["meta"].items())
		date = [int(d) for d in data["date"].split('-')]
		timestamp = datetime.datetime(date[0], date[1], date[2])
		# await ctx.embed_reply(data["horoscope"].replace(data["credit"], ""), 
		await ctx.embed_reply(data["horoscope"], 
								title = data["sunsign"], fields = fields, 
		#						footer_text = data["credit"], timestamp = timestamp)
								timestamp = timestamp)
	
	@commands.command(usage = "<input>")
	@checks.not_forbidden()
	async def latex(self, ctx, *, latex_input: str):
		R'''
		Render LaTeX
		"The server is currently running TeX Live 2016 with most* popular packages installed."
		"Potential security flaws such as \write18 and \input have been disabled."
		"There is a rendering time limit of 8 seconds."
		'''
		# http://rtex.probablyaweb.site/docs
		url = "http://rtex.probablyaweb.site/api/v2"
		latex_input = (
			R"\documentclass{article}" '\n'
			R"\usepackage{amsmath}" '\n'
			R"\usepackage{mathtools}" '\n'
			R"\usepackage{pagecolor}" '\n'
			R"\begin{document}" '\n'
			R"\pagecolor{white}" '\n'
			f"{latex_input}\n"
			R"\pagenumbering{gobble}" '\n'
			R"\end{document}"
		)
		data = {"code": latex_input, "format": "png"}
		# TODO: Add jpg + pdf format options
		async with ctx.bot.aiohttp_session.post(url, data = data) as resp:
			if resp.status == 500:
				return await ctx.embed_reply(":no_entry: Error")
			data = await resp.json()
		if data["status"] == "error":
			return await ctx.embed_reply(f":no_entry: Error: {data['description']}")
			# TODO: Include log?
		await ctx.embed_reply(image_url = f"{url}/{data['filename']}")
	
	# TODO: Use other URL unshortener API?
	@commands.command(enabled = False, hidden = True)
	async def longurl(self, ctx, url: str):
		'''Deprecated due to https://developers.googleblog.com/2018/03/transitioning-google-url-shortener.html'''
		url = "https://www.googleapis.com/urlshortener/v1/url"
		params = {"shortUrl": url, "key": ctx.bot.GOOGLE_API_KEY}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			if resp.status == 400:
				return await ctx.embed_reply(":no_entry: Error")
			data = await resp.json()
		await ctx.embed_reply(data["longUrl"])
	
	@commands.group(case_insensitive = True, invoke_without_command = True)
	@checks.not_forbidden()
	async def news(self, ctx, source: str):
		'''
		News
		Powered by NewsAPI.org
		'''
		url = "https://newsapi.org/v2/top-headlines"
		params = {"sources": source, "apiKey": ctx.bot.NEWSAPI_ORG_API_KEY}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		
		if data["status"] != "ok":
			await ctx.embed_reply(
				f"{ctx.bot.error_emoji} Error: {data['message']}"
			)
			return
		
		if not data["totalResults"]:
			await ctx.embed_reply(
				f"{ctx.bot.error_emoji} Error: No news articles found for that source"
			)
			return
		
		paginator = NewsButtonPaginator(ctx, NewsSource(data["articles"]))
		await paginator.start()
		ctx.bot.views.append(paginator)
	
	@news.command(name = "sources")
	@checks.not_forbidden()
	async def news_sources(self, ctx):
		'''
		News sources
		https://newsapi.org/sources
		'''
		url = "https://newsapi.org/v1/sources"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		
		if data["status"] != "ok":
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error")
			return
		
		# TODO: Show source names, descriptions, URLs, etc.
		await ctx.embed_reply(
			title = "News Sources",
			title_url = "https://newsapi.org/sources",
			description = ", ".join(
				source["id"] for source in data["sources"]
			)
		)
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def oeis(self, ctx, *, search: str):
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
	async def oeis_graph(self, ctx, *, search: str):
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
	async def phone(self, ctx, *, phone: str):
		'''Get phone specifications'''
		# TODO: Add menu version
		async with ctx.bot.aiohttp_session.get("https://fonoapi.freshpixl.com/v1/getdevice?device={}&position=0&token={}".format(phone.replace(' ', '+'), ctx.bot.FONO_API_TOKEN)) as resp:
			data = await resp.json()
		if "status" in data and data["status"] == "error":
			await ctx.embed_reply(":no_entry: Error: {}".format(data["message"]))
			return
		data = data[0]
		embed = discord.Embed(title = data["DeviceName"], color = ctx.bot.bot_color)
		embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar.url)
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
		# Send
		await ctx.send(embed = embed)
	
	@commands.command(hidden = True)
	@checks.not_forbidden()
	async def redditsearch(self, ctx):
		'''WIP'''
		return
	
	# TODO: Use other URL shortener API? e.g. Bitly?, Ow.ly?
	@commands.command(enabled = False, hidden = True)
	async def shorturl(self, ctx, url: str):
		'''Deprecated due to https://developers.googleblog.com/2018/03/transitioning-google-url-shortener.html'''
		url = f"https://www.googleapis.com/urlshortener/v1/url"
		params = {"key": self.bot.GOOGLE_API_KEY}
		headers = {"Content-Type": "application/json"}
		data = f'{{"longUrl": "{url}"}}'
		async with self.bot.aiohttp_session.post(url, params = params, headers = headers, data = data) as resp:
			data = await resp.json()
		await ctx.embed_reply(data["id"])
	
	@commands.command(aliases = ["sptoyt", "spotify_to_youtube", "sp_to_yt"])
	@checks.not_forbidden()
	async def spotifytoyoutube(self, ctx, url: str):
		'''Find a Spotify track on YouTube'''
		if link := (await self.bot.cogs["Audio"].spotify_to_youtube(url)):
			await ctx.reply(link)
		else:
			await ctx.embed_reply(":no_entry: Error")
	
	@commands.command()
	@checks.not_forbidden()
	async def strawpoll(self, ctx, question: str, *options: str):
		'''
		Generate a strawpoll link
		Use qoutes for spaces in the question or options
		'''
		url = "https://www.strawpoll.me/api/v2/polls"
		data = json.dumps({"title": question, "options": options})
		async with ctx.bot.aiohttp_session.post(url, data = data) as resp:
			poll = await resp.json()
			if resp.status == 400 or "errorCode" in poll:
				return await ctx.embed_reply(f":no_entry: Error: {poll['errorMessage']}")
		await ctx.reply("http://strawpoll.me/" + str(poll["id"]))
	
	@commands.command()
	@checks.not_forbidden()
	async def websitescreenshot(self, ctx, url: str):
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
					embed.description = f"Processing {url}\nEstimated wait time: {wait_time} sec"
					await response.edit(embed = embed)
				else:
					response = await ctx.embed_reply(f"Processing {url}\nEstimated wait time: {wait_time} sec")
				await asyncio.sleep(wait_time)
			elif data["status"] == "finished":
				return await ctx.embed_reply(f"Your screenshot of {url}:", image_url = data["image_url"])
			elif data["status"] == "error":
				return await ctx.embed_reply(f":no_entry: Error: {data['msg']}")
	
	@commands.command(aliases = ["whatare"])
	@checks.not_forbidden()
	async def whatis(self, ctx, *, search: Optional[str]):
		'''WIP'''
		if not search:
			return await ctx.embed_reply("What is what?")
		url = "https://kgsearch.googleapis.com/v1/entities:search"
		params = {"limit": 1, "query": search, "key": ctx.bot.GOOGLE_API_KEY}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if data.get("itemListElement") and data["itemListElement"][0].get("result", {}).get("detailedDescription", {}).get("articleBody", {}):
			await ctx.embed_reply(data["itemListElement"][0]["result"]["detailedDescription"]["articleBody"])
		else:
			await ctx.embed_reply("I don't know what that is")

class NewsButtonPaginator(ButtonPaginator):
	
	def __init__(self, ctx, source):
		super().__init__(ctx, source)
		if self.children:
			# Reorder
			self.remove_item(self.send_article_link)
			self.remove_item(self.stop_button)
			self.add_item(self.send_article_link)
			self.add_item(self.stop_button)
	
	@discord.ui.button(
		label = "Send Article Link", style = discord.ButtonStyle.blurple
	)
	async def send_article_link(self, interaction, button):
		await interaction.response.send_message(
			f"{interaction.user.mention}: {self.source.entries[self.current_page]['url']}"
		)
	
	async def stop(self, interaction = None):
		self.send_article_link.disabled = True
		await super().stop(interaction = interaction)

class NewsSource(menus.ListPageSource):
	
	def __init__(self, articles):
		super().__init__(articles, per_page = 1)
	
	async def format_page(self, menu, article):
		embed = discord.Embed(
			title = article["title"],
			url = article["url"],
			description = article["description"],
			color = menu.ctx.bot.bot_color
		).set_author(
			name = menu.ctx.author.display_name,
			icon_url = menu.ctx.author.avatar.url
		).set_image(
			url = article["urlToImage"]
		).set_footer(
			text = article['source']['name']
		)
		if timestamp := article.get("publishedAt"):
			embed.timestamp = dateutil.parser.parse(timestamp)
		return {
			"content": f"In response to: `{menu.ctx.message.clean_content}`",
			"embed": embed
		}

