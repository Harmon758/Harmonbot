
from __future__ import annotations

from discord import app_commands
from discord.ext import commands

import functools
from typing import Optional, TYPE_CHECKING

import youtube_dl

from units.wikis import get_random_article, search_wiki, WIKIS
from units import wolfram_alpha
from utilities import checks
from utilities.menu_sources import WolframAlphaSource
from utilities.paginators import ButtonPaginator
from utilities.views import WikiArticlesView

if TYPE_CHECKING:
    from utilities.context import Context


async def setup(bot):
    await bot.add_cog(Search())


class Search(commands.Cog):
    """Search"""

    async def cog_check(self, ctx):
        return await checks.not_forbidden().predicate(ctx)

    @commands.hybrid_group(case_insensitive = True)
    @app_commands.allowed_installs(guilds = True, users = True)
    @app_commands.allowed_contexts(
        guilds = True, dms = True, private_channels = True
    )
    async def search(self, ctx: Context):
        """
        Search things
        All search subcommands are also commands
        """
        await ctx.embed_reply("\N{WHITE QUESTION MARK ORNAMENT} Search what?")

    @search.command(name = "amazon", with_app_command = False)
    async def search_amazon(self, ctx: Context, *search: str):
        """Search with Amazon"""
        # Note: amazon command invokes this command
        await ctx.embed_reply(
            f"[Amazon search for \"{' '.join(search)}\"]"
            f"(https://www.amazon.com/s?k={'+'.join(search)})"
        )

    @commands.command()
    async def amazon(self, ctx: Context, *search: str):
        """Search with Amazon"""
        if command := ctx.bot.get_command("search amazon"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search amazon command not found when amazon command invoked"
            )

    @search.command(name = "aol", with_app_command = False)
    async def search_aol(self, ctx: Context, *search: str):
        """Search with AOL"""
        # Note: aol command invokes this command
        await ctx.embed_reply(
            f"[AOL search for \"{' '.join(search)}\"]"
            f"(https://search.aol.com/aol/search?q={'+'.join(search)})"
        )

    @commands.command()
    async def aol(self, ctx: Context, *search: str):
        """Search with AOL"""
        if command := ctx.bot.get_command("search aol"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search aol command not found when aol command invoked"
            )

    @search.command(name = "ask.com", with_app_command = False)
    async def search_ask_com(self, ctx: Context, *search: str):
        """Search with Ask.com"""
        # Note: ask.com command invokes this command
        await ctx.embed_reply(
            f"[Ask.com search for \"{' '.join(search)}\"]"
            f"(http://www.ask.com/web?q={'+'.join(search)})"
        )

    @commands.command(name = "ask.com")
    async def ask_com(self, ctx: Context, *search: str):
        """Search with Ask.com"""
        if command := ctx.bot.get_command("search ask.com"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search ask.com command not found when ask.com command invoked"
            )

    @search.command(name = "baidu", with_app_command = False)
    async def search_baidu(self, ctx: Context, *search: str):
        """Search with Baidu"""
        # Note: baidu command invokes this command
        await ctx.embed_reply(
            f"[Baidu search for \"{' '.join(search)}\"]"
            f"(http://www.baidu.com/s?wd={'+'.join(search)})"
        )

    @commands.command()
    async def baidu(self, ctx: Context, *search: str):
        """Search with Baidu"""
        if command := ctx.bot.get_command("search baidu"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search baidu command not found when baidu command invoked"
            )

    @search.command(name = "bing", with_app_command = False)
    async def search_bing(self, ctx: Context, *search: str):
        """Search with Bing"""
        # Note: bing command invokes this command
        await ctx.embed_reply(
            f"[Bing search for \"{' '.join(search)}\"]"
            f"(http://www.bing.com/search?q={'+'.join(search)})"
        )

    @commands.command()
    async def bing(self, ctx: Context, *search: str):
        """Search with Bing"""
        if command := ctx.bot.get_command("search bing"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search bing command not found when bing command invoked"
            )

    @search.command(name = "duckduckgo", with_app_command = False)
    async def search_duckduckgo(self, ctx: Context, *search: str):
        """Search with DuckDuckGo"""
        # Note: duckduckgo command invokes this command
        await ctx.embed_reply(
            f"[DuckDuckGo search for \"{' '.join(search)}\"]"
            f"(https://www.duckduckgo.com/?q={'+'.join(search)})"
        )

    @commands.command()
    async def duckduckgo(self, ctx: Context, *search: str):
        """Search with DuckDuckGo"""
        if command := ctx.bot.get_command("search duckduckgo"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search duckduckgo command not found "
                "when duckduckgo command invoked"
            )

    @search.group(
        name = "google", case_insensitive = True, with_app_command = False
    )
    async def search_google(self, ctx: Context, *, search: str):
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
    async def google(self, ctx: Context, *, search: str):
        """Google search"""
        if command := ctx.bot.get_command("search google"):
            await ctx.invoke(command, search = search)
        else:
            raise RuntimeError(
                "search google command not found when google command invoked"
            )

    @search_google.command(
        name = "images", aliases = ["image"], with_app_command = False
    )
    async def search_google_images(self, ctx: Context, *, search: str):
        '''Google image search something'''
        if command := ctx.bot.get_command("image google"):
            await ctx.invoke(command, search = search)
        else:
            raise RuntimeError(
                "image google command not found "
                "when search google images command invoked"
            )

    @google.command(name = "images", aliases = ["image"])
    async def google_images(self, ctx: Context, *, search: str):
        '''Google image search something'''
        if command := ctx.bot.get_command("image google"):
            await ctx.invoke(command, search = search)
        else:
            raise RuntimeError(
                "image google command not found "
                "when google images command invoked"
            )

    @search.command(
        name = "imfeelinglucky", aliases = ["im_feeling_lucky"],
        with_app_command = False
    )
    async def search_imfeelinglucky(self, ctx: Context, *search: str):
        """First Google result of a search"""
        # Note: imfeelinglucky command invokes this command
        await ctx.embed_reply(
            f"[First Google result of \"{' '.join(search)}\"]"
            f"(https://www.google.com/search?btnI&q={'+'.join(search)})"
        )

    @commands.command(aliases = ["im_feeling_lucky"])
    async def imfeelinglucky(self, ctx: Context, *search: str):
        """First Google result of a search"""
        if command := ctx.bot.get_command("search imfeelinglucky"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search imfeelinglucky command not found "
                "when imfeelinglucky command invoked"
            )

    @search.command(name = "imgur", with_app_command = False)
    async def search_imgur(self, ctx: Context, *, search: str):
        '''Search images on Imgur'''
        if command := ctx.bot.get_command("imgur search"):
            await ctx.invoke(command, search = search)
        else:
            raise RuntimeError(
                "imgur search command not found "
                "when search imgur command invoked"
            )

    @search.command(name = "lma.ctfy", with_app_command = False)
    async def search_lma_ctfy(self, ctx: Context, *search: str):
        """Let Me Ask.Com That For You"""
        # Note: lma.ctfy command invokes this command
        await ctx.embed_reply(
            f"[LMA.CTFY: \"{' '.join(search)}\"]"
            f"(http://lmgtfy.com/?s=k&q={'+'.join(search)})"
        )

    @commands.command(name = "lma.ctfy")
    async def lma_ctfy(self, ctx: Context, *search: str):
        """Let Me Ask.Com That For You"""
        if command := ctx.bot.get_command("search lma.ctfy"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search lma.ctfy command not found "
                "when lma.ctfy command invoked"
            )

    @search.command(name = "lmaoltfy", with_app_command = False)
    async def search_lmaoltfy(self, ctx: Context, *search: str):
        """Let Me AOL That For You"""
        # Note: lmaoltfy command invokes this command
        await ctx.embed_reply(
            f"[LMAOLTFY: \"{' '.join(search)}\"]"
            f"(http://lmgtfy.com/?s=a&q={'+'.join(search)})"
        )

    @commands.command()
    async def lmaoltfy(self, ctx: Context, *search: str):
        """Let Me AOL That For You"""
        if command := ctx.bot.get_command("search lmaoltfy"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search lmaoltfy command not found "
                "when lmaoltfy command invoked"
            )

    @search.command(name = "lmatfy", with_app_command = False)
    async def search_lmatfy(self, ctx: Context, *search: str):
        """Let Me Amazon That For You"""
        # Note: lmatfy command invokes this command
        await ctx.embed_reply(
            f"[LMATFY: \"{' '.join(search)}\"]"
            f"(http://lmatfy.co/?q={'+'.join(search)})"
        )

    @commands.command()
    async def lmatfy(self, ctx: Context, *search: str):
        """Let Me Amazon That For You"""
        if command := ctx.bot.get_command("search lmatfy"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search lmatfy command not found when lmatfy command invoked"
            )

    @search.command(name = "lmbdtfy", with_app_command = False)
    async def search_lmbdtfy(self, ctx: Context, *search: str):
        """Let Me Baidu That For You"""
        # Note: lmbdtfy command invokes this command
        await ctx.embed_reply(
            f"[LMBDTFY: \"{' '.join(search)}\"]"
            f"(https://lmbtfy.cn/?{'+'.join(search)})"
        )

    @commands.command()
    async def lmbdtfy(self, ctx: Context, *search: str):
        """Let Me Baidu That For You"""
        if command := ctx.bot.get_command("search lmbdtfy"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search lmbdtfy command not found when lmbdtfy command invoked"
            )

    @search.command(name = "lmbtfy", with_app_command = False)
    async def search_lmbtfy(self, ctx: Context, *search: str):
        """Let Me Bing That For You"""
        # Note: lmbtfy command invokes this command
        output = f"[LMBTFY: \"{' '.join(search)}\"](http://lmbtfy.com/?s=b&q={'+'.join(search)})\n"
        output += f"[LMBTFY: \"{' '.join(search)}\"](http://letmebingthatforyou.com/?q={'+'.join(search)})"
        await ctx.embed_reply(output)

    @commands.command()
    async def lmbtfy(self, ctx: Context, *search: str):
        """Let Me Bing That For You"""
        if command := ctx.bot.get_command("search lmbtfy"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search lmbtfy command not found when lmbtfy command invoked"
            )

    @search.command(name = "lmdtfy", with_app_command = False)
    async def search_lmdtfy(self, ctx: Context, *search: str):
        """Let Me DuckDuckGo That For You"""
        # Note: lmdtfy command invokes this command
        await ctx.embed_reply(
            f"[LMDTFY: \"{' '.join(search)}\"]"
            f"(http://lmgtfy.com/?s=d&q={'+'.join(search)})"
        )

    @commands.command()
    async def lmdtfy(self, ctx: Context, *search: str):
        """Let Me DuckDuckGo That For You"""
        if command := ctx.bot.get_command("search lmdtfy"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search lmdtfy command not found when lmdtfy command invoked"
            )

    @search.command(name = "lmgtfy", with_app_command = False)
    async def search_lmgtfy(self, ctx: Context, *search: str):
        """Let Me Google That For You"""
        # Note: lmgtfy command invokes this command
        await ctx.embed_reply(
            f"[LMGTFY: \"{' '.join(search)}\"]"
            f"(http://lmgtfy.com/?q={'+'.join(search)})"
        )

    @commands.command()
    async def lmgtfy(self, ctx: Context, *search: str):
        """Let Me Google That For You"""
        if command := ctx.bot.get_command("search lmgtfy"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search lmgtfy command not found when lmgtfy command invoked"
            )

    @search.command(name = "lmytfy", with_app_command = False)
    async def search_lmytfy(self, ctx: Context, *search: str):
        """Let Me Yahoo That For You"""
        # Note: lmytfy command invokes this command
        await ctx.embed_reply(
            f"[LMYTFY: \"{' '.join(search)}\"]"
            f"(http://lmgtfy.com/?s=y&q={'+'.join(search)})"
        )

    @commands.command()
    async def lmytfy(self, ctx: Context, *search: str):
        """Let Me Yahoo That For You"""
        if command := ctx.bot.get_command("search lmytfy"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search lmytfy command not found when lmytfy command invoked"
            )

    @search.command(name = "startpage", with_app_command = False)
    async def search_startpage(self, ctx: Context, *search: str):
        """Search with StartPage"""
        # Note: startpage command invokes this command
        await ctx.embed_reply(
            f"[StartPage search for \"{' '.join(search)}\"]"
            f"(https://www.startpage.com/do/search?query={'+'.join(search)})"
        )

    @commands.command()
    async def startpage(self, ctx: Context, *search: str):
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
        case_insensitive = True, with_app_command = False
    )
    async def search_uesp(self, ctx: Context, *, search: str):
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
        view.message = await ctx.reply(
            "",
            embed = await view.initial_embed(ctx),
            view = view
        )
        ctx.bot.views.append(view)

    @commands.group(
        description = "[UESP](http://uesp.net/wiki/Main_Page)",
        case_insensitive = True, invoke_without_command = True
    )
    async def uesp(self, ctx: Context, *, search: str):
        """Look something up on the Unofficial Elder Scrolls Pages"""
        if command := ctx.bot.get_command("search uesp"):
            await ctx.invoke(command, search = search)
        else:
            raise RuntimeError(
                "search uesp command not found when uesp command invoked"
            )

    @search_uesp.command(name = "random", with_app_command = False)
    async def search_uesp_random(self, ctx: Context):
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
    async def uesp_random(self, ctx: Context):
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

    @commands.group(
        aliases = ["wiki"],
        case_insensitive = True, invoke_without_command = True
    )
    async def wikipedia(self, ctx: Context, *, query: str):
        """
        Search for an article on Wikipedia

        Parameters
        ----------
        query
            Search query
        """
        if command := ctx.bot.get_command("search wiki"):
            await ctx.invoke(command, query = query)
        else:
            raise RuntimeError(
                "search wiki command not found when wikipedia command invoked"
            )

    @wikipedia.command(name = "random")
    async def wikipedia_random(self, ctx: Context):
        """Random Wikipedia article"""
        if command := ctx.bot.get_command("random wikipedia"):
            await ctx.invoke(command)
        else:
            raise RuntimeError(
                "random wikipedia command not found "
                "when wikipedia random command invoked"
            )

    @search.command(
        name = "wiki",
        aliases = ["fandom", "tolkien", "wikia", "wikicities", "wikipedia"]
    )
    async def search_wiki(
        self, ctx: Context, wiki: str = "Wikipedia", *, query: str
    ):
        """
        Search for an article on a wiki

        Parameters
        ----------
        query
            Search query
        wiki
            Wiki to search
            (Defaults to Wikipedia)
        """
        # Note: fandom command invokes this command
        # Note: genshin_impact wiki command invokes this command
        # Note: tolkien command invokes this command
        # Note: wikipedia command invokes this command
        await ctx.defer()
        try:
            articles = await search_wiki(
                WIKIS[wiki], query, aiohttp_session = ctx.bot.aiohttp_session
            )
        except KeyError:
            await ctx.embed_reply(
                f"{ctx.bot.error_emoji} Unknown wiki: `{wiki}`"
            )
            return
        except ValueError as e:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} {e}")
            return

        view = WikiArticlesView(articles)
        view.message = await ctx.reply(
            "",
            embed = await view.initial_embed(ctx),
            view = view
        )
        ctx.bot.views.append(view)

    @search_wiki.autocomplete("wiki")
    async def search_wiki_wiki_autocomplete(self, interaction, current):
        current = current.lower()

        primary_matches = set()
        secondary_matches = set()

        for wiki in WIKIS:
            if wiki.lower().startswith(current):
                primary_matches.add(wiki)
            elif current in wiki.lower():
                secondary_matches.add(wiki)

        matches = sorted(primary_matches) + sorted(secondary_matches)

        return [
            app_commands.Choice(name = match, value = match)
            for match in matches[:25]
        ]

    @commands.command(aliases = ["wikia", "wikicities"])
    async def fandom(self, ctx: Context, wiki: str, *, query: str):
        """
        Search for an article on a Fandom wiki

        Parameters
        ----------
        query
            Search query
        wiki
            Fandom wiki to search
        """
        if command := ctx.bot.get_command("search wiki"):
            await ctx.invoke(command, wiki = wiki, query = query)
        else:
            raise RuntimeError(
                "search wiki command not found when fandom command invoked"
            )

    @commands.command()
    async def tolkien(self, ctx: Context, *, query: str):
        """Search for an article on Tolkien Gateway"""
        if command := ctx.bot.get_command("search wiki"):
            await ctx.invoke(command, wiki = "Tolkien Gateway", query = query)
        else:
            raise RuntimeError(
                "search wiki command not found when tolkien command invoked"
            )

    @search.command(
        name = "wolframalpha", aliases = ["wa", "wolfram_alpha"],
        case_insensitive = True
    )
    async def search_wolframalpha(
        self, ctx, location: Optional[str], *, query: str  # noqa: UP045 (non-pep604-annotation-optional)
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
        # Note: wolframalpha command invokes this command
        # TODO: Option to display all results?, single image?
        # TODO: Plaintext option - pod.title with subpod.plaintext
        # TODO: Include examples? - https://www.wolframalpha.com/examples/
        await ctx.defer()
        location = location or ctx.bot.mock_location
        try:
            result = await ctx.bot.wolfram_alpha_client.aquery(
                query.strip('`'), ip = ctx.bot.mock_ip, location = location
            )
            # TODO: Handle httpx.ReadTimeout / httpcore.ReadTimeout ?
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
                result = await ctx.bot.wolfram_alpha_client.aquery(
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
                ctx,
                WolframAlphaSource(
                    result.pods,
                    didyoumean = didyoumean,
                    timedout = result.timedout
                ),
                selection = [pod.title for pod in result.pods]
            )
            await paginator.start()
            ctx.bot.views.append(paginator)
        elif result.timedout:
            await ctx.embed_reply("Standard computation time exceeded")
        else:
            await ctx.embed_reply(f"{ctx.bot.error_emoji} No results found")

    @commands.command(aliases = ["wa", "wolfram_alpha"])
    async def wolframalpha(self, ctx, *, query: str):
        """
        Query Wolfram|Alpha

        Parameters
        ----------
        query
            Search query
        """
        if command := ctx.bot.get_command("search wolframalpha"):
            await ctx.invoke(command, location = None, query = query)
        else:
            raise RuntimeError(
                "search wolframalpha command not found "
                "when wolframalpha command invoked"
            )

    @search.command(name = "yahoo", with_app_command = False)
    async def search_yahoo(self, ctx: Context, *search: str):
        """Search with Yahoo"""
        # Note: yahoo command invokes this command
        await ctx.embed_reply(
            f"[Yahoo search for \"{' '.join(search)}\"]"
            f"(https://search.yahoo.com/search?q={'+'.join(search)})"
        )

    @commands.command()
    async def yahoo(self, ctx: Context, *search: str):
        """Search with Yahoo"""
        if command := ctx.bot.get_command("search yahoo"):
            await ctx.invoke(command, *search)
        else:
            raise RuntimeError(
                "search yahoo command not found when yahoo command invoked"
            )

    @search.command(
        name = "youtube", aliases = ["yt"], with_app_command = False
    )
    async def search_youtube(self, ctx, *, search: str):
        '''Search for a YouTube video'''
        # Note: youtube search command invokes this command
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

