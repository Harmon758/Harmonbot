
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


class WikiInfo(BaseModel):
    name: str
    logo: str


class WikiArticle(BaseModel):
    title: str
    url: str
    extract: str
    image_url: str | None
    wiki: WikiInfo | None


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
            logo = logo
        )


async def search_wiki(
    url: str,
    search: str,
    *,
    aiohttp_session: aiohttp.ClientSession | None = None,
    random: bool = False,
    random_namespaces: Iterable[int | str] | int | str = 0,
    # https://www.mediawiki.org/wiki/API:Random
    # https://www.mediawiki.org/wiki/Help:Namespaces
    # https://en.wikipedia.org/wiki/Wikipedia:Namespace
    # https://community.fandom.com/wiki/Help:Namespaces
    redirect: bool = True,
    wiki_info: bool = True
) -> WikiArticle:
    # TODO: Add User-Agent
    # TODO: Use textwrap
    async with ensure_session(aiohttp_session) as aiohttp_session:
        api_url = await get_api_endpoint(
            url, aiohttp_session = aiohttp_session
        )
        if random:
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

            search = data["query"]["random"][0]["title"]
        else:
            async with aiohttp_session.get(
                api_url, params = {
                    "action": "query", "list": "search", "srsearch": search,
                    "srinfo": "suggestion", "srlimit": 1, "format": "json"
                }
            ) as resp:  # https://www.mediawiki.org/wiki/API:Search
                data = await resp.json()

            if search := data["query"]["search"]:
                search = search[0]["title"]
            elif not (
                search := data["query"].get("searchinfo", {}).get("suggestion")
            ):
                raise ValueError("Page not found")

        async with aiohttp_session.get(
            api_url, params = {
                "action": "query", "redirects": "",
                "prop": "info|extracts|pageimages", "titles": search,
                "inprop": "url", "exintro": "", "explaintext": "",
                "pithumbsize": 9000, "pilicense": "any", "format": "json"
            }
            # TODO: Use exchars?
            # TODO: Use images prop?
            # TODO: Use revisions prop and content rvprop?
            #       for links, italics, bold
        ) as resp:  # https://www.mediawiki.org/wiki/API:Query
            data = await resp.json()

        if "pages" not in data["query"]:
            raise ValueError("Error")  # TODO: More descriptive error

        page_id = list(data["query"]["pages"].keys())[0]
        page = data["query"]["pages"][page_id]

        if "missing" in page:
            raise ValueError("Page not found")
        if "invalid" in page:
            raise ValueError(page["invalidreason"])

        if redirect and "redirects" in data["query"]:
            return await search_wiki(
                url, data["query"]["redirects"][-1]["to"],
                aiohttp_session = aiohttp_session,
                redirect = False
            )
            # TODO: Handle section links/tofragments

        if "extract" in page:
            extract = re.sub(
                r"\s+ \s+", ' ',
                (
                    page["extract"] if len(page["extract"]) <= 512
                    else page["extract"][:512] + '…'
                )
            )
        else:
            # https://www.mediawiki.org/wiki/API:Parsing_wikitext
            async with aiohttp_session.get(
                api_url, params = {
                    "action": "parse", "page": search, "prop": "text",
                    "format": "json"
                }
            ) as resp:
                data = await resp.json()

            p = BeautifulSoup(
                data["parse"]["text"]['*'], "lxml"
            ).body.div.find_all(
                'p', recursive = False
            )

            first_p = p[0]
            if first_p.aside:
                first_p.aside.clear()
            extract = first_p.get_text()

            if len(p) > 1:
                second_p = p[1]
                extract += '\n' + second_p.get_text()

            extract = re.sub(
                r"\n\s*\n", "\n\n",
                (
                    extract if len(extract) <= 512
                    else extract[:512] + '…'
                )
            )

        thumbnail = page.get("thumbnail")

        return WikiArticle(
            title = page["title"],
            url = page["fullurl"],  # TODO: Use canonicalurl?
            extract = extract,
            image_url = (
                thumbnail["source"].replace(
                    f"{thumbnail['width']}px", "1200px"
                ) if thumbnail else None
            ),
            wiki = (
                await get_wiki_info(url, aiohttp_session = aiohttp_session)
                if wiki_info else None
            )
        )

