
import discord
from discord.ext import commands

from utilities import checks
import clients

def setup(bot):
	bot.add_cog(Search(bot))

class Search:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command()
	@checks.not_forbidden()
	async def amazon(self, *search : str):
		'''Search with Amazon'''
		await self.bot.embed_reply("[Amazon search for \"{}\"](https://www.amazon.com/s/?field-keywords={})".format(' '.join(search), '+'.join(search)))
	
	@commands.command()
	@checks.not_forbidden()
	async def aol(self, *search : str):
		'''Search with AOL'''
		await self.bot.embed_reply("[AOL search for \"{}\"](https://search.aol.com/aol/search?q={})".format(' '.join(search), '+'.join(search)))
	
	@commands.command(name = "ask.com")
	@checks.not_forbidden()
	async def ask_com(self, *search : str):
		'''Search with Ask.com'''
		await self.bot.embed_reply("[Ask.com search for \"{}\"](http://www.ask.com/web?q={})".format(' '.join(search), '+'.join(search)))
	
	@commands.command()
	@checks.not_forbidden()
	async def baidu(self, *search : str):
		'''Search with Baidu'''
		await self.bot.embed_reply("[Baidu search for \"{}\"](http://www.baidu.com/s?wd={})".format(' '.join(search), '+'.join(search)))
	
	@commands.command()
	@checks.not_forbidden()
	async def bing(self, *search : str):
		'''Search with Bing'''
		await self.bot.embed_reply("[Bing search for \"{}\"](http://www.bing.com/search?q={})".format(' '.join(search), '+'.join(search)))
	
	@commands.command()
	@checks.not_forbidden()
	async def duckduckgo(self, *search : str):
		'''Search with DuckDuckGo'''
		await self.bot.embed_reply("[DuckDuckGo search for \"{}\"](https://www.duckduckgo.com/?q={})".format(' '.join(search), '+'.join(search)))
	
	@commands.command(aliases = ["search", "googlesearch"])
	@checks.not_forbidden()
	async def google(self, *, search : str):
		'''Google search'''
		await self.bot.embed_reply("[Google search for \"{}\"](https://www.google.com/search?q={})".format(search, search.replace(' ', '+')))
	
	@commands.command()
	@checks.not_forbidden()
	async def imfeelinglucky(self, *search : str):
		'''First Google result of a search'''
		await self.bot.embed_reply("[First Google result of \"{}\"](https://www.google.com/search?btnI&q={})".format(' '.join(search), '+'.join(search)))
	
	@commands.command(name = "lma.ctfy")
	@checks.not_forbidden()
	async def lma_ctfy(self, *search : str):
		'''Let Me Ask.Com That For You'''
		await self.bot.embed_reply("[LMA.CTFY: \"{}\"](http://lmgtfy.com/?s=k&q={})".format(' '.join(search), '+'.join(search)))
	
	@commands.command()
	@checks.not_forbidden()
	async def lmaoltfy(self, *search : str):
		'''Let Me AOL That For You'''
		await self.bot.embed_reply("[LMAOLTFY: \"{}\"](http://lmgtfy.com/?s=a&q={})".format(' '.join(search), '+'.join(search)))
	
	@commands.command()
	@checks.not_forbidden()
	async def lmatfy(self, *search : str):
		'''Let Me Amazon That For You'''
		await self.bot.embed_reply("[LMATFY: \"{}\"](http://lmatfy.co/?q={})".format(' '.join(search), '+'.join(search)))
	
	@commands.command()
	@checks.not_forbidden()
	async def lmbdtfy(self, *search : str):
		'''Let Me Baidu That For You'''
		await self.bot.embed_reply("[LMBDTFY: \"{}\"](https://lmbtfy.cn/?{})".format(' '.join(search), '+'.join(search)))
	
	@commands.command()
	@checks.not_forbidden()
	async def lmbtfy(self, *search : str):
		'''Let Me Bing That For You'''
		output = "[LMBTFY: \"{}\"](http://lmbtfy.com/?s=b&q={})\n".format(' '.join(search), '+'.join(search))
		output += "[LMBTFY: \"{}\"](http://letmebingthatforyou.com/q={})".format(' '.join(search), '+'.join(search))
		await self.bot.embed_reply(output)
	
	@commands.command()
	@checks.not_forbidden()
	async def lmdtfy(self, *search : str):
		'''Let Me DuckDuckGo That For You'''
		await self.bot.embed_reply("[LMDTFY: \"{}\"](http://lmgtfy.com/?s=d&q={})".format(' '.join(search), '+'.join(search)))
	
	@commands.command()
	@checks.not_forbidden()
	async def lmgtfy(self, *search : str):
		'''Let Me Google That For You'''
		await self.bot.embed_reply("[LMGTFY: \"{}\"](http://lmgtfy.com/?q={})".format(' '.join(search), '+'.join(search)))
	
	@commands.command()
	@checks.not_forbidden()
	async def lmytfy(self, *search : str):
		'''Let Me Yahoo That For You'''
		await self.bot.embed_reply("[LMYTFY: \"{}\"](http://lmgtfy.com/?s=y&q={})".format(' '.join(search), '+'.join(search)))
	
	@commands.group(aliases = ["wa"], pass_context = True, invoke_without_command = True)
	@checks.not_forbidden()
	async def wolframalpha(self, ctx, *, search : str):
		'''
		Wolfram|Alpha
		http://www.wolframalpha.com/examples/
		'''
		await self._wolframalpha(ctx, search)
	
	@wolframalpha.command(name = "location", pass_context = True)
	@checks.not_forbidden()
	async def wolframalpha_location(self, ctx, location: str, *, search : str):
		'''Input location'''
		await self._wolframalpha(ctx, search, location = location)
	
	async def _wolframalpha(self, ctx, search, location = clients.fake_location):
		search = search.strip('`')
		result = clients.wolfram_alpha_client.query(search, ip = clients.fake_ip, location = location) # options
		if not hasattr(result, "pods") and hasattr(result, "didyoumeans"):
			if result.didyoumeans["@count"] == '1':
				didyoumean = result.didyoumeans["didyoumean"]["#text"]
			else:
				didyoumean = result.didyoumeans["didyoumean"][0]["#text"]
			await self.bot.embed_reply("Using closest Wolfram|Alpha interpretation: `{}`".format(didyoumean))
			result = clients.wolfram_alpha_client.query(didyoumean, ip = clients.fake_ip, location = location)
		if hasattr(result, "pods"):
			for pod in result.pods:
				images, text_output = [], []
				for subpod in pod.subpods:
					image = next(subpod.img)
					images.append(image.src)
					if subpod.plaintext and subpod.plaintext.replace('\n', ' ') not in (image.title, image.alt, image.title.strip(' '), image.alt.strip(' ')) or not ctx.message.server.me.permissions_in(ctx.message.channel).embed_links:
						print("Wolfram Alpha:\n")
						print(image.title)
						print(image.alt)
						print(subpod.plaintext.replace('\n', ' '))
						text_output.append("\n{}".format(subpod.plaintext))
				if not text_output:
					await self.bot.embed_reply(None, title = pod.title, image_url = images[0])
					for image in images[1:]:
						embed = discord.Embed(color = clients.bot_color)
						embed.set_image(url = image)
						await self.bot.say(embed = embed)
				else:
					for i, link in enumerate(images):
						images[i] = await self._shorturl(link)
					output = ("**{}** ({})".format(pod.title, ', '.join(images)))
					output += "".join(text_output)
					await self.bot.reply(output)
			if result.timedout:
				await self.bot.embed_reply("Some results timed out: {}".format(result.timedout.replace(',', ", ")))
		elif result.timedout:
			await self.bot.embed_reply("Standard computation time exceeded")
		else:
			await self.bot.embed_reply(":no_entry: No results found")
		# await self.bot.reply(next(result.results).text)
	
	@commands.command()
	@checks.not_forbidden()
	async def yahoo(self, *search : str):
		'''Search with Yahoo'''
		await self.bot.embed_reply("[Yahoo search for \"{}\"](https://search.yahoo.com/search?q={})".format(' '.join(search), '+'.join(search)))

