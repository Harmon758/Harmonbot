
from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ValidationError

from .aiohttp_client import ensure_session
from .cache import async_cache

if TYPE_CHECKING:
    import aiohttp


class DotaPlayer(BaseModel):
    profile: DotaPlayerProfile
    rank_tier: int | None = None

class DotaPlayerProfile(BaseModel):
    account_id: int
    personaname: str | None = None
    name: str | None = None
    avatarfull: str | None = None
    profileurl: str | None = None
    loccountrycode: str | None = None

class DotaPlayerWL(BaseModel):
    win: int
    lose: int


@async_cache(ignore_kwargs = "aiohttp_session")
async def get_player(
    account_id: int | str, *,
    aiohttp_session: aiohttp.ClientSession | None = None
) -> DotaPlayer | None:
    async with (
        ensure_session(aiohttp_session) as aiohttp_session,
        aiohttp_session.get(
            f"https://api.opendota.com/api/players/{account_id}"
        ) as response
        # https://docs.opendota.com/#tag/players/operation/get_players_by_account_id
    ):
        data = await response.json()

    if "profile" not in data:
        raise ValueError("DotA 2 profile not found")

    try:
        return DotaPlayer(
            profile = DotaPlayerProfile(**data["profile"]),
            rank_tier = data.get("rank_tier")
        )
    except ValidationError as e:
        raise RuntimeError from e


@async_cache(ignore_kwargs = "aiohttp_session")
async def get_player_wl(
    account_id: int | str, *,
    aiohttp_session: aiohttp.ClientSession | None = None
) -> DotaPlayerWL:
    async with (
        ensure_session(aiohttp_session) as aiohttp_session,
        aiohttp_session.get(
            f"https://api.opendota.com/api/players/{account_id}/wl"
        ) as response
        # https://docs.opendota.com/#tag/players/operation/get_players_by_account_id_select_wl
    ):
        return DotaPlayerWL(**await response.json())

