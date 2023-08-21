
from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from . import API_BASE_URL
from ..aiohttp_client import ensure_session
from ..cache import async_cache

if TYPE_CHECKING:
    import aiohttp


class Character(BaseModel):
    model_config = ConfigDict(extra = "allow")

    name: str
    title: str | None = None
    vision: str
    weapon: str
    nation: str
    affiliation: str
    rarity: int
    constellation: str
    birthday: str | None = None
    description: str
    combat_talents: list[CombatTalent] = Field(alias = "skillTalents")
    passive_talents: list[PassiveTalent] = Field(alias = "passiveTalents")
    constellations: list[Constellation]
    # vision_key
    # weapon_type


class CombatTalent(BaseModel):
    name: str
    unlock: str
    description: str
    upgrades: list[CombatTalentUpgrades] | None = None
    type: str | None = None


class CombatTalentUpgrades(BaseModel):
    name: str
    value: str


class PassiveTalent(BaseModel):
    name: str
    unlock: str
    description: str
    level: int | None = None


class Constellation(BaseModel):
    name: str
    unlock: str
    description: str
    level: int


@async_cache(ignore_kwargs = "aiohttp_session")
async def get_all_characters(
    *, aiohttp_session: aiohttp.ClientSession | None = None
) -> list[Character]:
    async with ensure_session(aiohttp_session) as aiohttp_session:
        async with aiohttp_session.get(
            f"{API_BASE_URL}/characters/all"
        ) as resp:
            data = await resp.json()

    try:
        return [Character.model_validate(character) for character in data]
    except ValidationError as e:
        raise RuntimeError from e


@async_cache(ignore_kwargs = "aiohttp_session")
async def get_character(
    name: str, *, aiohttp_session: aiohttp.ClientSession | None = None
) -> Character:
    async with ensure_session(aiohttp_session) as aiohttp_session:
        async with aiohttp_session.get(
            f"{API_BASE_URL}/characters/{name.lower().replace(' ', '-')}"
        ) as resp:
            if resp.status == 404:
                raise ValueError("Character not found")

            data = await resp.json()

    try:
        return Character.model_validate(data)
    except ValidationError as e:
        raise RuntimeError from e


@async_cache(ignore_kwargs = "aiohttp_session")
async def get_character_images(
    name: str, *, aiohttp_session: aiohttp.ClientSession | None = None
) -> list[str]:
    async with ensure_session(aiohttp_session) as aiohttp_session:
        async with aiohttp_session.get(
            f"{API_BASE_URL}/characters/{name.lower().replace(' ', '-')}/list"
        ) as resp:
            return await resp.json()


@async_cache(ignore_kwargs = "aiohttp_session")
async def get_characters(
    *, aiohttp_session: aiohttp.ClientSession | None = None
) -> list[str]:
    async with ensure_session(aiohttp_session) as aiohttp_session:
        async with aiohttp_session.get(
            f"{API_BASE_URL}/characters"
        ) as resp:
            return await resp.json()

