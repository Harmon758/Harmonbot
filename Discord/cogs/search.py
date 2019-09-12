
from discord.ext import commands

import functools
import inspect
import re
import youtube_dl

from modules import utilities
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
		# Add search subcommands as subcommands of corresponding commands
		self.search_subcommands = ((self.youtube, "Audio.audio"),)
		for command, parent_name in self.search_subcommands:
			utilities.add_as_subcommand(self, command, parent_name, "search")
	
	def cog_unload(self):
		for command, parent_name in self.search_subcommands:
			utilities.remove_as_subcommand(self, parent_name, "search")
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def search(self, ctx):
		'''
		Search things
		All search subcommands are also commands
		'''
		await ctx.embed_reply(":grey_question: Search what?")
	
	@search.command(aliases = ["yt"])
	@checks.not_forbidden()
	async def youtube(self, ctx, *, search : str):
		'''Find a Youtube video'''
		ydl = youtube_dl.YoutubeDL({"default_search": "auto", "noplaylist": True, "quiet": True})
		func = functools.partial(ydl.extract_info, search, download = False)
		info = await self.bot.loop.run_in_executor(None, func)
		if "entries" in info: info = info["entries"][0]
		await ctx.reply(info.get("webpage_url"))
	
	@youtube.error
	async def youtube_error(self, error, ctx):
		if isinstance(error, commands.errors.CommandInvokeError) and isinstance(error.original, youtube_dl.utils.DownloadError):
			await ctx.embed_reply(f":no_entry: Error: {error.original}")
	
	@commands.command()
	@checks.not_forbidden()
	async def amazon(self, ctx, *search : str):
		'''Search with Amazon'''
		await ctx.embed_reply(f"[Amazon search for \"{' '.join(search)}\"](https://smile.amazon.com/s/?field-keywords={'+'.join(search)})")
	
	@commands.command()
	@checks.not_forbidden()
	async def aol(self, ctx, *search : str):
		'''Search with AOL'''
		await ctx.embed_reply(f"[AOL search for \"{' '.join(search)}\"](https://search.aol.com/aol/search?q={'+'.join(search)})")
	
	@commands.command(name = "ask.com")
	@checks.not_forbidden()
	async def ask_com(self, ctx, *search : str):
		'''Search with Ask.com'''
		await ctx.embed_reply(f"[Ask.com search for \"{' '.join(search)}\"](http://www.ask.com/web?q={'+'.join(search)})")
	
	@commands.command()
	@checks.not_forbidden()
	async def baidu(self, ctx, *search : str):
		'''Search with Baidu'''
		await ctx.embed_reply(f"[Baidu search for \"{' '.join(search)}\"](http://www.baidu.com/s?wd={'+'.join(search)})")
	
	@commands.command()
	@checks.not_forbidden()
	async def bing(self, ctx, *search : str):
		'''Search with Bing'''
		await ctx.embed_reply(f"[Bing search for \"{' '.join(search)}\"](http://www.bing.com/search?q={'+'.join(search)})")
	
	@commands.command()
	@checks.not_forbidden()
	async def duckduckgo(self, ctx, *search : str):
		'''Search with DuckDuckGo'''
		await ctx.embed_reply(f"[DuckDuckGo search for \"{' '.join(search)}\"](https://www.duckduckgo.com/?q={'+'.join(search)})")
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def google(self, ctx, *, search : str):
		'''Google search'''
		await ctx.embed_reply(f"[Google search for \"{search}\"](https://www.google.com/search?q={search.replace(' ', '+')})")
	
	@commands.command(aliases = ["im_feeling_lucky"])
	@checks.not_forbidden()
	async def imfeelinglucky(self, ctx, *search : str):
		'''First Google result of a search'''
		await ctx.embed_reply(f"[First Google result of \"{' '.join(search)}\"](https://www.google.com/search?btnI&q={'+'.join(search)})")
	
	@commands.command(name = "lma.ctfy")
	@checks.not_forbidden()
	async def lma_ctfy(self, ctx, *search : str):
		'''Let Me Ask.Com That For You'''
		await ctx.embed_reply(f"[LMA.CTFY: \"{' '.join(search)}\"](http://lmgtfy.com/?s=k&q={'+'.join(search)})")
	
	@commands.command()
	@checks.not_forbidden()
	async def lmaoltfy(self, ctx, *search : str):
		'''Let Me AOL That For You'''
		await ctx.embed_reply(f"[LMAOLTFY: \"{' '.join(search)}\"](http://lmgtfy.com/?s=a&q={'+'.join(search)})")
	
	@commands.command()
	@checks.not_forbidden()
	async def lmatfy(self, ctx, *search : str):
		'''Let Me Amazon That For You'''
		await ctx.embed_reply(f"[LMATFY: \"{' '.join(search)}\"](http://lmatfy.co/?q={'+'.join(search)})")
	
	@commands.command()
	@checks.not_forbidden()
	async def lmbdtfy(self, ctx, *search : str):
		'''Let Me Baidu That For You'''
		await ctx.embed_reply(f"[LMBDTFY: \"{' '.join(search)}\"](https://lmbtfy.cn/?{'+'.join(search)})")
	
	@commands.command()
	@checks.not_forbidden()
	async def lmbtfy(self, ctx, *search : str):
		'''Let Me Bing That For You'''
		output = "[LMBTFY: \"{}\"](http://lmbtfy.com/?s=b&q={})\n".format(' '.join(search), '+'.join(search))
		output += "[LMBTFY: \"{}\"](http://letmebingthatforyou.com/q={})".format(' '.join(search), '+'.join(search))
		await ctx.embed_reply(output)
	
	@commands.command()
	@checks.not_forbidden()
	async def lmdtfy(self, ctx, *search : str):
		'''Let Me DuckDuckGo That For You'''
		await ctx.embed_reply("[LMDTFY: \"{}\"](http://lmgtfy.com/?s=d&q={})".format(' '.join(search), '+'.join(search)))
	
	@commands.command()
	@checks.not_forbidden()
	async def lmgtfy(self, ctx, *search : str):
		'''Let Me Google That For You'''
		await ctx.embed_reply("[LMGTFY: \"{}\"](http://lmgtfy.com/?q={})".format(' '.join(search), '+'.join(search)))
	
	@commands.command()
	@checks.not_forbidden()
	async def lmytfy(self, ctx, *search : str):
		'''Let Me Yahoo That For You'''
		await ctx.embed_reply("[LMYTFY: \"{}\"](http://lmgtfy.com/?s=y&q={})".format(' '.join(search), '+'.join(search)))
	
	@commands.command()
	@checks.not_forbidden()
	async def startpage(self, ctx, *search : str):
		'''Search with StartPage'''
		await ctx.embed_reply("[StartPage search for \"{}\"](https://www.startpage.com/do/search?query={})".format(' '.join(search), '+'.join(search)))
	
	@commands.group(description = "[UESP](http://uesp.net/wiki/Main_Page)", 
					invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def uesp(self, ctx, *, search : str):
		'''Look something up on the Unofficial Elder Scrolls Pages'''
		await self.process_uesp(ctx, search)
	
	async def process_uesp(self, ctx, search, random = False, redirect = True):
		# TODO: Add User-Agent
		if random:
			async with ctx.bot.aiohttp_session.get("http://en.uesp.net/w/api.php", params = {"action": "query", "list": "random", "rnnamespace": "0|" + '|'.join(str(i) for i in range(100, 152)) + "|200|201", "format": "json"}) as resp:
				data = await resp.json()
			search = data["query"]["random"][0]["title"]
		else:
			async with ctx.bot.aiohttp_session.get("http://en.uesp.net/w/api.php", params = {"action": "query", "list": "search", "srsearch": search, "srinfo": "suggestion", "srlimit": 1, "format": "json"}) as resp:
				data = await resp.json()
			try:
				search = data["query"].get("searchinfo", {}).get("suggestion") or data["query"]["search"][0]["title"]
			except IndexError:
				await ctx.embed_reply(":no_entry: Page not found")
				return
		async with ctx.bot.aiohttp_session.get("http://en.uesp.net/w/api.php", params = {"action": "query", "redirects": "", "prop": "info|revisions|images", "titles": search, "inprop": "url", "rvprop": "content", "format": "json"}) as resp:
			data = await resp.json()
		if "pages" not in data["query"]:
			await ctx.embed_reply(":no_entry: Error")
			return
		page_id = list(data["query"]["pages"].keys())[0]
		page = data["query"]["pages"][page_id]
		if "missing" in page:
			await ctx.embed_reply(":no_entry: Page not found")
		elif "invalid" in page:
			await ctx.embed_reply(":no_entry: Error: {}".format(page["invalidreason"]))
		elif redirect and "redirects" in data["query"]:
			await self.process_uesp(ctx, data["query"]["redirects"][-1]["to"], redirect = False)
			# TODO: Handle section links/tofragments
		else:
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
			description = re.sub(r"\[\[(.+?)\|(.+?)\]\]|\[(.+?)[ ](.+?)\]", lambda match: "[{}](http://en.uesp.net/wiki/{})".format(match.group(2), match.group(1).replace(' ', '_')) if match.group(1) else "[{}]({})".format(match.group(4), match.group(3)), description)
			description = description.replace("'''", "**").replace("''", "*")
			description = re.sub("\n+", '\n', description)
			thumbnail = data["query"]["pages"][page_id].get("thumbnail")
			image_url = thumbnail["source"].replace("{}px".format(thumbnail["width"]), "1200px") if thumbnail else None
			await ctx.embed_reply(description, title = page["title"], title_url = page["fullurl"], image_url = image_url) # canonicalurl?
	
	@commands.group(aliases = ["wiki"], invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def wikipedia(self, ctx, *, search : str):
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
			await ctx.embed_reply(":no_entry: Error: {}".format(page["invalidreason"]))
		elif redirect and "redirects" in data["query"]:
			await self.process_wikipedia(ctx, data["query"]["redirects"][-1]["to"], redirect = False)
			# TODO: Handle section links/tofragments
		else:
			description = page["extract"] if len(page["extract"]) <= 512 else page["extract"][:512] + "..."
			description = re.sub(r"\s+ \s+", ' ', description)
			thumbnail = data["query"]["pages"][page_id].get("thumbnail")
			image_url = thumbnail["source"].replace("{}px".format(thumbnail["width"]), "1200px") if thumbnail else None
			await ctx.embed_reply(description, title = page["title"], title_url = page["fullurl"], image_url = image_url) # canonicalurl?
	
	@commands.group(aliases = ["wa", "wolfram_alpha"], invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def wolframalpha(self, ctx, *, search : str):
		'''
		Wolfram|Alpha
		http://www.wolframalpha.com/examples/
		'''
		await self.process_wolframalpha(ctx, search)
	
	@wolframalpha.command(name = "location")
	@checks.not_forbidden()
	async def wolframalpha_location(self, ctx, location: str, *, search : str):
		'''Input location'''
		await self.process_wolframalpha(ctx, search, location = location)
	
	async def process_wolframalpha(self, ctx, search, location = None):
		# TODO: process asynchronously
		if not location: location = self.bot.fake_location
		search = search.strip('`')
		result = self.bot.wolfram_alpha_client.query(search, ip = self.bot.fake_ip, location = location)  # options
		if not hasattr(result, "pods") and hasattr(result, "didyoumeans"):
			if result.didyoumeans["@count"] == '1':
				didyoumean = result.didyoumeans["didyoumean"]["#text"]
			else:
				didyoumean = result.didyoumeans["didyoumean"][0]["#text"]
			await ctx.embed_reply("Using closest Wolfram|Alpha interpretation: `{}`".format(didyoumean))
			result = self.bot.wolfram_alpha_client.query(didyoumean, ip = self.bot.fake_ip, location = location)
		if hasattr(result, "pods"):
			for pod in result.pods:
				images, text_output = [], []
				# TODO: use text output by default?
				for subpod in pod.subpods:
					image = next(subpod.img)
					images.append(image.src)
					if subpod.plaintext and subpod.plaintext.replace('\n', ' ') not in (image.title, image.alt, image.title.strip(' '), image.alt.strip(' ')) or not ctx.me.permissions_in(ctx.channel).embed_links:
						print("Wolfram Alpha:\n")
						print(image.title)
						print(image.alt)
						print(subpod.plaintext.replace('\n', ' '))
						text_output.append("\n{}".format(subpod.plaintext))
				if not text_output:
					await ctx.embed_reply(title = pod.title, image_url = images[0])
					for image in images[1:]:
						await ctx.embed_send(image_url = image)
				else:
					for i, link in enumerate(images):
						images[i] = await self._shorturl(link)
					output = ("**{}** ({})".format(pod.title, ', '.join(images)))
					output += "".join(text_output)
					await ctx.reply(output)
			if result.timedout:
				await ctx.embed_reply("Some results timed out: {}".format(result.timedout.replace(',', ", ")))
		elif result.timedout:
			await ctx.embed_reply("Standard computation time exceeded")
		else:
			await ctx.embed_reply(":no_entry: No results found")
		# await ctx.reply(next(result.results).text)
	
	@commands.command()
	@checks.not_forbidden()
	async def yahoo(self, ctx, *search : str):
		'''Search with Yahoo'''
		await ctx.embed_reply("[Yahoo search for \"{}\"](https://search.yahoo.com/search?q={})".format(' '.join(search), '+'.join(search)))

