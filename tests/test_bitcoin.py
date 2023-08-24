
import unittest

import asyncio

from tests import vcr
from units.bitcoin import get_supported_currencies


class TestGetSupportedCurrencies(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        asyncio.get_running_loop().slow_callback_duration = 1

    @vcr.use_cassette(
        "bitcoin/get_supported_currencies/get_supported_currencies.yaml"
    )
    async def test_get_supported_currencies(self):
        await get_supported_currencies()

    async def asyncTearDown(self):
        # Wait 250 ms for the underlying SSL connections to close
        # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        await asyncio.sleep(0.25)

