
from __future__ import annotations

from typing import TYPE_CHECKING

from .aiohttp_client import ensure_session
from .cache import async_cache

if TYPE_CHECKING:
    import aiohttp


@async_cache(ignore_kwargs = "aiohttp_session")
async def get_cat_breeds(
    *, aiohttp_session: aiohttp.ClientSession | None = None
) -> dict:
    async with (
        ensure_session(aiohttp_session) as aiohttp_session,
        aiohttp_session.get(
            "https://api.thecatapi.com/v1/breeds"
        ) as response
    ):
        data = await response.json()

    return {breed["name"]: breed for breed in data}


async def get_random_cat_image(
    *, aiohttp_session: aiohttp.ClientSession | None = None,
    breed: str | None = None
) -> str:
    async with (
        ensure_session(aiohttp_session) as aiohttp_session,
        aiohttp_session.get(
            "https://api.thecatapi.com/v1/images/search",
            params = {"breed_ids": breed_data["id"]} if breed and (
                breed_data := (
                    await get_cat_breeds(aiohttp_session = aiohttp_session)
                ).get(breed)
            ) else None
        ) as response
    ):
        return (await response.json())[0]["url"]

