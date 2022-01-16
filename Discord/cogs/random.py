
import discord
from discord.ext import commands

import asyncio
import calendar
import concurrent.futures
import csv
import datetime
import inspect
import io
import json
import multiprocessing
import random
import string
from typing import Optional
import xml.etree.ElementTree

from bs4 import BeautifulSoup
import dice
import emoji
import pydealer
import pyparsing

from utilities import checks
from utilities.converters import Maptype

def setup(bot):
	bot.add_cog(Random(bot))

class Random(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		# Add commands as random subcommands
		for name, command in inspect.getmembers(self):
			if isinstance(command, commands.Command) and command.parent is None and name != "random":
				self.bot.add_command(command)
				self.random.add_command(command)
		# Add fact subcommands as subcommands of corresponding commands
		for command, parent in ((self.fact_cat, self.cat), (self.fact_date, self.date), (self.fact_number, self.number)):
			self.fact.add_command(commands.Command(command, name = parent.name, aliases = [parent.name + 's'], 
													checks = [checks.not_forbidden().predicate]))
			parent.add_command(commands.Command(command, name = "fact", aliases = ["facts"], 
													checks = [checks.not_forbidden().predicate]))
		# Add random subcommands as subcommands of corresponding commands
		self.random_commands = (
			(self.blob, "Blobs", "blobs", []), 
			(self.color, "Resources", "color", ["colour"]), 
			(self.giphy, "Images", "giphy", []), 
			(self.map, "Location", "map", []), 
			(self.photo, "Images", "image", ["image"]), 
			(self.streetview, "Location", "streetview", []), 
			(self.time, "Location", "time", []), 
			(self.uesp, "Search", "uesp", []), 
			(self.user, "User", "user", ["member"]), 
			(self.wikipedia, "Search", "wikipedia", ["wiki"]), 
			(self.xkcd, "Entertainment", "xkcd", [])
		)
		for command, cog_name, parent_name, aliases in self.random_commands:
			self.random.add_command(commands.Command(command, aliases = aliases, checks = [checks.not_forbidden().predicate]))
			if (cog := self.bot.get_cog(cog_name)) and (parent := getattr(cog, parent_name)):
				parent.add_command(commands.Command(command, name = "random", checks = [checks.not_forbidden().predicate]))
		# Import jokes
		self.jokes = []
		try:
			with open(self.bot.data_path + "/jokes.csv", newline = "") as jokes_file:
				jokes_reader = csv.reader(jokes_file)
				for row in jokes_reader:
					self.jokes.append(row[0])
		except FileNotFoundError:
			pass
	
	def cog_unload(self):
		for command, cog_name, parent_name, _ in self.random_commands:
			if (cog := self.bot.get_cog(cog_name)) and (parent := getattr(cog, parent_name)):
				parent.remove_command("random")
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	async def random(self, ctx):
		'''
		Random things
		All random subcommands are also commands
		'''
		# TODO: random random
		await ctx.embed_reply(":grey_question: Random what?")
	
	async def blob(self, ctx):
		'''Random blob emoji'''
		if "Blobs" in self.bot.cogs:
			record = await ctx.bot.db.fetchrow("SELECT * FROM blobs.blobs TABLESAMPLE BERNOULLI (1) LIMIT 1")
			await ctx.embed_reply(title = record["blob"], image_url = record["image"])
	
	async def color(self, ctx):
		'''Information on a random color'''
		url = "http://www.colourlovers.com/api/colors/random"
		params = {"numResults": 1}
		if cog := self.bot.get_cog("Resources"):
			await cog.process_color(ctx, url, params)
	
	async def giphy(self, ctx):
		'''Random gif from giphy'''
		url = "http://api.giphy.com/v1/gifs/random"
		params = {"api_key": ctx.bot.GIPHY_API_KEY}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		await ctx.embed_reply(image_url = data["data"]["image_url"])
	
	async def map(self, ctx, zoom: Optional[int] = 13, maptype: Optional[Maptype] = "roadmap"):
		'''
		See map of random location
		Zoom: 0 - 21+
		Map Types: roadmap, satellite, hybrid, terrain
		'''
		latitude = random.uniform(-90, 90)
		longitude = random.uniform(-180, 180)
		url = "https://maps.googleapis.com/maps/api/staticmap"
		params = {"center": f"{latitude},{longitude}", "zoom": zoom, "maptype": maptype, "size": "640x640", 
					"key": ctx.bot.GOOGLE_API_KEY}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.read()
		await ctx.embed_reply(fields = (("latitude", latitude), ("longitude", longitude)), 
								image_url = "attachment://map.png", 
								file = discord.File(io.BytesIO(data), filename = "map.png"))
	
	async def photo(self, ctx, *, query = ""):
		'''Random photo from Unsplash'''
		url = "https://api.unsplash.com/photos/random"
		headers = {"Accept-Version": "v1", "Authorization": f"Client-ID {ctx.bot.UNSPLASH_ACCESS_KEY}"}
		params = {"query": query}
		async with ctx.bot.aiohttp_session.get(url, headers = headers, params = params) as resp:
			data = await resp.json()
		if "errors" in data:
			errors = '\n'.join(data["errors"])
			return await ctx.embed_reply(f":no_entry: Error:\n{errors}")
		await ctx.embed_reply(data["description"] or "", 
								author_name = f"{data['user']['name']} on Unsplash", 
								author_url = f"{data['user']['links']['html']}?utm_source=Harmonbot&utm_medium=referral", 
								author_icon_url = data["user"]["profile_image"]["small"], 
								image_url = data["urls"]["full"])
	
	async def streetview(self, ctx, radius: int = 5_000_000):
		'''
		Generate street view of a random location
		`radius`: sets a radius, specified in meters, in which to search for a panorama, centered on the given latitude and longitude.
		Valid values are non-negative integers.
		'''
		latitude = random.uniform(-90, 90)
		longitude = random.uniform(-180, 180)
		url = "https://maps.googleapis.com/maps/api/streetview"
		params = {"location": f"{latitude},{longitude}", "size": "640x640", "fov": 120, "radius": radius, 
					"key": ctx.bot.GOOGLE_API_KEY}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.read()
		await ctx.embed_reply(fields = (("latitude", latitude), ("longitude", longitude)), 
								image_url = "attachment://streetview.png", 
								file = discord.File(io.BytesIO(data), filename = "streetview.png"))
	
	async def time(self, ctx):
		'''Random time'''
		await ctx.embed_reply(f"{random.randint(0, 23):02}:{random.randint(0, 59):02}")
	
	async def uesp(self, ctx):
		'''
		Random UESP page
		[UESP](http://uesp.net/wiki/Main_Page)
		'''
		if cog := self.bot.get_cog("Search"):
			await cog.process_uesp(ctx, None, random = True)
		else:
			await ctx.embed_reply(title = "Random UESP page", title_url = "http://uesp.net/wiki/Special:Random")  # necessary?
	
	async def user(self, ctx):
		'''Random user/member'''
		await ctx.embed_reply(random.choice(ctx.guild.members).mention)
	
	async def wikipedia(self, ctx):
		'''Random Wikipedia article'''
		if cog := self.bot.get_cog("Search"):
			await cog.process_wikipedia(ctx, None, random = True)
		else:
			await ctx.embed_reply(title = "Random Wikipedia article", title_url = "https://wikipedia.org/wiki/Special:Random")  # necessary?
	
	async def xkcd(self, ctx):
		'''Random xkcd'''
		url = "http://xkcd.com/info.0.json"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		number = random.randint(1, data['num'])
		url = f"http://xkcd.com/{number}/info.0.json"
		if cog := self.bot.get_cog("Entertainment"):
			await cog.process_xkcd(ctx, url)
	
	@commands.command(aliases = ["rabbit"])
	async def bunny(self, ctx):
		'''Random bunny'''
		url = "https://api.bunnies.io/v2/loop/random/?media=gif"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		gif = data["media"]["gif"]
		await ctx.embed_reply(f"[:rabbit2:]({gif})", image_url = gif)
	
	@commands.command()
	async def card(self, ctx):
		'''Random playing card'''
		await ctx.embed_reply(f":{random.choice(pydealer.const.SUITS).lower()}: {random.choice(pydealer.const.VALUES)}")
	
	@commands.group(case_insensitive = True, invoke_without_command = True)
	async def cat(self, ctx, category: Optional[str]):
		'''Random image of a cat'''
		url = "http://thecatapi.com/api/images/get"
		params = {"format": "xml", "results_per_page": 1}
		if category:
			params["category"] = category
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.text()
		try:
			if (url := xml.etree.ElementTree.fromstring(data).find(".//url")) is None:
				await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: Category not found")
				return
		except xml.etree.ElementTree.ParseError:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error")
		else:
			await ctx.embed_reply(f"[\N{CAT FACE}]({url.text})", image_url = url.text)
	
	@cat.command(name = "categories", aliases = ["cats"])
	async def cat_categories(self, ctx):
		'''Categories of cat images'''
		url = "http://thecatapi.com/api/categories/list"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.text()
		try:
			categories = xml.etree.ElementTree.fromstring(data).findall(".//name")
		except xml.etree.ElementTree.ParseError:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error")
		else:
			await ctx.embed_reply('\n'.join(sorted(category.text for category in categories)))
	
	@commands.command(aliases = ["choice", "pick"], require_var_positional = True)
	async def choose(self, ctx, *choices: str):
		'''
		Randomly chooses between multiple options
		choose <option1> <option2> <...>
		'''
		await ctx.embed_reply(random.choice(choices))
	
	@commands.command(aliases = ["flip"])
	async def coin(self, ctx):
		'''Flip a coin'''
		await ctx.embed_reply(random.choice(("Heads!", "Tails!")))
	
	@commands.command()
	async def command(self, ctx):
		'''Random command'''
		await ctx.embed_reply(f"{ctx.prefix}{random.choice(tuple(set(command.name for command in self.bot.commands)))}")
	
	@commands.command(aliases = ["die", "roll"])
	async def dice(self, ctx, *, input: str = '6'):
		'''
		Roll dice
		Inputs:                                      Examples:
		S     |  S - number of sides (default is 6)  [6      | 12]
		AdS   |  A - amount (default is 1)           [5d6    | 2d10]
		AdSt  |  t - return total                    [2d6t   | 20d5t]
		AdSs  |  s - return sorted                   [4d6s   | 5d8s]
		AdS^H | ^H - return highest H rolls          [10d6^4 | 2d7^1]
		AdSvL | vL - return lowest L rolls           [15d7v2 | 8d9v2]
		'''
		# TODO: Add documentation on arithmetic/basic integer operations
		if 'd' not in input:
			input = 'd' + input
		with multiprocessing.Pool(1) as pool:
			async_result = pool.apply_async(dice.roll, (input,))
			future = self.bot.loop.run_in_executor(None, async_result.get, 10.0)
			try:
				result = await asyncio.wait_for(future, 10.0)
				if isinstance(result, int):
					await ctx.embed_reply(result)
				else:
					await ctx.embed_reply(", ".join(str(roll) for roll in result))
			except discord.HTTPException:
				# TODO: use textwrap/paginate
				await ctx.embed_reply(":no_entry: Output too long")
			except pyparsing.ParseException:
				await ctx.embed_reply(":no_entry: Invalid input")
			except (concurrent.futures.TimeoutError, multiprocessing.context.TimeoutError):
				await ctx.embed_reply(":no_entry: Execution exceeded time limit")
			except dice.DiceFatalException as e:
				await ctx.embed_reply(f":no_entry: Error: {e}")
	
	@commands.group(case_insensitive = True, invoke_without_command = True)
	async def date(self, ctx):
		'''Random date'''
		await ctx.embed_reply(
			datetime.date.fromordinal(
				random.randint(1, 365)
			).strftime("%B %d")
		)
	
	@commands.command()
	async def day(self, ctx):
		'''Random day of week'''
		await ctx.embed_reply(random.choice(calendar.day_name))
	
	@commands.group(case_insensitive = True, invoke_without_command = True)
	async def dog(self, ctx, *, breed: Optional[str]):
		'''
		Random image of a dog
		[breed] [sub-breed] to specify a specific sub-breed
		'''
		if breed:
			url = f"https://dog.ceo/api/breed/{breed.lower().replace(' ', '/')}/images/random"
			async with ctx.bot.aiohttp_session.get(url) as resp:
				data = await resp.json()
			if data["status"] == "error":
				await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {data['message']}")
				return
			await ctx.embed_reply(f"[:dog2:]({data['message']})", image_url = data["message"])
		else:
			url = "https://dog.ceo/api/breeds/image/random"
			async with ctx.bot.aiohttp_session.get(url) as resp:
				data = await resp.json()
			await ctx.embed_reply(f"[:dog2:]({data['message']})", image_url = data["message"])
	
	@dog.command(name = "breeds", aliases = ["breed", "subbreeds", "subbreed", "sub-breeds", "sub-breed"])
	async def dog_breeds(self, ctx):
		'''Breeds and sub-breeds of dogs for which images are categorized under'''
		url = "https://dog.ceo/api/breeds/list/all"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		breeds = data["message"]
		await ctx.embed_reply(", ".join(f"**{breed.capitalize()}** ({', '.join(sub.capitalize() for sub in subs)})" if subs 
										else f"**{breed.capitalize()}**"
										for breed, subs in breeds.items()), 
								footer_text = "Sub-breeds are in parentheses after the corresponding breed")
	
	@commands.command(aliases = ["emoji"])
	async def emote(self, ctx):
		'''Random emote/emoji'''
		await ctx.embed_reply(random.choice(list(emoji.UNICODE_EMOJI)))
	
	@commands.group(case_insensitive = True, invoke_without_command = True)
	async def fact(self, ctx):
		'''Random fact'''
		url = "https://mentalfloss.com/api/facts"
		# params = {"limit": 1, "cb": random.random()}
		# https://mentalfloss.com/amazingfactgenerator
		# uses page, limit, and cb parameters, seemingly to no effect
		async with ctx.bot.aiohttp_session.get(url) as resp:
			if resp.status == 503:
				return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: API Service Unavailable")
			data = await resp.json(content_type = "text/plain")
		await ctx.embed_reply(BeautifulSoup(data[0]["fact"], "lxml").text, 
								image_url = data[0]["primaryImage"])
	
	async def fact_cat(self, ctx):
		'''Random fact about cats'''
		url = "https://cat-facts-as-a-service.appspot.com/fact"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			fact = await resp.text()
		await ctx.embed_reply(fact)
	
	async def fact_date(self, ctx, date: str):
		'''
		Random fact about a date
		Format: month/date
		Example: 1/1
		'''
		url = f"http://numbersapi.com/{date}/date"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			if resp.status == 404:
				await ctx.embed_reply(f"{ctx.bot.error_emoji} Error")
				return
			data = await resp.text()
		await ctx.embed_reply(data)
	
	@fact.command(name = "math")
	async def fact_math(self, ctx, number: int):
		'''Random math fact about a number'''
		url = f"http://numbersapi.com/{number}/math"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.text()
		await ctx.embed_reply(data)
	
	async def fact_number(self, ctx, number: int):
		'''Random fact about a number'''
		url = f"http://numbersapi.com/{number}"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.text()
		await ctx.embed_reply(data)
	
	@fact.command(name = "year")
	async def fact_year(self, ctx, year: int):
		'''Random fact about a year'''
		url = f"http://numbersapi.com/{year}/year"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.text()
		await ctx.embed_reply(data)
	
	@commands.command()
	async def idea(self, ctx):
		'''Random idea'''
		url = "http://itsthisforthat.com/api.php"
		async with ctx.bot.aiohttp_session.get(url, params = "json") as resp:
			data = await resp.json(content_type = "text/javascript")
		await ctx.embed_reply(f"{data['this']} for {data['that']}")
	
	@commands.command()
	async def insult(self, ctx):
		'''Random insult'''
		url = "http://quandyfactory.com/insult/json"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			if resp.status == 500:
				await ctx.embed_reply(
					f"{ctx.bot.error_emoji} API Error: "
					f"{resp.status} {resp.reason}"
				)
				return
			data = await resp.json()
		await ctx.embed_reply(data["insult"])
	
	@commands.group(case_insensitive = True, invoke_without_command = True)
	async def joke(self, ctx):
		'''Random joke'''
		# Sources:
		# https://github.com/KiaFathi/tambalAPI
		# https://www.kaggle.com/abhinavmoudgil95/short-jokes 
		# (https://github.com/amoudgl/short-jokes-dataset)
		if self.jokes:
			await ctx.embed_reply(random.choice(self.jokes))
	
	@joke.group(name = "dad", case_insensitive = True, invoke_without_command = True)
	async def joke_dad(self, ctx, joke_id: Optional[str]):
		'''Random dad joke'''
		# TODO: search, GraphQL?
		url = "https://icanhazdadjoke.com/"
		if joke_id:
			url += "j/" + joke_id
		headers = {"Accept": "application/json", "User-Agent": ctx.bot.user_agent}
		async with ctx.bot.aiohttp_session.get(url, headers = headers) as resp:
			data = await resp.json()
		
		if data["status"] == 404:
			await ctx.embed_reply(f":no_entry: Error: {data['message']}")
			return
		
		await ctx.embed_reply(data["joke"], footer_text = f"Joke ID: {data['id']}")
	
	@joke_dad.command(name = "image")
	async def joke_dad_image(self, ctx, joke_id: Optional[str]):
		'''Random dad joke as an image'''
		if not joke_id:
			url = "https://icanhazdadjoke.com/"
			headers = {"Accept": "application/json", "User-Agent": ctx.bot.user_agent}
			async with ctx.bot.aiohttp_session.get(url, headers = headers) as resp:
				data = await resp.json()
			joke_id = data["id"]
		await ctx.embed_reply(image_url = f"https://icanhazdadjoke.com/j/{joke_id}.png")
	
	@commands.command(aliases = ["lat"])
	async def latitude(self, ctx):
		'''Random latitude'''
		await ctx.embed_reply(str(random.uniform(-90, 90)))
	
	@commands.command()
	async def letter(self, ctx):
		'''Random letter'''
		await ctx.embed_reply(random.choice(string.ascii_uppercase))
	
	@commands.command()
	async def location(self, ctx):
		'''Random location'''
		await ctx.embed_reply(f"{random.uniform(-90, 90)}, {random.uniform(-180, 180)}")
	
	@commands.command(aliases = ["long"])
	async def longitude(self, ctx):
		'''Random longitude'''
		await ctx.embed_reply(str(random.uniform(-180, 180)))
	
	@commands.group(aliases = ["rng"], invoke_without_command = True, case_insensitive = True)
	async def number(self, ctx, number: int = 10):
		'''
		Random number
		Default range is 1 to 10
		'''
		try:
			await ctx.embed_reply(random.randint(1, number))
		except ValueError:
			await ctx.embed_reply(":no_entry: Error: Input must be >= 1")
	
	@commands.command(aliases = ["why"])
	async def question(self, ctx):
		'''Random question'''
		async with ctx.bot.aiohttp_session.get("http://xkcd.com/why.txt") as resp:
			data = await resp.text()
		questions = data.split('\n')
		await ctx.embed_reply("{}?".format(random.choice(questions).capitalize()))
	
	@commands.command()
	async def quote(self, ctx, message: Optional[discord.Message]):
		'''Random quote or quote a message'''
		# TODO: separate message quoting
		# TODO: other options to quote by?
		if message:
			await ctx.embed_reply(
				author_name = message.author.display_name,
				author_icon_url = message.author.display_avatar.url,
				description = message.content,
				footer_text = "Sent", timestamp = message.created_at
			)
			return
		
		url = "http://api.forismatic.com/api/1.0/"
		params = {"method": "getQuote", "format": "json", "lang": "en"}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			try:
				data = await resp.json()
			except json.JSONDecodeError:
				# Handle invalid JSON - escaped single quotes
				data = await resp.text()
				data = json.loads(data.replace("\\'", "'"))
		await ctx.embed_reply(
			description = data["quoteText"],
			footer_text = data["quoteAuthor"]
		)  # TODO: quoteLink?
	
	@commands.command()
	async def word(self, ctx):
		'''Random word'''
		await ctx.embed_reply(self.bot.wordnik_words_api.getRandomWord().word.capitalize())

