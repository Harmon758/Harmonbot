
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from aiohttp import ClientSession

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@asynccontextmanager
async def ensure_session(
    session: ClientSession | None, *, default_user_agent: str | None = None
) -> AsyncIterator[ClientSession]:
    if session_not_passed := (session is None):
        session = ClientSession()

    set_default_user_agent = False
    if default_user_agent is not None and "User-Agent" not in session.headers:
        session.headers["User-Agent"] = default_user_agent
        set_default_user_agent = True

    try:
        yield session
    finally:
        if set_default_user_agent:
            del session.headers["User-Agent"]
        if session_not_passed:
            await session.close()

