
import discord
from discord import app_commands
from discord.ext import commands

import functools
import inspect
import re
from typing import Optional

from bs4 import BeautifulSoup
import youtube_dl

from utilities import checks
from utilities.menu_sources import WolframAlphaSource
from utilities.paginators import ButtonPaginator

async def setup(bot):
	await bot.add_cog(Search(bot))

class Search(commands.GroupCog, group_name = "search"):
	"""Search"""
	
	def __init__(self, bot):
		self.bot = bot
		super().__init__()
		# Add commands as search subcommands
		for name, command in inspect.getmembers(self):
			if isinstance(command, commands.Command) and command.parent is None and name != "search":
				self.bot.add_command(command)
				self.search.add_command(command)
		# Add search youtube / youtube (audio) search subcommands
		command = commands.Command(self.youtube, aliases = ["yt"], checks = [checks.not_forbidden().predicate])
		command.error(self.youtube_error)
		self.search.add_command(command)
		if (cog := self.bot.get_cog("Audio")) and (parent := getattr(cog, "audio")):
			command = commands.Command(self.youtube, name = "search", checks = [checks.not_forbidden().predicate])
			command.error(self.youtube_error)
			parent.add_command(command)
	
	def cog_unload(self):
		if (cog := self.bot.get_cog("Audio")) and (parent := getattr(cog, "audio")):
			parent.remove_command("search")
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	async def search(self, ctx):
		'''
		Search things
		All search subcommands are also commands
		'''
		await ctx.embed_reply(":grey_question: Search what?")
	
	async def youtube(self, ctx, *, search: str):
		'''Find a Youtube video'''
		ydl = youtube_dl.YoutubeDL({"default_search": "auto", "noplaylist": True, "quiet": True})
		func = functools.partial(ydl.extract_info, search, download = False)
		info = await self.bot.loop.run_in_executor(None, func)
		if not info.get("entries"):
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Video not found")
		await ctx.message.reply(info["entries"][0].get("webpage_url"))
	
	async def youtube_error(self, ctx, error):
		if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, youtube_dl.utils.DownloadError):
			await ctx.embed_reply(f":no_entry: Error: {error.original}")
	
	@commands.command()
	async def amazon(self, ctx, *search: str):
		"""Search with Amazon"""
		await ctx.embed_reply(
			f"[Amazon search for \"{' '.join(search)}\"]"
			f"(https://smile.amazon.com/s/?field-keywords={'+'.join(search)})"
		)
	
	@commands.command()
	async def aol(self, ctx, *search: str):
		"""Search with AOL"""
		await ctx.embed_reply(
			f"[AOL search for \"{' '.join(search)}\"]"
			f"(https://search.aol.com/aol/search?q={'+'.join(search)})"
		)
	
	@commands.command(name = "ask.com")
	async def ask_com(self, ctx, *search: str):
		"""Search with Ask.com"""
		await ctx.embed_reply(
			f"[Ask.com search for \"{' '.join(search)}\"]"
			f"(http://www.ask.com/web?q={'+'.join(search)})"
		)
	
	@commands.command()
	async def baidu(self, ctx, *search: str):
		"""Search with Baidu"""
		await ctx.embed_reply(
			f"[Baidu search for \"{' '.join(search)}\"]"
			f"(http://www.baidu.com/s?wd={'+'.join(search)})"
		)
	
	@commands.command()
	async def bing(self, ctx, *search: str):
		"""Search with Bing"""
		await ctx.embed_reply(
			f"[Bing search for \"{' '.join(search)}\"]"
			f"(http://www.bing.com/search?q={'+'.join(search)})"
		)
	
	@commands.command()
	async def duckduckgo(self, ctx, *search: str):
		"""Search with DuckDuckGo"""
		await ctx.embed_reply(
			f"[DuckDuckGo search for \"{' '.join(search)}\"]"
			f"(https://www.duckduckgo.com/?q={'+'.join(search)})"
		)
	
	@commands.group(case_insensitive = True, invoke_without_command = True)
	async def google(self, ctx, *, search: str):
		"""Google search"""
		await ctx.embed_reply(
			f"[Google search for \"{search}\"]"
			f"(https://www.google.com/search?q={search.replace(' ', '+')})"
		)
	
	@commands.command(aliases = ["im_feeling_lucky"])
	async def imfeelinglucky(self, ctx, *search: str):
		"""First Google result of a search"""
		await ctx.embed_reply(
			f"[First Google result of \"{' '.join(search)}\"]"
			f"(https://www.google.com/search?btnI&q={'+'.join(search)})"
		)
	
	@commands.command(name = "lma.ctfy")
	async def lma_ctfy(self, ctx, *search: str):
		"""Let Me Ask.Com That For You"""
		await ctx.embed_reply(
			f"[LMA.CTFY: \"{' '.join(search)}\"]"
			f"(http://lmgtfy.com/?s=k&q={'+'.join(search)})"
		)
	
	@commands.command()
	async def lmaoltfy(self, ctx, *search: str):
		"""Let Me AOL That For You"""
		await ctx.embed_reply(
			f"[LMAOLTFY: \"{' '.join(search)}\"]"
			f"(http://lmgtfy.com/?s=a&q={'+'.join(search)})"
		)
	
	@commands.command()
	async def lmatfy(self, ctx, *search: str):
		"""Let Me Amazon That For You"""
		await ctx.embed_reply(
			f"[LMATFY: \"{' '.join(search)}\"]"
			f"(http://lmatfy.co/?q={'+'.join(search)})"
		)
	
	@commands.command()
	async def lmbdtfy(self, ctx, *search: str):
		"""Let Me Baidu That For You"""
		await ctx.embed_reply(
			f"[LMBDTFY: \"{' '.join(search)}\"]"
			f"(https://lmbtfy.cn/?{'+'.join(search)})"
		)
	
	@commands.command()
	async def lmbtfy(self, ctx, *search: str):
		"""Let Me Bing That For You"""
		output = f"[LMBTFY: \"{' '.join(search)}\"](http://lmbtfy.com/?s=b&q={'+'.join(search)})\n"
		output += f"[LMBTFY: \"{' '.join(search)}\"](http://letmebingthatforyou.com/q={'+'.join(search)})"
		await ctx.embed_reply(output)
	
	@commands.command()
	async def lmdtfy(self, ctx, *search: str):
		"""Let Me DuckDuckGo That For You"""
		await ctx.embed_reply(
			f"[LMDTFY: \"{' '.join(search)}\"]"
			f"(http://lmgtfy.com/?s=d&q={'+'.join(search)})"
		)
	
	@commands.command()
	async def lmgtfy(self, ctx, *search: str):
		"""Let Me Google That For You"""
		await ctx.embed_reply(
			f"[LMGTFY: \"{' '.join(search)}\"]"
			f"(http://lmgtfy.com/?q={'+'.join(search)})"
		)
	
	@commands.command()
	async def lmytfy(self, ctx, *search: str):
		"""Let Me Yahoo That For You"""
		await ctx.embed_reply(
			f"[LMYTFY: \"{' '.join(search)}\"]"
			f"(http://lmgtfy.com/?s=y&q={'+'.join(search)})"
		)
	
	@commands.command()
	async def startpage(self, ctx, *search: str):
		"""Search with StartPage"""
		await ctx.embed_reply(
			f"[StartPage search for \"{' '.join(search)}\"]"
			f"(https://www.startpage.com/do/search?query={'+'.join(search)})"
		)
	
	@commands.group(description = "[UESP](http://uesp.net/wiki/Main_Page)", 
					invoke_without_command = True, case_insensitive = True)
	async def uesp(self, ctx, *, search: str):
		"""Look something up on the Unofficial Elder Scrolls Pages"""
		await self.process_uesp(ctx, search)
	
	async def process_uesp(self, ctx, search, random = False, redirect = True):
		# TODO: Add User-Agent
		url = "https://en.uesp.net/w/api.php"
		if random:
			params = {"action": "query", "list": "random", 
						"rnnamespace": f"0|{'|'.join(str(i) for i in range(100, 152))}|200|201", 
						"format": "json"}
			async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			search = data["query"]["random"][0]["title"]
		else:
			params = {"action": "query", "list": "search", 
						"srsearch": search, "srinfo": "suggestion", "srlimit": 1, 
						"format": "json"}
			async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json()
			try:
				search = data["query"].get("searchinfo", {}).get("suggestion") or data["query"]["search"][0]["title"]
			except IndexError:
				return await ctx.embed_reply(":no_entry: Page not found")
		params = {"action": "query", "redirects": "", "prop": "info|revisions|images", 
					"titles": search, "inprop": "url", "rvprop": "content", "format": "json"}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if "pages" not in data["query"]:
			return await ctx.embed_reply(":no_entry: Error")
		page_id = list(data["query"]["pages"].keys())[0]
		page = data["query"]["pages"][page_id]
		if "missing" in page:
			return await ctx.embed_reply(":no_entry: Page not found")
		if "invalid" in page:
			return await ctx.embed_reply(f":no_entry: Error: {page['invalidreason']}")
		if redirect and "redirects" in data["query"]:
			return await self.process_uesp(ctx, data["query"]["redirects"][-1]["to"], redirect = False)
			# TODO: Handle section links/tofragments
		description = page["revisions"][0]['*']
		description = re.sub(r"\s+ \s+", ' ', description)
		while re.findall("{{[^{]+?}}", description):
			description = re.sub("{{[^{]+?}}", "", description)
		while re.findall("{[^{]*?}", description):
			description = re.sub("{[^{]*?}", "", description)
		description = re.sub("<.+?>", "", description, flags = re.DOTALL)
		description = re.sub("__.+?__", "", description)
		description = description.strip()
		description = '\n'.join(line.lstrip(':') for line in description.split('\n'))
		while len(description) > 1024:
			description = '\n'.join(description.split('\n')[:-1])
		description = description.split("==")[0]
		## description = description if len(description) <= 1024 else description[:1024] + "..."
		description = re.sub(r"\[\[Category:.+?\]\]", "", description)
		description = re.sub(
			r"\[\[(.+?)\|(.+?)\]\]|\[(.+?)[ ](.+?)\]", 
			lambda match: 
				f"[{match.group(2)}](https://en.uesp.net/wiki/{match.group(1).replace(' ', '_')})"
				if match.group(1) else f"[{match.group(4)}]({match.group(3)})", 
			description
		)
		description = description.replace("'''", "**").replace("''", "*")
		description = re.sub("\n+", '\n', description)
		thumbnail = data["query"]["pages"][page_id].get("thumbnail")
		image_url = thumbnail["source"].replace(f"{thumbnail['width']}px", "1200px") if thumbnail else None
		await ctx.embed_reply(description, title = page["title"], title_url = page["fullurl"], image_url = image_url)  # canonicalurl?
	
	@commands.group(
		aliases = ["wiki"],
		case_insensitive = True, invoke_without_command = True
	)
	async def wikipedia(self, ctx, *, query: str):
		"""Search for an article on Wikipedia"""
		await self.process_wiki(
			ctx, "https://en.wikipedia.org/w/api.php", query
		)
	
	@app_commands.command(name = "wikipedia")
	async def slash_wikipedia(self, interaction, *, query: str):
		"""
		Search for an article on Wikipedia
		
		Parameters
		----------
		query
			Query to search for
		"""
		ctx = await interaction.client.get_context(interaction)
		await self.wikipedia(ctx, query = query)
	
	@commands.group(
		aliases = ["wikia", "wikicities"],
		case_insensitive = True, invoke_without_command = True
	)
	async def fandom(self, ctx):
		"""Search for an article on a Fandom wiki"""
		await ctx.send_help(ctx.command)
	
	@fandom.command(aliases = ["lord_of_the_rings"])
	async def lotr(self, ctx, *, query: str):
		"""Search for an article on The Lord of The Rings Wiki"""
		await self.process_wiki(ctx, "https://lotr.fandom.com/api.php", query)
	
	@commands.command()
	async def tolkien(self, ctx, *, query: str):
		"""Search for an article on Tolkien Gateway"""
		await self.process_wiki(
			ctx, "https://tolkiengateway.net/w/api.php", query
		)
	
	async def process_wiki(
		self, ctx, url, search, random = False, redirect = True
	):
		# TODO: Add User-Agent
		# TODO: Use textwrap
		if random:
			async with ctx.bot.aiohttp_session.get(
				url, params = {
					"action": "query", "list": "random", "rnnamespace": 0,
					"format": "json"
				}
			) as resp:
				data = await resp.json()
			
			search = data["query"]["random"][0]["title"]
		else:
			async with ctx.bot.aiohttp_session.get(
				url, params = {
					"action": "query", "list": "search", "srsearch": search,
					"srinfo": "suggestion", "srlimit": 1, "format": "json"
				}
			) as resp:
				data = await resp.json()
			
			if search := data["query"]["search"]:
				search = search[0]["title"]
			elif not (
				search := data["query"].get("searchinfo", {}).get("suggestion")
			):
				await ctx.embed_reply(f"{ctx.bot.error_emoji} Page not found")
				return
		
		async with ctx.bot.aiohttp_session.get(
			url, params = {
				"action": "query", "redirects": "",
				"prop": "info|extracts|pageimages", "titles": search,
				"inprop": "url", "exintro": "", "explaintext": "",
				"pithumbsize": 9000, "pilicense": "any", "format": "json"
			}  # TODO: Use exchars?
		) as resp:
			data = await resp.json()
		
		if "pages" not in data["query"]:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error")
			return
		
		page_id = list(data["query"]["pages"].keys())[0]
		page = data["query"]["pages"][page_id]
		
		if "missing" in page:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Page not found")
		elif "invalid" in page:
			await ctx.embed_reply(
				f"{ctx.bot.error_emoji} Error: {page['invalidreason']}"
			)
		elif redirect and "redirects" in data["query"]:
			await self.process_wiki(
				ctx, url, data["query"]["redirects"][-1]["to"],
				redirect = False
			)
			# TODO: Handle section links/tofragments
		else:
			thumbnail = data["query"]["pages"][page_id].get("thumbnail")
			
			if "extract" not in page:
				async with ctx.bot.aiohttp_session.get(
					url, params = {
						"action": "parse", "page": search, "prop": "text",
						"format": "json"
					}
				) as resp:
					data = await resp.json()
				
				p = BeautifulSoup(
					data["parse"]["text"]['*'], "lxml"
				).body.div.find_all('p', recursive = False)
				
				first_p = p[0]
				if first_p.aside:
					first_p.aside.clear()
				description = first_p.get_text()
				
				if len(p) > 1:
					second_p = p[1]
					description += '\n' + second_p.get_text()
				
				description = re.sub(
					r"\n\s*\n", "\n\n",
					description if len(description) <= 512
					else description[:512] + "..."
				)
			else:
				description = re.sub(
					r"\s+ \s+", ' ',
					page["extract"] if len(page["extract"]) <= 512
					else page["extract"][:512] + "..."
				)
			
			await ctx.embed_reply(
				title = page["title"],
				title_url = page["fullurl"],  # TODO: Use canonicalurl?
				description = description,
				image_url = (
					thumbnail["source"].replace(
						f"{thumbnail['width']}px", "1200px"
					) if thumbnail else None
				)
			)
	
	@commands.group(
		aliases = ["wa", "wolfram_alpha"],
		case_insensitive = True, invoke_without_command = True
	)
	async def wolframalpha(self, ctx, *, search: str):
		"""
		Wolfram|Alpha
		http://www.wolframalpha.com/examples/
		"""
		await self.process_wolframalpha(ctx, search)
	
	@wolframalpha.command(name = "location")
	async def wolframalpha_location(self, ctx, location: str, *, search: str):
		'''Input location'''
		await self.process_wolframalpha(ctx, search, location = location)
	
	@app_commands.command(name = "wolframalpha")
	async def slash_wolframalpha(
		self, interaction, location: Optional[str], *, query: str
	):
		"""
		Query Wolfram|Alpha
		
		Parameters
		----------
		query
			Search query
		location
			Location to associate with query
		"""
		await interaction.response.defer()
		ctx = await interaction.client.get_context(interaction)
		# TODO: process asynchronously
		location = location or ctx.bot.fake_location
		try:
			result = ctx.bot.wolfram_alpha_client.query(
				query.strip('`'), ip = ctx.bot.fake_ip, location = location
			)
		except Exception as e:
			if str(e).startswith("Error "):
				await ctx.embed_reply(f"{ctx.bot.error_emoji} {e}")
				return
			raise
		# TODO: other options?
		didyoumean = None
		if not hasattr(result, "pod") and hasattr(result, "didyoumeans"):
			if result.didyoumeans["@count"] == '1':
				didyoumean = result.didyoumeans["didyoumean"]["#text"]
			else:
				didyoumean = result.didyoumeans["didyoumean"][0]["#text"]
			try:
				result = ctx.bot.wolfram_alpha_client.query(
					didyoumean, ip = ctx.bot.fake_ip, location = location
				)
			except Exception as e:
				if str(e).startswith("Error "):
					await ctx.embed_reply(
						"Using closest Wolfram|Alpha interpretation: "
						f"`{didyoumean}`\n"
						f"{ctx.bot.error_emoji} {e}"
					)
					return
				raise
		if hasattr(result, "pod"):
			paginator = ButtonPaginator(
				interaction,
				WolframAlphaSource(
					result.pods,
					didyoumean = didyoumean,
					timedout = result.timedout
				)
			)
			await paginator.start()
			interaction.client.views.append(paginator)
		elif result.timedout:
			await ctx.embed_reply("Standard computation time exceeded")
		else:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} No results found")
	
	async def process_wolframalpha(self, ctx, search, location = None):
		# TODO: process asynchronously
		if not location:
			location = ctx.bot.fake_location
		try:
			result = ctx.bot.wolfram_alpha_client.query(search.strip('`'), ip = ctx.bot.fake_ip, location = location)
		except Exception as e:
			if str(e).startswith("Error "):
				return await ctx.embed_reply(f"{ctx.bot.error_emoji} {e}")
			raise
		# TODO: other options?
		if not hasattr(result, "pod") and hasattr(result, "didyoumeans"):
			if result.didyoumeans["@count"] == '1':
				didyoumean = result.didyoumeans["didyoumean"]["#text"]
			else:
				didyoumean = result.didyoumeans["didyoumean"][0]["#text"]
			await ctx.embed_reply(f"Using closest Wolfram|Alpha interpretation: `{didyoumean}`")
			try:
				result = ctx.bot.wolfram_alpha_client.query(didyoumean, ip = ctx.bot.fake_ip, location = location)
			except Exception as e:
				if str(e).startswith("Error "):
					return await ctx.embed_reply(f"{ctx.bot.error_emoji} {e}")
				raise
		if not hasattr(result, "pod"):
			if result.timedout:
				return await ctx.embed_reply("Standard computation time exceeded")
			else:
				return await ctx.embed_reply(f"{ctx.bot.error_emoji} No results found")
		if ctx.channel.permissions_for(ctx.me).embed_links:
			embeds = []
			for pod_number, pod in enumerate(result.pods):
				for subpod_number, subpod in enumerate(pod.subpods):
					if subpod_number:
						embed = discord.Embed(color = ctx.bot.bot_color)
						embed.set_image(url = subpod.img.src)
						embeds.append(embed)
					elif pod_number:
						embed = discord.Embed(
							title = pod.title, color = ctx.bot.bot_color
						)
						embed.set_image(url = subpod.img.src)
						embeds.append(embed)
					else:
						message = await ctx.embed_reply(title = pod.title, image_url = subpod.img.src, footer_text = None)
			await message.edit(embeds = message.embeds + embeds[:9])
			for index in range(9, len(embeds), 10):
				await ctx.send(embeds = embeds[index:index + 10])
		else:
			text_output = ""
			for pod in result.pods:
				text_output += f"**{pod.title}**\n"
				for subpod in pod.subpods:
					if subpod.plaintext:
						text_output += ctx.bot.CODE_BLOCK.format(subpod.plaintext)
			await ctx.reply(text_output)
			# TODO: Handle message too long
		# TODO: single embed with plaintext version?
		if result.timedout:
			await ctx.embed_reply(f"Some results timed out: {result.timedout.replace(',', ', ')}")
	
	@commands.command()
	async def yahoo(self, ctx, *search: str):
		"""Search with Yahoo"""
		await ctx.embed_reply(
			f"[Yahoo search for \"{' '.join(search)}\"]"
			f"(https://search.yahoo.com/search?q={'+'.join(search)})"
		)

