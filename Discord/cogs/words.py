
import discord
from discord.ext import commands, menus

import urllib.error

from bs4 import BeautifulSoup
import spellchecker

from utilities import checks
from utilities.paginator import ButtonPaginator

def setup(bot):
	bot.add_cog(Words())

class Words(commands.Cog):
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.command(aliases = ["antonyms"])
	async def antonym(self, ctx, word : str):
		'''Antonyms of a word'''
		try:
			antonyms = ctx.bot.wordnik_word_api.getRelatedWords(word, relationshipTypes = "antonym", 
																useCanonical = "true", limitPerRelationshipType = 100)
		except urllib.error.HTTPError as e:
			if e.code == 404:
				return await ctx.embed_reply(f"{ctx.bot.error_emoji} Word or antonyms not found")
			raise
		if not antonyms:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Word or antonyms not found")
		await ctx.embed_reply(", ".join(antonyms[0].words), title = f"Antonyms of {word.capitalize()}")
	
	@commands.group(
		aliases = ["definition", "definitions", "dictionary"],
		case_insensitive = True, invoke_without_command = True,
	)
	async def define(self, ctx, word: str):
		'''Define a word'''
		try:
			definitions = ctx.bot.wordnik_word_api.getDefinitions(word)
			# useCanonical = True ?
		except urllib.error.HTTPError as e:
			if e.code in (404, 429):
				await ctx.embed_reply(
					f"{ctx.bot.error_emoji} Error: {e.reason}"
				)
				return
			raise
		
		definitions = [
			definition for definition in definitions if definition.text
		]
		
		if not definitions:
			await ctx.embed_reply(
				f"{ctx.bot.error_emoji} Definition not found"
			)
		
		paginator = ButtonPaginator(ctx, DefineSource(definitions))
		await paginator.start()
		ctx.bot.views.append(paginator)
	
	@commands.command(aliases = ["audiodefine", "pronounce"])
	async def pronunciation(self, ctx, word : str):
		'''Pronunciation of a word'''
		pronunciation = ctx.bot.wordnik_word_api.getTextPronunciations(word, limit = 1)
		description = pronunciation[0].raw.strip("()") if pronunciation else "Audio File Link"
		audio_file = ctx.bot.wordnik_word_api.getAudio(word, limit = 1)
		if audio_file:
			description = f"[{description}]({audio_file[0].fileUrl})"
		elif not pronunciation:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Word or pronunciation not found")
		await ctx.embed_reply(description, title = f"Pronunciation of {word.capitalize()}")
	
	@commands.command(aliases = ["rhymes"])
	async def rhyme(self, ctx, word : str):
		'''Rhymes of a word'''
		try:
			rhymes = ctx.bot.wordnik_word_api.getRelatedWords(word, relationshipTypes = "rhyme", 
																limitPerRelationshipType = 100)
		except urllib.error.HTTPError as e:
			if e.code == 404:
				return await ctx.embed_reply(f"{ctx.bot.error_emoji} Word or rhymes not found")
			raise
		if not rhymes:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Word or rhymes not found")
		await ctx.embed_reply(", ".join(rhymes[0].words), 
								title = f"Words that rhyme with {word.capitalize()}")
	
	@commands.command()
	async def spellcheck(self, ctx, *words: str):
		'''Check the spelling of words'''
		checker = spellchecker.SpellChecker()
		if len(words) == 1:
			await ctx.embed_reply(", ".join(checker.candidates(words[0])))
		else:
			await ctx.embed_reply(' '.join(checker.correction(word) for word in words))
	
	@commands.command(aliases = ["synonyms"])
	async def synonym(self, ctx, word : str):
		'''Synonyms of a word'''
		try:
			synonyms = ctx.bot.wordnik_word_api.getRelatedWords(word, relationshipTypes = "synonym", 
																useCanonical = "true", limitPerRelationshipType = 100)
		except urllib.error.HTTPError as e:
			if e.code == 404:
				return await ctx.embed_reply(f"{ctx.bot.error_emoji} Word or synonyms not found")
			raise
		if not synonyms:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Word or synonyms not found")
		await ctx.embed_reply(", ".join(synonyms[0].words), title = f"Synonyms of {word.capitalize()}")
	
	@commands.group(description = "[Language Codes](https://tech.yandex.com/translate/doc/dg/concepts/api-overview-docpage/#languages)\n"
									"Powered by [Yandex.Translate](http://translate.yandex.com/)", 
					invoke_without_command = True, case_insensitive = True)
	async def translate(self, ctx, *, text: str):
		'''Translate to English'''
		# TODO: From and to language code options?
		await self.process_translate(ctx, text, "en")
	
	@translate.command(name = "from")
	async def translate_from(
		self, ctx, from_language_code: str, to_language_code: str, *,
		text: str
	):
		'''
		Translate from a specific language to another
		[Language Codes](https://tech.yandex.com/translate/doc/dg/concepts/api-overview-docpage/#languages)
		Powered by [Yandex.Translate](http://translate.yandex.com/)
		'''
		# TODO: Default to_language_code?
		await self.process_translate(
			ctx, text, to_language_code, from_language_code
		)
	
	@translate.command(name = "languages", aliases = ["codes", "language_codes"])
	async def translate_languages(self, ctx, language_code: str = "en"):
		'''Language Codes'''
		url = "https://translate.yandex.net/api/v1.5/tr.json/getLangs"
		params = {"ui": language_code, "key": ctx.bot.YANDEX_TRANSLATE_API_KEY}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		if "langs" not in data:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: Invalid Language Code")
		await ctx.embed_reply(", ".join(sorted(f"{language} ({code})" for code, language in data["langs"].items())))
	
	@translate.command(name = "to")
	async def translate_to(self, ctx, language_code: str, *, text: str):
		'''
		Translate to a specific language
		[Language Codes](https://tech.yandex.com/translate/doc/dg/concepts/api-overview-docpage/#languages)
		Powered by [Yandex.Translate](http://translate.yandex.com/)
		'''
		await self.process_translate(ctx, text, language_code)
	
	async def process_translate(
		self, ctx, text, to_language_code, from_language_code = None
	):
		url = "https://translate.yandex.net/api/v1.5/tr.json/translate"
		params = {
			"key": ctx.bot.YANDEX_TRANSLATE_API_KEY, 
			"lang": (
				to_language_code if not from_language_code
				else f"{from_language_code}-{to_language_code}"
			), 
			"text": text, "options": 1
		}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			if resp.status == 400:  # Bad Request
				await ctx.embed_reply(f"{ctx.bot.error_emoji} Error")
				return
			data = await resp.json()
		
		if data["code"] != 200:
			await ctx.embed_reply(
				f"{ctx.bot.error_emoji} Error: {data['message']}"
			)
			return
		
		if from_language_code:
			footer_text = ""
		else:
			footer_text = f"Detected Language Code: {data['detected']['lang']} | "
		footer_text += "Powered by Yandex.Translate"
		await ctx.embed_reply(data["text"][0], footer_text = footer_text)
	
	@commands.group(
		aliases = ["urband", "urban_dictionary", "urbandefine", "urban_define"],
		case_insensitive = True, invoke_without_command = True
	)
	async def urbandictionary(self, ctx, *, term: str):
		'''Urban Dictionary'''
		# TODO: Convert to define/dictionary subcommand urban and add urband etc. as command aliases
		
		url = "http://api.urbandictionary.com/v0/define"
		params = {"term": term}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		
		if not (definitions := data.get("list")):
			await ctx.embed_reply(
				f"{ctx.bot.error_emoji} No results found"
			)
			return
		
		paginator = ButtonPaginator(ctx, UrbanDictionarySource(definitions))
		await paginator.start()
		ctx.bot.views.append(paginator)

class DefineSource(menus.ListPageSource):
	
	def __init__(self, definitions):
		super().__init__(definitions, per_page = 1)
	
	async def format_page(self, menu, definition):
		return {
			"content": f"In response to: `{menu.ctx.message.clean_content}`",
			"embed": discord.Embed(
				title = definition.word,
				description = BeautifulSoup(definition.text, "html.parser").get_text(),
				color = menu.ctx.bot.bot_color
			).set_author(
				name = menu.ctx.author.display_name,
				icon_url = menu.ctx.author.display_avatar.url
			).set_footer(
				text = definition.attributionText
			)
		}

class UrbanDictionarySource(menus.ListPageSource):
	
	def __init__(self, definitions):
		super().__init__(definitions, per_page = 1)
	
	async def format_page(self, menu, definition):
		return {
			"content": f"In response to: `{menu.ctx.message.clean_content}`",
			"embed": discord.Embed(
				title = definition["word"], url = definition["permalink"],
				description = definition["definition"],
				color = menu.ctx.bot.bot_color
			).set_author(
				name = menu.ctx.author.display_name,
				icon_url = menu.ctx.author.display_avatar.url
			).add_field(
				name = "Example",
				value = f"{definition['example']}\n\n"
						f"\N{THUMBS UP SIGN}{menu.ctx.bot.emoji_skin_tone} {definition['thumbs_up']}"
						" | "
						f"\N{THUMBS DOWN SIGN}{menu.ctx.bot.emoji_skin_tone} {definition['thumbs_down']}"
			)
		}
		# TODO: Check description/definition length?

