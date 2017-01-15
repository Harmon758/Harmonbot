
from discord.ext import commands

from bs4 import BeautifulSoup
import calendar
import copy
import datetime
import inspect
import pydealer
import random
import string
import xml.etree.ElementTree

from utilities import checks
import clients
import credentials

def setup(bot):
	bot.add_cog(Random(bot))

class Random:
	
	def __init__(self, bot):
		self.bot = bot
		for name, command in inspect.getmembers(self):
			if isinstance(command, commands.Command) and command.parent is None and name != "random":
				self.bot.add_command(command)
				self.random.add_command(command)
		self.fact_commands = ((self.fact_cat, self.cat), (self.fact_date, self.date), (self.fact_number, self.number))
		for command, parent in self.fact_commands:
			subcommand = copy.copy(command)
			subcommand.name = "fact"
			subcommand.aliases = []
			async def wrapper(*args, command = command, **kwargs):
				await command.callback(self, *args, **kwargs)
			subcommand.callback = wrapper
			subcommand.params = inspect.signature(subcommand.callback).parameters.copy()
			parent.add_command(subcommand)
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def random(self):
		'''
		Random things
		All random subcommands are also commands
		'''
		await self.bot.embed_reply(":grey_question: Random what?")
	
	@commands.command()
	@checks.not_forbidden()
	async def card(self):
		'''Random playing card'''
		await self.bot.embed_reply(":{}: {}".format(random.choice(pydealer.const.SUITS).lower(), random.choice(pydealer.const.VALUES)))
	
	@commands.group(pass_context = True, invoke_without_command = True)
	@checks.not_forbidden()
	async def cat(self, ctx, *, category : str = ""):
		'''
		Random image of a cat
		cat categories (cats) for different categories you can choose from
		cat <category> for a random image of a cat from that category
		'''
		if category and category in ("categories", "cats"):
			async with clients.aiohttp_session.get("http://thecatapi.com/api/categories/list") as resp:
				data = await resp.text()
			categories = xml.etree.ElementTree.fromstring(data).findall(".//name")
			await self.bot.embed_reply('\n'.join(sorted(category.text for category in categories)))
		elif category:
			async with clients.aiohttp_session.get("http://thecatapi.com/api/images/get?format=xml&results_per_page=1&category={}".format(category)) as resp:
				data = await resp.text()
			url = xml.etree.ElementTree.fromstring(data).find(".//url")
			if url is not None:
				await self.bot.embed_reply("[:cat:]({})".format(url.text), image_url = url.text)
			else:
				await self.bot.embed_reply(":no_entry: Error: Category not found")
		else:
			async with clients.aiohttp_session.get("http://thecatapi.com/api/images/get?format=xml&results_per_page=1") as resp:
				data = await resp.text()
			url = xml.etree.ElementTree.fromstring(data).find(".//url").text
			await self.bot.embed_reply("[:cat:]({})".format(url), image_url = url)
	
	@commands.command(pass_context = True)
	@checks.not_forbidden()
	async def command(self, ctx):
		'''Random command'''
		await self.bot.embed_reply("{}{}".format(ctx.prefix, random.choice(tuple(set(command.name for command in self.bot.commands.values())))))
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def date(self):
		'''Random date'''
		await self.bot.embed_reply(datetime.date.fromordinal(random.randint(1, 365)).strftime("%B %d"))
	
	@commands.command()
	@checks.not_forbidden()
	async def day(self):
		'''Random day of week'''
		await self.bot.embed_reply(random.choice(calendar.day_name))
	
	@commands.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def fact(self):
		'''Random fact'''
		async with clients.aiohttp_session.get("http://mentalfloss.com/api/1.0/views/amazing_facts.json?limit=1&bypass=1") as resp:
			data = await resp.json()
		await self.bot.embed_reply(BeautifulSoup(data[0]["nid"]).text)
	
	@fact.command(name = "cat", aliases = ["cats"], pass_context = True)
	@checks.not_forbidden()
	async def fact_cat(self, ctx):
		'''Random fact about cats'''
		async with clients.aiohttp_session.get("http://catfacts-api.appspot.com/api/facts") as resp:
			data = await resp.json()
		if data["success"]:
			await self.bot.embed_reply(data["facts"][0])
		else:
			await self.bot.embed_reply(":no_entry: Error")
	
	@fact.command(name = "date")
	@checks.not_forbidden()
	async def fact_date(self, date : str):
		'''
		Random fact about a date
		Format: month/date
		Example: 1/1
		'''
		async with clients.aiohttp_session.get("http://numbersapi.com/{}/date".format(date)) as resp:
			if resp.status == 404:
				await self.bot.embed_reply(":no_entry: Error")
				return
			data = await resp.text()
		await self.bot.embed_reply(data)
	
	@fact.command(name = "math")
	@checks.not_forbidden()
	async def fact_math(self, number : int):
		'''Random math fact about a number'''
		async with clients.aiohttp_session.get("http://numbersapi.com/{}/math".format(number)) as resp:
			data = await resp.text()
		await self.bot.embed_reply(data)
	
	@fact.command(name = "number")
	@checks.not_forbidden()
	async def fact_number(self, number : int):
		'''Random fact about a number'''
		async with clients.aiohttp_session.get("http://numbersapi.com/{}".format(number)) as resp:
			data = await resp.text()
		await self.bot.embed_reply(data)
	
	@fact.command(name = "year")
	@checks.not_forbidden()
	async def fact_year(self, year : int):
		'''Random fact about a year'''
		async with clients.aiohttp_session.get("http://numbersapi.com/{}/year".format(year)) as resp:
			data = await resp.text()
		await self.bot.embed_reply(data)
	
	@commands.command()
	@checks.not_forbidden()
	async def idea(self):
		'''Random idea'''
		async with clients.aiohttp_session.get("http://itsthisforthat.com/api.php?json") as resp:
			data = await resp.json()
		await self.bot.embed_reply("{0[this]} for {0[that]}".format(data))
	
	@commands.command()
	@checks.not_forbidden()
	async def insult(self):
		'''Random insult'''
		async with clients.aiohttp_session.get("http://quandyfactory.com/insult/json") as resp:
			data = await resp.json()
		await self.bot.embed_say(data["insult"])
	
	@commands.command()
	@checks.not_forbidden()
	async def joke(self):
		'''Random joke'''
		async with clients.aiohttp_session.get("http://tambal.azurewebsites.net/joke/random") as resp:
			data = await resp.json()
		await self.bot.embed_reply(data["joke"])
	
	@commands.command()
	@checks.not_forbidden()
	async def letter(self):
		'''Random letter'''
		await self.bot.embed_reply(random.choice(string.ascii_uppercase))
	
	@commands.command()
	@checks.not_forbidden()
	async def location(self):
		'''Random location'''
		await self.bot.embed_reply("{}, {}".format(random.uniform(-90, 90), random.uniform(-180, 180)))
	
	@commands.group(aliases = ["rng"], invoke_without_command = True)
	@checks.not_forbidden()
	async def number(self, number : int = 10):
		'''
		Random number
		Default range is 1 to 10
		'''
		await self.bot.embed_reply(random.randint(1, number))
	
	@commands.command(aliases = ["why"])
	@checks.not_forbidden()
	async def question(self):
		'''Random question'''
		async with clients.aiohttp_session.get("http://xkcd.com/why.txt") as resp:
			data = await resp.text()
		questions = data.split('\n')
		await self.bot.embed_reply("{}?".format(random.choice(questions).capitalize()))
	
	@commands.command()
	@checks.not_forbidden()
	async def quote(self):
		'''Random quote'''
		async with clients.aiohttp_session.get("http://api.forismatic.com/api/1.0/?method=getQuote&format=json&lang=en") as resp:
			try:
				data = await resp.json()
			except:
				await self.bot.embed_reply(":no_entry: Error")
				return
		await self.bot.embed_reply(data["quoteText"], footer_text = data["quoteAuthor"]) # quoteLink?
	
	@commands.command()
	@checks.not_forbidden()
	async def time(self):
		'''Random time'''
		await self.bot.embed_reply("{:02d}:{:02d}".format(random.randint(0, 23), random.randint(0, 59)))
	
	@commands.command()
	@checks.not_forbidden()
	async def word(self):
		'''Random word'''
		url = "http://api.wordnik.com:80/v4/words.json/randomWord?hasDictionaryDef=false&minCorpusCount=0&maxCorpusCount=-1&minDictionaryCount=1&maxDictionaryCount=-1&minLength=5&maxLength=-1&api_key={0}".format(credentials.wordnik_apikey)
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json()
		word = data["word"]
		await self.bot.embed_reply(word.capitalize())
