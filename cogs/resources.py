
from discord.ext import commands

# import aiohttp
import asyncio
import isodate
import json
import random
import seaborn
# import spotipy
import urllib
import xml.etree.ElementTree
import wolframalpha

import credentials
from modules import utilities
from modules import weather
from utilities import checks
from clients import aiohttp_session

def setup(bot):
	bot.add_cog(Resources(bot))

class Resources:
	
	def __init__(self, bot):
		self.bot = bot
		self.tags_data, self.tags = None, None
		self.waclient = wolframalpha.Client(credentials.wolframalpha_appid)
		#wolframalpha (wa)
		# spotify = spotipy.Spotify()
		try:
			with open("data/tags.json", "x") as tags_file:
				json.dump({}, tags_file)
		except FileExistsError:
			pass
	
	@commands.command()
	@checks.not_forbidden()
	async def audiodefine(self, word : str):
		'''Generate link for pronounciation of a word'''
		url = "http://api.wordnik.com:80/v4/word.json/{0}/audio?useCanonical=false&limit=1&api_key={1}".format(word, credentials.wordnik_apikey)
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		if data:
			data = data[0]
			audio = data["fileUrl"]
			word = data["word"]
			await self.bot.reply(word.capitalize() + ": " + audio)
		else:
			await self.bot.reply("Word or audio not found.")
	
	@commands.command()
	@checks.not_forbidden()
	async def bing(self, *search : str):
		'''Look something up on Bing'''
		await self.bot.reply("http://www.bing.com/search?q={0}".format('+'.join(search)))
	
	@commands.command()
	@checks.not_forbidden()
	async def cat(self, *, category : str):
		'''
		Random image of a cat
		cat categories (cats) for different categories you can choose from
		cat <category> for a random image of a cat from that category
		'''
		if category:
			if category == "categories" or category == "cats":
				async with aiohttp_session.get("http://thecatapi.com/api/categories/list") as resp:
					data = await resp.text()
				root = xml.etree.ElementTree.fromstring(data)
				categories = ""
				for category in root.findall(".//name"):
					categories += category.text + ' '
				await self.bot.reply(categories[:-1])
			else:
				url = "http://thecatapi.com/api/images/get?format=xml&results_per_page=1&category={0}".format(category)
				async with aiohttp_session.get(url) as resp:
					data = await resp.text()
				root = xml.etree.ElementTree.fromstring(data)
				if root.find(".//url") is not None:
					await self.bot.reply(root.find(".//url").text)
				else:
					async with aiohttp_session.get("http://thecatapi.com/api/images/get?format=xml&results_per_page=1") as resp:
						data = await resp.text()
					root = xml.etree.ElementTree.fromstring(data)
					await self.bot.reply(root.find(".//url").text)
		else:
			async with aiohttp_session.get("http://thecatapi.com/api/images/get?format=xml&results_per_page=1") as resp:
				data = await resp.text()
			root = xml.etree.ElementTree.fromstring(data)
			await self.bot.reply(root.find(".//url").text)
	
	@commands.command(aliases = ["colour"])
	@checks.not_forbidden()
	async def color(self, *options : str):
		'''
		Information on colors
		options: random, (hex color code), (search for a color)
		'''
		if not options or options[0] == "random":
			url = "http://www.colourlovers.com/api/colors/random?numResults=1&format=json"
		elif utilities.is_hex(options[0]) and len(options[0]) == 6:
			url = "http://www.colourlovers.com/api/color/{0}?format=json".format(options[0])
		else:
			url = "http://www.colourlovers.com/api/colors?numResults=1&format=json&keywords={0}".format('+'.join(options))
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		if not data:
			await self.bot.reply("Error.")
		else:
			data = data[0]
			rgb = data["rgb"]
			hsv = data["hsv"]
			await self.bot.reply("\n"
			"{name} ({hex})\n"
			"RGB: ({red}, {green}, {blue})\n"
			"HSV: ({hue}°, {saturation}%, {value}%)\n"
			"{image}".format(name = data["title"].capitalize(), hex = "#{}".format(data["hex"]), red = str(rgb["red"]), green = str(rgb["green"]), blue = str(rgb["blue"]),	hue = str(hsv["hue"]), saturation = str(hsv["saturation"]), value = str(hsv["value"]), image = data["imageUrl"]))
	
	@commands.command()
	@checks.not_forbidden()
	async def date(self, date : str):
		'''Facts about dates'''
		url = "http://numbersapi.com/{0}/date".format(date)
		async with aiohttp_session.get(url) as resp:
			status = resp.status
			data = await resp.text()
		if status == 404:
			await self.bot.reply("Error.")
		else:
			await self.bot.reply(data)
	
	@commands.command()
	@checks.not_forbidden()
	async def define(self, word : str):
		'''Define a word'''
		url = "http://api.wordnik.com:80/v4/word.json/{0}/definitions?limit=1&includeRelated=false&useCanonical=false&includeTags=false&api_key={1}".format(word, credentials.wordnik_apikey)
		# page = urllib.request.urlopen(url)
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		if data:
			data = data[0]
			definition = data["text"]
			word = data["word"]
			await self.bot.reply(word.capitalize() + ": " + definition)
		else:
			await self.bot.reply("Definition not found.")
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def giphy(self, *search : str):
		'''
		Find something on giphy
		options: random, trending, (search)
		'''
		url = "http://api.giphy.com/v1/gifs/search?q={0}&limit=1&api_key=dc6zaTOxFJmzC".format("+".join(search))
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		data = data["data"]
		await self.bot.reply(data[0]["url"])
	
	@giphy.command(name = "random")
	async def giphy_random(self):
		'''Random gif'''
		url = "http://api.giphy.com/v1/gifs/random?api_key=dc6zaTOxFJmzC"
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		data = data["data"]
		await self.bot.reply(data["url"])
	
	@giphy.command(name = "trending")
	async def giphy_trending(self):
		'''Trending gif'''
		url = "http://api.giphy.com/v1/gifs/trending?api_key=dc6zaTOxFJmzC"
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		data = data["data"]
		await self.bot.reply(data[0]["url"])
	
	@commands.command(aliases = ["search"])
	@checks.not_forbidden()
	async def google(self, *search : str):
		'''Google something'''
		await self.bot.reply("https://www.google.com/search?q={0}".format(('+').join(search)))
	
	@commands.command(aliases = ["imagesearch"])
	@checks.not_forbidden()
	async def googleimage(self, *search : str):
		'''Google image search something'''
		url = "https://www.googleapis.com/customsearch/v1?key={0}&cx={1}&searchType=image&q={2}".format(credentials.google_apikey, credentials.google_cse_cx, '+'.join(search))
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		image_link = data["items"][0]["link"]
		await self.bot.reply(image_link)
		# handle 403 daily limit exceeded error
	
	@commands.command()
	@checks.not_forbidden()
	async def haveibeenpwned(self, name : str):
		'''Check if your account has been breached'''
		url = "https://haveibeenpwned.com/api/v2/breachedaccount/{0}?truncateResponse=true".format(name)
		async with aiohttp_session.get(url) as resp:
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
		async with aiohttp_session.get(url) as resp:
			status = resp.status
			data = await resp.json()
		if status in [404, 400]:
			pastedaccounts = "None"
		else:
			pastedaccounts = ""
			for pastedaccount in data:
				pastedaccounts += pastedaccount["Source"] + " (" + pastedaccount["Id"] + "), "
			pastedaccounts = pastedaccounts[:-2]
		await self.bot.reply("Breached accounts: " + breachedaccounts + "\nPastes: " + pastedaccounts)
	
	@commands.command(aliases = ["movie"])
	@checks.not_forbidden()
	async def imdb(self, *search : str):
		'''IMDb Information'''
		url = "http://www.omdbapi.com/?t={0}&y=&plot=short&r=json".format('+'.join(search))
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		if data["Response"] == "False":
			await self.bot.reply(data["Error"])
		else:
			await self.bot.reply("```"
			"{title} ({year})\n"
			"Type: {type}\n"
			"IMDb Rating: {rating}\n"
			"Runtime: {runtime}\n"
			"Genre(s): {genre}\n"
			"Plot: {plot}```"
			"Poster: {poster}".format(title = data["Title"], year = data["Year"], type = data["Type"], rating = data["imdbRating"], runtime = data["Runtime"], genre = data["Genre"], plot = data["Plot"], poster = data["Poster"]))
	
	@commands.command()
	@checks.not_forbidden()
	async def imfeelinglucky(self, *search : str):
		'''First Google result of a search'''
		await self.bot.reply("https://www.google.com/search?btnI&q={0}".format('+'.join(search)))
	
	@commands.command()
	@checks.not_forbidden()
	async def insult(self):
		'''Generate insult'''
		url = "http://quandyfactory.com/insult/json"
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		await self.bot.say(data["insult"])
	
	@commands.command()
	@checks.not_forbidden()
	async def joke(self):
		'''Generate joke'''
		url = "http://tambal.azurewebsites.net/joke/random"
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		joke = data["joke"]
		await self.bot.reply(joke)
	
	@commands.command()
	@checks.not_forbidden()
	async def lmbtfy(self, *search : str):
		'''Let Me Bing That For You'''
		await self.bot.reply("http://lmbtfy.com/?q={0}".format(('+').join(search)))
	
	@commands.command()
	@checks.not_forbidden()
	async def lmgtfy(self, *search : str):
		'''Let Me Google That For You'''
		await self.bot.reply("http://www.lmgtfy.com/?q={0}".format(('+').join(search)))
	
	@commands.command()
	@checks.not_forbidden()
	async def longurl(self, url : str):
		'''Expand a short goo.gl url'''
		url = "https://www.googleapis.com/urlshortener/v1/url?shortUrl={0}&key={1}".format(url, credentials.google_apikey)
		async with aiohttp_session.get(url) as resp:
			status = resp.status
			data = await resp.json()
		if status == 400:
			await self.bot.reply("Error.")
		else:
			await self.bot.reply(data["longUrl"])
	
	@commands.command()
	@checks.not_forbidden()
	async def map(self, *options : str):
		'''Get map of location'''
		if options and options[0] == "random":
			latitude = random.uniform(-90, 90)
			longitude = random.uniform(-180, 180)
			await self.bot.reply("https://maps.googleapis.com/maps/api/staticmap?center={0},{1}&zoom=13&size=600x300".format(str(latitude), str(longitude)))
		else:
			await self.bot.reply("https://maps.googleapis.com/maps/api/staticmap?center={0}&zoom=13&size=600x300".format("+".join(options)))
	
	@commands.command()
	@checks.not_forbidden()
	async def math(self, number : int):
		'''Math facts about numbers'''
		async with aiohttp_session.get("http://numbersapi.com/{0}/math".format(number)) as resp:
			data = await resp.text()
		await self.bot.reply(data)
	
	@commands.command()
	@checks.not_forbidden()
	async def number(self, number : int):
		'''Facts about numbers'''
		async with aiohttp_session.get("http://numbersapi.com/{0}".format(number)) as resp:
			data = await resp.text()
		await self.bot.reply(data)
	
	@commands.command()
	@checks.not_forbidden()
	async def randomidea(self):
		'''Generate random idea'''
		async with aiohttp_session.get("http://itsthisforthat.com/api.php?json") as resp:
			data = await resp.json()
		await self.bot.reply("{0} for {1}".format(data["this"], data["that"]))
	
	@commands.command()
	@checks.not_forbidden()
	async def randomword(self):
		'''Generate random word'''
		url = "http://api.wordnik.com:80/v4/words.json/randomWord?hasDictionaryDef=false&minCorpusCount=0&maxCorpusCount=-1&minDictionaryCount=1&maxDictionaryCount=-1&minLength=5&maxLength=-1&api_key={0}".format(credentials.wordnik_apikey)
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		word = data["word"]
		await self.bot.reply(word.capitalize())
	
	@commands.command(hidden = True)
	@checks.not_forbidden()
	async def redditsearch(self): #WIP
		'''WIP'''
		return
	
	@commands.command()
	@checks.not_forbidden()
	async def shorturl(self, url : str):
		'''Generate a short goo.gl url for your link'''
		async with aiohttp_session.post("https://www.googleapis.com/urlshortener/v1/url?key={0}".format(credentials.google_apikey), \
		headers = {'Content-Type': 'application/json'}, data = '{"longUrl": "' + url +'"}') as resp:
			data = await resp.json()
		await self.bot.reply(data["id"])
	
	@commands.command()
	@checks.not_forbidden()
	async def spellcheck(self, *words : str):
		'''Spell check words'''
		async with aiohttp_session.post("https://bingapis.azure-api.net/api/v5/spellcheck?Text=" + '+'.join(words), headers = {"Ocp-Apim-Subscription-Key" : credentials.bing_spell_check_key}) as resp:
			data = await resp.json()
		corrections = data["flaggedTokens"]
		corrected = ' '.join(words)
		offset = 0
		for correction in corrections:
			offset += correction["offset"]
			suggestion = correction["suggestions"][0]["suggestion"]
			corrected = corrected[:offset] + suggestion + corrected[offset + len(correction["token"]):]
			offset += (len(suggestion) - len(correction["token"])) - correction["offset"]
		await self.bot.reply(corrected)
	
	@commands.command()
	@checks.not_forbidden()
	async def spotifyinfo(self, url : str):
		'''Information about a Spotify track'''
		path = urllib.parse.urlparse(url).path
		if path[:7] == "/track/":
			trackid = path[7:]
			url = "https://api.spotify.com/v1/tracks/" + trackid
			async with aiohttp_session.get(url) as resp:
				data = await resp.json()
			# tracknumber = str(data["track_number"])
			# albumlink = data["album"]["href"]
			await self.bot.reply("```\n{songname} by {artistname}\n{albumname}\n{duration}```Preview: {preview}\nArtist: {artistlink}\nAlbum: {albumlink}".format( \
				songname =  data["name"], artistname = data["artists"][0]["name"], albumname = data["album"]["name"], 
				duration = utilities.secs_to_colon_format(data["duration_ms"] / 1000), preview = data["preview_url"], 
				artistlink = data["artists"][0]["external_urls"]["spotify"], albumlink = data["album"]["external_urls"]["spotify"]))
		else:
			await self.bot.reply("Syntax error.")
	
	@commands.command(aliases = ["sptoyt"])
	@checks.not_forbidden()
	async def spotifytoyoutube(self, url : str):
		'''Find a Spotify track on Youtube'''
		link = await self.bot.cogs["Audio"].spotify_to_youtube(url)
		if link:
			await self.bot.reply(link)
		else:
			await self.bot.reply("Error")
	
	@commands.group()
	@checks.not_forbidden()
	async def steam(self, *options : str):
		'''Steam Information'''
		return
	
	@steam.command(name = "appid")
	async def steam_appid(self, *, app : str):
		'''Get the appid'''
		async with aiohttp_session.get("http://api.steampowered.com/ISteamApps/GetAppList/v0002/") as resp:
			data = await resp.json()
		apps = data["applist"]["apps"]
		appid = 0
		for _app in apps:
			if _app["name"].lower() == app.lower():
				appid = _app["appid"]
				break
		await self.bot.reply(str(appid))
	
	@steam.command(name = "gamecount")
	async def steam_gamecount(self, vanity_name : str):
		'''Find how many games someone has'''
		url = "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={0}&vanityurl={1}".format(credentials.steam_apikey, vanity_name)
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		id = data["response"]["steamid"]
		url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={0}&steamid={1}".format(credentials.steam_apikey, id)
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		gamecount = data["response"]["game_count"]
		await self.bot.reply("{0} has {1} games.".format(vanity_name, str(gamecount)))
	
	@steam.command(name = "gameinfo")
	async def steam_gameinfo(self, *, game : str):
		'''Information about a game'''
		async with aiohttp_session.get("http://api.steampowered.com/ISteamApps/GetAppList/v0002/") as resp:
			data = await resp.json()
		apps = data["applist"]["apps"]
		appid = 0
		for app in apps:
			if app["name"].lower() == game.lower():
				appid = app["appid"]
				break
		url = "http://store.steampowered.com/api/appdetails/?appids={0}".format(str(appid))
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		data = data[str(appid)]["data"]
		type = data["type"]
		appid = data["steam_appid"]
		#required_age = data["required_age"]
		isfree = data["is_free"]
		if isfree:
			isfree = "Yes"
		else:
			isfree = "No"
		detaileddescription = data["detailed_description"]
		description = data["about_the_game"]
		await self.bot.reply("{name}\n{appid}\nFree?: {0}\n{website}\n{header_image}".format( \
			isfree, name = data["name"], appid = str(data["steam_appid"]), website = data["website"], header_image = data["header_image"]))
	
	@commands.command()
	@checks.not_forbidden()
	async def strawpoll(self, question : str, *options : str):
		'''
		Generates a strawpoll link
		Use qoutes for spaces in the question or options
		'''
		async with aiohttp_session.post("https://strawpoll.me/api/v2/polls", data = json.dumps({"title" : question, "options" : options})) as resp:
			poll = await resp.json()
		await self.bot.reply("http://strawpoll.me/" + str(poll["id"]))
	
	@commands.command()
	@checks.not_forbidden()
	async def streetview(self, *options : str):
		'''Generate street view of a location'''
		if options:
			if options[0] == "random":
				latitude = random.uniform(-90, 90)
				longitude = random.uniform(-180, 180)
				await self.bot.reply("https://maps.googleapis.com/maps/api/streetview?size=400x400&location={0},{1}".format(str(latitude), str(longitude)))
			else:
				await self.bot.reply("https://maps.googleapis.com/maps/api/streetview?size=400x400&location={0}".format('+'.join(options)))
	
	@commands.command(hidden = True)
	@checks.not_forbidden()
	async def weather(self, *options : str): #WIP
		'''WIP'''
		await self.bot.reply(str(weather.tempc(' '.join(options))))
	
	@commands.command()
	@checks.not_forbidden()
	async def websitescreenshot(self, url : str):
		'''WIP'''
		response = await self.bot.reply("Loading...")
		url = "http://api.page2images.com/restfullink?p2i_url={}&p2i_screen=1280x1024&p2i_size=1280x0&p2i_fullpage=1&p2i_key={}".format(url, credentials.page2images_api_key)
		while True:
			async with aiohttp_session.get(url) as resp:
				data = await resp.json()
			if data["status"] == "processing":
				wait_time = int(data["estimated_need_time"])
				await self.bot.edit_message(response, "Processing. Estimated wait time: {} sec.".format(wait_time))
				await asyncio.sleep(wait_time)
			elif data["status"] == "finished":
				await self.bot.edit_message(response, data["image_url"])
				return
			elif data["status"] == "error":
				await self.bot.edit_message(response, "Error: {}".format(data["msg"]))
				return
	
	@commands.command(hidden = True)
	@checks.not_forbidden()
	async def whatis(self, *search : str): #WIP
		'''WIP'''
		if not search:
			await self.bot.reply("What is what?")
		else:
			await self.bot.reply("I don't know what that is.")
	
	@commands.command()
	@checks.not_forbidden()
	async def wiki(self, *search : str):
		'''Look something up on Wikipedia'''
		await self.bot.reply("https://en.wikipedia.org/wiki/{0}".format("_".join(search)))
	
	@commands.command(hidden = True, aliases = ["wa"])
	@checks.is_owner()
	async def wolframalpha(self, *, search : str): #WIP
		'''WIP'''
		result = self.waclient.query(search)
		for pod in result.pods:
			await self.bot.reply(pod.img)
			await self.bot.reply(pod.text)
		#await self.bot.reply(next(result.results).text)
	
	@commands.command()
	@checks.not_forbidden()
	async def xkcd(self, *options : str):
		'''Find xkcd's'''
		if not options:
			url = "http://xkcd.com/info.0.json" # http://dynamic.xkcd.com/api-0/jsonp/comic/
		elif utilities.is_digit_gtz(options[0]):
			url = "http://xkcd.com/{0}/info.0.json".format(options[0]) # http://dynamic.xkcd.com/api-0/jsonp/comic/#
		elif options[0] == "random":
			async with aiohttp_session.get("http://xkcd.com/info.0.json") as resp:
				data = await resp.text()
			total = json.loads(data)["num"]
			url = "http://xkcd.com/{0}/info.0.json".format(str(random.randint(1, total)))
		else:
			await self.bot.reply("Syntax error.")
		async with aiohttp_session.get(url) as resp:
			if resp.status == 404:
				await self.bot.reply("Error.")
				return
			data = await resp.json()
		await self.bot.reply("\n"
		"http://xkcd.com/{num} ({date})\n"
		"{image_link}\n"
		"{title}\n"
		"Alt Text: {alt_text}".format(num = str(data["num"]), date = "{month}/{day}/{year}".format(month = data["month"], day = data["day"], year = data["year"]), image_link = data["img"], title = data["title"], alt_text = data["alt"]))
	
	@commands.command(aliases = ["ytinfo"])
	@checks.not_forbidden()
	async def youtubeinfo(self, url : str):
		'''Information on Youtube videos'''
		# toggles = {}
		# with open(message.server.name + "_toggles.json", "r") as toggles_file:
			# toggles = json.load(toggles_file)
		# if message.content.split()[1] == "on":
			# toggles["youtubeinfo"] = True
			# with open(message.server.name + "_toggles.json", "w") as toggles_file:
				# json.dump(toggles, toggles_file, indent = 4)
		# elif message.content.split()[1] == "off":
			# toggles["youtubeinfo"] = False
			# with open(message.server.name + "_toggles.json", "w") as toggles_file:
				# json.dump(toggles, toggles_file, indent = 4)
		# else:
		url_data = urllib.parse.urlparse(url)
		query = urllib.parse.parse_qs(url_data.query)
		videoid = query["v"][0]
		api_url = "https://www.googleapis.com/youtube/v3/videos?id={0}&key={1}&part=snippet,contentDetails,statistics".format(videoid, credentials.google_apikey)
		async with aiohttp_session.get(api_url) as resp:
			data = await resp.json()
		if data:
			data = data["items"][0]
			title = data["snippet"]["title"]
			length_iso = data["contentDetails"]["duration"]
			length_timedelta = isodate.parse_duration(length_iso)
			length = utilities.secs_to_letter_format(length_timedelta.total_seconds())
			likes = data["statistics"]["likeCount"]
			dislikes = data["statistics"]["dislikeCount"]
			likepercentage = round(float(likes) / (float(likes) + float(dislikes)) * 100, 2)
			likes = utilities.add_commas(int(likes))
			dislikes = utilities.add_commas(int(dislikes))
			views = utilities.add_commas(int(data["statistics"]["viewCount"]))
			channel = data["snippet"]["channelTitle"]
			published = data["snippet"]["publishedAt"][:10]
			# await self.bot.send_message(message.channel, message.author.mention + "\n**" + title + "**\n**Length**: " + str(length) + "\n**Likes**: " + likes + ", **Dislikes**: " + dislikes + " (" + str(likepercentage) + "%)\n**Views**: " + views + "\n" + channel + " on " + published)
			await self.bot.reply("\n```" + title + "\nLength: " + str(length) + "\nLikes: " + likes + ", Dislikes: " + dislikes + " (" + str(likepercentage) + "%)\nViews: " + views + "\n" + channel + " on " + published + "```")
	
	@commands.command(aliases = ["ytsearch"])
	@checks.not_forbidden()
	async def youtubesearch(self, *search : str):
		'''Find a Youtube video'''
		link = await utilities.youtubesearch(search)
		await self.bot.reply(link)
	
	@commands.command()
	@checks.not_forbidden()
	async def year(self, year : int):
		'''Facts about years'''
		async with aiohttp_session.get("http://numbersapi.com/{0}/year".format(year)) as resp:
			data = await resp.text()
		await self.bot.reply(data)
