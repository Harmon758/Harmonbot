
import discord
from discord import app_commands
from discord.ext import commands, menus

import textwrap
from typing import Optional
import urllib.error

from bs4 import BeautifulSoup
from google.api_core.exceptions import InvalidArgument
import spellchecker

from utilities import checks
from utilities.paginator import ButtonPaginator

async def setup(bot):
    await bot.add_cog(Words())

class Words(commands.Cog):

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.command(aliases = ["antonyms"])
    async def antonym(self, ctx, word: str):
        '''Antonyms of a word'''
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
        aliases = ["definition", "definitions", "dictionary"],
        case_insensitive = True, invoke_without_command = True
    )
    async def define(self, ctx, word: str):
        """
        Define a word

        Parameters
        ----------
        word
            Word to define
        """
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
    async def pronunciation(self, ctx, word: str):
        '''Pronunciation of a word'''
        pronunciation = ctx.bot.wordnik_word_api.getTextPronunciations(
            word, limit = 1
        )
        description = (
            pronunciation[0].raw.strip("()")
            if pronunciation else "Audio File Link"
        )

        audio_file = ctx.bot.wordnik_word_api.getAudio(word, limit = 1)
        if audio_file:
            description = f"[{description}]({audio_file[0].fileUrl})"
        elif not pronunciation:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Word or pronunciation not found"
            )
            return

        await ctx.embed_reply(
            title = f"Pronunciation of {word.capitalize()}",
            description = description
        )

    @commands.command(aliases = ["rhymes"])
    async def rhyme(self, ctx, word: str):
        '''Rhymes of a word'''
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

    @commands.command()
    async def spellcheck(self, ctx, *words: str):
        '''Check the spelling of words'''
        checker = spellchecker.SpellChecker()
        if len(words) == 1:
            await ctx.embed_reply(", ".join(checker.candidates(words[0])))
        else:
            await ctx.embed_reply(
                ' '.join(checker.correction(word) for word in words)
            )

    @commands.command(aliases = ["synonyms"])
    async def synonym(self, ctx, word: str):
        """Synonyms of a word"""
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
            reference = ctx.message.reference,
            mention_author = (
                referenced_message.author in ctx.message.mentions
                if ctx.message.reference else None
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
        response = await ctx.bot.google_cloud_translation_service_client.get_supported_languages(
            display_language_code = language_code,
            parent = f"projects/{ctx.bot.google_cloud_project_id}/locations/global",
        )
        await ctx.embed_reply(
            ", ".join(
                f"{language.display_name} ({language.language_code})"
                for language in response.languages
            )
        )

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
            reference = ctx.message.reference,
            mention_author = (
                referenced_message.author in ctx.message.mentions
                if ctx.message.reference else None
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

