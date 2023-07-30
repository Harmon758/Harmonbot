
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
from pydantic import BaseModel

from .aiohttp_client import ensure_session
from .cache import async_cache

if TYPE_CHECKING:
    import aiohttp
    from collections.abc import Iterable
    from types import NotImplementedType


class WikiInfo(BaseModel):
    name: str
    logo: str
    api_url: str


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


@async_cache
async def get_api_endpoint(
    url: str, *, aiohttp_session: aiohttp.ClientSession | None = None
) -> str:
    # TODO: Add User-Agent
    async with ensure_session(aiohttp_session) as aiohttp_session:
        url = url.rstrip('/')
        for script_path in ('/w', ""):
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
    async with ensure_session(aiohttp_session) as aiohttp_session:
        # https://www.mediawiki.org/wiki/API:Parsing_wikitext
        async with aiohttp_session.get(
            article.wiki.api_url, params = {
                "action": "parse", "page": article.title, "prop": "text",
                "format": "json"
            }
        ) as resp:
            data = await resp.json()

        text = BeautifulSoup(data["parse"]["text"]['*'], "lxml")
        if text.body and text.body.div:
            p = text.body.div.find_all(
                'p', recursive = False
            )
        else:
            raise RuntimeError("Unexpected wikitext HTML format")

        first_p = p[0]
        if first_p.aside:
            first_p.aside.clear()
        beginning = first_p.get_text()

        if len(p) > 1:
            second_p = p[1]
            beginning += '\n' + second_p.get_text()

        if len(p) > 2:
            third_p = p[2]
            beginning += '\n' + third_p.get_text()

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
    remove_duplicate = True
) -> list[WikiArticle]:
    # TODO: Add User-Agent
    async with ensure_session(aiohttp_session) as aiohttp_session:
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

        wiki_info_data = data["query"]["general"]

        logo = wiki_info_data["logo"]
        if logo.startswith("//"):
            logo = "https:" + logo

        wiki_info = WikiInfo(
            name = wiki_info_data["sitename"],
            logo = logo,
            api_url = api_url
        )

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

            article_path = wiki_info_data["articlepath"]
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
                lambda match: replacement_texts[re.escape(match.group(0))],
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
):
    async with ensure_session(aiohttp_session) as aiohttp_session:
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


@async_cache
async def get_wiki_info(
    url: str, *, aiohttp_session: aiohttp.ClientSession | None = None
) -> WikiInfo:
    # TODO: Add User-Agent
    async with ensure_session(aiohttp_session) as aiohttp_session:
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
        logo = wiki_info["logo"]
        if logo.startswith("//"):
            logo = "https:" + logo

        return WikiInfo(
            name = wiki_info["sitename"],
            logo = logo,
            api_url = api_url
        )


async def search_wiki(
    url: str,
    search: str,
    *,
    aiohttp_session: aiohttp.ClientSession | None = None
) -> list[WikiArticle]:
    # TODO: Add User-Agent
    # TODO: Use textwrap
    async with ensure_session(aiohttp_session) as aiohttp_session:
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

