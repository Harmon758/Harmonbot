
from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from .aiohttp_client import ensure_session
from .cache import async_cache

if TYPE_CHECKING:
    import aiohttp


# https://web.archive.org/web/20191106152143/https://www.coindesk.com/api
# https://web.archive.org/web/20210802085504/https://www.coindesk.com/coindesk-api
ACKNOWLEDGEMENT = ACKNOWLEDGMENT = (
    "Powered by [CoinDesk](https://www.coindesk.com/price/bitcoin)"
)


class Currency(BaseModel):
    code: str = Field(alias = "currency")
    country: str


@async_cache(ignore_kwargs = "aiohttp_session")
async def get_supported_currencies(
    *, aiohttp_session: aiohttp.ClientSession | None = None
) -> list[Currency]:
    async with ensure_session(aiohttp_session) as aiohttp_session:
        async with aiohttp_session.get(
            "https://api.coindesk.com/v1/bpi/supported-currencies.json"
        ) as resp:
            data = await resp.json(content_type = "text/html")

    return [Currency.model_validate(currency) for currency in data]

