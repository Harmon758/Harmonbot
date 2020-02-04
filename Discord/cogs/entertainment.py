
import discord
from discord.ext import commands, menus

import datetime
from typing import Optional, Union

from utilities import checks
from utilities.menu import Menu

def setup(bot):
	bot.add_cog(Entertainment())

class Entertainment(commands.Cog):
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.command(aliases = ["movie"])
	async def imdb(self, ctx, *, search: str):
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
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	async def xkcd(self, ctx, *, query: Optional[Union[int, str]]):
		'''See xkcd comics'''
		if isinstance(query, str):
			# Query by title
			url = "https://www.explainxkcd.com/wiki/api.php"
			params = {"action": "query", "list": "search", "format": "json", 
						"srsearch": query, "srwhat": "title", "srlimit": "max"}
			async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
				if results := (await resp.json())["query"]["search"]:
					number = results[0]['title'].split(':')[0]
					url = f"http://xkcd.com/{number}/info.0.json"
					return await self.process_xkcd(ctx, url)
			# Query by text
			params["srwhat"] = "text"
			async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
				results = (await resp.json())["query"]["search"]
			# Query by exact text in quotation marks
			params["srsearch"] = f'"{query}"'
			async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
				exact_results = (await resp.json())["query"]["search"]
			# Look for query in target sections
			sections = {}
			query = query.lower()
			words = query.split()
			for target_section in ("Transcript", "Explanation", "Discussion"):
				for result in exact_results + results:
					# Parse page sections
					if (page_id := result["pageid"]) not in sections:
						params = {"action": "parse", "pageid": page_id, 
									"prop": "sections", "format": "json"}
						async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
							sections[page_id] = (await resp.json())["parse"]["sections"]
					# Find target section
					section = discord.utils.find(
						lambda section:
							target_section in (section["line"], section["anchor"]), 
						sections[page_id]
					)
					if section and section["index"]:
						# Parse section text
						params = {"action": "parse", "pageid": page_id, "format": "json", 
									"prop": "parsetree", "section": section["index"]}
						async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
							section_text = (await resp.json())["parse"]["parsetree"]['*'].lower()
						# Check for query in section text
						if query in section_text or all(word in section_text for word in words):
							number = result['title'].split(':')[0]
							url = f"http://xkcd.com/{number}/info.0.json"
							return await self.process_xkcd(ctx, url)
			# Exhausted query results
			await ctx.embed_reply(":no_entry: Error: Not found")
		elif query:
			await self.process_xkcd(ctx, f"http://xkcd.com/{query}/info.0.json")
		else:
			await self.process_xkcd(ctx, "http://xkcd.com/info.0.json")
	
	@xkcd.command(name = "menu", aliases = ['m', "menus", 'r', "reaction", "reactions"])
	async def xkcd_menu(self, ctx, number: Optional[int]):
		'''xkcd comics menu'''
		await XKCDMenu(number).start(ctx)
	
	async def process_xkcd(self, ctx, url):
		async with ctx.bot.aiohttp_session.get(url) as resp:
			if resp.status == 404:
				return await ctx.embed_reply(":no_entry: Error: Not found")
			data = await resp.json()
		await ctx.embed_reply(title = data["title"], title_url = f"http://xkcd.com/{data['num']}", 
								image_url = data["img"], footer_text = data["alt"], 
								timestamp = datetime.datetime(int(data["year"]), int(data["month"]), int(data["day"])))

class XKCDSource(menus.PageSource):
	
	async def prepare(self, ctx):
		self.bot = ctx.bot
		url = "http://xkcd.com/info.0.json"
		async with ctx.bot.aiohttp_session.get(url) as resp:
			data = await resp.json()
		self.max_pages = data["num"]
	
	def is_paginating(self):
		return True
	
	def get_max_pages(self):
		return self.max_pages
	
	async def get_page(self, page_number):
		url = f"http://xkcd.com/{page_number + 1}/info.0.json"
		async with self.bot.aiohttp_session.get(url) as resp:
			return await resp.json()
	
	async def format_page(self, menu, page):
		embed = discord.Embed(title = page["title"], url = f"http://xkcd.com/{page['num']}", color = menu.bot.bot_color)
		embed.set_author(name = menu.ctx.author.display_name, icon_url = menu.ctx.author.avatar_url)
		embed.set_image(url = page["img"])
		embed.set_footer(text = page["alt"])
		embed.timestamp = datetime.datetime(int(page["year"]), int(page["month"]), int(page["day"]))
		return embed

class XKCDMenu(Menu, menus.MenuPages):
	
	def __init__(self, initial_number = None):
		self.initial_number = initial_number
		super().__init__(XKCDSource(), timeout = None, clear_reactions_after = True, check_embeds = True)
	
	async def send_initial_message(self, ctx, channel):
		if self.initial_number is None or self.initial_number >= self.source.max_pages:
			self.current_page = self.source.max_pages - 1
		else:
			self.current_page = max(0, self.initial_number - 1)
		page = await self.source.get_page(self.current_page)
		embed = await self.source.format_page(self, page)
		message = await channel.send(embed = embed)
		await ctx.bot.attempt_delete_message(ctx.message)
		return message
	
	async def start(self, ctx):
		await self.source.prepare(ctx)
		await menus.Menu.start(self, ctx)

