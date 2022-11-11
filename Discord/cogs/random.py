
import discord
from discord.ext import commands

import asyncio
import calendar
import concurrent.futures
import csv
import datetime
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
from utilities.menu_sources import XKCDSource
from utilities.paginators import ButtonPaginator

async def setup(bot):
	await bot.add_cog(Random(bot))

class Random(commands.Cog):
	"""Random"""
	
	def __init__(self, bot):
		self.bot = bot
		# Import jokes
		self.jokes = []
		try:
			with open(self.bot.data_path + "/jokes.csv", newline = "") as jokes_file:
				jokes_reader = csv.reader(jokes_file)
				for row in jokes_reader:
					self.jokes.append(row[0])
		except FileNotFoundError:
			pass
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.hybrid_group(case_insensitive = True)
	async def random(self, ctx):
		'''
		Random things
		All random subcommands are also commands
		'''
		# TODO: random random
		await ctx.embed_reply(":grey_question: Random what?")
	
	@random.command(with_app_command = False)
	async def blob(self, ctx):
		"""Random blob emoji"""
		if command := ctx.bot.get_command("blob random"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"blob random command not found "
				"when random blob command invoked"
			)
	
	@random.command(
		name = "bunny", aliases = ["rabbit"], with_app_command = False
	)
	async def random_bunny(self, ctx):
		'''Random bunny'''
		# Note: bunny command invokes this command
		url = "https://api.bunnies.io/v2/loop/random/?media=gif"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		gif = data["media"]["gif"]
		await ctx.embed_reply(f"[:rabbit2:]({gif})", image_url = gif)
	
	@commands.command(aliases = ["rabbit"])
	async def bunny(self, ctx):
		"""Random bunny"""
		if command := ctx.bot.get_command("random bunny"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random bunny command not found when bunny command invoked"
			)
	
	@random.command(name = "card", with_app_command = False)
	async def random_card(self, ctx):
		'''Random playing card'''
		# Note: card command invokes this command
		await ctx.embed_reply(f":{random.choice(pydealer.const.SUITS).lower()}: {random.choice(pydealer.const.VALUES)}")
	
	@commands.command()
	async def card(self, ctx):
		"""Random playing card"""
		if command := ctx.bot.get_command("random card"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random card command not found when card command invoked"
			)
	
	@random.group(name = "cat", fallback = "image", case_insensitive = True)
	async def random_cat(self, ctx, category: Optional[str]):
		'''Random image of a cat'''
		# Note: cat command invokes this command
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
	
	@commands.group(case_insensitive = True, invoke_without_command = True)
	async def cat(self, ctx, category: Optional[str]):
		"""Random image of a cat"""
		if command := ctx.bot.get_command("random cat"):
			await ctx.invoke(command, category = category)
		else:
			raise RuntimeError(
				"random cat command not found when cat command invoked"
			)
	
	@random_cat.command(
		name = "categories", aliases = ["cats"], with_app_command = False
	)
	async def random_cat_categories(self, ctx):
		'''Categories of cat images'''
		# Note: cat categories command invokes this command
		url = "http://thecatapi.com/api/categories/list"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.text()
		try:
			categories = xml.etree.ElementTree.fromstring(data).findall(".//name")
		except xml.etree.ElementTree.ParseError:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error")
		else:
			await ctx.embed_reply('\n'.join(sorted(category.text for category in categories)))
	
	@cat.command(name = "categories", aliases = ["cats"])
	async def cat_categories(self, ctx):
		"""Categories of cat images"""
		if command := ctx.bot.get_command("random cat categories"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random cat categories command not found "
				"when cat categories command invoked"
			)
	
	@random_cat.command(name = "fact")
	async def random_cat_fact(self, ctx):
		'''Random fact about cats'''
		# Note: cat fact command invokes this command
		# Note: fact cat command invokes this command
		# Note: random fact cat command invokes this command
		url = "https://catfact.ninja/fact"
		# https://cat-facts-as-a-service.appspot.com/fact returns a 500 Server
		# Error now
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		await ctx.embed_reply(data["fact"])
	
	@cat.command(name = "fact")
	async def cat_fact(self, ctx):
		"""Random fact about cats"""
		if command := ctx.bot.get_command("random cat fact"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random cat fact command not found "
				"when cat fact command invoked"
			)
	
	@random.command(name = "choose", aliases = ["choice", "pick"], require_var_positional = True, with_app_command = False)
	async def random_choose(self, ctx, *choices: str):
		'''
		Randomly chooses between multiple options
		choose <option1> <option2> <...>
		'''
		# Note: choose command invokes this command
		await ctx.embed_reply(random.choice(choices))
	
	@commands.command(
		aliases = ["choice", "pick"], require_var_positional = True
	)
	async def choose(self, ctx, *choices: str):
		"""
		Randomly chooses between multiple options
		choose <option1> <option2> <...>
		"""
		if command := ctx.bot.get_command("random choose"):
			await ctx.invoke(command, *choices)
		else:
			raise RuntimeError(
				"random choose command not found when choose command invoked"
			)
	
	@random.command(name = "coin", aliases = ["flip"], with_app_command = False)
	async def random_coin(self, ctx):
		'''Flip a coin'''
		# Note: coin command invokes this command
		await ctx.embed_reply(random.choice(("Heads!", "Tails!")))
	
	@commands.command(aliases = ["flip"])
	async def coin(self, ctx):
		"""Flip a coin"""
		if command := ctx.bot.get_command("random coin"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random coin command not found when coin command invoked"
			)
	
	@random.command(aliases = ["colour"], with_app_command = False)
	async def color(self, ctx):
		"""Information on a random color"""
		if command := ctx.bot.get_command("color random"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"color random command not found "
				"when random color command invoked"
			)
	
	@random.command(name = "command", with_app_command = False)
	async def random_command(self, ctx):
		'''Random command'''
		# Note: command command invokes this command
		await ctx.embed_reply(f"{ctx.prefix}{random.choice(tuple(set(command.name for command in ctx.bot.commands)))}")
	
	@commands.command()
	async def command(self, ctx):
		"""Random command"""
		if command := ctx.bot.get_command("random command"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random command command not found when command command invoked"
			)
	
	@random.command(
		name = "dice", aliases = ["die", "roll"], with_app_command = False
	)
	async def random_dice(self, ctx, *, input: str = '6'):
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
		# Note: dice command invokes this command
		# TODO: Add documentation on arithmetic/basic integer operations
		if 'd' not in input:
			input = 'd' + input
		with multiprocessing.Pool(1) as pool:
			async_result = pool.apply_async(dice.roll, (input,))
			future = ctx.bot.loop.run_in_executor(None, async_result.get, 10.0)
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
	
	@commands.command(aliases = ["die", "roll"])
	async def dice(self, ctx, *, input: str = '6'):
		"""
		Roll dice
		Inputs:                                      Examples:
		S     |  S - number of sides (default is 6)  [6      | 12]
		AdS   |  A - amount (default is 1)           [5d6    | 2d10]
		AdSt  |  t - return total                    [2d6t   | 20d5t]
		AdSs  |  s - return sorted                   [4d6s   | 5d8s]
		AdS^H | ^H - return highest H rolls          [10d6^4 | 2d7^1]
		AdSvL | vL - return lowest L rolls           [15d7v2 | 8d9v2]
		"""
		if command := ctx.bot.get_command("random dice"):
			await ctx.invoke(command, input = input)
		else:
			raise RuntimeError(
				"random dice command not found when dice command invoked"
			)
	
	@random.group(
		name = "date", case_insensitive = True, with_app_command = False
	)
	async def random_date(self, ctx):
		'''Random date'''
		# Note: date command invokes this command
		await ctx.embed_reply(
			datetime.date.fromordinal(
				random.randint(1, 365)
			).strftime("%B %d")
		)
	
	@commands.group(case_insensitive = True, invoke_without_command = True)
	async def date(self, ctx):
		"""Random date"""
		if command := ctx.bot.get_command("random date"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random date command not found when date command invoked"
			)
	
	@random_date.command(name = "fact", with_app_command = False)
	async def random_date_fact(self, ctx, date: str):
		'''
		Random fact about a date
		Format: month/date
		Example: 1/1
		'''
		# Note: date fact command invokes this command
		# Note: fact date command invokes this command
		# Note: random fact date command invokes this command
		url = f"http://numbersapi.com/{date}/date"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			if resp.status == 404:
				await ctx.embed_reply(f"{ctx.bot.error_emoji} Error")
				return
			data = await resp.text()
		await ctx.embed_reply(data)
	
	@date.command(name = "fact")
	async def date_fact(self, ctx, date: str):
		"""
		Random fact about a date
		Format: month/date
		Example: 1/1
		"""
		if command := ctx.bot.get_command("random date fact"):
			await ctx.invoke(command, date = date)
		else:
			raise RuntimeError(
				"random date fact command not found "
				"when date fact command invoked"
			)
	
	@random.command(name = "day", with_app_command = False)
	async def random_day(self, ctx):
		"""Random day of week"""
		# Note: day command invokes this command
		await ctx.embed_reply(random.choice(calendar.day_name))
	
	@commands.command()
	async def day(self, ctx):
		"""Random day of week"""
		if command := ctx.bot.get_command("random day"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random day command not found when day command invoked"
			)
	
	@random.group(
		name = "dog", case_insensitive = True, with_app_command = False
	)
	async def random_dog(self, ctx, *, breed: Optional[str]):
		'''
		Random image of a dog
		[breed] [sub-breed] to specify a specific sub-breed
		'''
		# Note: dog command invokes this command
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
	
	@commands.group(case_insensitive = True, invoke_without_command = True)
	async def dog(self, ctx, *, breed: Optional[str]):
		"""
		Random image of a dog
		[breed] [sub-breed] to specify a specific sub-breed
		"""
		if command := ctx.bot.get_command("random dog"):
			await ctx.invoke(command, breed = breed)
		else:
			raise RuntimeError(
				"random dog command not found when dog command invoked"
			)
	
	@random_dog.command(name = "breeds", aliases = ["breed", "subbreeds", "subbreed", "sub-breeds", "sub-breed"], with_app_command = False)
	async def random_dog_breeds(self, ctx):
		'''Breeds and sub-breeds of dogs for which images are categorized under'''
		# Note: dog breeds command invokes this command
		url = "https://dog.ceo/api/breeds/list/all"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		breeds = data["message"]
		await ctx.embed_reply(", ".join(f"**{breed.capitalize()}** ({', '.join(sub.capitalize() for sub in subs)})" if subs 
										else f"**{breed.capitalize()}**"
										for breed, subs in breeds.items()), 
								footer_text = "Sub-breeds are in parentheses after the corresponding breed")
	
	@dog.command(
		name = "breeds",
		aliases = ["breed", "subbreeds", "subbreed", "sub-breeds", "sub-breed"]
	)
	async def dog_breeds(self, ctx):
		"""
		Breeds and sub-breeds of dogs for which images are categorized under
		"""
		if command := ctx.bot.get_command("random dog breeds"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random dog breeds command not found "
				"when dog breeds command invoked"
			)
	
	@random.command(name = "emoji", aliases = ["emote"])
	async def random_emoji(self, ctx):
		"""Random emoji"""
		# Note: emoji command invokes this command
		await ctx.embed_reply(random.choice(list(emoji.UNICODE_EMOJI["en"])))
	
	@commands.command(aliases = ["emote"])
	async def emoji(self, ctx):
		"""Random emoji"""
		if command := ctx.bot.get_command("random emoji"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random emoji command not found when emoji command invoked"
			)
	
	@random.group(
		name = "fact", case_insensitive = True, with_app_command = False
	)
	async def random_fact(self, ctx):
		'''Random fact'''
		# Note: fact command invokes this command
		url = "https://mentalfloss.com/api/facts"
		# params = {"limit": 1, "cb": random.random()}
		# https://mentalfloss.com/amazingfactgenerator
		# uses page, limit, and cb parameters, seemingly to no effect
		async with ctx.bot.aiohttp_session.get(url) as resp:
			if resp.status == 503:
				await ctx.embed_reply(
					f"{ctx.bot.error_emoji} Error: API Service Unavailable"
				)
				return
			data = await resp.json(content_type = "text/plain")
		await ctx.embed_reply(
			BeautifulSoup(data[0]["fact"], "lxml").text, 
			image_url = data[0]["primaryImage"]
		)
	
	@commands.group(case_insensitive = True, invoke_without_command = True)
	async def fact(self, ctx):
		"""Random fact"""
		if command := ctx.bot.get_command("random fact"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random fact command not found when fact command invoked"
			)
	
	@random_fact.command(name = "cat", with_app_command = False)
	async def random_fact_cat(self, ctx):
		"""Random fact about cats"""
		if command := ctx.bot.get_command("random cat fact"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random cat fact command not found "
				"when random fact cat command invoked"
			)
	
	@fact.command(name = "cat")
	async def fact_cat(self, ctx):
		"""Random fact about cats"""
		if command := ctx.bot.get_command("random cat fact"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random cat fact command not found "
				"when fact cat command invoked"
			)
	
	@random_fact.command(name = "date", with_app_command = False)
	async def random_fact_date(self, ctx, date: str):
		"""
		Random fact about a date
		Format: month/date
		Example: 1/1
		"""
		if command := ctx.bot.get_command("random date fact"):
			await ctx.invoke(command, date = date)
		else:
			raise RuntimeError(
				"random date fact command not found "
				"when random fact date command invoked"
			)
	
	@fact.command(name = "date")
	async def fact_date(self, ctx, date: str):
		"""
		Random fact about a date
		Format: month/date
		Example: 1/1
		"""
		if command := ctx.bot.get_command("random date fact"):
			await ctx.invoke(command, date = date)
		else:
			raise RuntimeError(
				"random date fact command not found "
				"when fact date command invoked"
			)
	
	@random_fact.command(name = "math", with_app_command = False)
	async def random_fact_math(self, ctx, number: int):
		'''Random math fact about a number'''
		# Note: fact math command invokes this command
		url = f"http://numbersapi.com/{number}/math"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.text()
		await ctx.embed_reply(data)
	
	@fact.command(name = "math")
	async def fact_math(self, ctx, number: int):
		"""Random math fact about a number"""
		if command := ctx.bot.get_command("random fact math"):
			await ctx.invoke(command, number = number)
		else:
			raise RuntimeError(
				"random fact math command not found "
				"when fact math command invoked"
			)
	
	@random_fact.command(name = "number", with_app_command = False)
	async def random_fact_number(self, ctx, number: int):
		"""Random fact about a number"""
		if command := ctx.bot.get_command("random number fact"):
			await ctx.invoke(command, number = number)
		else:
			raise RuntimeError(
				"random number fact command not found "
				"when random fact number command invoked"
			)
	
	@fact.command(name = "number")
	async def fact_number(self, ctx, number: int):
		"""Random fact about a number"""
		if command := ctx.bot.get_command("random number fact"):
			await ctx.invoke(command, number = number)
		else:
			raise RuntimeError(
				"random number fact command not found "
				"when fact number command invoked"
			)
	
	@random_fact.command(name = "year", with_app_command = False)
	async def random_fact_year(self, ctx, year: int):
		'''Random fact about a year'''
		# Note: fact year command invokes this command
		url = f"http://numbersapi.com/{year}/year"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.text()
		await ctx.embed_reply(data)
	
	@fact.command(name = "year")
	async def fact_year(self, ctx, year: int):
		"""Random fact about a year"""
		if command := ctx.bot.get_command("random fact year"):
			await ctx.invoke(command, year = year)
		else:
			raise RuntimeError(
				"random fact year command not found "
				"when fact year command invoked"
			)
	
	@random.command(with_app_command = False)
	async def giphy(self, ctx):
		"""Random gif from giphy"""
		if command := ctx.bot.get_command("giphy random"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"giphy random command not found "
				"when random giphy command invoked"
			)
	
	@random.command(name = "idea", with_app_command = False)
	async def random_idea(self, ctx):
		'''Random idea'''
		# Note: idea command invokes this command
		url = "http://itsthisforthat.com/api.php"
		async with ctx.bot.aiohttp_session.get(url, params = "json") as resp:
			data = await resp.json(content_type = "text/javascript")
		await ctx.embed_reply(f"{data['this']} for {data['that']}")
	
	@commands.command()
	async def idea(self, ctx):
		"""Random idea"""
		if command := ctx.bot.get_command("random idea"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random idea command not found when idea command invoked"
			)
	
	@random.command(name = "insult", with_app_command = False)
	async def random_insult(self, ctx):
		'''Random insult'''
		# Note: insult command invokes this command
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
	
	@commands.command()
	async def insult(self, ctx):
		"""Random insult"""
		if command := ctx.bot.get_command("random insult"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random insult command not found when insult command invoked"
			)
	
	@random.group(
		name = "joke", case_insensitive = True, with_app_command = False
	)
	async def random_joke(self, ctx):
		'''Random joke'''
		# Note: joke command invokes this command
		# Sources:
		# https://github.com/KiaFathi/tambalAPI
		# https://www.kaggle.com/abhinavmoudgil95/short-jokes 
		# (https://github.com/amoudgl/short-jokes-dataset)
		if self.jokes:
			await ctx.embed_reply(random.choice(self.jokes))
	
	@commands.group(case_insensitive = True, invoke_without_command = True)
	async def joke(self, ctx):
		"""Random joke"""
		if command := ctx.bot.get_command("random joke"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random joke command not found when joke command invoked"
			)
	
	@random_joke.command(name = "dad", with_app_command = False)
	async def random_joke_dad(
		self, ctx, image: Optional[bool] = False, joke_id: Optional[str] = None
	):
		'''Random dad joke'''
		# Note: joke dad command invokes this command
		# TODO: search, GraphQL?
		if image and joke_id:
			await ctx.embed_reply(
				image_url = f"https://icanhazdadjoke.com/j/{joke_id}.png"
			)
			return
		
		url = "https://icanhazdadjoke.com/"
		headers = {
			"Accept": "application/json", "User-Agent": ctx.bot.user_agent
		}
		
		if joke_id:
			url += "j/" + joke_id
		async with ctx.bot.aiohttp_session.get(url, headers = headers) as resp:
			data = await resp.json()
		
		if data["status"] == 404:
			await ctx.embed_reply(
				f"{ctx.bot.error_emoji} Error: {data['message']}"
			)
			return
		
		if image:
			await ctx.embed_reply(
				image_url = f"https://icanhazdadjoke.com/j/{data['id']}.png"
			)
		else:
			await ctx.embed_reply(
				data["joke"], footer_text = f"Joke ID: {data['id']}"
			)
	
	@joke.command(name = "dad")
	async def joke_dad(
		self, ctx, image: Optional[bool] = False, joke_id: Optional[str] = None
	):
		"""Random dad joke"""
		if command := ctx.bot.get_command("random joke dad"):
			await ctx.invoke(command, image = image, joke_id = joke_id)
		else:
			raise RuntimeError(
				"random joke dad command not found "
				"when joke dad command invoked"
			)
	
	@random.command(
		name = "laititude", aliases = ["lat"], with_app_command = False
	)
	async def random_latitude(self, ctx):
		"""Random latitude"""
		# Note: latitude command invokes this command
		await ctx.embed_reply(str(random.uniform(-90, 90)))
	
	@commands.command(aliases =["lat"])
	async def laititude(self, ctx):
		"""Random laititude"""
		if command := ctx.bot.get_command("random laititude"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random laititude command not found "
				"when laititude command invoked"
			)
	
	@random.command(name = "letter")
	async def random_letter(self, ctx):
		"""Random letter"""
		# Note: letter command invokes this command
		await ctx.embed_reply(random.choice(string.ascii_uppercase))
	
	@commands.command()
	async def letter(self, ctx):
		"""Random letter"""
		if command := ctx.bot.get_command("random letter"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random letter command not found when letter command invoked"
			)
	
	@random.command(name = "location", with_app_command = False)
	async def random_location(self, ctx):
		"""Random location"""
		# Note: location command invokes this command
		await ctx.embed_reply(
			f"{random.uniform(-90, 90)}, {random.uniform(-180, 180)}"
		)
	
	@commands.command()
	async def location(self, ctx):
		"""Random location"""
		if command := ctx.bot.get_command("random location"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random location command not found "
				"when location command invoked"
			)
	
	@random.command(
		name = "longitude", aliases = ["long"], with_app_command = False
	)
	async def random_longitude(self, ctx):
		"""Random longitude"""
		# Note: longitude command invokes this command
		await ctx.embed_reply(str(random.uniform(-180, 180)))
	
	@commands.command(aliases = ["long"])
	async def longitude(self, ctx):
		"""Random longitude"""
		if command := ctx.bot.get_command("random longitude"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random longitude command not found "
				"when longitude command invoked"
			)
	
	@random.command(with_app_command = False)
	async def map(
		self, ctx, zoom: Optional[int] = 13,
		maptype: Optional[Maptype] = "roadmap"
	):
		"""
		See map of random location
		Zoom: 0 - 21+
		Map Types: roadmap, satellite, hybrid, terrain
		"""
		if command := ctx.bot.get_command("map random"):
			await ctx.invoke(command, zoom = zoom, maptype = maptype)
		else:
			raise RuntimeError(
				"map random command not found "
				"when random map command invoked"
			)
	
	@random.group(
		name = "number", aliases = ["rng"],
		case_insensitive = True, with_app_command = False
	)
	async def random_number(self, ctx, number: int = 10):
		'''
		Random number
		Default range is 1 to 10
		'''
		# Note: number command invokes this command
		try:
			await ctx.embed_reply(random.randint(1, number))
		except ValueError:
			await ctx.embed_reply(
				f"{ctx.bot.error_emoji} Error: Input must be >= 1"
			)
	
	@commands.group(
		aliases = ["rng"],
		case_insensitive = True, invoke_without_command = True
	)
	async def number(self, ctx, number: int = 10):
		"""
		Random number
		Default range is 1 to 10
		"""
		if command := ctx.bot.get_command("random number"):
			await ctx.invoke(command, number = number)
		else:
			raise RuntimeError(
				"random number command not found when number command invoked"
			)
	
	@random_number.command(name = "fact", with_app_command = False)
	async def random_number_fact(self, ctx, number: int):
		"""Random fact about a number"""
		# Note: fact number command invokes this command
		# Note: number fact command invokes this command
		# Note: random fact number command invokes this command
		url = f"http://numbersapi.com/{number}"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.text()
		await ctx.embed_reply(data)
	
	@number.command(name = "fact")
	async def number_fact(self, ctx, number: int):
		"""Random fact about a number"""
		if command := ctx.bot.get_command("random number fact"):
			await ctx.invoke(command, number = number)
		else:
			raise RuntimeError(
				"random number fact command not found "
				"when number fact command invoked"
			)
	
	@random.command(aliases = ["image"], with_app_command = False)
	async def photo(self, ctx, *, query: Optional[str] = ""):
		"""Random photo from Unsplash"""
		if command := ctx.bot.get_command("image random"):
			await ctx.invoke(command, query = query)
		else:
			raise RuntimeError(
				"image random command not found "
				"when random photo command invoked"
			)
	
	@random.command(
		name = "question", aliases = ["why"], with_app_command = False
	)
	async def random_question(self, ctx):
		'''Random question'''
		# Note: question command invokes this command
		async with ctx.bot.aiohttp_session.get("http://xkcd.com/why.txt") as resp:
			data = await resp.text()
		questions = data.split('\n')
		await ctx.embed_reply("{}?".format(random.choice(questions).capitalize()))
	
	@commands.command(aliases = ["why"])
	async def question(self, ctx):
		"""Random question"""
		if command := ctx.bot.get_command("random question"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random question command not found "
				"when question command invoked"
			)
	
	@random.command(name = "quote")
	async def random_quote(self, ctx):
		"""Random quote"""
		# Note: quote command invokes this command
		await ctx.defer()
		async with ctx.bot.aiohttp_session.get(
			"http://api.forismatic.com/api/1.0/",
			params = {"method": "getQuote", "format": "json", "lang": "en"}
		) as resp:
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
	async def quote(self, ctx, message: Optional[discord.Message]):
		"""Random quote or quote a message"""
		# TODO: other options to quote by?
		if message:
			await ctx.embed_reply(
				author_name = message.author.display_name,
				author_icon_url = message.author.display_avatar.url,
				description = message.content,
				footer_text = "Sent", timestamp = message.created_at
			)
		elif command := ctx.bot.get_command("random quote"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random quote command not found when quote command invoked"
			)
	
	@random.command(with_app_command = False)
	async def streetview(self, ctx, radius: int = 5_000_000):
		"""
		Generate street view of a random location
		`radius`: sets a radius, specified in meters, in which to search for a panorama, centered on the given latitude and longitude.
		Valid values are non-negative integers.
		"""
		if command := ctx.bot.get_command("streetview random"):
			await ctx.invoke(command, radius = radius)
		else:
			raise RuntimeError(
				"streetview random command not found "
				"when random streetview command invoked"
			)
	
	@random.command()
	async def time(self, ctx):
		"""Random time"""
		# Note: time random command invokes this command
		await ctx.embed_reply(
			f"{random.randint(0, 23):02}:{random.randint(0, 59):02}"
		)
	
	@random.command(with_app_command = False)
	async def uesp(self, ctx):
		"""
		Random UESP page
		[UESP](http://uesp.net/wiki/Main_Page)
		"""
		if command := ctx.bot.get_command("uesp random"):
			await ctx.invoke(command)
		else:
			await ctx.embed_reply(
				title = "Random UESP page",
				title_url = "http://uesp.net/wiki/Special:Random"
			)
	
	@random.command(aliases = ["member"], with_app_command = False)
	async def user(self, ctx):
		'''Random user/member'''
		# Note: user random command invokes this command
		await ctx.embed_reply(random.choice(ctx.guild.members).mention)
	
	@random.command(aliases = ["wiki"])
	async def wikipedia(self, ctx):
		"""Random Wikipedia article"""
		if command := ctx.bot.get_command("wikipedia random"):
			await ctx.invoke(command)
		else:
			await ctx.embed_reply(
				title = "Random Wikipedia article",
				title_url = "https://wikipedia.org/wiki/Special:Random"
			)
	
	@random.command(name = "word")
	async def random_word(self, ctx):
		"""Random word"""
		# Note: word command invokes this command
		await ctx.defer()
		await ctx.embed_reply(
			ctx.bot.wordnik_words_api.getRandomWord().word
		)
	
	@commands.command()
	async def word(self, ctx):
		"""Random word"""
		if command := ctx.bot.get_command("random word"):
			await ctx.invoke(command)
		else:
			raise RuntimeError(
				"random word command not found when word command invoked"
			)
	
	@random.command(with_app_command = False)
	async def xkcd(self, ctx):
		"""Random xkcd comic"""
		# Note: xkcd random command invokes this command
		url = "http://xkcd.com/info.0.json"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		number = random.randint(1, data['num'])
		# TODO: Optimize random comic / page selection?
		paginator = ButtonPaginator(
			ctx, XKCDSource(ctx), initial_page = number
		)
		await paginator.start()
		ctx.bot.views.append(paginator)

