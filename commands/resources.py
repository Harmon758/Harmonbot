
from discord.ext import commands

import json
import random
import requests

import keys
from modules import utilities
from modules import voice
from client import client

def setup(bot):
	bot.add_cog(Resources())

class Resources:

	@commands.command()
	async def add(self, *numbers : float):
		'''Adds numbers together.'''
		result = sum(numbers)
		if result.is_integer():
			result = int(result)
		addends = []
		for number in numbers:
			if number.is_integer():
				addends.append(str(int(number)))
			else:
				addends.append(str(number))
		await client.reply(" + ".join(addends) + " = " + str(result))

	@commands.command()
	async def audiodefine(self, word : str):
		'''Generate link for pronounciation of a word'''
		url = "http://api.wordnik.com:80/v4/word.json/{0}/audio?useCanonical=false&limit=1&api_key={1}".format(word, keys.wordnik_apikey)
		if requests.get(url).json():
			data = requests.get(url).json()[0]
			audio = data["fileUrl"]
			word = data["word"]
			await client.reply(word.capitalize() + ": " + audio)
		else:
			await client.reply("Word or audio not found.")

	@commands.command()
	async def bing(self, *search : str):
		'''Look something up on Bing'''
		await client.reply("http://www.bing.com/search?q={0}".format('+'.join(search)))

	@commands.command(aliases = ["calc", "calculator"])
	async def calculate(self, *equation : str):
		'''Simple calculator
		
		calculate <number> <operation> <number>
		'''
		if len(equation) >= 3 and equation[0].isnumeric and equation[2].isnumeric and equation[1] in ['+', '-', '*', '/']:
			await client.reply(' '.join(equation[:3]) + " = " + str(eval(''.join(equation[:3]))))
		else:
			await send_mention_space(message, "That's not a valid input.")

	@commands.command()
	async def cat(self, *options : str):
		'''Cats'''
		if options:
			if options[0] == "categories" or options[0] == "cats":
				root = xml.etree.ElementTree.fromstring(requests.get("http://thecatapi.com/api/categories/list").text)
				categories = ""
				for category in root.findall(".//name"):
					categories += category.text + " "
				await client.reply(categories[:-1])
			else:
				url = "http://thecatapi.com/api/images/get?format=xml&results_per_page=1&category={0}".format(options[0])
				root = xml.etree.ElementTree.fromstring(requests.get(url).text)
				if root.find(".//url") is not None:
					await client.reply(root.find(".//url").text)
				else:
					root = xml.etree.ElementTree.fromstring(requests.get("http://thecatapi.com/api/images/get?format=xml&results_per_page=1").text)
					await client.reply(root.find(".//url").text)
		else:
			root = xml.etree.ElementTree.fromstring(requests.get("http://thecatapi.com/api/images/get?format=xml&results_per_page=1").text)
			await client.reply(root.find(".//url").text)

	@commands.command()
	async def choose(self, *choices : str):
		'''Randomly choose'''
		if not choices:
			await client.reply("Choose between what?")
		await client.reply(random.choice(choices))

	@commands.command(aliases = ["flip"])
	async def coin(self):
		'''Flip a coin'''
		await client.reply(random.choice(["Heads!", "Tails!"]))

	@commands.command(aliases = ["colour"])
	async def color(self, *options : str):
		'''Information on colors'''
		if not options or options[0] == "random":
			url = "http://www.colourlovers.com/api/colors/random?numResults=1&format=json"
		elif utilities.is_hex(options[0]) and len(options[0]) == 6:
			url = "http://www.colourlovers.com/api/color/{0}?format=json".format(options[0])
		else:
			url = "http://www.colourlovers.com/api/colors?numResults=1&format=json&keywords={0}".format('+'.join(options))
		data = requests.get(url).json()[0]
		rgb = data["rgb"]
		hsv = data["hsv"]
		await client.reply("\n{name} ({hex})\nRGB: ({red}, {green}, {blue})\nHSV: ({hue}°, {saturation}%, {value}%)\n{image}".format( \
			name = data["title"].capitalize(), hex = '#' + data["hex"], red = str(rgb["red"]), green = str(rgb["green"]), blue = str(rgb["blue"]),
			hue = str(hsv["hue"]), saturation = str(hsv["saturation"]), value = str(hsv["value"]), image = data["imageUrl"]))

	@commands.command()
	async def date(self, date : str):
		'''Facts about dates'''
		url = "http://numbersapi.com/{0}/date".format(date)
		await client.reply(requests.get(url).text)

	@commands.command()
	async def define(self, word : str):
		'''Define a word'''
		url = "http://api.wordnik.com:80/v4/word.json/{0}/definitions?limit=1&includeRelated=false&useCanonical=false&includeTags=false&api_key={1}".format(word, keys.wordnik_apikey)
		# page = urllib.request.urlopen(url)
		if requests.get(url).json():
			data = requests.get(url).json()[0]
			definition = data["text"]
			word = data["word"]
			await client.reply(word.capitalize() + ": " + definition)
		else:
			await client.reply("Definition not found.")

	@commands.command()
	async def fancify(self, *text : str):
		'''Fancify text'''
		output = ""
		for letter in " ".join(text):
			if 65 <= ord(letter) <= 90:
				output += chr(ord(letter) + 119951)
			elif 97 <= ord(letter) <= 122:
				output += chr(ord(letter) + 119919)
			elif letter == ' ':
				output += ' '
		await client.reply(output)

	@commands.command()
	async def giphy(self, *options : str):
		'''Find something on giphy
		
		giphy <random/trending/(search)>
		'''
		if options and options[0] == "random":
			url = "http://api.giphy.com/v1/gifs/random?api_key=dc6zaTOxFJmzC"
			data = requests.get(url).json()["data"]
			await send_mention_space(message, data["url"])
		elif options and options[0] == "trending":
			url = "http://api.giphy.com/v1/gifs/trending?api_key=dc6zaTOxFJmzC"
			data = requests.get(url).json()["data"]
			await send_mention_space(message, data[0]["url"])
		else:
			url = "http://api.giphy.com/v1/gifs/search?q={0}&limit=1&api_key=dc6zaTOxFJmzC".format("+".join(options))
			data = requests.get(url).json()["data"]
			await send_mention_space(message, data[0]["url"])

	@commands.command(aliases = ["search"])
	async def google(self, *search : str):
		'''Google something'''
		await client.reply("https://www.google.com/search?q={0}".format(('+').join(search)))

	@commands.command(aliases = ["imagesearch"])
	async def googleimage(self, *search : str):
		'''Google image search something'''
		url = "https://www.googleapis.com/customsearch/v1?key={0}&cx={1}&searchType=image&q={2}".format(keys.google_apikey, keys.google_cse_cx, '+'.join(search))
		data = requests.get(url).json()
		image_link = data["items"][0]["link"]
		await client.reply(image_link)
		# handle 403 daily limit exceeded error

	@commands.command()
	async def haveibeenpwned(self, name : str):
		'''Check if your account has been breached'''
		url = "https://haveibeenpwned.com/api/v2/breachedaccount/{0}?truncateResponse=true".format(name)
		data = requests.get(url)
		if data.status_code == 404 or data.status_code == 400:
			breachedaccounts = "None"
		else:
			data = data.json()
			breachedaccounts = ""
			for breachedaccount in data:
				breachedaccounts += breachedaccount["Name"] + ", "
			breachedaccounts = breachedaccounts[:-2]
		url = "https://haveibeenpwned.com/api/v2/pasteaccount/{0}".format(name)
		data = requests.get(url)
		if data.status_code == 404 or data.status_code == 400:
			pastedaccounts = "None"
		else:
			data = data.json()
			pastedaccounts = ""
			for pastedaccount in data:
				pastedaccounts += pastedaccount["Source"] + " (" + pastedaccount["Id"] + "), "
			pastedaccounts = pastedaccounts[:-2]
		await client.reply("Breached accounts: " + breachedaccounts + "\nPastes: " + pastedaccounts)

	@commands.command(aliases = ["movie"])
	async def imdb(self, *search : str):
		'''IMDb Information'''
		url = "http://www.omdbapi.com/?t={0}&y=&plot=short&r=json".format(" ".join(search))
		data = requests.get(url).json()
		await client.reply("```\n{title} ({year})\nType: {type}\nIMDb Rating: {rating}\nRuntime: {runtime}\nGenre(s): {genre}\nPlot: {plot}Poster: {poster}".format( \
			title = data["Title"], year = data["Year"], type = data["Type"], rating = data["imdbRating"], runtime = data["Runtime"], genre = data["Genre"], 
			plot = data["Plot"], poster = data["Poster"]))

	@commands.command()
	async def imfeelinglucky(self, *search : str):
		'''First Google result of a search'''
		await client.reply("https://www.google.com/search?btnI&q={0}".format(('+').join(search)))

	@commands.command()
	async def insult(self):
		'''Generate insult'''
		url = "http://quandyfactory.com/insult/json"
		data = requests.get(url).json()
		await client.say(data["insult"])

	@commands.command()
	async def joke(self):
		'''Generate joke'''
		url = "http://tambal.azurewebsites.net/joke/random"
		data = requests.get(url).json()
		joke = data["joke"]
		await client.reply(joke)

	@commands.command()
	async def lmbtfy(self, *search : str):
		'''Let Me Bing That For You'''
		await client.reply("http://lmbtfy.com/?q={0}".format(('+').join(search)))

	@commands.command()
	async def lmgtfy(self, *search : str):
		'''Let Me Google That For You'''
		await client.reply("http://www.lmgtfy.com/?q={0}".format(('+').join(search)))

	@commands.command()
	async def longurl(self, url : str):
		'''Expand a short goo.gl url'''
		url = "https://www.googleapis.com/urlshortener/v1/url?shortUrl={0}&key={1}".format(url, keys.google_apikey)
		data = requests.get(url).json()
		await client.reply(data["longUrl"])

	@commands.command()
	async def map(self, *options : str):
		'''Get map of location'''
		if options and options[0] == "random":
			latitude = random.uniform(-90, 90)
			longitude = random.uniform(-180, 180)
			await client.reply("https://maps.googleapis.com/maps/api/staticmap?center={0},{1}&zoom=13&size=600x300".format(str(latitude), str(longitude)))
		else:
			await client.reply("https://maps.googleapis.com/maps/api/staticmap?center={0}&zoom=13&size=600x300".format("+".join(options)))

	@commands.command()
	async def math(self, number : str):
		'''Math facts about numbers'''
		await client.reply(requests.get("http://numbersapi.com/{0}/math".format(number)).text)

	@commands.command()
	async def number(self, number : str):
		'''Facts about numbers'''
		await client.reply(requests.get("http://numbersapi.com/{0}".format(number)).text)

	@commands.command()
	async def randomidea(self):
		'''Generate random idea'''
		data = requests.get("http://itsthisforthat.com/api.php?json").json()
		await client.reply("{0} for {1}".format(data["this"], data["that"]))

	@commands.command()
	async def randomlocation(self):
		'''Generate random location'''
		await client.reply("{0}, {1}".format(str(random.uniform(-90, 90)), str(random.uniform(-180, 180))))

	@commands.command()
	async def randomword(self):
		'''Generate random word'''
		url = "http://api.wordnik.com:80/v4/words.json/randomWord?hasDictionaryDef=false&minCorpusCount=0&maxCorpusCount=-1&minDictionaryCount=1&maxDictionaryCount=-1&minLength=5&maxLength=-1&api_key={0}".format(keys.wordnik_apikey)
		data = requests.get(url).json()
		word = data["word"]
		await client.reply(word.capitalize())

	@commands.command(aliases = ["randomnumber"])
	async def rng(self, *number : int):
		'''Generate random number'''
		if len(number) and number[0] > 0:
			await client.reply(str(random.randint(1, number[0])))
		else:
			await client.reply(str(random.randint(1, 10)))

	@commands.command()
	async def shorturl(self, url : str):
		'''Generate a short goo.gl url for your link'''
		await client.reply(requests.post('https://www.googleapis.com/urlshortener/v1/url?key={0}'.format(keys.google_apikey), headers = {'Content-Type': 'application/json'}, data = '{"longUrl": "' + url +'"}').json()["id"])

	@commands.command()
	async def spotifyinfo(self, url : str):
		'''Information about a Spotify track'''
		path = urllib.parse.urlparse(url).path
		if path[:7] == "/track/":
			trackid = path[7:]
			url = "https://api.spotify.com/v1/tracks/" + trackid
			data = requests.get(url).json()
			# tracknumber = str(data["track_number"])
			# albumlink = data["album"]["href"]
			await client.reply("```\n{songname} by {artistname}\n{albumname}\n{duration}```Preview: {preview}\nArtist: {artistlink}\nAlbum: {albumlink}".format( \
				songname =  data["name"], artistname = data["artists"][0]["name"], albumname = data["album"]["name"], 
				duration = utilities.secs_to_colon_format(data["duration_ms"] / 1000), preview = data["preview_url"], 
				artistlink = data["artists"][0]["external_urls"]["spotify"], albumlink = data["album"]["external_urls"]["spotify"]))
		else:
			await client.reply("Syntax error.")

	@commands.command(aliases = ["sptoyt"])
	async def spotifytoyoutube(self, url : str):
		'''Find a Spotify track on Youtube'''
		link = voice.spotify_to_youtube(url)
		if link:
			await client.reply(link)
		else:
			await client.reply("Error")

	@commands.command()
	async def steam(self, *options : str):
		'''Steam Information'''
		if options and options[0] == "appid":
			apps = requests.get("http://api.steampowered.com/ISteamApps/GetAppList/v0002/").json()["applist"]["apps"]
			appid = 0
			for app in apps:
				if app["name"].lower() == " ".join(options[1:]).lower():
					appid = app["appid"]
					break
			await client.reply(str(appid))
		elif options and options[0] == "gamecount":
			url = "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={0}&vanityurl={1}".format(keys.steam_apikey, options[1])
			id = requests.get(url).json()["response"]["steamid"]
			url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={0}&steamid={1}".format(keys.steam_apikey, id)
			gamecount = requests.get(url).json()["response"]["game_count"]
			await client.reply("{0} has {1} games.".format(options[1], str(gamecount)))
		elif options and options[0] == "gameinfo":
			apps = requests.get("http://api.steampowered.com/ISteamApps/GetAppList/v0002/").json()["applist"]["apps"]
			appid = 0
			for app in apps:
				if app["name"].lower() == " ".join(options[1:]).lower():
					appid = app["appid"]
					break
			url = "http://store.steampowered.com/api/appdetails/?appids={0}".format(str(appid))
			data = requests.get(url).json()[str(appid)]["data"]
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
			await client.reply("{name}\n{appid}\nFree?: {0}\n{website}\n{header_image}".format( \
				isfree, name = data["name"], appid = str(data["steam_appid"]), website = data["website"], header_image = data["header_image"]))

	@commands.command()
	async def streetview(self, *options : str):
		'''Generate street view of a location'''
		if options:
			if options[0] == "random":
				latitude = random.uniform(-90, 90)
				longitude = random.uniform(-180, 180)
				await send_mention_space(message, "https://maps.googleapis.com/maps/api/streetview?size=400x400&location={0},{1}".format(str(latitude), str(longitude)))
			else:
				await send_mention_space(message, "https://maps.googleapis.com/maps/api/streetview?size=400x400&location={0}".format('+'.join(options)))

	@commands.command()
	async def wiki(self, *search : str):
		'''Look something up on Wikipedia'''
		await client.reply("https://en.wikipedia.org/wiki/{0}".format("_".join(search)))

	@commands.command()
	async def xkcd(self, *options : str):
		'''Find xkcd's'''
		if not options:
			url = "http://xkcd.com/info.0.json" # http://dynamic.xkcd.com/api-0/jsonp/comic/
		elif utilities.is_digit_gtz(options[0]):
			url = "http://xkcd.com/{0}/info.0.json".format(options[0]) # http://dynamic.xkcd.com/api-0/jsonp/comic/#
		elif options[0] == "random":
			total = json.loads(requests.get("http://xkcd.com/info.0.json").text)["num"]
			url = "http://xkcd.com/{0}/info.0.json".format(str(random.randint(1, total)))
		data = requests.get(url).json()
		await client.reply("http://xkcd.com/{num} ({date})\n{image_link}\n{title}\nAlt Text: {alt_text}".format( \
			num = str(data["num"]), date = "{month}/{day}/{year}".format(month = data["month"], day = data["day"], year = data["year"]),
			image_link = data["img"], title = data["title"], alt_text = data["alt"]))

	@commands.command(aliases = ["ytinfo"])
	async def youtubeinfo(self, url : str):
		'''Information on Youtube videos'''
		# toggles = {}
		# with open(message.server.name + "_toggles.json", "r") as toggles_file:
			# toggles = json.load(toggles_file)
		# if message.content.split()[1] == "on":
			# toggles["youtubeinfo"] = True
			# with open(message.server.name + "_toggles.json", "w") as toggles_file:
				# json.dump(toggles, toggles_file)
		# elif message.content.split()[1] == "off":
			# toggles["youtubeinfo"] = False
			# with open(message.server.name + "_toggles.json", "w") as toggles_file:
				# json.dump(toggles, toggles_file)
		# else:
		url_data = urllib.parse.urlparse(url)
		query = urllib.parse.parse_qs(url_data.query)
		videoid = query["v"][0]
		api_url = "https://www.googleapis.com/youtube/v3/videos?id={0}&key={1}&part=snippet,contentDetails,statistics".format(videoid, keys.google_apikey)
		if requests.get(api_url).json():
			data = requests.get(api_url).json()["items"][0]
			title = data["snippet"]["title"]
			length_iso = data["contentDetails"]["duration"]
			length_timedelta = isodate.parse_duration(length_iso)
			length = secs_to_letter_format(length_timedelta.total_seconds())
			likes = data["statistics"]["likeCount"]
			dislikes = data["statistics"]["dislikeCount"]
			likepercentage = round(float(likes) / (float(likes) + float(dislikes)) * 100, 2)
			likes = add_commas(int(likes))
			dislikes = add_commas(int(dislikes))
			views = add_commas(int(data["statistics"]["viewCount"]))
			channel = data["snippet"]["channelTitle"]
			published = data["snippet"]["publishedAt"][:10]
			# await client.send_message(message.channel, message.author.mention + "\n**" + title + "**\n**Length**: " + str(length) + "\n**Likes**: " + likes + ", **Dislikes**: " + dislikes + " (" + str(likepercentage) + "%)\n**Views**: " + views + "\n" + channel + " on " + published)
			await client.reply("\n```" + title + "\nLength: " + str(length) + "\nLikes: " + likes + ", Dislikes: " + dislikes + " (" + str(likepercentage) + "%)\nViews: " + views + "\n" + channel + " on " + published + "```")
	
	@commands.command(aliases = ["ytsearch"])
	async def youtubesearch(self, *search : str):
		'''Find a Youtube video'''
		url = "https://www.googleapis.com/youtube/v3/search?part=snippet&q={0}&key={1}".format("+".join(search), keys.google_apikey)
		data = requests.get(url).json()["items"][0]
		if "videoId" not in data["id"]:
			data = requests.get(url).json()["items"][1]
		link = "https://www.youtube.com/watch?v={0}".format(data["id"]["videoId"])
		await client.reply(link)

	@commands.command()
	async def year(self, year : int):
		'''Facts about years'''
		url = "http://numbersapi.com/{0}/year".format(year)
		await client.reply(requests.get(url).text)
