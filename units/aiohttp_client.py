
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from aiohttp import ClientSession

if TYPE_CHECKING:
    from collections.abc import Iterator


@asynccontextmanager
async def ensure_session(
    session: ClientSession | None
) -> Iterator[ClientSession]:
    if session_not_passed := (session is None):
        session = ClientSession()
    try:
        yield session
    finally:
        if session_not_passed:
            await session.close()

