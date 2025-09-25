
from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

from .aiohttp_client import ensure_session
from .user_agent import AIOHTTP_USER_AGENT as USER_AGENT

if TYPE_CHECKING:
    import aiohttp


# https://icanhazdadjoke.com
# https://icanhazdadjoke.com/api


class DadJoke(BaseModel):
    id: str
    joke: str

class DadJokeError(BaseModel):
    message: str
    status: int


async def get_random_dad_joke(
    *, aiohttp_session: aiohttp.ClientSession | None = None,
    joke_id: str | None = None
) -> DadJoke | DadJokeError:
    async with (
        ensure_session(aiohttp_session) as aiohttp_session,
        aiohttp_session.get(
            f"https://icanhazdadjoke.com/{'j/' + joke_id if joke_id else ''}",
            headers={
                "Accept": "application/json", "User-Agent": USER_AGENT
            }
        ) as response
    ):
        data = await response.json()
        return (
            DadJoke(**data) if data["status"] == 200 else DadJokeError(**data)
        )


def construct_dad_joke_image_url(joke_id: str) -> str:
    return f"https://icanhazdadjoke.com/j/{joke_id}.png"

