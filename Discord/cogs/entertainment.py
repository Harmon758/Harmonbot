
import discord
from discord.ext import commands, menus

import datetime
from typing import Optional, Union

from bs4 import BeautifulSoup

from utilities import checks
from utilities.menu import Menu

def setup(bot):
	bot.add_cog(Entertainment())

class Entertainment(commands.Cog):
	
	def __init__(self):
		self.menus = []
	
	def cog_unload(self):
		for menu in self.menus:
			menu.stop()
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	# TODO: manga
	# TODO: anime menu
	
	@commands.group(aliases = ["anilsit"], invoke_without_command = True, case_insensitive = True)
	async def anime(self, ctx, *, search: str):
		'''Search AniList'''
		url = "https://graphql.anilist.co"
		query = """
		query ($search: String) {
			Media (search: $search, type: ANIME) {
				title { romaji english native }
				format status description
				startDate { year month day }
				endDate { year month day }
				season seasonYear episodes duration
				source (version: 2)
				hashtag
				coverImage { extraLarge }
				bannerImage genres synonyms averageScore meanScore popularity favourites
				tags { name rank isMediaSpoiler }
				relations { edges {
					node {
						title { romaji english native }
						type
						status
					}
					relationType
				} }
				studios { edges {
					node { name siteUrl }
					isMain
				} }
				isAdult
				nextAiringEpisode { airingAt timeUntilAiring episode }
				rankings { rank type year season allTime context }
				siteUrl
			}
		}
		"""
		# Use?:
		# relations
		# nextAiringEpisode
		# rankings
		# Other commands?:
		# airingSchedule
		# characters
		# recommendations
		# reviews
		# staff
		# stats
		# streamingEpisodes
		# trailer
		# trending
		# trends
		data = {"query": query, "variables": {"search": search}}
		async with ctx.bot.aiohttp_session.post(url, json = data) as resp:
			data = await resp.json()
		if not (media := data["data"]["Media"]) and "errors" in data:
			return await ctx.embed_reply(f":no_entry: Error: {data['errors'][0]['message']}")
		# Title
		english_title = media["title"]["english"]
		native_title = media["title"]["native"]
		romaji_title = media["title"]["romaji"]
		title = english_title or native_title
		if native_title != title:
			title += f" ({native_title})"
		if romaji_title != english_title and len(title) + len(romaji_title) < ctx.bot.EMBED_TITLE_CHARACTER_LIMIT:
			title += f" ({romaji_title})"
		# Description
		description = ""
		if media["description"]:
			description = BeautifulSoup(media["description"], "lxml").text
		# Format + Episodes
		fields = [("Format", ' '.join(word if word in ("TV", "OVA", "ONA") else word.capitalize() for word in media["format"].split('_'))), 
					("Episodes", media["episodes"])]
		non_inline_fields = []
		# Episode Duration
		if duration := media["duration"]:
			fields.append(("Episode Duration", f"{duration} minutes"))
		# Status
		fields.append(("Status", ' '.join(word.capitalize() for word in media["status"].split('_'))))
		# Start + End Date
		for date_type in ("start", "end"):
			if year := media[date_type + "Date"]["year"]:
				date = str(year)
				if month := media[date_type + "Date"]["month"]:
					date += f"-{month:0>2}"
					if day := media[date_type + "Date"]["day"]:
						date += f"-{day:0>2}"
				fields.append((date_type.capitalize() + " Date", date))
		# Season
		if media["season"]:  # and media["seasonYear"] ?
			fields.append(("Season", f"{media['season'].capitalize()} {media['seasonYear']}"))
		# Average Score
		if average_score := media["averageScore"]:
			fields.append(("Average Score", f"{average_score}%"))
		# Mean Score
		if mean_score := media["meanScore"]:
			fields.append(("Mean Score", f"{mean_score}%"))
		# Popularity + Favorites
		fields.extend((("Popularity", media["popularity"]), ("Favorites", media["favourites"])))
		# Main Studio + Producers
		main_studio = None
		producers = []
		for studio in media["studios"]["edges"]:
			if studio["isMain"]:
				main_studio = studio["node"]
			else:
				producers.append(studio["node"])
		if main_studio: 
			fields.append(("Studio", f"[{main_studio['name']}]({main_studio['siteUrl']})"))
		if producers:
			fields.append(("Producers", ", ".join(f"[{producer['name']}]({producer['siteUrl']})" for producer in producers), len(producers) <= 2))
		# Source
		if source := media["source"]:
			fields.append(("Source", ' '.join(word.capitalize() for word in source.split('_'))))
		# Hashtag
		if hashtag := media["hashtag"]:
			fields.append(("Hashtag", hashtag))
		# Genres
		if len(media["genres"]) <= 2:
			fields.append(("Genres", ", ".join(media["genres"])))
		else:
			non_inline_fields.append(("Genres", ", ".join(media["genres"]), False))
		# Synonyms
		if synonyms := media["synonyms"]:
			fields.append(("Synonyms", ", ".join(synonyms)))
		# Adult
		fields.append(("Adult", media["isAdult"]))
		# Tags
		tags = []
		for tag in media["tags"]:
			if tag["isMediaSpoiler"]:
				tags.append(f"||{tag['name']}|| ({tag['rank']}%)")
			else:
				tags.append(f"{tag['name']} ({tag['rank']}%)")
		if 0 < len(tags) <= 2:
			fields.append(("Tags", ", ".join(tags)))
		elif tags:
			non_inline_fields.append(("Tags", ", ".join(tags), False))
		await ctx.embed_reply(description, title = title, title_url = media["siteUrl"], 
								thumbnail_url = media["coverImage"]["extraLarge"], 
								fields = fields + non_inline_fields, 
								image_url = media["bannerImage"])
	
	@anime.command(name = "links", aliases = ["link"])
	async def anime_links(self, ctx, *, search: str):
		'''Links for anime'''
		url = "https://graphql.anilist.co"
		query = """
		query ($search: String) {
			Media (search: $search, type: ANIME) {
				title { romaji english native}
				coverImage { extraLarge }
				bannerImage
				externalLinks { url site }
				siteUrl
			}
		}
		"""
		data = {"query": query, "variables": {"search": search}}
		async with ctx.bot.aiohttp_session.post(url, json = data) as resp:
			data = await resp.json()
		if not (media := data["data"]["Media"]) and "errors" in data:
			return await ctx.embed_reply(f":no_entry: Error: {data['errors'][0]['message']}")
		english_title = media["title"]["english"]
		native_title = media["title"]["native"]
		romaji_title = media["title"]["romaji"]
		title = english_title or native_title
		if native_title != title:
			title += f" ({native_title})"
		if romaji_title != english_title and len(title) + len(romaji_title) < ctx.bot.EMBED_TITLE_CHARACTER_LIMIT:
			title += f" ({romaji_title})"
		await ctx.embed_reply('\n'.join(f"[{link['site']}]({link['url']})" for link in media['externalLinks']), 
								title = title, title_url = media["siteUrl"], 
								thumbnail_url = media["coverImage"]["extraLarge"], image_url = media["bannerImage"])
	
	# TODO: Switch name + alias
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
	
	@xkcd.command(
		name = "menu", aliases = ['m', "menus", 'r', "reaction", "reactions"]
	)
	async def xkcd_menu(self, ctx, number: Optional[int]):
		'''xkcd comics menu'''
		menu = XKCDMenu(number)
		self.menus.append(menu)
		await menu.start(ctx, wait = True)
		self.menus.remove(menu)
	
	async def process_xkcd(self, ctx, url):
		async with ctx.bot.aiohttp_session.get(url) as resp:
			if resp.status == 404:
				await ctx.embed_reply(
					f"{ctx.bot.error_emoji} Error: Not found"
				)
				return
			data = await resp.json()
		await ctx.embed_reply(
			title = data["title"],
			title_url = f"http://xkcd.com/{data['num']}", 
			image_url = data["img"],
			footer_text = data["alt"], 
			timestamp = datetime.datetime(
				int(data["year"]), int(data["month"]), int(data["day"])
			)
		)

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
		embed.set_author(name = menu.ctx.author.display_name, icon_url = menu.ctx.author.avatar.url)
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
	
	async def start(self, ctx, wait = True):
		await self.source.prepare(ctx)
		await menus.Menu.start(self, ctx, wait = wait)

