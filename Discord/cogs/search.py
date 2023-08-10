
import discord
from discord import app_commands
from discord.ext import commands

import functools
import sys
from typing import Literal, Optional

import youtube_dl

from utilities import checks
from utilities.menu_sources import WolframAlphaSource
from utilities.paginators import ButtonPaginator
from utilities.views import WikiArticlesView

sys.path.insert(0, "..")
from units.wikis import get_random_article, search_wiki
sys.path.pop(0)


FANDOM_WIKIS = {
    "The Lord of the Rings": "https://lotr.fandom.com/",
    "Transformers Movie": "https://michaelbaystransformers.fandom.com/"
}


async def setup(bot):
    await bot.add_cog(Search())


class Search(commands.GroupCog, group_name = "search"):
    """Search"""

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.group(invoke_without_command = True, case_insensitive = True)
    async def search(self, ctx):
        '''
        Search things
        All search subcommands are also commands
        '''
        await ctx.embed_reply(":grey_question: Search what?")

    @search.command(name = "amazon")
    async def search_amazon(self, ctx, *search: str):
        """Search with Amazon"""
        # Note: amazon command invokes this command
        await ctx.embed_reply(
            f"[Amazon search for \"{' '.join(search)}\"]"
            f"(https://www.amazon.com/s?k={'+'.join(search)})"
        )

    @commands.command()
    async def amazon(self, ctx, *search: str):
        """Search with Amazon"""
        if command := ctx.bot.get_command("search amazon"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search amazon command not found when amazon command invoked"
            )

    @search.command(name = "aol")
    async def search_aol(self, ctx, *search: str):
        """Search with AOL"""
        # Note: aol command invokes this command
        await ctx.embed_reply(
            f"[AOL search for \"{' '.join(search)}\"]"
            f"(https://search.aol.com/aol/search?q={'+'.join(search)})"
        )

    @commands.command()
    async def aol(self, ctx, *search: str):
        """Search with AOL"""
        if command := ctx.bot.get_command("search aol"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search aol command not found when aol command invoked"
            )

    @search.command(name = "ask.com")
    async def search_ask_com(self, ctx, *search: str):
        """Search with Ask.com"""
        # Note: ask.com command invokes this command
        await ctx.embed_reply(
            f"[Ask.com search for \"{' '.join(search)}\"]"
            f"(http://www.ask.com/web?q={'+'.join(search)})"
        )

    @commands.command(name = "ask.com")
    async def ask_com(self, ctx, *search: str):
        """Search with Ask.com"""
        if command := ctx.bot.get_command("search ask.com"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search ask.com command not found when ask.com command invoked"
            )

    @search.command(name = "baidu")
    async def search_baidu(self, ctx, *search: str):
        """Search with Baidu"""
        # Note: baidu command invokes this command
        await ctx.embed_reply(
            f"[Baidu search for \"{' '.join(search)}\"]"
            f"(http://www.baidu.com/s?wd={'+'.join(search)})"
        )

    @commands.command()
    async def baidu(self, ctx, *search: str):
        """Search with Baidu"""
        if command := ctx.bot.get_command("search baidu"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search baidu command not found when baidu command invoked"
            )

    @search.command(name = "bing")
    async def search_bing(self, ctx, *search: str):
        """Search with Bing"""
        # Note: bing command invokes this command
        await ctx.embed_reply(
            f"[Bing search for \"{' '.join(search)}\"]"
            f"(http://www.bing.com/search?q={'+'.join(search)})"
        )

    @commands.command()
    async def bing(self, ctx, *search: str):
        """Search with Bing"""
        if command := ctx.bot.get_command("search bing"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search bing command not found when bing command invoked"
            )

    @search.command(name = "duckduckgo")
    async def search_duckduckgo(self, ctx, *search: str):
        """Search with DuckDuckGo"""
        # Note: duckduckgo command invokes this command
        await ctx.embed_reply(
            f"[DuckDuckGo search for \"{' '.join(search)}\"]"
            f"(https://www.duckduckgo.com/?q={'+'.join(search)})"
        )

    @commands.command()
    async def duckduckgo(self, ctx, *search: str):
        """Search with DuckDuckGo"""
        if command := ctx.bot.get_command("search duckduckgo"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search duckduckgo command not found "
                "when duckduckgo command invoked"
            )

    @search.group(
        name = "google",
        case_insensitive = True, invoke_without_command = True
    )
    async def search_google(self, ctx, *, search: str):
        """Google search"""
        # Note: google command invokes this command
        await ctx.embed_reply(
            f"[Google search for \"{search}\"]"
            f"(https://www.google.com/search?q={search.replace(' ', '+')})"
        )

    @commands.group(
        name = "google",
        case_insensitive = True, invoke_without_command = True
    )
    async def google(self, ctx, *, search: str):
        """Google search"""
        if command := ctx.bot.get_command("search google"):
            await ctx.invoke(command, search = search)
        else:
            raise RuntimeError(
                "search google command not found when google command invoked"
            )

    @search_google.command(name = "images", aliases = ["image"])
    async def search_google_images(self, ctx, *, search: str):
        '''Google image search something'''
        if command := ctx.bot.get_command("image google"):
            await ctx.invoke(command, search = search)
        else:
            raise RuntimeError(
                "image google command not found "
                "when search google images command invoked"
            )

    @google.command(name = "images", aliases = ["image"])
    async def google_images(self, ctx, *, search: str):
        '''Google image search something'''
        if command := ctx.bot.get_command("image google"):
            await ctx.invoke(command, search = search)
        else:
            raise RuntimeError(
                "image google command not found "
                "when google images command invoked"
            )

    @search.command(name = "imfeelinglucky", aliases = ["im_feeling_lucky"])
    async def search_imfeelinglucky(self, ctx, *search: str):
        """First Google result of a search"""
        # Note: imfeelinglucky command invokes this command
        await ctx.embed_reply(
            f"[First Google result of \"{' '.join(search)}\"]"
            f"(https://www.google.com/search?btnI&q={'+'.join(search)})"
        )

    @commands.command(aliases = ["im_feeling_lucky"])
    async def imfeelinglucky(self, ctx, *search: str):
        """First Google result of a search"""
        if command := ctx.bot.get_command("search imfeelinglucky"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search imfeelinglucky command not found "
                "when imfeelinglucky command invoked"
            )

    @search.command(name = "imgur")
    async def search_imgur(self, ctx, *, search: str):
        '''Search images on Imgur'''
        if command := ctx.bot.get_command("imgur search"):
            await ctx.invoke(command, search = search)
        else:
            raise RuntimeError(
                "imgur search command not found "
                "when search imgur command invoked"
            )

    @search.command(name = "lma.ctfy")
    async def search_lma_ctfy(self, ctx, *search: str):
        """Let Me Ask.Com That For You"""
        # Note: lma.ctfy command invokes this command
        await ctx.embed_reply(
            f"[LMA.CTFY: \"{' '.join(search)}\"]"
            f"(http://lmgtfy.com/?s=k&q={'+'.join(search)})"
        )

    @commands.command(name = "lma.ctfy")
    async def lma_ctfy(self, ctx, *search: str):
        """Let Me Ask.Com That For You"""
        if command := ctx.bot.get_command("search lma.ctfy"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search lma.ctfy command not found "
                "when lma.ctfy command invoked"
            )

    @search.command(name = "lmaoltfy")
    async def search_lmaoltfy(self, ctx, *search: str):
        """Let Me AOL That For You"""
        # Note: lmaoltfy command invokes this command
        await ctx.embed_reply(
            f"[LMAOLTFY: \"{' '.join(search)}\"]"
            f"(http://lmgtfy.com/?s=a&q={'+'.join(search)})"
        )

    @commands.command()
    async def lmaoltfy(self, ctx, *search: str):
        """Let Me AOL That For You"""
        if command := ctx.bot.get_command("search lmaoltfy"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search lmaoltfy command not found "
                "when lmaoltfy command invoked"
            )

    @search.command(name = "lmatfy")
    async def search_lmatfy(self, ctx, *search: str):
        """Let Me Amazon That For You"""
        # Note: lmatfy command invokes this command
        await ctx.embed_reply(
            f"[LMATFY: \"{' '.join(search)}\"]"
            f"(http://lmatfy.co/?q={'+'.join(search)})"
        )

    @commands.command()
    async def lmatfy(self, ctx, *search: str):
        """Let Me Amazon That For You"""
        if command := ctx.bot.get_command("search lmatfy"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search lmatfy command not found when lmatfy command invoked"
            )

    @search.command(name = "lmbdtfy")
    async def search_lmbdtfy(self, ctx, *search: str):
        """Let Me Baidu That For You"""
        # Note: lmbdtfy command invokes this command
        await ctx.embed_reply(
            f"[LMBDTFY: \"{' '.join(search)}\"]"
            f"(https://lmbtfy.cn/?{'+'.join(search)})"
        )

    @commands.command()
    async def lmbdtfy(self, ctx, *search: str):
        """Let Me Baidu That For You"""
        if command := ctx.bot.get_command("search lmbdtfy"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search lmbdtfy command not found when lmbdtfy command invoked"
            )

    @search.command(name = "lmbtfy")
    async def search_lmbtfy(self, ctx, *search: str):
        """Let Me Bing That For You"""
        # Note: lmbtfy command invokes this command
        output = f"[LMBTFY: \"{' '.join(search)}\"](http://lmbtfy.com/?s=b&q={'+'.join(search)})\n"
        output += f"[LMBTFY: \"{' '.join(search)}\"](http://letmebingthatforyou.com/?q={'+'.join(search)})"
        await ctx.embed_reply(output)

    @commands.command()
    async def lmbtfy(self, ctx, *search: str):
        """Let Me Bing That For You"""
        if command := ctx.bot.get_command("search lmbtfy"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search lmbtfy command not found when lmbtfy command invoked"
            )

    @search.command(name = "lmdtfy")
    async def search_lmdtfy(self, ctx, *search: str):
        """Let Me DuckDuckGo That For You"""
        # Note: lmdtfy command invokes this command
        await ctx.embed_reply(
            f"[LMDTFY: \"{' '.join(search)}\"]"
            f"(http://lmgtfy.com/?s=d&q={'+'.join(search)})"
        )

    @commands.command()
    async def lmdtfy(self, ctx, *search: str):
        """Let Me DuckDuckGo That For You"""
        if command := ctx.bot.get_command("search lmdtfy"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search lmdtfy command not found when lmdtfy command invoked"
            )

    @search.command(name = "lmgtfy")
    async def search_lmgtfy(self, ctx, *search: str):
        """Let Me Google That For You"""
        # Note: lmgtfy command invokes this command
        await ctx.embed_reply(
            f"[LMGTFY: \"{' '.join(search)}\"]"
            f"(http://lmgtfy.com/?q={'+'.join(search)})"
        )

    @commands.command()
    async def lmgtfy(self, ctx, *search: str):
        """Let Me Google That For You"""
        if command := ctx.bot.get_command("search lmgtfy"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search lmgtfy command not found when lmgtfy command invoked"
            )

    @search.command(name = "lmytfy")
    async def search_lmytfy(self, ctx, *search: str):
        """Let Me Yahoo That For You"""
        # Note: lmytfy command invokes this command
        await ctx.embed_reply(
            f"[LMYTFY: \"{' '.join(search)}\"]"
            f"(http://lmgtfy.com/?s=y&q={'+'.join(search)})"
        )

    @commands.command()
    async def lmytfy(self, ctx, *search: str):
        """Let Me Yahoo That For You"""
        if command := ctx.bot.get_command("search lmytfy"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search lmytfy command not found when lmytfy command invoked"
            )

    @search.command(name = "startpage")
    async def search_startpage(self, ctx, *search: str):
        """Search with StartPage"""
        # Note: startpage command invokes this command
        await ctx.embed_reply(
            f"[StartPage search for \"{' '.join(search)}\"]"
            f"(https://www.startpage.com/do/search?query={'+'.join(search)})"
        )

    @commands.command()
    async def startpage(self, ctx, *search: str):
        """Search with StartPage"""
        if command := ctx.bot.get_command("search startpage"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search startpage command not found "
                "when startpage command invoked"
            )

    @search.group(
        name = "uesp", description = "[UESP](http://uesp.net/wiki/Main_Page)",
        case_insensitive = True, invoke_without_command = True
    )
    async def search_uesp(self, ctx, *, search: str):
        """Look something up on the Unofficial Elder Scrolls Pages"""
        # Note: uesp command invokes this command
        try:
            articles = await search_wiki(
                "https://en.uesp.net/", search,
                aiohttp_session = ctx.bot.aiohttp_session
            )
        except ValueError as e:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} {e}")
            return

        view = WikiArticlesView(articles)
        message = await ctx.reply(
            "",
            embed = await view.initial_embed(ctx),
            view = view
        )

        if ctx.interaction:
            # Fetch Message, as InteractionMessage token expires after 15 min.
            message = await message.fetch()
        view.message = message
        ctx.bot.views.append(view)

    @commands.group(
        description = "[UESP](http://uesp.net/wiki/Main_Page)",
        case_insensitive = True, invoke_without_command = True
    )
    async def uesp(self, ctx, *, search: str):
        """Look something up on the Unofficial Elder Scrolls Pages"""
        if command := ctx.bot.get_command("search uesp"):
            await ctx.invoke(command, search = search)
        else:
            raise RuntimeError(
                "search uesp command not found when uesp command invoked"
            )

    @search_uesp.command(name = "random")
    async def search_uesp_random(self, ctx):
        '''
        Random UESP page
        [UESP](http://uesp.net/wiki/Main_Page)
        '''
        # Note: random uesp command invokes this command
        # Note: uesp random command invokes this command
        try:
            article = await get_random_article(
                "https://en.uesp.net/",
                aiohttp_session = ctx.bot.aiohttp_session,
                random_namespaces = [0] + list(range(100, 152)) + [200, 201]
                # https://en.uesp.net/wiki/UESPWiki:Namespaces
                # https://en.uesp.net/w/api.php?action=query&meta=siteinfo&siprop=namespaces&formatversion=2
            )
        except ValueError as e:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} {e}")
        else:
            await ctx.embed_reply(
                title = article.title,
                title_url = article.url,
                description = article.extract,
                image_url = article.image_url,
                footer_icon_url = article.wiki.logo,
                footer_text = article.wiki.name
            )

    @uesp.command(name = "random")
    async def uesp_random(self, ctx):
        '''
        Random UESP page
        [UESP](http://uesp.net/wiki/Main_Page)
        '''
        if command := ctx.bot.get_command("search uesp random"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "search uesp random command not found "
                "when uesp random command invoked"
            )

    @search.group(
        name = "wikipedia", aliases = ["wiki"],
        case_insensitive = True, invoke_without_command = True
    )
    async def search_wikipedia(self, ctx, *, query: str):
        """
        Search for an article on Wikipedia

        Parameters
        ----------
        query
            Search query
        """
        # Note: /search wikipedia command invokes this command
        # Note: wikipedia command invokes this command
        try:
            articles = await search_wiki(
                "https://en.wikipedia.org/", query,
                aiohttp_session = ctx.bot.aiohttp_session
            )
        except ValueError as e:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} {e}")
            return

        view = WikiArticlesView(articles)
        message = await ctx.reply(
            "",
            embed = await view.initial_embed(ctx),
            view = view
        )

        if ctx.interaction:
            # Fetch Message, as InteractionMessage token expires after 15 min.
            message = await message.fetch()
        view.message = message
        ctx.bot.views.append(view)

    @app_commands.command(name = "wikipedia")
    async def slash_search_wikipedia(self, interaction, *, query: str):
        """
        Search for an article on Wikipedia

        Parameters
        ----------
        query
            Search query
        """
        ctx = await interaction.client.get_context(interaction)
        await ctx.defer()
        await self.wikipedia(ctx, query = query)

    @commands.group(
        aliases = ["wiki"],
        case_insensitive = True, invoke_without_command = True
    )
    async def wikipedia(self, ctx, *, query: str):
        """
        Search for an article on Wikipedia

        Parameters
        ----------
        query
            Search query
        """
        if command := ctx.bot.get_command("search wikipedia"):
            await ctx.invoke(command, query = query)
        else:
            raise RuntimeError(
                "search wikipedia command not found "
                "when wikipedia command invoked"
            )

    @search_wikipedia.command(name = "random")
    async def search_wikipedia_random(self, ctx):
        """Random Wikipedia article"""
        # Note: random wikipedia command invokes this command
        # Note: wikipedia random command invokes this command
        await ctx.defer()
        try:
            article = await get_random_article(
                "https://en.wikipedia.org/",
                aiohttp_session = ctx.bot.aiohttp_session
            )
        except ValueError as e:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} {e}")
        else:
            await ctx.embed_reply(
                title = article.title,
                title_url = article.url,
                description = article.extract,
                image_url = article.image_url,
                footer_icon_url = article.wiki.logo,
                footer_text = article.wiki.name
            )

    @wikipedia.command(name = "random")
    async def wikipedia_random(self, ctx):
        """Random Wikipedia article"""
        if command := ctx.bot.get_command("search wikipedia random"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "search wikipedia random command not found "
                "when wikipedia random command invoked"
            )

    @search.command(name = "fandom", aliases = ["wikia", "wikicities"])
    async def search_fandom(
        self, ctx,
        wiki: Literal["The Lord of the Rings", "Transformers Movie"], *,
        query: str
    ):
        """
        Search for an article on a Fandom wiki

        Parameters
        ----------
        query
            Search query
        wiki
            Fandom wiki to search
        """
        # Note: /search fandom command invokes this command
        # Note: fandom command invokes this command
        try:
            articles = await search_wiki(
                FANDOM_WIKIS[wiki], query,
                aiohttp_session = ctx.bot.aiohttp_session
            )
        except ValueError as e:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} {e}")
            return

        view = WikiArticlesView(articles)
        message = await ctx.reply(
            "",
            embed = await view.initial_embed(ctx),
            view = view
        )

        if ctx.interaction:
            # Fetch Message, as InteractionMessage token expires after 15 min.
            message = await message.fetch()
        view.message = message
        ctx.bot.views.append(view)

    @app_commands.command(name = "fandom")
    async def slash_search_fandom(
        self, interaction,
        wiki: Literal["The Lord of the Rings", "Transformers Movie"], *,
        query: str
    ):
        """
        Search for an article on a Fandom wiki

        Parameters
        ----------
        query
            Search query
        wiki
            Fandom wiki to search
        """
        ctx = await interaction.client.get_context(interaction)
        await ctx.defer()

        if command := ctx.bot.get_command("search fandom"):
            await ctx.invoke(command, wiki = wiki, query = query)
        else:
            raise RuntimeError(
                "search fandom command not found when fandom command invoked"
            )

    @commands.command(aliases = ["wikia", "wikicities"])
    async def fandom(
        self, ctx,
        wiki: Literal["The Lord of the Rings", "Transformers Movie"], *,
        query: str
    ):
        """
        Search for an article on a Fandom wiki

        Parameters
        ----------
        query
            Search query
        wiki
            Fandom wiki to search
        """
        if command := ctx.bot.get_command("search fandom"):
            await ctx.invoke(command, wiki = wiki, query = query)
        else:
            raise RuntimeError(
                "search fandom command not found when fandom command invoked"
            )

    @search.command(name = "tolkien")
    async def search_tolkien(self, ctx, *, query: str):
        """Search for an article on Tolkien Gateway"""
        # Note: tolkien command invokes this command
        try:
            articles = await search_wiki(
                "https://tolkiengateway.net/", query,
                aiohttp_session = ctx.bot.aiohttp_session
            )
        except ValueError as e:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} {e}")
            return

        view = WikiArticlesView(articles)
        message = await ctx.reply(
            "",
            embed = await view.initial_embed(ctx),
            view = view
        )

        if ctx.interaction:
            # Fetch Message, as InteractionMessage token expires after 15 min.
            message = await message.fetch()
        view.message = message
        ctx.bot.views.append(view)

    @commands.command()
    async def tolkien(self, ctx, *, query: str):
        """Search for an article on Tolkien Gateway"""
        if command := ctx.bot.get_command("search tolkien"):
            await ctx.invoke(command, query = query)
        else:
            raise RuntimeError(
                "search tolkien command not found when tolkien command invoked"
            )

    @search.group(
        name = "wolframalpha", aliases = ["wa", "wolfram_alpha"],
        case_insensitive = True, invoke_without_command = True
    )
    async def search_wolframalpha(self, ctx, *, search: str):
        """
        Wolfram|Alpha
        http://www.wolframalpha.com/examples/
        """
        # Note: wolframalpha command invokes this command
        await self.process_wolframalpha(ctx, search)

    @commands.group(
        aliases = ["wa", "wolfram_alpha"],
        case_insensitive = True, invoke_without_command = True
    )
    async def wolframalpha(self, ctx, *, search: str):
        """
        Wolfram|Alpha
        http://www.wolframalpha.com/examples/
        """
        if command := ctx.bot.get_command("search wolframalpha"):
            await ctx.invoke(command, search = search)
        else:
            raise RuntimeError(
                "search wolframalpha command not found "
                "when wolframalpha command invoked"
            )

    @search_wolframalpha.command(name = "location")
    async def search_wolframalpha_location(
        self, ctx, location: str, *, search: str
    ):
        '''Input location'''
        # Note: wolframalpha location command invokes this command
        await self.process_wolframalpha(ctx, search, location = location)

    @wolframalpha.command(name = "location")
    async def wolframalpha_location(self, ctx, location: str, *, search: str):
        '''Input location'''
        if command := ctx.bot.get_command("search wolframalpha location"):
            await ctx.invoke(command, location = location, search = search)
        else:
            raise RuntimeError(
                "search wolframalpha location command not found "
                "when wolframalpha location command invoked"
            )

    @app_commands.command(name = "wolframalpha")
    async def slash_search_wolframalpha(
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
        location = location or ctx.bot.mock_location
        try:
            result = ctx.bot.wolfram_alpha_client.query(
                query.strip('`'), ip = ctx.bot.mock_ip, location = location
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
                    didyoumean, ip = ctx.bot.mock_ip, location = location
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
            location = ctx.bot.mock_location
        try:
            result = ctx.bot.wolfram_alpha_client.query(search.strip('`'), ip = ctx.bot.mock_ip, location = location)
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
                result = ctx.bot.wolfram_alpha_client.query(didyoumean, ip = ctx.bot.mock_ip, location = location)
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

    @search.command(name = "yahoo")
    async def search_yahoo(self, ctx, *search: str):
        """Search with Yahoo"""
        # Note: yahoo command invokes this command
        await ctx.embed_reply(
            f"[Yahoo search for \"{' '.join(search)}\"]"
            f"(https://search.yahoo.com/search?q={'+'.join(search)})"
        )

    @commands.command()
    async def yahoo(self, ctx, *search: str):
        """Search with Yahoo"""
        if command := ctx.bot.get_command("search yahoo"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search yahoo command not found when yahoo command invoked"
            )

    @search.command(name = "youtube", aliases = ["yt"])
    async def search_youtube(self, ctx, *, search: str):
        '''Search for a YouTube video'''
        # Note: audio search command invokes this command
        ydl = youtube_dl.YoutubeDL(
            {"default_search": "auto", "noplaylist": True, "quiet": True}
        )
        func = functools.partial(ydl.extract_info, search, download = False)
        try:
            info = await ctx.bot.loop.run_in_executor(None, func)
        except youtube_dl.utils.DownloadError as e:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")
            return

        if not info.get("entries"):
            await ctx.embed_reply(f"{ctx.bot.error_emoji} Video not found")
            return

        await ctx.message.reply(info["entries"][0].get("webpage_url"))

