
import discord
from discord.ext import commands

import asyncio
import clarifai.rest
import collections
import datetime
import dateutil.parser
import imgurpython
import isodate
import json
import pyowm.exceptions
# import spotipy
import unicodedata
import urllib

import credentials
from modules import utilities
from utilities import checks
from utilities import errors
import clients

def setup(bot):
	bot.add_cog(Resources(bot))

class Resources:
	
	def __init__(self, bot):
		self.bot = bot
		self.lichess_user_data, self.lichess_tournaments_data = None, None
		# spotify = spotipy.Spotify()
	
	@commands.command(aliases = ["antonyms"])
	@checks.not_forbidden()
	async def antonym(self, ctx, word : str):
		'''Antonyms of a word'''
		antonyms = clients.wordnik_word_api.getRelatedWords(word, relationshipTypes = "antonym", useCanonical = "true", limitPerRelationshipType = 100)
		if not antonyms:
			await ctx.embed_reply(":no_entry: Word or antonyms not found")
			return
		await ctx.embed_reply(', '.join(antonyms[0].words), title = "Antonyms of {}".format(word.capitalize()))
	
	@commands.group(aliases = ["blizzard"], invoke_without_command = True)
	@checks.not_forbidden()
	async def battlenet(self, ctx):
		'''Battle.net'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	@battlenet.command(name = "run", aliases = ["launch"])
	@checks.not_forbidden()
	async def battlenet_run(self, ctx, *, game : str):
		'''
		Generate a Battle.net link to launch a game
		You must have the Battle.net launcher open for the link to work
		'''
		lower_game = game.lower()
		if lower_game in ("world of warcraft", "wow"): abbrev = "WoW"
		elif lower_game in ("diablo 3"): abbrev = "D3"
		elif lower_game in ("starcraft 2"): abbrev = "S2"
		elif lower_game in ("hearthstone"): abbrev = "WTCG"
		elif lower_game in ("heroes of the storm", "hots"): abbrev = "Hero"
		elif lower_game in ("overwatch"): abbrev = "Pro"
		else:
			await ctx.embed_reply(":no_entry: Game not found")
			return
		await ctx.embed_reply("[Launch {}](battlenet://{})".format(game, abbrev))
	
	@commands.group(aliases = ["colour"], invoke_without_command = True)
	@checks.not_forbidden()
	async def color(self, ctx, *, color : str):
		'''
		Information on colors
		Accepts hex color codes and search by keyword
		'''
		color = color.strip('#')
		if utilities.is_hex(color) and len(color) == 6:
			url = "http://www.colourlovers.com/api/color/{}?format=json".format(color)
		else:
			url = "http://www.colourlovers.com/api/colors?numResults=1&format=json&keywords={}".format(color)
		await self.process_color(ctx, url)
	
	async def process_color(self, ctx, url):
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json()
		if not data:
			await ctx.embed_reply(":no_entry: Error")
			return
		data = data[0]
		embed = discord.Embed(title = data["title"].capitalize(), description = "#{}".format(data["hex"]), color = clients.bot_color)
		avatar = ctx.author.avatar_url or ctx.author.default_avatar_url
		embed.set_author(name = ctx.author.display_name, icon_url = avatar)
		embed.add_field(name = "RGB", value = "{0[red]}, {0[green]}, {0[blue]}".format(data["rgb"]))
		embed.add_field(name = "HSV", value = "{0[hue]}°, {0[saturation]}%, {0[value]}%".format(data["hsv"]))
		embed.set_image(url = data["imageUrl"])
		await self.bot.say(embed = embed)
	
	@commands.command()
	@checks.not_forbidden()
	async def define(self, ctx, word : str):
		'''Define a word'''
		definition = clients.wordnik_word_api.getDefinitions(word, limit = 1) # useCanonical = True ?
		if not definition:
			await ctx.embed_reply(":no_entry: Definition not found")
			return
		await ctx.embed_reply(definition[0].text, title = definition[0].word.capitalize(), footer_text = definition[0].attributionText)
	
	@commands.command()
	@checks.not_forbidden()
	async def dotabuff(self, ctx, account : str):
		'''Get Dotabuff link'''
		try:
			url = "https://www.dotabuff.com/players/{}".format(int(account) - 76561197960265728)
		except ValueError:
			url = "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={}&vanityurl={}".format(credentials.steam_apikey, account)
			async with clients.aiohttp_session.get(url) as resp:
				data = await resp.json()
			url = "https://www.dotabuff.com/players/{}".format(int(data["response"]["steamid"]) - 76561197960265728)
		await ctx.embed_reply(title = "{}'s Dotabuff profile".format(account), title_url = url)
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def giphy(self, ctx, *, search : str):
		'''Find an image on giphy'''
		url = "http://api.giphy.com/v1/gifs/search?api_key={}&q={}&limit=1".format(credentials.giphy_public_beta_api_key, search)
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json()
		await ctx.embed_reply(image_url = data["data"][0]["images"]["original"]["url"])
	
	@giphy.command(name = "trending")
	async def giphy_trending(self, ctx):
		'''Trending gif'''
		url = "http://api.giphy.com/v1/gifs/trending?api_key={}".format(credentials.giphy_public_beta_api_key)
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json()
		await ctx.embed_reply(image_url = data["data"][0]["images"]["original"]["url"])
	
	@commands.command(aliases = ["imagesearch", "googleimages"])
	@checks.not_forbidden()
	async def googleimage(self, ctx, *, search : str):
		'''Google image search something'''
		url = "https://www.googleapis.com/customsearch/v1?key={}&cx={}&searchType=image&q={}".format(credentials.google_apikey, credentials.google_cse_cx, search.replace(' ', '+'))
		async with clients.aiohttp_session.get(url) as resp:
			if resp.status == 403:
				await ctx.embed_reply(":no_entry: Daily limit exceeded")
				return
			data = await resp.json()
		if "items" not in data:
			await ctx.embed_reply(":no_entry: No images with that search found")
			return
		await ctx.embed_reply(image_url = data["items"][0]["link"], title = "Image of {}".format(search), title_url = data["items"][0]["link"])
		# handle 403 daily limit exceeded error
	
	@commands.command()
	@checks.not_forbidden()
	async def haveibeenpwned(self, ctx, name : str):
		'''Check if your account has been breached'''
		url = "https://haveibeenpwned.com/api/v2/breachedaccount/{0}?truncateResponse=true".format(name)
		async with clients.aiohttp_session.get(url) as resp:
			status = resp.status
			data = await resp.json()
		if status in [404, 400]:
			breachedaccounts = "None"
		else:
			breachedaccounts = ""
			for breachedaccount in data:
				breachedaccounts += breachedaccount["Name"] + ", "
			breachedaccounts = breachedaccounts[:-2]
		url = "https://haveibeenpwned.com/api/v2/pasteaccount/{0}".format(name)
		async with clients.aiohttp_session.get(url) as resp:
			status = resp.status
			data = await resp.json()
		if status in [404, 400]:
			pastedaccounts = "None"
		else:
			pastedaccounts = ""
			for pastedaccount in data:
				pastedaccounts += pastedaccount["Source"] + " (" + pastedaccount["Id"] + "), "
			pastedaccounts = pastedaccounts[:-2]
		await ctx.embed_reply("Breached accounts: {}\nPastes: {}".format(breachedaccounts, pastedaccounts))
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def horoscope(self, ctx, sign : str):
		'''Horoscope'''
		await self.process_horoscope(ctx, sign, "today")
	
	@horoscope.command(name = "signs", aliases = ["sun_signs", "sunsigns"])
	@checks.not_forbidden()
	async def horoscope_signs(self, ctx):
		'''Sun signs'''
		async with clients.aiohttp_session.get("http://sandipbgt.com/theastrologer/api/sunsigns") as resp:
			data = await resp.json()
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
		if len(sign) == 1:
			sign = unicodedata.name(sign).lower()
		async with clients.aiohttp_session.get("http://sandipbgt.com/theastrologer/api/horoscope/{}/{}/".format(sign, day)) as resp:
			if resp.status == 404:
				await ctx.embed_reply(":no_entry: Error")
				return
			data = await resp.json()
		date = [int(d) for d in data["date"].split('-')]
		await ctx.embed_reply(data["horoscope"].replace(data["credit"], ""), title = data["sunsign"], fields = sorted((k.capitalize(), v) for k, v in data["meta"].items()), footer_text = data["credit"], timestamp = datetime.datetime(date[0], date[1], date[2]))
	
	@commands.command(aliases = ["imagerecog", "imager", "image_recognition"])
	@checks.not_forbidden()
	async def imagerecognition(self, ctx, image_url : str):
		'''Image recognition'''
		try:
			response = self.bot.clarifai_general_model.predict_by_url(image_url)
		except clarifai.rest.ApiError as e:
			await ctx.embed_reply(":no_entry: Error: `{}`".format(e.response.json()["outputs"][0]["status"]["details"]))
			return
		if response["status"]["description"] != "Ok":
			await ctx.embed_reply(":no_entry: Error")
			return
		names = {}
		for concept in response["outputs"][0]["data"]["concepts"]:
			names[concept["name"]] = concept["value"] * 100
		output = ""
		for name, value in sorted(names.items(), key = lambda i: i[1], reverse = True):
			output += "**{}**: {:.2f}%, ".format(name, value)
		output = output[:-2]
		await ctx.embed_reply(output)
	
	@commands.command()
	@checks.not_forbidden()
	async def nsfw(self, ctx, image_url : str):
		'''NSFW recognition'''
		try:
			response = self.bot.clarifai_nsfw_model.predict_by_url(image_url)
		except clarifai.rest.ApiError as e:
			await ctx.embed_reply(":no_entry: Error: `{}`".format(e.response.json()["outputs"][0]["status"]["details"]))
			return
		if response["status"]["description"] != "Ok":
			await ctx.embed_reply(":no_entry: Error")
			return
		percentages = {}
		for concept in response["outputs"][0]["data"]["concepts"]:
			percentages[concept["name"]] = concept["value"] * 100
		await ctx.embed_reply("NSFW: {:.2f}%".format(percentages["nsfw"]))
	
	@commands.command(aliases = ["movie"])
	@checks.not_forbidden()
	async def imdb(self, ctx, *search : str):
		'''IMDb Information'''
		url = "http://www.omdbapi.com/?t={}&plot=short".format('+'.join(search))
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json()
		if data["Response"] == "False":
			await ctx.embed_reply(":no_entry: Error: {}".format(data["Error"]))
			return
		embed = discord.Embed(title = data["Title"], url = "http://www.imdb.com/title/{}".format(data["imdbID"]), color = clients.bot_color)
		avatar = ctx.author.avatar_url or ctx.author.default_avatar_url
		embed.set_author(name = ctx.author.display_name, icon_url = avatar)
		embed.description = "{0[Year]} {0[Type]}".format(data)
		embed.add_field(name = "IMDb Rating", value = data["imdbRating"])
		embed.add_field(name = "Runtime", value = data["Runtime"])
		embed.add_field(name = "Genre(s)", value = data["Genre"])
		embed.add_field(name = "Director", value = data["Director"])
		embed.add_field(name = "Writer", value = data["Writer"])
		embed.add_field(name = "Cast", value = data["Actors"])
		embed.add_field(name = "Language", value = data["Language"])
		embed.add_field(name = "Country", value = data["Country"])
		embed.add_field(name = "Awards", value = data["Awards"])
		if "totalSeasons" in data: embed.add_field(name = "Total Seasons", value = data["totalSeasons"])
		embed.add_field(name = "Plot", value = data["Plot"], inline = False)
		if data["Poster"] != "N/A": embed.set_thumbnail(url = data["Poster"])
		await self.bot.say(embed = embed)
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def imgur(self, ctx):
		'''Imgur'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	@imgur.command(name = "upload")
	@checks.not_forbidden()
	async def imgur_upload(self, ctx, url : str = ""):
		'''Upload images to Imgur'''
		if url:
			await self._imgur_upload(ctx, url)
		if ctx.message.attachments:
			await self._imgur_upload(ctx, ctx.message.attachments[0]["url"])
		if not (url or ctx.message.attachments):
			await ctx.embed_reply(":no_entry: Please input an image and/or url")
	
	async def _imgur_upload(self, ctx, url):
		try:
			await ctx.embed_reply(self.bot.imgur_client.upload_from_url(url)["link"])
		except imgurpython.helpers.error.ImgurClientError as e:
			await ctx.embed_reply(":no_entry: Error: {}".format(e))
	
	@commands.group()
	@checks.not_forbidden()
	async def lichess(self, ctx):
		'''WIP'''
		return
	
	@lichess.group(name = "user")
	async def lichess_user(self, ctx):
		'''WIP'''
		if len(ctx.message.content.split()) == 2:
			pass
		elif len(ctx.message.content.split()) >= 4:
			url = "https://en.lichess.org/api/user/{}".format(ctx.message.content.split()[3])
			async with clients.aiohttp_session.get(url) as resp:
				self.lichess_user_data = await resp.json()
			if not self.lichess_user_data:
				raise errors.LichessUserNotFound
	
	@lichess_user.command(name = "bullet")
	async def lichess_user_bullet(self, ctx, username : str):
		'''WIP'''
		data = self.lichess_user_data
		await self.bot.embed_reply(":zap: Bullet | **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {chart} {0[prog]}".format(data["perfs"]["bullet"], prov = "?" if data["perfs"]["bullet"]["prov"] else "", chart = ":chart_with_upwards_trend:" if data["perfs"]["bullet"]["prog"] >= 0 else ":chart_with_downwards_trend:"), title = data["username"])
	
	@lichess_user.command(name = "blitz")
	async def lichess_user_blitz(self, ctx, username : str):
		'''WIP'''
		data = self.lichess_user_data
		await self.bot.embed_reply(":fire: Blitz | **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {chart} {0[prog]}".format(data["perfs"]["blitz"], prov = "?" if data["perfs"]["blitz"]["prov"] else "", chart = ":chart_with_upwards_trend:" if data["perfs"]["blitz"]["prog"] >= 0 else ":chart_with_downwards_trend:"), title = data["username"])
	
	@lichess_user.error
	async def lichess_user_error(self, error, ctx):
		if isinstance(error, errors.LichessUserNotFound):
			await self.bot.embed_reply(":no_entry: User not found")
	
	@lichess_user.command(name = "all")
	async def lichess_user_all(self, ctx, username : str):
		'''WIP'''
		data = self.lichess_user_data
		embed = discord.Embed(title = data["username"], url = data["url"], color = clients.bot_color)
		avatar = ctx.author.avatar_url or ctx.author.default_avatar_url
		embed.set_author(name = ctx.author.display_name, icon_url = avatar)
		embed.description = "Online: {}\n".format(data["online"])
		embed.description += "Member since {}\n".format(datetime.datetime.utcfromtimestamp(data["createdAt"] / 1000.0).strftime("%b %#d, %Y")) #
		embed.add_field(name = "Games", value = "Played: {0[all]}\nRated: {0[rated]}\nWins: {0[win]}\nLosses: {0[loss]}\nDraws: {0[draw]}\nBookmarks: {0[bookmark]}\nAI: {0[ai]}".format(data["count"]))
		embed.add_field(name = "Follows", value = "Followers: {0[nbFollowers]}\nFollowing: {0[nbFollowing]}".format(data))
		embed.add_field(name = "Time", value = "Spent playing: {}\nOn TV: {}".format(utilities.secs_to_letter_format(data["playTime"]["total"]), utilities.secs_to_letter_format(data["playTime"]["tv"])))
		for mode, field_name in (("bullet", ":zap: Bullet"), ("blitz", ":fire: Blitz"), ("classical", ":hourglass: Classical"), ("correspondence", ":envelope: Correspondence"), ("crazyhouse", ":pisces: Crazyhouse"), ("chess960", ":game_die: Chess960"), ("kingOfTheHill", ":triangular_flag_on_post: King Of The Hill"), ("threeCheck", ":three: Three-Check"), ("antichess", ":arrows_clockwise: Antichess"), ("atomic", ":atom: Atomic"), ("horde", ":question: Horde"), ("racingKings", ":checkered_flag: Racing Kings"), ("puzzle", ":bow_and_arrow: Training")):
			if data["perfs"].get(mode, {}).get("games", 0) == 0: continue
			prov = '?' if data["perfs"][mode]["prov"] else ""
			chart = ":chart_with_upwards_trend:" if data["perfs"][mode]["prog"] >= 0 else ":chart_with_downwards_trend:"
			value = "Games: {0[games]}\nRating: {0[rating]}{1} ± {0[rd]}\n{2} {0[prog]}".format(data["perfs"][mode], prov, chart)
			embed.add_field(name = field_name, value = value)
		embed.set_footer(text = "Last seen")
		embed.timestamp = datetime.datetime.utcfromtimestamp(data["seenAt"] / 1000.0)
		await self.bot.say(embed = embed)
	
	@lichess.group(name = "tournaments")
	async def lichess_tournaments(self, ctx):
		'''WIP'''
		url = "https://en.lichess.org/api/tournament"
		async with clients.aiohttp_session.get(url) as resp:
			self.lichess_tournaments_data = await resp.json()
	
	@lichess_tournaments.command(name = "current", aliases = ["started"])
	async def lichess_tournaments_current(self, ctx):
		'''WIP'''
		data = self.lichess_tournaments_data["started"]
		embed = discord.Embed(title = "Current Lichess Tournaments", color = clients.bot_color)
		avatar = ctx.author.avatar_url or ctx.author.default_avatar_url
		embed.set_author(name = ctx.author.display_name, icon_url = avatar)
		for tournament in data:
			value = "{:g}+{} {} {rated}".format(tournament["clock"]["limit"] / 60, tournament["clock"]["increment"], tournament["perf"]["name"], rated = "Rated" if tournament["rated"] else "Casual")
			value += "\nEnds in: {:g}m".format((datetime.datetime.utcfromtimestamp(tournament["finishesAt"] / 1000.0) - datetime.datetime.utcnow()).total_seconds() // 60)
			value += "\n[Link](https://en.lichess.org/tournament/{})".format(tournament["id"])
			embed.add_field(name = tournament["fullName"], value = value)
		await self.bot.say(embed = embed)
	
	@lichess.command(name = "tournament")
	async def lichess_tournament(self, ctx):
		'''WIP'''
		pass
	
	@commands.command()
	@checks.not_forbidden()
	async def longurl(self, ctx, url : str):
		'''Expand a short goo.gl url'''
		url = "https://www.googleapis.com/urlshortener/v1/url?shortUrl={}&key={}".format(url, credentials.google_apikey)
		async with clients.aiohttp_session.get(url) as resp:
			if resp.status == 400:
				await ctx.embed_reply(":no_entry: Error")
				return
			data = await resp.json()
		await ctx.embed_reply(data["longUrl"])
	
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
	async def news(self, ctx, source : str):
		'''
		News
		Powered by NewsAPI.org
		'''
		async with clients.aiohttp_session.get("https://newsapi.org/v1/articles?source={}&apiKey={}".format(source, credentials.news_api_key)) as resp:
			data = await resp.json()
		if data["status"] != "ok":
			await ctx.embed_reply(":no_entry: Error: {}".format(data["message"]))
			return
		'''
		paginator = commands.formatter.Paginator(prefix = "{}:".format(ctx.author.display_name), suffix = "")
		for article in data["articles"]:
			paginator.add_line("**{}** ({})".format(article["title"], article["publishedAt"].replace('T', " ").replace('Z', "")))
			paginator.add_line("{}".format(article["description"]))
			paginator.add_line("<{}>".format(article["url"]))
			# output += "\n{}".format(article["urlToImage"])
		for page in paginator.pages:
			await self.bot.say(page)
		'''
		response, embed = await self.bot.reply("React with a number from 1 to 10 to view each news article")
		numbers = {'\N{KEYCAP TEN}': 10}
		for number in range(9):
			numbers[chr(ord('\u0031') + number) + '\N{COMBINING ENCLOSING KEYCAP}'] = number + 1 # '\u0031' - 1
		for number_emote in sorted(numbers.keys()):
			await self.bot.add_reaction(response, number_emote)
		while True:
			emoji_response = await self.bot.wait_for_reaction(user = ctx.author, message = response, emoji = numbers.keys())
			reaction = emoji_response.reaction
			number = numbers[reaction.emoji]
			article = data["articles"][number - 1]
			output = "Article {}:".format(number)
			output += "\n**{}**".format(article["title"])
			if article.get("publishedAt"):
				output += " ({})".format(article.get("publishedAt").replace('T', " ").replace('Z', ""))
			# output += "\n{}".format(article["description"])
			# output += "\n<{}>".format(article["url"])
			output += "\n{}".format(article["url"])
			output += "\nSelect a different number for another article"
			await self.bot.edit_message(response, "{}: {}".format(ctx.author.display_name, output))
	
	@news.command(name = "sources")
	@checks.not_forbidden()
	async def news_sources(self, ctx):
		'''
		News sources
		https://newsapi.org/sources
		'''
		async with clients.aiohttp_session.get("https://newsapi.org/v1/sources") as resp:
			data = await resp.json()
		if data["status"] != "ok":
			await ctx.embed_reply(":no_entry: Error")
			return
		# for source in data["sources"]:
		await self.bot.reply("<https://newsapi.org/sources>\n{}".format(", ".join([source["id"] for source in data["sources"]])))
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def oeis(self, ctx, *, search : str):
		'''
		The On-Line Encyclopedia of Integer Sequences
		Does not accept spaces for search by sequence
		'''
		url = "http://oeis.org/search?fmt=json&q=" + search
		async with clients.aiohttp_session.get(url) as resp:
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
		'''
		The On-Line Encyclopedia of Integer Sequences
		Does not accept spaces for search by sequence
		Returns sequence graph if found
		'''
		url = "http://oeis.org/search?fmt=json&q=" + search
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json()
		if data["results"]:
			await ctx.embed_reply(image_url = "https://oeis.org/A{:06d}/graph?png=1".format(data["results"][0]["number"]))
		elif data["count"]:
			await ctx.embed_reply(":no_entry: Too many sequences found")
		else:
			await ctx.embed_reply(":no_entry: Sequence not found")
	
	@commands.command()
	@checks.not_forbidden()
	async def phone(self, ctx, *, phone : str): # add reactions version
		'''Get phone specifications'''
		async with clients.aiohttp_session.get("https://fonoapi.freshpixl.com/v1/getdevice?device={}&position=0&token={}".format(phone.replace(' ', '+'), credentials.fonoapi_token)) as resp:
			data = await resp.json()
		if "status" in data and data["status"] == "error":
			await ctx.embed_reply(":no_entry: Error: {}".format(data["message"]))
			return
		data = data[0]
		embed = discord.Embed(title = data["DeviceName"], color = clients.bot_color)
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
		await self.bot.say(embed = embed)
	
	@commands.command(aliases = ["audiodefine", "pronounce"])
	@checks.not_forbidden()
	async def pronunciation(self, ctx, word : str):
		'''Pronunciation of a word'''
		pronunciation = clients.wordnik_word_api.getTextPronunciations(word, limit = 1)
		description = pronunciation[0].raw.strip("()") if pronunciation else "Audio File Link"
		audio_file = clients.wordnik_word_api.getAudio(word, limit = 1)
		if audio_file:
			description = "[{}]({})".format(description, audio_file[0].fileUrl)
		elif not pronunciation:
			await ctx.embed_reply(":no_entry: Word or pronunciation not found")
			return
		await ctx.embed_reply(description, title = "Pronunciation of {}".format(word.capitalize()))
	
	@commands.command(hidden = True)
	@checks.not_forbidden()
	async def redditsearch(self, ctx):
		'''WIP'''
		return
	
	@commands.command(aliases = ["rhymes"])
	@checks.not_forbidden()
	async def rhyme(self, ctx, word : str):
		'''Rhymes of a word'''
		rhymes = clients.wordnik_word_api.getRelatedWords(word, relationshipTypes = "rhyme", limitPerRelationshipType = 100)
		if not rhymes:
			await ctx.embed_reply(":no_entry: Word or rhymes not found")
			return
		await ctx.embed_reply(', '.join(rhymes[0].words), title = "Words that rhyme with {}".format(word.capitalize()))
	
	@commands.group(aliases = ["realmofthemadgod"], invoke_without_command = True)
	@checks.not_forbidden()
	async def rotmg(self, ctx, player : str):
		'''Realm of the Mad God player information'''
		url = "https://nightfirec.at/realmeye-api/?player={}".format(player)
		# http://webhost.ischool.uw.edu/~joatwood/realmeye_api/0.3/
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json()
		if "error" in data:
			await ctx.embed_reply("Error: " + data["error"])
			return
		embed = discord.Embed(title = data["player"], url = "https://www.realmeye.com/player/{}".format(player), color = clients.bot_color)
		avatar = ctx.author.avatar_url or ctx.author.default_avatar_url
		embed.set_author(name = ctx.author.display_name, icon_url = avatar)
		if data["donator"] == "true": embed.description = "Donator"
		embed.add_field(name = "Characters", value = data["chars"])
		embed.add_field(name = "Total Fame", value = "{:,}".format(data["fame"]))
		embed.add_field(name = "Fame Rank", value = "{:,}".format(data["fame_rank"]))
		embed.add_field(name = "Class Quests Completed", value = data["rank"])
		embed.add_field(name = "Account Fame", value = "{:,}".format(data["account_fame"]))
		embed.add_field(name = "Account Fame Rank", value = "{:,}".format(data["account_fame_rank"]))
		embed.add_field(name = "Created", value = data["created"])
		embed.add_field(name = "Total Exp", value = "{:,}".format(data["exp"]))
		embed.add_field(name = "Exp Rank", value = "{:,}".format(data["exp_rank"]))
		embed.add_field(name = "Last Seen", value = data["last_seen"])
		if "guild" in data:
			embed.add_field(name = "Guild", value = data["guild"])
			embed.add_field(name = "Guild Position", value = data["guild_rank"])
		if data["desc1"] or data["desc2"] or data["desc3"]:
			embed.add_field(name = "Description", value = "{}\n{}\n{}".format(data["desc1"], data["desc2"], data["desc3"]))
		await self.bot.say(embed = embed)
	
	@rotmg.command(name = "characters")
	@checks.not_forbidden()
	async def rotmg_characters(self, ctx, player : str):
		'''Realm of the Mad God player characters information'''
		url = "https://nightfirec.at/realmeye-api/?player={}".format(player)
		# http://webhost.ischool.uw.edu/~joatwood/realmeye_api/0.3/
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json()
		if "error" in data:
			await ctx.embed_reply("Error: " + data["error"])
			return
		embed = discord.Embed(title = "{}'s Characters".format(data["player"]), color = clients.bot_color)
		avatar = ctx.author.avatar_url or ctx.author.default_avatar_url
		embed.set_author(name = ctx.author.display_name, icon_url = avatar)
		for character in data["characters"]:
			value = "Fame: {0[fame]:,}, Exp: {0[exp]:,}, Rank: {0[place]:,}, Class Quests Completed: {0[cqc]}, Stats Maxed: {0[stats_maxed]}".format(character)
			value += "\nHP: {0[hp]}, MP: {0[mp]}, Attack: {0[attack]}, Defense: {0[defense]}, Speed: {0[speed]}, Vitality: {0[vitality]}, Wisdom: {0[wisdom]}, Dexterity: {0[dexterity]}".format(character["stats"])
			equips = []
			for type, equip in character["equips"].items():
				equips.append("{}: {}".format(type.capitalize(), equip))
			value += '\n' + ", ".join(equips)
			value += "\nPet: {0[pet]}, Clothing Dye: {0[character_dyes][clothing_dye]}, Accessory Dye: {0[character_dyes][accessory_dye]}, Backpack: {0[backpack]}".format(character)
			value += "\nLast Seen: {0[last_seen]}, Last Server: {0[last_server]}".format(character)
			embed.add_field(name = "Level {0[level]} {0[class]}".format(character), value = value, inline = False)
		await self.bot.say(embed = embed)
	
	@commands.command()
	@checks.not_forbidden()
	async def shorturl(self, ctx, url : str):
		'''Generate a short goo.gl url for your link'''
		short_url = await self._shorturl(url)
		await ctx.embed_reply(short_url)
	
	async def _shorturl(self, url):
		async with clients.aiohttp_session.post("https://www.googleapis.com/urlshortener/v1/url?key={}".format(credentials.google_apikey), headers = {'Content-Type': 'application/json'}, data = '{"longUrl": "' + url +'"}') as resp:
			data = await resp.json()
		return data["id"]
	
	@commands.command()
	@checks.not_forbidden()
	async def spellcheck(self, ctx, *, words : str):
		'''Spell check words'''
		async with clients.aiohttp_session.post("https://api.cognitive.microsoft.com/bing/v5.0/spellcheck?Text=" + words.replace(' ', '+'), headers = {"Ocp-Apim-Subscription-Key" : credentials.bing_spell_check_key}) as resp:
			data = await resp.json()
		corrections = data["flaggedTokens"]
		corrected = words
		offset = 0
		for correction in corrections:
			offset += correction["offset"]
			suggestion = correction["suggestions"][0]["suggestion"]
			corrected = corrected[:offset] + suggestion + corrected[offset + len(correction["token"]):]
			offset += (len(suggestion) - len(correction["token"])) - correction["offset"]
		await ctx.embed_reply(corrected)
	
	@commands.command(aliases = ["spotify_info"])
	@checks.not_forbidden()
	async def spotifyinfo(self, ctx, url : str):
		'''Information about a Spotify track'''
		path = urllib.parse.urlparse(url).path
		if path[:7] != "/track/":
			await self.bot.embed_reply(":no_entry: Syntax error")
			return
		trackid = path[7:]
		api_url = "https://api.spotify.com/v1/tracks/" + trackid
		async with clients.aiohttp_session.get(api_url) as resp:
			data = await resp.json()
		# tracknumber = str(data["track_number"])
		description = "Artist: [{}]({})\n".format(data["artists"][0]["name"], data["artists"][0]["external_urls"]["spotify"])
		description += "Album: [{}]({})\n".format(data["album"]["name"], data["album"]["external_urls"]["spotify"])
		description += "Duration: {}\n".format(utilities.secs_to_colon_format(data["duration_ms"] / 1000))
		description += "[Preview]({})".format(data["preview_url"])
		await self.bot.embed_reply(description, title = data["name"], title_url = url, thumbnail_url = data["album"]["images"][0]["url"])
	
	@commands.command(aliases = ["sptoyt", "spotify_to_youtube", "sp_to_yt"])
	@checks.not_forbidden()
	async def spotifytoyoutube(self, ctx, url : str):
		'''Find a Spotify track on Youtube'''
		link = await self.bot.cogs["Audio"].spotify_to_youtube(url)
		if link:
			await self.bot.reply(link)
		else:
			await ctx.embed_reply(":no_entry: Error")
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def steam(self, ctx):
		'''Steam Information'''
		return
	
	@steam.command(name = "appid")
	@checks.not_forbidden()
	async def steam_appid(self, ctx, *, app : str):
		'''Get the AppID'''
		async with clients.aiohttp_session.get("http://api.steampowered.com/ISteamApps/GetAppList/v0002/") as resp:
			data = await resp.json()
		apps = data["applist"]["apps"]
		appid = 0
		for _app in apps:
			if _app["name"].lower() == app.lower():
				appid = _app["appid"]
				break
		await ctx.embed_reply(appid)
	
	@steam.command(name = "gamecount", aliases = ["game_count"])
	@checks.not_forbidden()
	async def steam_gamecount(self, ctx, vanity_name : str):
		'''Find how many games someone has'''
		url = "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={0}&vanityurl={1}".format(credentials.steam_apikey, vanity_name)
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json()
		id = data["response"]["steamid"]
		url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={0}&steamid={1}".format(credentials.steam_apikey, id)
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json()
		gamecount = data["response"]["game_count"]
		await ctx.embed_reply("{} has {} games".format(vanity_name, gamecount))
	
	@steam.command(name = "gameinfo", aliases = ["game_info"])
	@checks.not_forbidden()
	async def steam_gameinfo(self, ctx, *, game : str):
		'''Information about a game'''
		async with clients.aiohttp_session.get("http://api.steampowered.com/ISteamApps/GetAppList/v0002/") as resp:
			data = await resp.json()
		app = discord.utils.find(lambda app: app["name"].lower() == game.lower(), data["applist"]["apps"])
		if not app:
			await ctx.embed_reply(":no_entry: Game not found")
			return
		appid = str(app["appid"])
		url = "http://store.steampowered.com/api/appdetails/?appids={}".format(appid)
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json()
		data = data[appid]["data"]
		await ctx.embed_reply(data["short_description"], title = data["name"], title_url = data["website"], fields = (("Release Date", data["release_date"]["date"]), ("Free", "Yes" if data["is_free"] else "No"), ("App ID", data["steam_appid"])), image_url = data["header_image"])
	
	@steam.command(name = "run", aliases = ["launch"])
	@checks.not_forbidden()
	async def steam_run(self, ctx, *, game : str):
		'''Generate a steam link to launch a game'''
		async with clients.aiohttp_session.get("http://api.steampowered.com/ISteamApps/GetAppList/v0002/") as resp:
			data = await resp.json()
		app = discord.utils.find(lambda app: app["name"].lower() == game.lower(), data["applist"]["apps"])
		if not app:
			await ctx.embed_reply(":no_entry: Game not found")
			return
		appid = app["appid"]
		await ctx.embed_reply("[Launch {}](steam://run/{})".format(game, appid))
	
	@commands.command()
	@checks.not_forbidden()
	async def strawpoll(self, ctx, question : str, *options : str):
		'''
		Generate a strawpoll link
		Use qoutes for spaces in the question or options
		'''
		async with clients.aiohttp_session.post("https://strawpoll.me/api/v2/polls", data = json.dumps({"title" : question, "options" : options})) as resp:
			poll = await resp.json()
		await self.bot.reply("http://strawpoll.me/" + str(poll["id"]))
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def streetview(self, ctx, *, location : str):
		'''Generate street view of a location'''
		image_url = "https://maps.googleapis.com/maps/api/streetview?size=400x400&location={}".format(location.replace(' ', '+'))
		await ctx.embed_reply(image_url = image_url)
	
	@commands.command(aliases = ["synonyms"])
	@checks.not_forbidden()
	async def synonym(self, ctx, word : str):
		'''Synonyms of a word'''
		synonyms = clients.wordnik_word_api.getRelatedWords(word, relationshipTypes = "synonym", useCanonical = "true", limitPerRelationshipType = 100)
		if not synonyms:
			await ctx.embed_reply(":no_entry: Word or synonyms not found")
			return
		await ctx.embed_reply(', '.join(synonyms[0].words), title = "Synonyms of {}".format(word.capitalize()))
	
	@commands.group(description = "[Language Codes](https://tech.yandex.com/translate/doc/dg/concepts/api-overview-docpage/#languages)\n"
	"Powered by [Yandex.Translate](http://translate.yandex.com/)", invoke_without_command = True)
	@checks.not_forbidden()
	async def translate(self, ctx, *, text : str):
		'''Translate to English'''
		# TODO: From and to language code options?
		await self.process_translate(ctx, text, "en")
	
	@translate.command(name = "from")
	@checks.not_forbidden()
	async def translate_from(self, ctx, from_language_code : str, to_language_code : str, *, text : str):
		'''
		Translate from a specific language to another
		[Language Codes](https://tech.yandex.com/translate/doc/dg/concepts/api-overview-docpage/#languages)
		Powered by [Yandex.Translate](http://translate.yandex.com/)
		'''
		# TODO: Default to_language_code?
		await self.process_translate(ctx, text, to_language_code, from_language_code)
	
	@translate.command(name = "languages", aliases = ["codes", "language_codes"])
	@checks.not_forbidden()
	async def translate_languages(self, ctx, language_code : str = "en"):
		'''Language Codes'''
		async with clients.aiohttp_session.get("https://translate.yandex.net/api/v1.5/tr.json/getLangs?ui={}&key={}".format(language_code, credentials.yandex_translate_api_key)) as resp:
			data = await resp.json()
		if "langs" not in data:
			await ctx.embed_reply(":no_entry: Error: Invalid Language Code")
			return
		await ctx.embed_reply(", ".join(sorted("{} ({})".format(language, code) for code, language in data["langs"].items())))
	
	@translate.command(name = "to")
	@checks.not_forbidden()
	async def translate_to(self, ctx, language_code : str, *, text : str):
		'''
		Translate to a specific language
		[Language Codes](https://tech.yandex.com/translate/doc/dg/concepts/api-overview-docpage/#languages)
		Powered by [Yandex.Translate](http://translate.yandex.com/)
		'''
		await self.process_translate(ctx, text, language_code)
	
	async def process_translate(self, ctx, text, to_language_code, from_language_code = None):
		url = "https://translate.yandex.net/api/v1.5/tr.json/translate?key={}&lang={}&text={}&options=1".format(credentials.yandex_translate_api_key, to_language_code if not from_language_code else "{}-{}".format(from_language_code, to_language_code), text.replace(' ', '+'))
		async with clients.aiohttp_session.get(url) as resp:
			if resp.status == 400: # Bad Request
				await ctx.embed_reply(":no_entry: Error")
				return
			data = await resp.json()
		if data["code"] != 200:
			await ctx.embed_reply(":no_entry: Error: {}".format(data["message"]))
			return
		await ctx.embed_reply(data["text"][0], footer_text = "{}Powered by Yandex.Translate".format("Detected Language Code: {} | ".format(data["detected"]["lang"]) if not from_language_code else ""))
	
	@commands.command(aliases = ["urband", "urban_dictionary", "urbandefine", "urban_define"])
	@checks.not_forbidden()
	async def urbandictionary(self, ctx, *, term : str):
		'''Urban Dictionary'''
		# TODO: Integrate into reactions system; Return first definition instead for non-reaction version?
		async with clients.aiohttp_session.get("http://api.urbandictionary.com/v0/define?term={}".format(term.replace('+', ' '))) as resp:
			data = await resp.json()
		if not data or "list" not in data or not data["list"]:
			await ctx.embed_reply(":no_entry: No results found")
			return
		num_results = len(data["list"]) # if one definition
		if num_results > 10: num_reults = 10
		response = await ctx.embed_reply("React with a number from 1 to {} to view each definition".format(num_results))
		embed = response.embeds[0]
		numbers = {"1⃣": 1, "2⃣": 2, "3⃣": 3, "4⃣": 4, "5⃣": 5, "6⃣": 6, "7⃣": 7, "8⃣": 8, "9⃣": 9, "🔟" : 10}
		for number_emote in sorted(numbers.keys())[:num_results]:
			await self.bot.add_reaction(response, number_emote)
		while True:
			emoji_response = await self.bot.wait_for_reaction(user = ctx.author, message = response, emoji = sorted(numbers.keys())[:num_results])
			reaction = emoji_response.reaction
			number = numbers[reaction.emoji]
			definition = data["list"][number - 1]
			embed.clear_fields()
			embed.title = definition["word"]
			embed.url = definition["permalink"]
			embed.description = definition["definition"]
			# TODO: Check description/definition length?
			embed.add_field(name = "Example", value = "{0[example]}\n\n:thumbsup::skin-tone-2: {0[thumbs_up]} :thumbsdown::skin-tone-2: {0[thumbs_down]}".format(definition))
			embed.set_footer(text = "Select a different number for another definition")
			await self.bot.edit_message(response, embed = embed)
	
	@commands.command()
	@checks.not_forbidden()
	async def weather(self, ctx, *, location : str):
		'''Weather'''
		# wunderground?
		try:
			observation = clients.owm_client.weather_at_place(location)
		except pyowm.exceptions.not_found_error.NotFoundError:
			await ctx.embed_reply(":no_entry: Location not found")
			return
		except pyowm.exceptions.api_call_error.BadGatewayError:
			await ctx.embed_reply(":no_entry: Error")
			# Add exception message to response when pyowm issue (https://github.com/csparpa/pyowm/issues/176) fixed
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
		avatar = ctx.author.avatar_url or ctx.author.default_avatar_url
		embed.set_author(name = ctx.author.display_name, icon_url = avatar)
		embed.add_field(name = "Conditions", value = "{}{}".format(condition, emote))
		embed.add_field(name = "Temperature", value = "{}°C\n{}°F".format(weather.get_temperature(unit = "celsius")["temp"], weather.get_temperature(unit = "fahrenheit")["temp"]))
		embed.add_field(name = "Wind", value = "{0} {1:.2f} km/h\n{0} {2:.2f} mi/h".format(self.wind_degrees_to_direction(wind["deg"]), wind["speed"] * 3.6, wind["speed"] * 2.236936))
		embed.add_field(name = "Humidity", value = "{}%".format(weather.get_humidity()))
		embed.add_field(name = "Pressure", value = "{} mb (hPa)\n{:.2f} inHg".format(pressure, pressure * 0.0295299830714))
		if visibility: embed.add_field(name = "Visibility", value = "{:.2f} km\n{:.2f} mi".format(visibility / 1000, visibility * 0.000621371192237))
		await self.bot.say(embed = embed)
	
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
		elif 258.75 <= degrees <= 281.25: return "W"
		elif 281.25 <= degrees <= 303.75: return "WNW"
		elif 303.75 <= degrees <= 326.25: return "NW"
		elif 326.25 <= degrees <= 348.75: return "NNW"
		else: return None
	
	@commands.command()
	@checks.not_forbidden()
	async def websitescreenshot(self, ctx, url : str):
		'''Take a screenshot of a website'''
		response, embed = None, None
		while True:
			async with clients.aiohttp_session.get("http://api.page2images.com/restfullink?"
			"p2i_url={}&p2i_screen=1280x1024&p2i_size=1280x0&p2i_fullpage=1&p2i_key={}".format(url, credentials.page2images_api_key)) as resp:
				data = await resp.json()
			if data["status"] == "processing":
				wait_time = int(data["estimated_need_time"])
				if response and embed:
					embed.description = "Processing {}\nEstimated wait time: {} sec".format(url, wait_time)
					await self.bot.edit_message(response, embed = embed)
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
			url = "https://kgsearch.googleapis.com/v1/entities:search?limit=1&query={}&key={}".format('+'.join(search), credentials.google_apikey)
			async with clients.aiohttp_session.get(url) as resp:
				data = await resp.json()
			if data.get("itemListElement") and data["itemListElement"][0].get("result", {}).get("detailedDescription", {}).get("articleBody", {}):
				await ctx.embed_reply(data["itemListElement"][0]["result"]["detailedDescription"]["articleBody"])
			else:
				await ctx.embed_reply("I don't know what that is")
	
	@commands.group(aliases = ["worldofwarcraft"])
	@checks.not_forbidden()
	async def wow(self, ctx):
		'''World of Warcraft'''
		pass
	
	@wow.command(name = "character")
	@checks.not_forbidden()
	async def wow_character(self, ctx, character : str, *, realm : str):
		'''WIP'''
		# get classes
		classes = {}
		async with clients.aiohttp_session.get("https://us.api.battle.net/wow/data/character/classes?apikey={}".format(credentials.battle_net_api_key)) as resp:
			data = await resp.json()
		for wow_class in data["classes"]:
			classes[wow_class["id"]] = wow_class["name"]
		# get races
		races = {}
		async with clients.aiohttp_session.get("https://us.api.battle.net/wow/data/character/races?apikey={}".format(credentials.battle_net_api_key)) as resp:
			data = await resp.json()
		for wow_race in data["races"]:
			races[wow_race["id"]] = wow_race["name"]
			# add side/faction?
		genders = {0: "Male", 1: "Female"}
		async with clients.aiohttp_session.get("https://us.api.battle.net/wow/character/{}/{}?apikey={}".format(realm, character, credentials.battle_net_api_key)) as resp:
			data = await resp.json()
			if resp.status != 200:
				await ctx.embed_reply(":no_entry: Error: {}".format(data["reason"]))
				return
		embed = discord.Embed(title = data["name"], url = "http://us.battle.net/wow/en/character/{}/{}/".format(data["realm"].replace(' ', '-'), data["name"]), description = "{} ({})".format(data["realm"], data["battlegroup"]), color = clients.bot_color)
		avatar = ctx.author.avatar_url or ctx.author.default_avatar_url
		embed.set_author(name = ctx.author.display_name, icon_url = avatar)
		embed.add_field(name = "Level", value = data["level"])
		embed.add_field(name = "Achievement Points", value = data["achievementPoints"])
		embed.add_field(name = "Class", value = "{}\n[Talent Calculator](http://us.battle.net/wow/en/tool/talent-calculator#{})".format(classes.get(data["class"], "Unknown"), data["calcClass"]))
		embed.add_field(name = "Race", value = races.get(data["race"], "Unknown"))
		embed.add_field(name = "Gender", value = genders.get(data["gender"], "Unknown"))
		embed.set_thumbnail(url = "http://render-us.worldofwarcraft.com/character/{}".format(data["thumbnail"]))
		embed.set_footer(text = "Last seen")
		embed.timestamp = datetime.datetime.utcfromtimestamp(data["lastModified"] / 1000.0)
		await self.bot.say(embed = embed)
		# faction and total honorable kills?
	
	@wow.command(name = "statistics")
	@checks.not_forbidden()
	async def wow_statistics(self, ctx, character : str, *, realm : str):
		'''WIP'''
		async with clients.aiohttp_session.get("https://us.api.battle.net/wow/character/{}/{}?fields=statistics&apikey={}".format(realm, character, credentials.battle_net_api_key)) as resp:
			data = await resp.json()
		embed = discord.Embed(title = data["name"], url = "http://us.battle.net/wow/en/character/{}/{}/".format(data["realm"].replace(' ', '-'), data["name"]), description = "{} ({})".format(data["realm"], data["battlegroup"]), color = clients.bot_color)
		avatar = ctx.author.avatar_url or ctx.author.default_avatar_url
		embed.set_author(name = ctx.author.display_name, icon_url = avatar)
		statistics = data["statistics"]
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def xkcd(self, ctx, number : int = 0):
		'''Find xkcd's'''
		if not number:
			url = "http://xkcd.com/info.0.json" # http://dynamic.xkcd.com/api-0/jsonp/comic/
		else:
			url = "http://xkcd.com/{0}/info.0.json".format(number) # http://dynamic.xkcd.com/api-0/jsonp/comic/#
		await self.process_xkcd(ctx, url)
	
	async def process_xkcd(self, ctx, url):
		async with clients.aiohttp_session.get(url) as resp:
			if resp.status == 404:
				await ctx.embed_reply(":no_entry: Error")
				return
			data = await resp.json()
		await ctx.embed_reply(title = data["title"], title_url = "http://xkcd.com/{}".format(data["num"]), image_url = data["img"], footer_text = data["alt"], timestamp = datetime.datetime(int(data["year"]), int(data["month"]), int(data["day"])))
	
	@commands.command(aliases = ["ytinfo", "youtube_info", "yt_info"])
	@checks.not_forbidden()
	async def youtubeinfo(self, ctx, url : str):
		'''Information on Youtube videos'''
		# TODO: Add to audio cog?
		'''
		toggles = {}
		with open(message.guild.name + "_toggles.json", "r") as toggles_file:
			toggles = json.load(toggles_file)
		if message.content.split()[1] == "on":
			toggles["youtubeinfo"] = True
			with open(message.guild.name + "_toggles.json", "w") as toggles_file:
				json.dump(toggles, toggles_file, indent = 4)
		elif message.content.split()[1] == "off":
			toggles["youtubeinfo"] = False
			with open(message.guild.name + "_toggles.json", "w") as toggles_file:
				json.dump(toggles, toggles_file, indent = 4)
		else:
		'''
		url_data = urllib.parse.urlparse(url)
		query = urllib.parse.parse_qs(url_data.query)
		if 'v' not in query:
			await self.bot.embed_reply(":no_entry: Invalid input")
			return
		videoid = query['v'][0]
		api_url = "https://www.googleapis.com/youtube/v3/videos?id={0}&key={1}&part=snippet,contentDetails,statistics".format(videoid, credentials.google_apikey)
		async with clients.aiohttp_session.get(api_url) as resp:
			data = await resp.json()
		if not data:
			await self.bot.embed_reply(":no_entry: Error")
			return
		data = data["items"][0]
		info = "Length: {}".format(utilities.secs_to_letter_format(isodate.parse_duration(data["contentDetails"]["duration"]).total_seconds()))
		likes, dislikes = int(data["statistics"]["likeCount"]), int(data["statistics"]["dislikeCount"])
		info += "\nLikes: {:,}, Dislikes: {:,} ({:.2f}%)".format(likes, dislikes, likes / (likes + dislikes) * 100)
		info += "\nViews: {:,}, Comments: {:,}".format(int(data["statistics"]["viewCount"]), int(data["statistics"]["commentCount"]))
		info += "\nChannel: [{0[channelTitle]}](https://www.youtube.com/channel/{0[channelId]})".format(data["snippet"])
		# data["snippet"]["description"]
		await self.bot.embed_reply(info, title = data["snippet"]["title"], title_url = url, thumbnail_url = data["snippet"]["thumbnails"]["high"]["url"], footer_text = "Published on", timestamp = dateutil.parser.parse(data["snippet"]["publishedAt"]).replace(tzinfo = None))
		await self.bot.attempt_delete_message(ctx.message)

