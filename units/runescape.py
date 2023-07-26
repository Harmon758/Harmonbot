
from __future__ import annotations

from typing import TYPE_CHECKING

from .aiohttp_client import ensure_session

if TYPE_CHECKING:
    import aiohttp


async def get_item_id(
    item: str, *, aiohttp_session: aiohttp.ClientSession | None = None
) -> int:
    async with ensure_session(aiohttp_session) as aiohttp_session:
        # https://runescape.wiki/w/Application_programming_interface#Grand_Exchange_Database_API
        # https://www.mediawiki.org/wiki/API:Opensearch
        # TODO: Handle redirects?
        async with aiohttp_session.get(
            "https://runescape.wiki/api.php",
            params = {"action": "opensearch", "search": item}
        ) as resp:
            data = await resp.json()

        if not data[1]:
            raise ValueError("Item not found")

        for item in data[1]:
            # https://www.semantic-mediawiki.org/wiki/Help:Ask
            # https://www.semantic-mediawiki.org/wiki/Help:Inline_queries
            async with aiohttp_session.get(
                "https://runescape.wiki/api.php",
                params = {
                    "action": "ask",
                    "query": f"[[{item}]]|?Item_ID",
                    "format": "json"
                }
            ) as resp:
                data = await resp.json()

            if item_id := (
                list(
                    data["query"]["results"].values()
                )[0]["printouts"]["Item ID"]
            ):
                return item_id[0]

        raise ValueError(f"{item} is not an item")


async def get_ge_data(
    item: str,
    *,
    item_id: int | str | None  = None,
    aiohttp_session: aiohttp.ClientSession | None = None
) -> dict:
    async with ensure_session(aiohttp_session) as aiohttp_session:
        if item_id is None:
            item_id = await get_item_id(item, aiohttp_session = aiohttp_session)
        async with aiohttp_session.get(
            "https://services.runescape.com/m=itemdb_rs/api/catalogue/detail.json",
            params = {"item": item_id}
        ) as resp:
            if resp.status == 404:
                raise ValueError(f"{item} not found on the Grand Exchange")
            data = await resp.json(content_type = "text/html")
        return data["item"]


async def get_monster_data(
    monster: str, *, aiohttp_session: aiohttp.ClientSession | None = None
) -> dict:
    async with ensure_session(aiohttp_session) as aiohttp_session:
        async with aiohttp_session.get(
            "http://services.runescape.com/m=itemdb_rs/bestiary/beastSearch.json",
            params = {"term": monster}
        ) as resp:
            data = await resp.json(content_type = "text/html")
        if "value" not in data[0]:
            raise ValueError("Monster not found")
        async with aiohttp_session.get(
            "http://services.runescape.com/m=itemdb_rs/bestiary/beastData.json",
            params = {"beastid": data[0]["value"]}
        ) as resp:
            data = await resp.json(content_type = "text/html")
        return data

