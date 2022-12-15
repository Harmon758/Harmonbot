
import discord
from discord.ext import commands, menus

import io
import textwrap
from typing import Optional
import urllib.error

from async_lru import alru_cache
from bs4 import BeautifulSoup
from google.api_core.exceptions import InvalidArgument
import spellchecker

from utilities import checks
from utilities.paginators import ButtonPaginator


async_cache = alru_cache(maxsize=None)
# https://github.com/python/cpython/issues/90780

async def setup(bot):
    await bot.add_cog(Words(bot))

class Words(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.hybrid_command(aliases = ["antonym"])
    async def antonyms(self, ctx, word: str):
        """
        Antonyms of a word

        Parameters
        ----------
        word
            Word to get antonyms for
        """
        await ctx.defer()

        try:
            antonyms = ctx.bot.wordnik_word_api.getRelatedWords(
                word, relationshipTypes = "antonym",
                useCanonical = "true", limitPerRelationshipType = 100
            )
        except urllib.error.HTTPError as e:
            if e.code == 404:
                await ctx.embed_reply(
                    f"{ctx.bot.error_emoji} Word or antonyms not found"
                )
                return
            raise

        if not antonyms:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Word or antonyms not found"
            )
            return

        await ctx.embed_reply(
            title = f"Antonyms of {word.capitalize()}",
            description = ", ".join(antonyms[0].words)
        )

    @commands.hybrid_command(
        aliases = ["definition", "definitions", "dictionary"]
    )
    async def define(self, ctx, word: str):
        """
        Define a word

        Parameters
        ----------
        word
            Word to define
        """
        await ctx.defer()

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

    @commands.hybrid_command(aliases = ["audiodefine", "pronunciation"])
    async def pronounce(self, ctx, word: str):
        """
        Pronunciation of a word

        Parameters
        ----------
        word
            Word to get pronunciation for
        """
        await ctx.defer()

        try:
            pronunciation = ctx.bot.wordnik_word_api.getTextPronunciations(
                word, limit = 1
            )
        except urllib.error.HTTPError as e:
            if e.code == 404:
                await ctx.embed_reply(
                    f"{ctx.bot.error_emoji} Word or pronunciation not found"
                )
                return
            raise

        description = (
            pronunciation[0].raw.strip("()")
            if pronunciation else "Audio File Link"
        )

        try:
            audio_file = ctx.bot.wordnik_word_api.getAudio(word, limit = 1)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                audio_file = None
            else:
                raise

        file = None
        if audio_file:
            file_url = audio_file[0].fileUrl
            async with ctx.bot.aiohttp_session.get(file_url) as resp:
                data = await resp.read()

            file = discord.File(
                io.BytesIO(data), filename = f"Pronunciation_of_{word}.mp3"
            )
        elif not pronunciation:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Word or pronunciation not found"
            )
            return

        await ctx.embed_reply(
            title = f"Pronunciation of \"{word}\"",
            description = description,
            file = file
        )

    @commands.hybrid_command(aliases = ["rhyme"])
    async def rhymes(self, ctx, word: str):
        """
        Rhymes of a word

        Paramters
        ---------
        word
            Word to get rhymes for
        """
        await ctx.defer()

        try:
            rhymes = ctx.bot.wordnik_word_api.getRelatedWords(
                word, relationshipTypes = "rhyme",
                limitPerRelationshipType = 100
            )
        except urllib.error.HTTPError as e:
            if e.code == 404:
                await ctx.embed_reply(
                    f"{ctx.bot.error_emoji} Word or rhymes not found"
                )
                return
            raise

        if not rhymes:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Word or rhymes not found"
            )
            return

        await ctx.embed_reply(
            title = f"Words that rhyme with {word.capitalize()}",
            description = ", ".join(rhymes[0].words)
        )

    @commands.command(require_var_positional = True)
    async def spellcheck(self, ctx, *words: str):
        """Check the spelling of words"""
        checker = spellchecker.SpellChecker()
        if len(words) == 1:
            candidates = checker.candidates(words[0])
            if candidates:
                await ctx.embed_reply(", ".join(candidates))
            else:
                await ctx.embed_reply(
                    f"{ctx.bot.error_emoji} No candidate spellings found"
                )
        else:
            corrected_output = ""
            corrected_words = ""
            for word in words:
                correction = checker.correction(word)
                if correction:
                    corrected_output += correction + ' '
                    if correction != word:
                        corrected_words += f"{word} -> {correction}\n"
                else:
                    corrected_output += word + ' '
                    corrected_words += (
                        f"No candidate spelling found for \"{word}\"\n"
                    )
            await ctx.embed_reply(
                description = corrected_output[:-1],
                footer_text = None,
                embeds = [
                    discord.Embed(
                        color = ctx.bot.bot_color,
                        description = corrected_words[:-1]
                    )
                ]
            )

    @commands.hybrid_command(aliases = ["synonym"])
    async def synonyms(self, ctx, word: str):
        """
        Synonyms of a word

        Parameters
        ----------
        word
            Word to get synonyms for
        """
        await ctx.defer()

        try:
            synonyms = ctx.bot.wordnik_word_api.getRelatedWords(
                word, relationshipTypes = "synonym",
                useCanonical = "true", limitPerRelationshipType = 100
            )
        except urllib.error.HTTPError as e:
            if e.code == 404:
                await ctx.embed_reply(
                    f"{ctx.bot.error_emoji} Word or synonyms not found"
                )
                return
            raise

        if not synonyms:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Word or synonyms not found"
            )
            return

        await ctx.embed_reply(
            title = f"Synonyms of {word.capitalize()}",
            description = ", ".join(synonyms[0].words)
        )

    @commands.group(case_insensitive = True, invoke_without_command = True)
    async def translate(self, ctx, *, text: Optional[str]):
        '''Translate to English'''
        # TODO: From and to language code options?
        if not text:
            if ctx.message.reference:
                referenced_message = (
                    ctx.message.reference.cached_message or
                    await ctx.channel.fetch_message(
                        ctx.message.reference.message_id
                    )
                )
                text = referenced_message.content
            else:
                await ctx.send_help(ctx.command)
                return

        response = await ctx.bot.google_cloud_translation_service_client.translate_text(
            contents = [text],
            mime_type = "text/plain",
            parent = f"projects/{ctx.bot.google_cloud_project_id}/locations/global",
            target_language_code = "en"
        )
        translation = response.translations[0]

        await ctx.embed_reply(
            translation.translated_text,
            footer_text = f"Detected Language Code: {translation.detected_language_code}",
            reference = ctx.message.reference if not text else None,
            mention_author = (
                referenced_message.author in ctx.message.mentions
                if ctx.message.reference and not text else None
            )
        )

    @translate.command(name = "from")
    async def translate_from(
        self, ctx, from_language_code: str, to_language_code: str, *,
        text: str
    ):
        '''Translate from a specific language to another'''
        # TODO: Default to_language_code?
        try:
            response = await ctx.bot.google_cloud_translation_service_client.translate_text(
                contents = [text],
                mime_type = "text/plain",
                parent = f"projects/{ctx.bot.google_cloud_project_id}/locations/global",
                source_language_code = from_language_code,
                target_language_code = to_language_code
            )
        except InvalidArgument as e:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")
            return
        await ctx.embed_reply(response.translations[0].translated_text)

    @translate.command(
        name = "languages", aliases = ["codes", "language_codes"]
    )
    async def translate_languages(self, ctx, language_code: str = "en"):
        '''Language Codes'''
        languages = await self.supported_translation_languages()
        await ctx.embed_reply(
            ", ".join(
                f"{language.display_name} ({language.language_code})"
                for language in languages
            )
        )

    @async_cache
    async def supported_translation_languages(self, language_code: str = "en"):
        response = await self.bot.google_cloud_translation_service_client.get_supported_languages(
            display_language_code = language_code,
            parent = f"projects/{self.bot.google_cloud_project_id}/locations/global",
        )
        return response.languages

    @translate.command(name = "to")
    async def translate_to(
        self, ctx, language_code: str, *, text: Optional[str]
    ):
        '''Translate to a specific language'''
        if not text:
            if ctx.message.reference:
                referenced_message = (
                    ctx.message.reference.cached_message or
                    await ctx.channel.fetch_message(
                        ctx.message.reference.message_id
                    )
                )
                text = referenced_message.content
            else:
                await ctx.send_help(ctx.command)
                return

        response = await ctx.bot.google_cloud_translation_service_client.translate_text(
            contents = [text],
            mime_type = "text/plain",
            parent = f"projects/{ctx.bot.google_cloud_project_id}/locations/global",
            target_language_code = language_code
        )
        translation = response.translations[0]

        await ctx.embed_reply(
            translation.translated_text,
            footer_text = f"Detected Language Code: {translation.detected_language_code}",
            reference = ctx.message.reference if not text else None,
            mention_author = (
                referenced_message.author in ctx.message.mentions
                if ctx.message.reference and not text else None
            )
        )

    @commands.group(
        aliases = [
            "urband", "urban_dictionary", "urbandefine", "urban_define"
        ], case_insensitive = True, invoke_without_command = True
    )
    async def urbandictionary(self, ctx, *, term: str):
        '''Urban Dictionary'''
        # TODO: Convert to define/dictionary subcommand urban and add urband
        # etc. as command aliases
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
        kwargs = {}

        embed = discord.Embed(
            title = definition.word,
            description = BeautifulSoup(
                definition.text, "html.parser"
            ).get_text(),
            color = menu.bot.bot_color
        ).set_footer(
            text = definition.attributionText
        )

        if isinstance(menu.ctx_or_interaction, commands.Context):
            if not menu.ctx_or_interaction.interaction:
                embed.set_author(
                    name = menu.ctx.author.display_name,
                    icon_url = menu.ctx.author.display_avatar.url
                )
                kwargs["content"] = (
                    f"In response to: `{menu.ctx.message.clean_content}`"
                )
        elif not isinstance(menu.ctx_or_interaction, discord.Interaction):
            raise RuntimeError(
                "DefineSource using neither Context nor Interaction"
            )

        kwargs["embed"] = embed

        return kwargs

class UrbanDictionarySource(menus.ListPageSource):

    def __init__(self, definitions):
        super().__init__(definitions, per_page = 1)

    async def format_page(self, menu, definition):
        votes = (
            f"\N{THUMBS UP SIGN}{menu.ctx.bot.emoji_skin_tone} {definition['thumbs_up']}"
            " | "
            f"\N{THUMBS DOWN SIGN}{menu.ctx.bot.emoji_skin_tone} {definition['thumbs_down']}"
        )
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
                value = (
                    textwrap.shorten(
                        definition["example"],
                        width = menu.ctx.bot.EFVCL - len(votes) - 2,
                        # EFVCL: Embed Field Value Character Limit
                        placeholder = "..."
                    ) + "\n\n" + votes
                )
            )
        }
        # TODO: Check description/definition length?

