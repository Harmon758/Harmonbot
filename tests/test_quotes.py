
import unittest

import asyncio
import os

from tests import vcr
from units.quotes import get_random_quote


class TestGetRandomQuote(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        asyncio.get_running_loop().slow_callback_duration = 1

    @vcr.use_cassette(
        "quotes/get_random_quote/get_random_quote.yaml",
        record_mode = "none" if os.getenv("CI") else "all"
    )
    async def test_get_random_quote(self):
        await get_random_quote()

    async def asyncTearDown(self):
        # Wait 250 ms for the underlying SSL connections to close
        # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        await asyncio.sleep(0.25)

