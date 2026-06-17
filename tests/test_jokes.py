
import unittest

import asyncio
import os

from tests import vcr
from units.jokes import get_dad_joke, DadJokeError


class TestGetDadJoke(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        asyncio.get_running_loop().slow_callback_duration = 1

    @vcr.use_cassette(
        "jokes/get_dad_joke/get_random_dad_joke.yaml",
        record_mode = "none" if os.getenv("CI") else "all"
    )
    async def test_get_random_dad_joke(self):
        await get_dad_joke()

    @vcr.use_cassette("jokes/get_dad_joke/get_dad_joke.yaml")
    async def test_get_specific_dad_joke(self):
        await get_dad_joke("2118E69prc")

    @vcr.use_cassette("jokes/get_dad_joke/get_invalid_dad_joke.yaml")
    async def test_get_invalid_dad_joke(self):
        assert isinstance(await get_dad_joke("invalid_id"), DadJokeError)

    async def asyncTearDown(self):
        # Wait 250 ms for the underlying SSL connections to close
        # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        await asyncio.sleep(0.25)


if __name__ == "__main__":
    unittest.main()

