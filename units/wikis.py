
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
from pydantic import BaseModel

from .aiohttp_client import ensure_session
from .cache import async_cache
from .user_agent import SIMPLE_USER_AGENT as USER_AGENT

if TYPE_CHECKING:
    import aiohttp
    from collections.abc import Iterable
    from types import NotImplementedType


WIKIS = {
    "Disney": "https://disney.fandom.com/",
    "Foundation": "https://foundation.fandom.com/",
    "Genshin Impact": "https://genshin-impact.fandom.com/",
    "Harry Potter": "https://harrypotter.fandom.com/",
    "Marvel Cinematic Universe": "https://marvelcinematicuniverse.fandom.com/",
    "Memory Alpha": "https://memory-alpha.fandom.com/",
    "Minecraft": "https://minecraft.wiki",
    "Ni no Kuni: Cross Worlds": "https://ni-no-kuni-cross-worlds.fandom.com/",
    "Pirate101 (Central)": "https://www.pirate101central.com/",
    "Pirate101 (Fandom)": "https://pirate101.fandom.com/",
    "Pixar": "https://pixar.fandom.com/",
    "Redwall": "https://redwall.fandom.com/",
    "RuneScape": "https://runescape.wiki/",
    "Seinfeld": "https://seinfeld.fandom.com/",
    "Spiral Games Universe Lore (Wiki101)": "https://101universe.fandom.com/",
    "Stardew Valley": "https://stardewvalleywiki.com/",
    "Suits": "https://suits.fandom.com/",
    "The Hunger Games": "https://thehungergames.fandom.com/",
    "The Lord of the Rings": "https://lotr.fandom.com/",
    "The Newsroom": "https://thenewsroom.fandom.com/",
    "The West Wing": "https://westwing.fandom.com/",
    "Tolkien Gateway": "https://tolkiengateway.net/",
    "Transformers": "https://transformers.fandom.com/",
    "Transformers Movie": "https://michaelbaystransformers.fandom.com/",
    "Unofficial Elder Scrolls Pages (UESP)": "https://en.uesp.net/",
    "Valorant": "https://valorant.fandom.com/",
    "Wikipedia": "https://en.wikipedia.org/",
    # "Wizard101 (Central)": "https://wiki.wizard101central.com/",
    # 403 Cloudflare error when accessing ^ + wiki/api.php
    # Others encountering this:
    # https://github.com/R-unic/WizWikiAPI/commit/b6e55af833e6cf40e6152adbb9a72d6d5cf73632
    # https://github.com/R-unic/WizWikiAPI/issues/3
    "Wizard101 (Fandom)": "https://wizard101.fandom.com/",
}

OBSOLETE_WIKIS = {
    "Minecraft (Fandom)": "https://minecraft.fandom.com/",
    # Superseded by https://minecraft.wiki/
    # https://minecraft.fandom.com/wiki/Minecraft_Wiki:Moving_from_Fandom
    # https://minecraft.wiki/w/Minecraft_Wiki:Moving_from_Fandom
    "RuneScape (Fandom)": "https://runescape.fandom.com/",
    # Superseded by https://runescape.wiki/
    # https://secure.runescape.com/m=news/the-runescape-wiki
    # https://runescape.wiki/w/Forum:Leaving_Wikia
    # https://web.archive.org/web/20181104061135/https://runescape.fandom.com/wiki/Forum:Leaving_Wikia
    "Stardew Valley (Fandom)": "https://stardewvalley.fandom.com/",
    # Superseded by https://stardewvalleywiki.com/
    # https://www.stardewvalley.net/stardew-valley-wiki-ownership-change/
}


class WikiInfo(BaseModel):
    name: str
    favicon: str | None
    logo: str | None
    api_url: str
    article_path: str


class WikiArticle(BaseModel):
    title: str
    url: str
    extract: str | None
    image_url: str | None
    wiki: WikiInfo

    def __eq__(self, other: object) -> bool | NotImplementedType:
        if isinstance(other, WikiArticle):
            return self.url == other.url
        else:
            return NotImplemented

    def __hash__(self) -> int:
        return hash(self.url)


@async_cache(ignore_kwargs = "aiohttp_session")
async def get_api_endpoint(
    url: str, *, aiohttp_session: aiohttp.ClientSession | None = None
) -> str:
    async with ensure_session(
        aiohttp_session, default_user_agent = USER_AGENT
    ) as aiohttp_session:
        url = url.rstrip('/')
        for script_path in ('/w', "", "/wiki", "/mediawiki"):
            async with aiohttp_session.get(
                api_url := f"{url}{script_path}/api.php"
            ) as resp:
                if resp.status == 200:
                    return api_url

        raise RuntimeError(f"Unable to find wiki API endpoint URL for {url}")


async def get_article_beginning(
    article: WikiArticle,
    *,
    aiohttp_session: aiohttp.ClientSession | None = None
) -> str:
    async with ensure_session(
        aiohttp_session, default_user_agent = USER_AGENT
    ) as aiohttp_session:
        # https://www.mediawiki.org/wiki/API:Parsing_wikitext
        async with aiohttp_session.get(
            article.wiki.api_url,
            params = {
                "action": "parse", "page": article.title, "prop": "text",
                "format": "json"
            }
        ) as resp:
            data = await resp.json()

        text = BeautifulSoup(data["parse"]["text"]['*'], "lxml")
        if text.body and text.body.div:  # type: ignore[attribute-error]
            # https://github.com/google/pytype/issues/1867
            all_p = (
                text.body.div.find_all('p', recursive = False) or  # type: ignore[attribute-error]
                text.body.find_all('p', recursive = False)  # type: ignore[attribute-error]
            )
        else:
            raise RuntimeError("Unexpected wikitext HTML format")

        first_p = all_p[0]
        if first_p.aside:  # type: ignore[union-attr]
            first_p.aside.clear()  # type: ignore[union-attr]
        # https://bugs.launchpad.net/beautifulsoup/+bug/2122019
        beginning = first_p.get_text()

        for p in all_p:
            beginning += '\n' + p.get_text()
            if len(beginning) > 512:
                break

        beginning = re.sub(r"\n\s*\n", "\n\n", beginning)

        beginning = (
            beginning if len(beginning) <= 512 else beginning[:512] + '…'
        )
        # TODO: Update character limit?, Discord now uses 350

        return beginning


async def get_articles(
    url: str,
    titles: Iterable[str],
    *,
    aiohttp_session: aiohttp.ClientSession | None = None,
    ordered: bool = True,
    redirect: bool = True,
    remove_duplicate: bool = True
) -> list[WikiArticle]:
    async with ensure_session(
        aiohttp_session, default_user_agent = USER_AGENT
    ) as aiohttp_session:
        api_url = await get_api_endpoint(
            url, aiohttp_session = aiohttp_session
        )
        async with aiohttp_session.get(
            api_url, params = {
                # https://www.mediawiki.org/wiki/API:Query
                "action": "query",
                "prop": "info|extracts|pageimages|revisions",
                "titles": '|'.join(titles),
                "redirects": "",
                # https://www.mediawiki.org/wiki/API:Info
                "inprop": "url",
                # https://www.mediawiki.org/wiki/Extension:TextExtracts
                "exintro": "",
                "explaintext": "",
                # https://www.mediawiki.org/wiki/Extension:PageImages
                "pithumbsize": 9000,
                "pilicense": "any",
                # https://www.mediawiki.org/wiki/API:Revisions
                "rvprop": "content",
                # https://www.mediawiki.org/wiki/API:Siteinfo
                "meta": "siteinfo",
                "format": "json"
            }
            # TODO: Use exchars?
            # TODO: Use images prop?
        ) as resp:
            data = await resp.json()

        wiki_info = await get_wiki_info(data = data)

        if "pages" not in data["query"]:
            raise ValueError("Error")  # TODO: More descriptive error

        articles = {}
        invalid_pages = []

        for page in data["query"]["pages"].values():
            if "missing" in page:
                continue
            if "invalid" in page:
                invalid_pages.append(page)
                continue

            title = page["title"]

            extract = page.get("extract", "")
            extract = re.sub(r"\s+ \s+", ' ', extract)
            extract = extract if len(extract) <= 512 else extract[:512] + '…'
            # TODO: Update character limit?, Discord now uses 350

            article_path = wiki_info.article_path
            url = url.rstrip('/')
            replacement_texts = {}

            # https://www.mediawiki.org/wiki/Help:Links
            for link in re.finditer(
                (
                    r"\[\[([^\[\]]+?)\|([^\[\]]+?)\]\]" + r'|' +
                    r"\[\[([^\|]+?)\]\]" + r'|' +
                    r"(?<!\[)\[([^\[\]]+?)[ ]([^\[\]]+?)\](?!\])"
                ),
                page["revisions"][0]['*']
            ):
                if (target := link.group(1)) and (text := link.group(2)):
                    # Piped Internal Link
                    if target.startswith("Category:"):
                        # Ignore Category Links
                        continue
                    target = target.replace(' ', '_')
                    replacement_texts[re.escape(text)] = (
                        f"[{text}]({url}{article_path.replace('$1', target)})"
                    )
                elif (text := link.group(3)):  # Non-Piped Internal Link
                    target = text.replace(' ', '_')
                    replacement_texts[re.escape(text)] = (
                        f"[{text}]({url}{article_path.replace('$1', target)})"
                    )
                else:  # External Link
                    target = link.group(4)
                    text = link.group(5)
                    replacement_texts[re.escape(text)] = f"[{text}]({target})"

            extract = re.sub(
                '|'.join(replacement_texts.keys()),
                lambda match: replacement_texts[re.escape(match.group(0))],  # type: ignore[index]
                # https://github.com/python/mypy/issues/18738
                extract
            )

            # TODO: Handle bold (''' -> **) and italics ('' -> *)

            if (thumbnail := page.get("thumbnail")):
                thumbnail = thumbnail["source"].replace(
                    f"{thumbnail['width']}px", "1200px"
                )

            articles[title] = WikiArticle(
                title = title,
                url = page["fullurl"],  # TODO: Use canonicalurl?
                extract = extract or None,
                image_url = thumbnail,
                wiki = wiki_info
            )

        if redirect and (redirects := data["query"].get("redirects")):
            redirected_articles_list = await get_articles(
                url, [redirect["to"] for redirect in redirects],
                aiohttp_session = aiohttp_session,
                ordered = False, redirect = False, remove_duplicate = False
            )
            # TODO: Handle section links/tofragments
            redirected_articles_dict = {
                redirected_article.title: redirected_article
                for redirected_article in redirected_articles_list
            }
            for redirect_dict in redirects:
                if redirected_article := redirected_articles_dict.get(
                    redirect_dict["to"]
                ):
                    articles[redirect_dict["from"]] = redirected_article
                else:
                    pass  # TODO: Handle?

        if not articles:
            if invalid_pages:
                raise ValueError(
                    "Error(s):\n" + '\n'.join(
                        invalid_page["invalidreason"]
                        for invalid_page in invalid_pages
                    )
                )
            else:
                raise ValueError("Page not found")

        if ordered:
            ordered_articles = []
            unique_articles = set()

            for title in titles:
                try:
                    article = articles[title]
                except KeyError:
                    pass  # TODO: Handle?

                if remove_duplicate:
                    if article in unique_articles:
                        continue
                    else:
                        unique_articles.add(article)

                ordered_articles.append(article)

            return ordered_articles
        elif remove_duplicate:
            return list(set(articles.values()))
        else:
            return list(articles.values())


async def get_random_article(
    url: str,
    *,
    aiohttp_session: aiohttp.ClientSession | None = None,
    random_namespaces: Iterable[int | str] | int | str = 0
    # https://www.mediawiki.org/wiki/API:Random
    # https://www.mediawiki.org/wiki/Help:Namespaces
    # https://en.wikipedia.org/wiki/Wikipedia:Namespace
    # https://community.fandom.com/wiki/Help:Namespaces
) -> WikiArticle:
    async with ensure_session(
        aiohttp_session, default_user_agent = USER_AGENT
    ) as aiohttp_session:
        api_url = await get_api_endpoint(
            url, aiohttp_session = aiohttp_session
        )
        if not isinstance(random_namespaces, int | str):
            random_namespaces = '|'.join(
                str(namespace) for namespace in random_namespaces
            )
        async with aiohttp_session.get(
            api_url, params = {
                "action": "query", "list": "random",
                "rnnamespace": random_namespaces, "format": "json"
            }
        ) as resp:  # https://www.mediawiki.org/wiki/API:Random
            data = await resp.json()

        return (
            await get_articles(
                url, (data["query"]["random"][0]["title"],),
                aiohttp_session = aiohttp_session,
                ordered = False, remove_duplicate = False
            )
        )[0]


@async_cache(ignore_kwargs = "aiohttp_session")
async def get_wiki_info(
    *,
    aiohttp_session: aiohttp.ClientSession | None = None,
    data: dict | None = None,
    url: str | None = None,
) -> WikiInfo:
    if not data:
        if not url:
            raise TypeError("Either data or url must be provided")

        async with ensure_session(
            aiohttp_session, default_user_agent = USER_AGENT
        ) as aiohttp_session:
            api_url = await get_api_endpoint(
                url, aiohttp_session = aiohttp_session
            )
            async with aiohttp_session.get(
                api_url, params = {
                    "action": "query", "meta": "siteinfo",
                    "format": "json", "formatversion": 2
                }
            ) as resp:  # https://www.mediawiki.org/wiki/API:Siteinfo
                data = await resp.json()

    wiki_info = data["query"]["general"]

    if (
        (favicon := wiki_info.get("favicon")) and
        favicon.startswith("$wgUploadPath")
    ):
        # https://www.mediawiki.org/wiki/Manual:$wgUploadPath
        favicon = favicon.replace(
            "$wgUploadPath",
            f"{wiki_info['server']}{wiki_info['scriptpath']}/images"
        )
    if favicon and favicon.startswith("//"):
        favicon = "https:" + favicon

    if (logo := wiki_info.get("logo")) and logo.startswith("//"):
        logo = "https:" + logo

    if (
        api_url := f"{wiki_info['server']}{wiki_info['scriptpath']}/api.php"
    ).startswith("//"):
        api_url = "https:" + api_url

    return WikiInfo(
        name = wiki_info["sitename"],
        favicon = favicon,
        logo = logo,
        api_url = api_url,
        article_path = wiki_info["articlepath"]
    )


async def search_wiki(
    url: str,
    search: str,
    *,
    aiohttp_session: aiohttp.ClientSession | None = None
) -> list[WikiArticle]:
    # TODO: Use textwrap
    async with ensure_session(
        aiohttp_session, default_user_agent = USER_AGENT
    ) as aiohttp_session:
        api_url = await get_api_endpoint(
            url, aiohttp_session = aiohttp_session
        )
        async with aiohttp_session.get(
            api_url, params = {
                "action": "query", "list": "search", "srsearch": search,
                "srinfo": "suggestion", "srlimit": 20, "format": "json"
            }  # max exlimit is 20
        ) as resp:  # https://www.mediawiki.org/wiki/API:Search
            data = await resp.json()

        if results := data["query"]["search"]:
            titles = [result["title"] for result in results]
        elif suggestion := data["query"].get("searchinfo", {}).get(
            "suggestion"
        ):
            titles = [suggestion]
        else:
            raise ValueError("Page not found")

        return await get_articles(
            url, titles, aiohttp_session = aiohttp_session
        )

