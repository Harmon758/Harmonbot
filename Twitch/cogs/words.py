
from twitchio.ext import commands

import textwrap

@commands.cog()
class Words:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command()
	async def audiodefine(self, ctx, word):
		url = f"http://api.wordnik.com:80/v4/word.json/{word}/audio"
		params = {"useCanonical": "false", "limit": 1, "api_key": self.bot.WORDNIK_API_KEY}
		async with self.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if data:
			await ctx.send(f"{data[0]['word'].capitalize()}: {data[0]['fileUrl']}")
		else:
			await ctx.send("Word or audio not found.")
	
	@commands.command()
	async def define(self, ctx, word):
		url = f"http://api.wordnik.com:80/v4/word.json/{word}/definitions"
		params = {"limit": 1, "includeRelated": "false", "useCanonical": "false", "includeTags": "false", 
					"api_key": self.bot.WORDNIK_API_KEY}
		async with self.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if data:
			await ctx.send(f"{data[0]['word'].capitalize()}: {data[0]['text']}")
		else:
			await ctx.send("Definition not found.")
	
	@commands.command()
	async def randomword(self, ctx):
		url = "http://api.wordnik.com:80/v4/words.json/randomWord"
		params = {"hasDictionaryDef": "false", "minCorpusCount": 0, "maxCorpusCount": -1, 
					"minDictionaryCount": 1, "maxDictionaryCount": -1, "minLength": 5, "maxLength": -1, 
					"api_key": self.bot.WORDNIK_API_KEY}
		async with self.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		await ctx.send(data["word"].capitalize())
	
	@commands.command()
	async def translate(self, ctx, *, words):
		url = "https://translate.yandex.net/api/v1.5/tr.json/translate"
		params = {"lang": "en", "text": words, "options": 1, 
					"key": self.bot.YANDEX_TRANSLATE_API_KEY}
		async with self.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if data["code"] != 200:
			return await ctx.send(f"Error: {data['message']}")
		await ctx.send(data["text"][0])
	
	@commands.command(aliases = ("urband",))
	async def urbandictionary(self, ctx, *, word):
		url = "http://api.urbandictionary.com/v0/define"
		params = {"term": word}
		async with self.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if not data or not data.get("list"):
			return await ctx.send("No results found.")
		definition = data["list"][0]
		message = textwrap.shorten(f"{definition['word']}: {definition['definition']}", 
									width = self.bot.char_limit - len(definition["permalink"]) - 1, 
									placeholder = "...")
		await ctx.send(f"{message} {definition['permalink']}")

