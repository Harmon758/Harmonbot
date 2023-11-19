
from __future__ import annotations

from operator import itemgetter
import random
from typing import TYPE_CHECKING

from .aiohttp_client import ensure_session
from .cache import async_cache

if TYPE_CHECKING:
    import aiohttp


# https://status.d420.de/about
# Uptime check interval: 900s
TTL = 900


@async_cache(ignore_kwargs = "aiohttp_session", ttl = TTL)
async def get_healthy_rss_instances(
    *, aiohttp_session: aiohttp.ClientSession | None = None,
    exclude: list[str] | tuple[str, ...] = ()
) -> list[dict]:
    # TODO: Add User-Agent
    async with (
        ensure_session(aiohttp_session) as aiohttp_session,
        aiohttp_session.get("https://status.d420.de/api/v1/instances") as resp
    ):
        data = await resp.json()

    return [
        instance
        for instance in data["hosts"]
        if (
            instance["healthy"] and instance["rss"] and
            instance["url"] not in exclude
        )
    ]


async def get_best_healthy_rss_instance_url(
    *, aiohttp_session: aiohttp.ClientSession | None = None,
    exclude: list[str] | tuple[str, ...] = ()
) -> str:
    return min(
        await get_healthy_rss_instances(
            aiohttp_session = aiohttp_session, exclude = exclude
        ),
        key = itemgetter("ping_avg")
    )["url"]


async def get_random_healthy_rss_instance_url(
    *, aiohttp_session: aiohttp.ClientSession | None = None,
    exclude: list[str] | tuple[str, ...] = ()
) -> str:
    return random.choice(
        await get_healthy_rss_instances(
            aiohttp_session = aiohttp_session, exclude = exclude
        )
    )["url"]

