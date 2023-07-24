
import unittest

import asyncio

from tests import vcr
from units.runescape import get_item_id, get_ge_data, get_monster_data


class TestGetItemID(unittest.IsolatedAsyncioTestCase):

    @vcr.use_cassette("runescape/get_item_id/get_vial_id.yaml")
    async def test_get_vial_id(self):
        self.assertEqual(await get_item_id("vial"), 229)

    @vcr.use_cassette("runescape/get_item_id/get_nonexistent_item_id.yaml")
    async def test_get_nonexistent_item_id(self):
        with self.assertRaises(ValueError):
            await get_item_id("nonexistent")

    @vcr.use_cassette("runescape/get_item_id/get_non-item_item_id.yaml")
    async def test_get_non_item_item_id(self):
        with self.assertRaises(ValueError):
            await get_item_id("Cook's Assistant")

    async def asyncTearDown(self):
        # Wait 250 ms for the underlying SSL connections to close
        # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        await asyncio.sleep(0.25)


class TestGetGEData(unittest.IsolatedAsyncioTestCase):

    @vcr.use_cassette("runescape/get_ge_data/get_vial_ge_data.yaml")
    async def test_get_vial_ge_data(self):
        self.assertEqual((await get_ge_data("vial"))["name"], "Vial")

    @vcr.use_cassette(
        "runescape/get_ge_data/get_nonexistent_item_ge_data.yaml"
    )
    async def test_get_nonexistent_item_ge_data(self):
        with self.assertRaises(ValueError):
            await get_ge_data("nonexistent")

    @vcr.use_cassette(
        "runescape/get_ge_data/get_untradeable_item_ge_data.yaml"
    )
    async def test_get_untradeable_item_ge_data(self):
        with self.assertRaises(ValueError):
            await get_ge_data("completionist cape")

    async def asyncTearDown(self):
        # Wait 250 ms for the underlying SSL connections to close
        # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        await asyncio.sleep(0.25)


class TestGetMonsterData(unittest.IsolatedAsyncioTestCase):

    @vcr.use_cassette("runescape/get_monster_data/get_cow_data.yaml")
    async def test_get_cow_data(self):
        self.assertEqual((await get_monster_data("cow"))["name"], "Cow")

    @vcr.use_cassette(
        "runescape/get_monster_data/get_nonexistent_monster_data.yaml"
    )
    async def test_get_nonexistent_monster_data(self):
        with self.assertRaises(ValueError):
            await get_monster_data("nonexistent")

    async def asyncTearDown(self):
        # Wait 250 ms for the underlying SSL connections to close
        # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        await asyncio.sleep(0.25)


if __name__ == "__main__":
    unittest.main()

