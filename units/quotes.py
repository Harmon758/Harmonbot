
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pydantic import BaseModel

from .aiohttp_client import ensure_session

if TYPE_CHECKING:
    import aiohttp


class Quote(BaseModel):
    text: str
    author: str
    link: str


async def get_random_quote(
    *, aiohttp_session: aiohttp.ClientSession | None = None
) -> Quote:
    # TODO: Add User-Agent
    async with ensure_session(aiohttp_session) as aiohttp_session:
        async with aiohttp_session.get(
            "http://api.forismatic.com/api/1.0/",
            params = {"method": "getQuote", "format": "json", "lang": "en"}
        ) as resp:
            try:
                data = await resp.json()
            except json.JSONDecodeError:  # Handle invalid JSON
                data = await resp.text()

                # Unescape single quotes
                data = data.replace("\\''", "'")
                data = data.replace("\\'", "'")

                # Escape double quotes
                before, quote_text, after_quote_text = data.partition(
                    "\"quoteText\":\""
                )
                text, quote_author, after = after_quote_text.partition(
                    "\", \"quoteAuthor\""
                )
                data = (
                    before + quote_text + text.replace('"', '\\"') +
                    quote_author + after
                )

                data = json.loads(data)

        return Quote(
            text = data["quoteText"],
            author = data["quoteAuthor"],
            link = data["quoteLink"]
        )

