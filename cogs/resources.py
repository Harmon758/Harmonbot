
from discord.ext import commands

# import aiohttp
import asyncio
import datetime
import functools
import isodate
import json
import random
# import spotipy
import urllib
import xml.etree.ElementTree
import wolframalpha
import youtube_dl

import credentials
from modules import utilities
from modules import weather
from utilities import checks
from utilities import errors
from clients import aiohttp_session

def setup(bot):
	bot.add_cog(Resources(bot))

class Resources:
	
	def __init__(self, bot):
		self.bot = bot
		self.waclient = wolframalpha.Client(credentials.wolframalpha_appid)
		self.lichess_user_data, self.lichess_tournaments_data = None, None
		#wolframalpha (wa)
		# spotify = spotipy.Spotify()
	
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
	async def cat(self, *, category : str = ""):
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
	async def google(self, *, search : str):
		'''Google something'''
		await self.bot.reply("https://www.google.com/search?q={0}".format(search.replace(' ', '+')))
	
	@commands.command(aliases = ["imagesearch", "googleimages"])
	@checks.not_forbidden()
	async def googleimage(self, *search : str):
		'''Google image search something'''
		url = "https://www.googleapis.com/customsearch/v1?key={0}&cx={1}&searchType=image&q={2}".format(credentials.google_apikey, credentials.google_cse_cx, '+'.join(search))
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		if "items" in data:
			image_link = data["items"][0]["link"]
			await self.bot.reply(image_link)
		else:
			await self.bot.reply("No images with that search found")
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
	
	@commands.group()
	@checks.not_forbidden()
	async def lichess(self):
		'''WIP'''
		return
	
	@lichess.group(name = "user", pass_context = True)
	async def lichess_user(self, ctx):
		'''WIP'''
		if len(ctx.message.content.split()) == 2:
			pass
		elif len(ctx.message.content.split()) >= 4:
			url = "https://en.lichess.org/api/user/{}".format(ctx.message.content.split()[3])
			async with aiohttp_session.get(url) as resp:
				self.lichess_user_data = await resp.json()
			if not self.lichess_user_data:
				raise errors.LichessUserNotFound
	
	@lichess_user.command(name = "bullet")
	async def lichess_user_bullet(self, username : str):
		'''WIP'''
		data = self.lichess_user_data
		await self.bot.reply("\n__{username}__\n:zap: Bullet | **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {chart} {prog}".format(data["perfs"]["bullet"], prov = "?" if data["perfs"]["bullet"]["prov"] else "", chart = ":chart_with_upwards_trend:" if data["perfs"]["bullet"]["prog"] >= 0 else ":chart_with_downwards_trend:", prog = data["perfs"]["bullet"]["prog"], username = data["username"]))
	
	@lichess_user.command(name = "blitz")
	async def lichess_user_blitz(self, username : str):
		'''WIP'''
		data = self.lichess_user_data
		await self.bot.reply("\n__{username}__\n:fire: Blitz | **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {chart} {prog}".format(data["perfs"]["blitz"], prov = "?" if data["perfs"]["blitz"]["prov"] else "", chart = ":chart_with_upwards_trend:" if data["perfs"]["blitz"]["prog"] >= 0 else ":chart_with_downwards_trend:", prog = data["perfs"]["blitz"]["prog"], username = data["username"]))
	
	@lichess_user.error
	async def lichess_user_error(self, error, ctx):
		if isinstance(error.original, errors.LichessUserNotFound):
			await self.bot.reply("User not found.")
	
	@lichess_user.command(name = "all")
	async def lichess_user_all(self, username : str):
		'''WIP'''
		data = self.lichess_user_data
		output = ["", "__{}__".format(data["username"])]
		output.append("Online: {}".format(data["online"]))
		output.append(":zap: `Bullet           |` **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {chart} {prog}".format(data["perfs"]["bullet"], prov = "?" if data["perfs"]["bullet"]["prov"] else "", chart = ":chart_with_upwards_trend:" if data["perfs"]["bullet"]["prog"] >= 0 else ":chart_with_downwards_trend:", prog = data["perfs"]["bullet"]["prog"]))
		output.append(":fire: `Blitz            |` **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {chart} {prog}".format(data["perfs"]["blitz"], prov = "?" if data["perfs"]["blitz"]["prov"] else "", chart = ":chart_with_upwards_trend:" if data["perfs"]["blitz"]["prog"] >= 0 else ":chart_with_downwards_trend:", prog = data["perfs"]["blitz"]["prog"]))
		output.append(":hourglass: `Classical        |` **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {chart} {prog}".format(data["perfs"]["classical"], prov = "?" if data["perfs"]["classical"]["prov"] else "", chart = ":chart_with_upwards_trend:" if data["perfs"]["classical"]["prog"] >= 0 else ":chart_with_downwards_trend:", prog = data["perfs"]["classical"]["prog"]))
		output.append(":envelope: `Correspondence   |` **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {chart} {prog}".format(data["perfs"]["correspondence"], prov = "?" if data["perfs"]["correspondence"]["prov"] else "", chart = ":chart_with_upwards_trend:" if data["perfs"]["correspondence"]["prog"] >= 0 else ":chart_with_downwards_trend:", prog = data["perfs"]["correspondence"]["prog"]))
		output.append(":pisces: `Crazyhouse       |` **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {chart} {prog}".format(data["perfs"]["crazyhouse"], prov = "?" if data["perfs"]["crazyhouse"]["prov"] else "", chart = ":chart_with_upwards_trend:" if data["perfs"]["crazyhouse"]["prog"] >= 0 else ":chart_with_downwards_trend:", prog = data["perfs"]["crazyhouse"]["prog"]))
		output.append(":game_die: `Chess960         |` **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {chart} {prog}".format(data["perfs"]["chess960"], prov = "?" if data["perfs"]["chess960"]["prov"] else "", chart = ":chart_with_upwards_trend:" if data["perfs"]["chess960"]["prog"] >= 0 else ":chart_with_downwards_trend:", prog = data["perfs"]["chess960"]["prog"]))
		output.append(":triangular_flag_on_post: `King Of The Hill |` **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {chart} {prog}".format(data["perfs"]["kingOfTheHill"], prov = "?" if data["perfs"]["kingOfTheHill"]["prov"] else "", chart = ":chart_with_upwards_trend:" if data["perfs"]["kingOfTheHill"]["prog"] >= 0 else ":chart_with_downwards_trend:", prog = data["perfs"]["kingOfTheHill"]["prog"]))
		output.append(":three: `Three-Check      |` **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {chart} {prog}".format(data["perfs"]["threeCheck"], prov = "?" if data["perfs"]["threeCheck"]["prov"] else "", chart = ":chart_with_upwards_trend:" if data["perfs"]["threeCheck"]["prog"] >= 0 else ":chart_with_downwards_trend:", prog = data["perfs"]["threeCheck"]["prog"]))
		output.append(":arrows_clockwise: `Antichess        |` **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {chart} {prog}".format(data["perfs"]["antichess"], prov = "?" if data["perfs"]["antichess"]["prov"] else "", chart = ":chart_with_upwards_trend:" if data["perfs"]["antichess"]["prog"] >= 0 else ":chart_with_downwards_trend:", prog = data["perfs"]["antichess"]["prog"]))
		output.append(":atom: `Atomic           |` **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {chart} {prog}".format(data["perfs"]["atomic"], prov = "?" if data["perfs"]["atomic"]["prov"] else "", chart = ":chart_with_upwards_trend:" if data["perfs"]["atomic"]["prog"] >= 0 else ":chart_with_downwards_trend:", prog = data["perfs"]["atomic"]["prog"]))
		output.append(":question: `Horde            |` **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {chart} {prog}".format(data["perfs"]["horde"], prov = "?" if data["perfs"]["horde"]["prov"] else "", chart = ":chart_with_upwards_trend:" if data["perfs"]["horde"]["prog"] >= 0 else ":chart_with_downwards_trend:", prog = data["perfs"]["horde"]["prog"]))
		output.append(":checkered_flag: `Racing Kings     |` **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {chart} {prog}".format(data["perfs"]["racingKings"], prov = "?" if data["perfs"]["racingKings"]["prov"] else "", chart = ":chart_with_upwards_trend:" if data["perfs"]["racingKings"]["prog"] >= 0 else ":chart_with_downwards_trend:", prog = data["perfs"]["racingKings"]["prog"]))
		output.append(":bow_and_arrow: `Puzzle/Training  |` **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {chart} {prog}".format(data["perfs"]["puzzle"], prov = "?" if data["perfs"]["puzzle"]["prov"] else "", chart = ":chart_with_upwards_trend:" if data["perfs"]["puzzle"]["prog"] >= 0 else ":chart_with_downwards_trend:", prog = data["perfs"]["puzzle"]["prog"]))
		output.append(":notebook_with_decorative_cover: `Opening          |` **Games**: {0[games]}, **Rating**: {0[rating]}{prov}±{0[rd]}, {chart} {prog}".format(data["perfs"]["opening"], prov = "?" if data["perfs"]["opening"]["prov"] else "", chart = ":chart_with_upwards_trend:" if data["perfs"]["opening"]["prog"] >= 0 else ":chart_with_downwards_trend:", prog = data["perfs"]["opening"]["prog"]))
		output.append("Member since {}".format(datetime.datetime.fromtimestamp(data["createdAt"] / 1000.0).strftime("%Y-%m-%d %H:%M:%S.%f")))
		output.append("Last seen {}".format(datetime.datetime.fromtimestamp(data["seenAt"] / 1000.0).strftime("%Y-%m-%d %H:%M:%S.%f")))
		output.append("Time spent playing: {}".format(utilities.secs_to_letter_format(data["playTime"]["total"])))
		output.append("Time on TV: {}".format(utilities.secs_to_letter_format(data["playTime"]["tv"])))
		output.append("Following: {0[nbFollowing]}, Followers: {0[nbFollowers]}".format(data))
		output.append("Games Played: {0[all]}, Rated: {0[rated]}, AI: {0[ai]}, Wins: {0[win]}, Losses: {0[loss]}, Draws: {0[draw]}, Bookmarks: {0[bookmark]}".format(data["count"]))
		output.append("<{}>".format(data["url"]))
		await self.bot.reply('\n'.join(output))
	
	@lichess.group(name = "tournaments")
	async def lichess_tournaments(self):
		'''WIP'''
		url = "https://en.lichess.org/api/tournament"
		async with aiohttp_session.get(url) as resp:
			self.lichess_tournaments_data = await resp.json()
	
	@lichess_tournaments.command(name = "current", aliases = ["started"])
	async def lichess_tournaments_current(self):
		'''WIP'''
		data = self.lichess_tournaments_data["started"]
		output = ["", "__Current Tournaments__"]
		for tournament in data:
			output.append("**{0[fullName]}**".format(tournament))
			# output.append("{:g}+{} {variant}{rated}".format(tournament["clock"]["limit"] / 60, tournament["clock"]["increment"], variant = tournament["variant"]["name"] + " " if tournament["variant"]["name"] != "Standard" else "", rated = "Rated" if tournament["rated"] else "Casual"))
			output.append("{:g}+{} {} {rated}".format(tournament["clock"]["limit"] / 60, tournament["clock"]["increment"], tournament["perf"]["name"], rated = "Rated" if tournament["rated"] else "Casual"))
			output[-1] += ", Ends in: {:g}m".format((datetime.datetime.utcfromtimestamp(tournament["finishesAt"] / 1000.0) - datetime.datetime.utcnow()).total_seconds() // 60)
			output.append("<https://en.lichess.org/tournament/{}>".format(tournament["id"]))
		await self.bot.reply('\n'.join(output))
	
	@lichess.command(name = "tournament")
	async def lichess_tournament(self):
		'''WIP'''
		pass
	
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
		'''
		Get map of location
		map [location] or map random
		'''
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
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def oeis(self, *, search : str):
		'''
		The On-Line Encyclopedia of Integer Sequences
		Does not accept spaces for search by sequence
		'''
		url = "http://oeis.org/search?fmt=json&q=" + search
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		if data["results"]:
			await self.bot.reply("{0[name]}\n{0[data]}".format(data["results"][0]))
		elif data["count"]:
			await self.bot.reply("Too many sequences found")
		else:
			await self.bot.reply("Sequence not found")
	
	@oeis.command(name = "graph")
	@checks.not_forbidden()
	async def oeis_graph(self, *, search : str):
		'''
		The On-Line Encyclopedia of Integer Sequences
		Does not accept spaces for search by sequence
		Returns sequence graph if found
		'''
		url = "http://oeis.org/search?fmt=json&q=" + search
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		if data["results"]:
			await self.bot.reply("https://oeis.org/A{:06d}/graph?png=1".format(data["results"][0]["number"]))
		elif data["count"]:
			await self.bot.reply("Too many sequences found")
		else:
			await self.bot.reply("Sequence not found")
	
	@commands.group()
	@checks.not_forbidden()
	async def overwatch(self):
		'''WIP'''
		pass
	
	@overwatch.command(name = "stats")
	async def overwatch_stats(self, battletag : str, number : str):
		'''
		Overwatch user statistics
		Note: battletags are case sensitive
		'''
		url = "https://owapi.net/api/v2/u/{}-{}/stats/general".format(battletag, number)
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		output = ["", "__**{}**__".format(data["battletag"].replace('-', '#'))]
		output.append("**Level**: {0[level]}".format(data["overall_stats"]))
		output.append("**Wins/Total**: {0[wins]}/{0[games]} ({1:g}%)".format(data["overall_stats"], 100 * data["overall_stats"]["wins"] / data["overall_stats"]["wins"] + data["overall_stats"]["losses"]))
		output.append(":medal: {0[medals]:,g} | :first_place_medal: {0[medals_gold]:,g} :second_place_medal: {0[medals_silver]:,g} :third_place_medal: {0[medals_bronze]:,g}".format(data["game_stats"]))
		output.append("**Cards**: {0[cards]:g}, **Damage Done**: {0[damage_done]:,}, **Deaths**: {0[deaths]:,g}, **Eliminations**: {0[eliminations]:,g}, **Healing Done**: {0[healing_done]:,}, **Eliminations/Deaths**: {0[kpd]}, **Time Played**: {0[time_played]}h **Time Spent On Fire**: {0[time_spent_on_fire]:.2f}".format(data["game_stats"]))
		output.append("__Most In One Game__ | **Damage Done**: {0[damage_done_most_in_game]:,g}, **Eliminations**: {0[eliminations_most_in_game]:,g}, **Healing Done**: {0[healing_done_most_in_game]:,g}, **Time Spent On Fire**: {0[time_spent_on_fire_most_in_game]:.2f}".format(data["game_stats"]))
		output.append("**Region**: {}".format(data["region"].upper()))
		await self.bot.reply('\n'.join(output))
	
	@overwatch.command(name = "heroes")
	async def overwatch_heroes(self, battletag : str, number : str):
		'''
		Overwatch user hero statistics
		Note: battletags are case sensitive
		'''
		url = "https://owapi.net/api/v2/u/{}-{}/heroes/general".format(battletag, number)
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		output = ["", "__{}__".format(data["battletag"].replace('-', '#'))]
		sorted_data = sorted(data["heroes"].items(), key = lambda beanisgod: beanisgod[1], reverse = True) # sanity pls
		for hero, time in sorted_data:
			if time >= 1:
				output.append("**{}**: {:g} hours".format(hero.capitalize(), time))
			else:
				output.append("**{}**: {:g} minutes".format(hero.capitalize(), time * 60))
			#plural
		await self.bot.reply('\n'.join(output))
	
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
	
	@commands.group(aliases = ["realmofthemadgod"], invoke_without_command = True)
	@checks.not_forbidden()
	async def rotmg(self, player : str):
		'''Realm of the Mad God player information'''
		url = "https://nightfirec.at/realmeye-api/?player={}".format(player)
		# http://webhost.ischool.uw.edu/~joatwood/realmeye_api/0.3/
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		if "error" in data:
			await self.bot.reply("Error: " + data["error"])
		else:
			output = ["", "__{}__".format(data["player"])]
			output.append("**Donator**: {}".format(data["donator"]))
			output.append("**Characters**: {}".format(data["chars"]))
			output.append("**Total Fame**: {:,}".format(data["fame"]))
			output.append("**Fame Rank**: {:,}".format(data["fame_rank"]))
			output.append("**Total Exp**: {:,}".format(data["exp"]))
			output.append("**Exp Rank**: {:,}".format(data["exp_rank"]))
			output.append("**Class Quests Completed**: {}".format(data["rank"]))
			output.append("**Account Fame**: {:,}".format(data["account_fame"]))
			output.append("**Account Fame Rank**: {:,}".format(data["account_fame_rank"]))
			if "guild" in data:
				output.append("**Guild**: {}".format(data["guild"]))
				output.append("**Guild Position**: {}".format(data["guild_rank"]))
			output.append("**Created**: {}".format(data["created"]))
			output.append("**Last Seen**: {}".format(data["last_seen"]))
			output.append("**Description**: ```{}```".format("\n".join((data["desc1"], data["desc2"], data["desc3"]))))
			output.append("https://www.realmeye.com/player/{}".format(player))
			await self.bot.reply('\n'.join(output))
	
	@rotmg.command(name = "characters")
	@checks.not_forbidden()
	async def rotmg_characters(self, player : str):
		'''Realm of the Mad God player characters information'''
		url = "https://nightfirec.at/realmeye-api/?player={}".format(player)
		# http://webhost.ischool.uw.edu/~joatwood/realmeye_api/0.3/
		async with aiohttp_session.get(url) as resp:
			data = await resp.json()
		if "error" in data:
			await self.bot.reply("Error: " + data["error"])
		else:
			output = ["", "__**{}'s Characters**__".format(data["player"])]
			for character in data["characters"]:
				output.append("**Level {0[level]} {0[class]}**".format(character))
				output.append("__Fame__: {0[fame]:,}, __Exp__: {0[exp]:,}, __Rank__: {0[place]:,} __Class Quests Completed__: {0[cqc]}, __Stats Maxed__: {0[stats_maxed]}".format(character))
				output.append("__HP__: {0[hp]}, __MP__: {0[mp]}, __Attack__: {0[attack]}, __Defense__: {0[defense]}, __Speed__: {0[speed]}, __Vitality__: {0[vitality]}, __Wisdom__: {0[wisdom]}, __Dexterity__: {0[dexterity]}".format(character["stats"]))
				equips = []
				for type, equip in character["equips"].items():
					equips.append("__{}__: {}".format(type.capitalize(), equip))
				output.append(", ".join(equips))
				output.append("__Pet__: {0[pet]}, __Clothing Dye__: {0[character_dyes][clothing_dye]}, __Accessory Dye__: {0[character_dyes][accessory_dye]}, __Backpack__: {0[backpack]}".format(character))
				output.append("__Last Seen__: {0[last_seen]}, __Last Server__: {0[last_server]}".format(character))
			await self.bot.reply('\n'.join(output[:len(output) // 2]))
			await self.bot.say('\n'.join(output[len(output) // 2:]))
	
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
	
	@commands.command(aliases = ["whatare"])
	@checks.not_forbidden()
	async def whatis(self, *search : str): #WIP
		'''WIP'''
		if not search:
			await self.bot.reply("What is what?")
		else:
			url = "https://kgsearch.googleapis.com/v1/entities:search?limit=1&query={}&key={}".format('+'.join(search), credentials.google_apikey)
			async with aiohttp_session.get(url) as resp:
				data = await resp.json()
			if data.get("itemListElement") and data["itemListElement"][0].get("result", {}).get("detailedDescription", {}).get("articleBody", {}):
				await self.bot.reply(data["itemListElement"][0]["result"]["detailedDescription"]["articleBody"])
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
			return
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
	async def youtubesearch(self, *, search : str):
		'''Find a Youtube video'''
		ydl = youtube_dl.YoutubeDL({"default_search": "auto", "noplaylist": True, "quiet": True})
		func = functools.partial(ydl.extract_info, search, download = False)
		info = await self.bot.loop.run_in_executor(None, func)
		if "entries" in info:
			info = info["entries"][0]
		await self.bot.reply(info.get("webpage_url"))
	
	@youtubesearch.error
	async def youtubesearch_error(self, error, ctx):
		if "No video results" in str(error):
			await self.bot.reply("Song not found")
	
	@commands.command()
	@checks.not_forbidden()
	async def year(self, year : int):
		'''Facts about years'''
		async with aiohttp_session.get("http://numbersapi.com/{0}/year".format(year)) as resp:
			data = await resp.text()
		await self.bot.reply(data)
