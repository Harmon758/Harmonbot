
import unittest

import asyncio

from tests import vcr
from units.genshin_impact import (
    get_all_characters, get_character, get_character_images, get_characters
)


class TestGetAllCharacters(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        asyncio.get_running_loop().slow_callback_duration = 1

    @vcr.use_cassette(
        "genshin_impact/get_all_characters/get_all_characters.yaml"
    )
    async def test_get_all_characters(self):
        await get_all_characters()

    async def asyncTearDown(self):
        # Wait 250 ms for the underlying SSL connections to close
        # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        await asyncio.sleep(0.25)


class TestGetCharacter(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        asyncio.get_running_loop().slow_callback_duration = 1

    @vcr.use_cassette("genshin_impact/get_character/get_amber_data.yaml")
    async def test_get_amber_data(self):
        self.assertEqual((await get_character("Amber")).name, "Amber")

    async def asyncTearDown(self):
        # Wait 250 ms for the underlying SSL connections to close
        # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        await asyncio.sleep(0.25)


class TestGetCharacterImages(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        asyncio.get_running_loop().slow_callback_duration = 1

    @vcr.use_cassette(
        "genshin_impact/get_character_images/get_amber_images.yaml"
    )
    async def test_get_amber_images(self):
        await get_character_images("Amber")

    async def asyncTearDown(self):
        # Wait 250 ms for the underlying SSL connections to close
        # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        await asyncio.sleep(0.25)


class TestGetCharacters(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        asyncio.get_running_loop().slow_callback_duration = 1

    @vcr.use_cassette(
        "genshin_impact/get_characters/get_characters.yaml"
    )
    async def test_get_characters(self):
        await get_characters()

    async def asyncTearDown(self):
        # Wait 250 ms for the underlying SSL connections to close
        # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        await asyncio.sleep(0.25)


if __name__ == "__main__":
    unittest.main()

