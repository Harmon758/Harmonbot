
import discord
from discord.ext import commands, menus

import urllib.error

from bs4 import BeautifulSoup

from utilities import checks
from utilities.menu import Menu

def setup(bot):
	bot.add_cog(Words(bot))

class Words(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.menus = []
	
	def cog_unload(self):
		for menu in self.menus:
			menu.stop()
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.command(aliases = ["antonyms"])
	async def antonym(self, ctx, word : str):
		'''Antonyms of a word'''
		try:
			antonyms = self.bot.wordnik_word_api.getRelatedWords(word, relationshipTypes = "antonym", 
																	useCanonical = "true", limitPerRelationshipType = 100)
		except urllib.error.HTTPError as e:
			if e.code == 404:
				return await ctx.embed_reply(":no_entry: Word or antonyms not found")
			raise
		if not antonyms:
			return await ctx.embed_reply(":no_entry: Word or antonyms not found")
		await ctx.embed_reply(", ".join(antonyms[0].words), title = f"Antonyms of {word.capitalize()}")
	
	@commands.group(aliases = ["definition", "definitions", "dictionary"], invoke_without_command = True, case_insensitive = True)
	async def define(self, ctx, word: str):
		'''Define a word'''
		try:
			definitions = self.bot.wordnik_word_api.getDefinitions(word)  # useCanonical = True ?
		except urllib.error.HTTPError as e:
			if e.code in (404, 429):
				return await ctx.embed_reply(f":no_entry: Error: {e.reason}")
			raise
		for definition in definitions:
			if definition.text:
				return await ctx.embed_reply(BeautifulSoup(definition.text, "html.parser").get_text(), 
												title = definition.word, 
												footer_text = definition.attributionText)
		await ctx.embed_reply(":no_entry: Definition not found")
	
	@define.command(name = "menu", aliases = ['m', "menus", 'r', "reaction", "reactions"])
	async def define_menu(self, ctx, word : str):
		'''Definitions menu'''
		try:
			definitions = self.bot.wordnik_word_api.getDefinitions(word)  # useCanonical = True ?
		except urllib.error.HTTPError as e:
			if e.code == 404:
				return await ctx.embed_reply(":no_entry: Error: Not found")
			raise
		definitions = [definition for definition in definitions if definition.text]
		if not definitions:
			await ctx.embed_reply(":no_entry: Definition not found")
		menu = DefineMenu(definitions)
		self.menus.append(menu)
		await menu.start(ctx, wait = True)
		self.menus.remove(menu)
	
	@commands.command(aliases = ["audiodefine", "pronounce"])
	async def pronunciation(self, ctx, word : str):
		'''Pronunciation of a word'''
		pronunciation = self.bot.wordnik_word_api.getTextPronunciations(word, limit = 1)
		description = pronunciation[0].raw.strip("()") if pronunciation else "Audio File Link"
		audio_file = self.bot.wordnik_word_api.getAudio(word, limit = 1)
		if audio_file:
			description = f"[{description}]({audio_file[0].fileUrl})"
		elif not pronunciation:
			return await ctx.embed_reply(":no_entry: Word or pronunciation not found")
		await ctx.embed_reply(description, title = f"Pronunciation of {word.capitalize()}")
	
	@commands.command(aliases = ["rhymes"])
	async def rhyme(self, ctx, word : str):
		'''Rhymes of a word'''
		try:
			rhymes = self.bot.wordnik_word_api.getRelatedWords(word, relationshipTypes = "rhyme", 
																limitPerRelationshipType = 100)
		except urllib.error.HTTPError as e:
			if e.code == 404:
				return await ctx.embed_reply(":no_entry: Word or rhymes not found")
			raise
		if not rhymes:
			return await ctx.embed_reply(":no_entry: Word or rhymes not found")
		await ctx.embed_reply(", ".join(rhymes[0].words), 
								title = f"Words that rhyme with {word.capitalize()}")
	
	@commands.command()
	async def spellcheck(self, ctx, *, words : str):
		'''Spell check words'''
		url = "https://api.cognitive.microsoft.com/bing/v5.0/spellcheck"
		headers = {"Ocp-Apim-Subscription-Key" : ctx.bot.BING_SPELL_CHECK_API_KEY}
		params = {"Text": words.replace(' ', '+')}  # replace necessary?
		async with ctx.bot.aiohttp_session.post(url, headers = headers, params = params) as resp:
			data = await resp.json()
		corrections = data["flaggedTokens"]
		corrected = words
		offset = 0
		for correction in corrections:
			offset += correction["offset"]
			suggestion = correction["suggestions"][0]["suggestion"]
			corrected = corrected[:offset] + suggestion + corrected[offset + len(correction["token"]):]
			offset += (len(suggestion) - len(correction["token"])) - correction["offset"]
		await ctx.embed_reply(corrected)
	
	@commands.command(aliases = ["synonyms"])
	async def synonym(self, ctx, word : str):
		'''Synonyms of a word'''
		try:
			synonyms = self.bot.wordnik_word_api.getRelatedWords(word, relationshipTypes = "synonym", 
																	useCanonical = "true", limitPerRelationshipType = 100)
		except urllib.error.HTTPError as e:
			if e.code == 404:
				return await ctx.embed_reply(":no_entry: Word or synonyms not found")
			raise
		if not synonyms:
			return await ctx.embed_reply(":no_entry: Word or synonyms not found")
		await ctx.embed_reply(", ".join(synonyms[0].words), title = f"Synonyms of {word.capitalize()}")
	
	@commands.group(description = "[Language Codes](https://tech.yandex.com/translate/doc/dg/concepts/api-overview-docpage/#languages)\n"
						"Powered by [Yandex.Translate](http://translate.yandex.com/)", 
					invoke_without_command = True, case_insensitive = True)
	async def translate(self, ctx, *, text : str):
		'''Translate to English'''
		# TODO: From and to language code options?
		await self.process_translate(ctx, text, "en")
	
	@translate.command(name = "from")
	async def translate_from(self, ctx, from_language_code : str, to_language_code : str, *, text : str):
		'''
		Translate from a specific language to another
		[Language Codes](https://tech.yandex.com/translate/doc/dg/concepts/api-overview-docpage/#languages)
		Powered by [Yandex.Translate](http://translate.yandex.com/)
		'''
		# TODO: Default to_language_code?
		await self.process_translate(ctx, text, to_language_code, from_language_code)
	
	@translate.command(name = "languages", aliases = ["codes", "language_codes"])
	async def translate_languages(self, ctx, language_code : str = "en"):
		'''Language Codes'''
		url = "https://translate.yandex.net/api/v1.5/tr.json/getLangs"
		params = {"ui": language_code, "key": ctx.bot.YANDEX_TRANSLATE_API_KEY}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if "langs" not in data:
			return await ctx.embed_reply(":no_entry: Error: Invalid Language Code")
		await ctx.embed_reply(", ".join(sorted(f"{language} ({code})" for code, language in data["langs"].items())))
	
	@translate.command(name = "to")
	async def translate_to(self, ctx, language_code : str, *, text : str):
		'''
		Translate to a specific language
		[Language Codes](https://tech.yandex.com/translate/doc/dg/concepts/api-overview-docpage/#languages)
		Powered by [Yandex.Translate](http://translate.yandex.com/)
		'''
		await self.process_translate(ctx, text, language_code)
	
	async def process_translate(self, ctx, text, to_language_code, from_language_code = None):
		url = "https://translate.yandex.net/api/v1.5/tr.json/translate"
		params = {"key": ctx.bot.YANDEX_TRANSLATE_API_KEY, 
					"lang": to_language_code if not from_language_code else f"{from_language_code}-{to_language_code}", 
					"text": text, "options": 1}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			if resp.status == 400:  # Bad Request
				return await ctx.embed_reply(":no_entry: Error")
			data = await resp.json()
		if data["code"] != 200:
			return await ctx.embed_reply(f":no_entry: Error: {data['message']}")
		footer_text = "Powered by Yandex.Translate"
		if not from_language_code:
			footer_text = f"Detected Language Code: {data['detected']['lang']} | " + footer_text
		await ctx.embed_reply(data["text"][0], footer_text = footer_text)

class DefineSource(menus.ListPageSource):
	
	def __init__(self, definitions):
		super().__init__(definitions, per_page = 1)
	
	async def format_page(self, menu, definition):
		embed = discord.Embed(title = definition.word, 
								description = BeautifulSoup(definition.text, "html.parser").get_text(), 
								color = menu.bot.bot_color)
		embed.set_author(name = menu.ctx.author.display_name, icon_url = menu.ctx.author.avatar_url)
		embed.set_footer(text = f"{definition.attributionText} (Definition {menu.current_page + 1} of {self.get_max_pages()})")
		return {"content": f"In response to: `{menu.ctx.message.clean_content}`", "embed": embed}

class DefineMenu(Menu, menus.MenuPages):
	
	def __init__(self, definitions):
		super().__init__(DefineSource(definitions), timeout = None, clear_reactions_after = True, check_embeds = True)
	
	async def send_initial_message(self, ctx, channel):
		message = await super().send_initial_message(ctx, channel)
		await ctx.bot.attempt_delete_message(ctx.message)
		return message

