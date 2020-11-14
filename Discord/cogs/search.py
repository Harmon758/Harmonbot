
import discord
from discord.ext import commands

import functools
import inspect
import re
import youtube_dl

from utilities import checks

def setup(bot):
	bot.add_cog(Search(bot))

class Search(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
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
		if "entries" in info: info = info["entries"][0]
		await ctx.reply(info.get("webpage_url"))
	
	async def youtube_error(self, ctx, error):
		if isinstance(error, commands.CommandInvokeError) and isinstance(error.original, youtube_dl.utils.DownloadError):
			await ctx.embed_reply(f":no_entry: Error: {error.original}")
	
	@commands.command()
	async def amazon(self, ctx, *search: str):
		'''Search with Amazon'''
		await ctx.embed_reply(f"[Amazon search for \"{' '.join(search)}\"](https://smile.amazon.com/s/?field-keywords={'+'.join(search)})")
	
	@commands.command()
	async def aol(self, ctx, *search: str):
		'''Search with AOL'''
		await ctx.embed_reply(f"[AOL search for \"{' '.join(search)}\"](https://search.aol.com/aol/search?q={'+'.join(search)})")
	
	@commands.command(name = "ask.com")
	async def ask_com(self, ctx, *search: str):
		'''Search with Ask.com'''
		await ctx.embed_reply(f"[Ask.com search for \"{' '.join(search)}\"](http://www.ask.com/web?q={'+'.join(search)})")
	
	@commands.command()
	async def baidu(self, ctx, *search: str):
		'''Search with Baidu'''
		await ctx.embed_reply(f"[Baidu search for \"{' '.join(search)}\"](http://www.baidu.com/s?wd={'+'.join(search)})")
	
	@commands.command()
	async def bing(self, ctx, *search: str):
		'''Search with Bing'''
		await ctx.embed_reply(f"[Bing search for \"{' '.join(search)}\"](http://www.bing.com/search?q={'+'.join(search)})")
	
	@commands.command()
	async def duckduckgo(self, ctx, *search: str):
		'''Search with DuckDuckGo'''
		await ctx.embed_reply(f"[DuckDuckGo search for \"{' '.join(search)}\"](https://www.duckduckgo.com/?q={'+'.join(search)})")
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	async def google(self, ctx, *, search: str):
		'''Google search'''
		await ctx.embed_reply(f"[Google search for \"{search}\"](https://www.google.com/search?q={search.replace(' ', '+')})")
	
	@commands.command(aliases = ["im_feeling_lucky"])
	async def imfeelinglucky(self, ctx, *search: str):
		'''First Google result of a search'''
		await ctx.embed_reply(f"[First Google result of \"{' '.join(search)}\"](https://www.google.com/search?btnI&q={'+'.join(search)})")
	
	@commands.command(name = "lma.ctfy")
	async def lma_ctfy(self, ctx, *search: str):
		'''Let Me Ask.Com That For You'''
		await ctx.embed_reply(f"[LMA.CTFY: \"{' '.join(search)}\"](http://lmgtfy.com/?s=k&q={'+'.join(search)})")
	
	@commands.command()
	async def lmaoltfy(self, ctx, *search: str):
		'''Let Me AOL That For You'''
		await ctx.embed_reply(f"[LMAOLTFY: \"{' '.join(search)}\"](http://lmgtfy.com/?s=a&q={'+'.join(search)})")
	
	@commands.command()
	async def lmatfy(self, ctx, *search: str):
		'''Let Me Amazon That For You'''
		await ctx.embed_reply(f"[LMATFY: \"{' '.join(search)}\"](http://lmatfy.co/?q={'+'.join(search)})")
	
	@commands.command()
	async def lmbdtfy(self, ctx, *search: str):
		'''Let Me Baidu That For You'''
		await ctx.embed_reply(f"[LMBDTFY: \"{' '.join(search)}\"](https://lmbtfy.cn/?{'+'.join(search)})")
	
	@commands.command()
	async def lmbtfy(self, ctx, *search: str):
		'''Let Me Bing That For You'''
		output = f"[LMBTFY: \"{' '.join(search)}\"](http://lmbtfy.com/?s=b&q={'+'.join(search)})\n"
		output += f"[LMBTFY: \"{' '.join(search)}\"](http://letmebingthatforyou.com/q={'+'.join(search)})"
		await ctx.embed_reply(output)
	
	@commands.command()
	async def lmdtfy(self, ctx, *search: str):
		'''Let Me DuckDuckGo That For You'''
		await ctx.embed_reply(f"[LMDTFY: \"{' '.join(search)}\"](http://lmgtfy.com/?s=d&q={'+'.join(search)})")
	
	@commands.command()
	async def lmgtfy(self, ctx, *search: str):
		'''Let Me Google That For You'''
		await ctx.embed_reply(f"[LMGTFY: \"{' '.join(search)}\"](http://lmgtfy.com/?q={'+'.join(search)})")
	
	@commands.command()
	async def lmytfy(self, ctx, *search: str):
		'''Let Me Yahoo That For You'''
		await ctx.embed_reply(f"[LMYTFY: \"{' '.join(search)}\"](http://lmgtfy.com/?s=y&q={'+'.join(search)})")
	
	@commands.command()
	async def startpage(self, ctx, *search: str):
		'''Search with StartPage'''
		await ctx.embed_reply(f"[StartPage search for \"{' '.join(search)}\"](https://www.startpage.com/do/search?query={'+'.join(search)})")
	
	@commands.group(description = "[UESP](http://uesp.net/wiki/Main_Page)", 
					invoke_without_command = True, case_insensitive = True)
	async def uesp(self, ctx, *, search: str):
		'''Look something up on the Unofficial Elder Scrolls Pages'''
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
	
	@commands.group(aliases = ["wiki"], invoke_without_command = True, case_insensitive = True)
	async def wikipedia(self, ctx, *, search: str):
		'''Look something up on Wikipedia'''
		await self.process_wikipedia(ctx, search)
	
	async def process_wikipedia(self, ctx, search, random = False, redirect = True):
		# TODO: Add User-Agent
		# TODO: use textwrap
		if random:
			async with ctx.bot.aiohttp_session.get("https://en.wikipedia.org/w/api.php", params = {"action": "query", "list": "random", "rnnamespace": 0, "format": "json"}) as resp:
				data = await resp.json()
			search = data["query"]["random"][0]["title"]
		else:
			async with ctx.bot.aiohttp_session.get("https://en.wikipedia.org/w/api.php", params = {"action": "query", "list": "search", "srsearch": search, "srinfo": "suggestion", "srlimit": 1, "format": "json"}) as resp:
				data = await resp.json()
			try:
				search = data["query"].get("searchinfo", {}).get("suggestion") or data["query"]["search"][0]["title"]
			except IndexError:
				await ctx.embed_reply(":no_entry: Page not found")
				return
		async with ctx.bot.aiohttp_session.get("https://en.wikipedia.org/w/api.php", params = {"action": "query", "redirects": "", "prop": "info|extracts|pageimages", "titles": search, "inprop": "url", "exintro": "", "explaintext": "", "pithumbsize": 9000, "pilicense": "any", "format": "json"}) as resp: # exchars?
			data = await resp.json()
		if "pages" not in data["query"]:
			await ctx.embed_reply(":no_entry: Error")
			return
		page_id = list(data["query"]["pages"].keys())[0]
		page = data["query"]["pages"][page_id]
		if "missing" in page:
			await ctx.embed_reply(":no_entry: Page not found")
		elif "invalid" in page:
			await ctx.embed_reply(f":no_entry: Error: {page['invalidreason']}")
		elif redirect and "redirects" in data["query"]:
			await self.process_wikipedia(ctx, data["query"]["redirects"][-1]["to"], redirect = False)
			# TODO: Handle section links/tofragments
		else:
			description = page["extract"] if len(page["extract"]) <= 512 else page["extract"][:512] + "..."
			description = re.sub(r"\s+ \s+", ' ', description)
			thumbnail = data["query"]["pages"][page_id].get("thumbnail")
			image_url = thumbnail["source"].replace(f"{thumbnail['width']}px", "1200px") if thumbnail else None
			await ctx.embed_reply(description, title = page["title"], title_url = page["fullurl"], image_url = image_url) # canonicalurl?
	
	@commands.group(aliases = ["wa", "wolfram_alpha"], invoke_without_command = True, case_insensitive = True)
	async def wolframalpha(self, ctx, *, search: str):
		'''
		Wolfram|Alpha
		http://www.wolframalpha.com/examples/
		'''
		await self.process_wolframalpha(ctx, search)
	
	@wolframalpha.command(name = "location")
	async def wolframalpha_location(self, ctx, location: str, *, search : str):
		'''Input location'''
		await self.process_wolframalpha(ctx, search, location = location)
	
	async def process_wolframalpha(self, ctx, search, location = None):
		# TODO: process asynchronously
		if not location:
			location = ctx.bot.fake_location
		try:
			result = ctx.bot.wolfram_alpha_client.query(search.strip('`'), ip = ctx.bot.fake_ip, location = location)
		except Exception as e:
			if str(e).startswith("Error "):
				return await ctx.embed_reply(f":no_entry: {e}")
			raise
		# TODO: other options?
		if not hasattr(result, "pods") and hasattr(result, "didyoumeans"):
			if result.didyoumeans["@count"] == '1':
				didyoumean = result.didyoumeans["didyoumean"]["#text"]
			else:
				didyoumean = result.didyoumeans["didyoumean"][0]["#text"]
			await ctx.embed_reply(f"Using closest Wolfram|Alpha interpretation: `{didyoumean}`")
			try:
				result = ctx.bot.wolfram_alpha_client.query(didyoumean, ip = ctx.bot.fake_ip, location = location)
			except Exception as e:
				if str(e).startswith("Error "):
					return await ctx.embed_reply(f":no_entry: {e}")
				raise
		if not hasattr(result, "pods"):
			if result.timedout:
				return await ctx.embed_reply("Standard computation time exceeded")
			else:
				return await ctx.embed_reply(":no_entry: No results found")
		if ctx.me.permissions_in(ctx.channel).embed_links:
			for pod_number, pod in enumerate(result.pods):
				for subpod_number, subpod in enumerate(pod.subpods):
					if subpod_number:
						await ctx.embed_send(image_url = next(subpod.img).src)
					elif pod_number:
						await ctx.embed_send(title = pod.title, image_url = next(subpod.img).src)
					else:
						await ctx.embed_reply(title = pod.title, image_url = next(subpod.img).src, footer_text = discord.Embed.Empty)
		else:
			text_output = ""
			for pod in result.pods:
				text_output += f"**{pod.title}**\n"
				for subpod in pod.subpods:
					if subpod.plaintext:
						text_output += ctx.bot.CODE_BLOCK.format(subpod.plaintext)
			await ctx.reply(text_output)
		# TODO: single embed with plaintext version?
		if result.timedout:
			await ctx.embed_reply(f"Some results timed out: {result.timedout.replace(',', ', ')}")
	
	@commands.command()
	async def yahoo(self, ctx, *search: str):
		'''Search with Yahoo'''
		await ctx.embed_reply(f"[Yahoo search for \"{' '.join(search)}\"](https://search.yahoo.com/search?q={'+'.join(search)})")

