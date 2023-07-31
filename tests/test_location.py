
import unittest

from hypothesis import given
from hypothesis.strategies import floats, uuids

import asyncio
import os

from tests import vcr
from units.location import get_geocode_data, wind_degrees_to_direction


def setUpModule():
    if not os.getenv("GOOGLE_API_KEY"):
        os.putenv("GOOGLE_API_KEY", "MOCK_KEY")

def tearDownModule():
    if os.getenv("GOOGLE_API_KEY") == "MOCK_KEY":
        os.unsetenv("GOOGLE_API_KEY")


class TestGetGeocodeData(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        asyncio.get_running_loop().slow_callback_duration = 1

    @vcr.use_cassette(
        "location/get_geocode_data/get_fort_yukon_alaska_data.yaml"
    )
    async def test_get_fort_yukon_alaska_data(self):
        await get_geocode_data("Fort Yukon, Alaska")

    @vcr.use_cassette("location/get_geocode_data/get_nyc_data.yaml")
    async def test_get_nyc_data(self):
        await get_geocode_data("New York City")

    @vcr.use_cassette(
        "location/get_geocode_data/get_nonexistent_location_data.yaml"
    )
    async def test_get_nonexistent_location_data(self):
        with self.assertRaises(ValueError):
            await get_geocode_data("nonexistent")

    async def asyncTearDown(self):
        # Wait 250 ms for the underlying SSL connections to close
        # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        await asyncio.sleep(0.25)


class TestWindDegreesToDirection(unittest.TestCase):

    @given(uuids())
    def test_invalid_degrees_type(self, degrees):
        with self.assertRaises(TypeError):
            wind_degrees_to_direction(degrees)

    @given(floats(max_value = 0, exclude_max = True))
    def test_negative_degrees(self, degrees):
        with self.assertRaises(ValueError):
            wind_degrees_to_direction(degrees)

    @given(floats(min_value = 360, exclude_min = True))
    def test_degrees_greater_than_360(self, degrees):
        with self.assertRaises(ValueError):
            wind_degrees_to_direction(degrees)

    @given(floats(min_value = 0, max_value = 360))
    def test_output_type(self, degrees):
        self.assertIsInstance(wind_degrees_to_direction(degrees), str)

    @given(floats(min_value = 0, max_value = 11.25))
    def test_low_n_output(self, degrees):
        self.assertEqual(wind_degrees_to_direction(degrees), 'N')

    @given(floats(min_value = 33.75, max_value = 56.25, exclude_min = True))
    def test_ne_output(self, degrees):
        self.assertEqual(wind_degrees_to_direction(degrees), "NE")

    @given(floats(min_value = 56.25, max_value = 78.75, exclude_min = True))
    def test_ene_output(self, degrees):
        self.assertEqual(wind_degrees_to_direction(degrees), "ENE")

    @given(floats(min_value = 78.75, max_value = 101.25, exclude_min = True))
    def test_e_output(self, degrees):
        self.assertEqual(wind_degrees_to_direction(degrees), 'E')

    @given(floats(min_value = 101.25, max_value = 123.75, exclude_min = True))
    def test_ese_output(self, degrees):
        self.assertEqual(wind_degrees_to_direction(degrees), "ESE")

    @given(floats(min_value = 123.75, max_value = 146.25, exclude_min = True))
    def test_se_output(self, degrees):
        self.assertEqual(wind_degrees_to_direction(degrees), "SE")

    @given(floats(min_value = 146.25, max_value = 168.75, exclude_min = True))
    def test_sse_output(self, degrees):
        self.assertEqual(wind_degrees_to_direction(degrees), "SSE")

    @given(floats(min_value = 168.75, max_value = 191.25, exclude_min = True))
    def test_s_output(self, degrees):
        self.assertEqual(wind_degrees_to_direction(degrees), 'S')

    @given(floats(min_value = 191.25, max_value = 213.75, exclude_min = True))
    def test_ssw_output(self, degrees):
        self.assertEqual(wind_degrees_to_direction(degrees), "SSW")

    @given(floats(min_value = 213.75, max_value = 236.25, exclude_min = True))
    def test_sw_output(self, degrees):
        self.assertEqual(wind_degrees_to_direction(degrees), "SW")

    @given(floats(min_value = 236.25, max_value = 258.75, exclude_min = True))
    def test_wsw_output(self, degrees):
        self.assertEqual(wind_degrees_to_direction(degrees), "WSW")

    @given(floats(min_value = 258.75, max_value = 281.25, exclude_min = True))
    def test_w_output(self, degrees):
        self.assertEqual(wind_degrees_to_direction(degrees), 'W')

    @given(floats(min_value = 281.25, max_value = 303.75, exclude_min = True))
    def test_wnw_output(self, degrees):
        self.assertEqual(wind_degrees_to_direction(degrees), "WNW")

    @given(floats(min_value = 303.75, max_value = 326.25, exclude_min = True))
    def test_nw_output(self, degrees):
        self.assertEqual(wind_degrees_to_direction(degrees), "NW")

    @given(floats(min_value = 326.25, max_value = 348.75, exclude_min = True))
    def test_nnw_output(self, degrees):
        self.assertEqual(wind_degrees_to_direction(degrees), "NNW")

    @given(floats(min_value = 348.75, max_value = 360, exclude_min = True))
    def test_high_n_output(self, degrees):
        self.assertEqual(wind_degrees_to_direction(degrees), 'N')


if __name__ == "__main__":
    unittest.main()

