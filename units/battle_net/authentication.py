
import os

import aiohttp

from ..aiohttp_client import ensure_session
from ..cache import async_cache


BATTLE_NET_CLIENT_ID = BLIZZARD_CLIENT_ID = (
    os.getenv("BATTLE_NET_CLIENT_ID") or os.getenv("BLIZZARD_CLIENT_ID")
)
BATTLE_NET_CLIENT_SECRET = BLIZZARD_CLIENT_SECRET = (
    os.getenv("BATTLE_NET_CLIENT_SECRET") or
    os.getenv("BLIZZARD_CLIENT_SECRET")
)


@async_cache(ignore_kwargs = "aiohttp_session", ttl = 86000)
async def request_access_token(
    *, aiohttp_session: aiohttp.ClientSession | None = None
) -> str:
    async with (
        ensure_session(aiohttp_session) as aiohttp_session,
        aiohttp_session.post(
            "https://oauth.battle.net/token",
            auth = aiohttp.BasicAuth(
                BATTLE_NET_CLIENT_ID, BATTLE_NET_CLIENT_SECRET
            ),
            data = {"grant_type": "client_credentials"}
        ) as resp
    ):
        return (await resp.json())["access_token"]

