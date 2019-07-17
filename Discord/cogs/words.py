
from discord.ext import commands

import urllib.error

from bs4 import BeautifulSoup

from utilities import checks

def setup(bot):
	bot.add_cog(Words(bot))

class Words(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command(aliases = ["antonyms"])
	@checks.not_forbidden()
	async def antonym(self, ctx, word : str):
		'''Antonyms of a word'''
		antonyms = self.bot.wordnik_word_api.getRelatedWords(word, relationshipTypes = "antonym", 
																useCanonical = "true", limitPerRelationshipType = 100)
		if not antonyms:
			return await ctx.embed_reply(":no_entry: Word or antonyms not found")
		await ctx.embed_reply(", ".join(antonyms[0].words), title = f"Antonyms of {word.capitalize()}")
	
	@commands.command(aliases = ["dictionary"])
	@checks.not_forbidden()
	async def define(self, ctx, word : str):
		'''Define a word'''
		try:
			definition = self.bot.wordnik_word_api.getDefinitions(word, limit = 1)  # useCanonical = True ?
		except urllib.error.HTTPError as e:
			if e.code == 404:
				return await ctx.embed_reply(":no_entry: Error: Not found")
			raise
		if not definition:
			return await ctx.embed_reply(":no_entry: Definition not found")
		await ctx.embed_reply(BeautifulSoup(definition[0].text, "html.parser").get_text(), 
								title = definition[0].word, 
								footer_text = definition[0].attributionText)
	
	@commands.command(aliases = ["audiodefine", "pronounce"])
	@checks.not_forbidden()
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
	@checks.not_forbidden()
	async def rhyme(self, ctx, word : str):
		'''Rhymes of a word'''
		rhymes = self.bot.wordnik_word_api.getRelatedWords(word, relationshipTypes = "rhyme", 
															limitPerRelationshipType = 100)
		if not rhymes:
			return await ctx.embed_reply(":no_entry: Word or rhymes not found")
		await ctx.embed_reply(", ".join(rhymes[0].words), 
								title = f"Words that rhyme with {word.capitalize()}")
	
	@commands.command()
	@checks.not_forbidden()
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
	@checks.not_forbidden()
	async def synonym(self, ctx, word : str):
		'''Synonyms of a word'''
		synonyms = self.bot.wordnik_word_api.getRelatedWords(word, relationshipTypes = "synonym", 
																useCanonical = "true", limitPerRelationshipType = 100)
		if not synonyms:
			return await ctx.embed_reply(":no_entry: Word or synonyms not found")
		await ctx.embed_reply(", ".join(synonyms[0].words), title = f"Synonyms of {word.capitalize()}")
	
	@commands.group(description = "[Language Codes](https://tech.yandex.com/translate/doc/dg/concepts/api-overview-docpage/#languages)\n"
						"Powered by [Yandex.Translate](http://translate.yandex.com/)", 
					invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def translate(self, ctx, *, text : str):
		'''Translate to English'''
		# TODO: From and to language code options?
		await self.process_translate(ctx, text, "en")
	
	@translate.command(name = "from")
	@checks.not_forbidden()
	async def translate_from(self, ctx, from_language_code : str, to_language_code : str, *, text : str):
		'''
		Translate from a specific language to another
		[Language Codes](https://tech.yandex.com/translate/doc/dg/concepts/api-overview-docpage/#languages)
		Powered by [Yandex.Translate](http://translate.yandex.com/)
		'''
		# TODO: Default to_language_code?
		await self.process_translate(ctx, text, to_language_code, from_language_code)
	
	@translate.command(name = "languages", aliases = ["codes", "language_codes"])
	@checks.not_forbidden()
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
	@checks.not_forbidden()
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

