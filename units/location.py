
import datetime
import os

import aiohttp

from .errors import UnitExecutionError, UnitOutputError


async def get_geocode_data(
    location: str, *, aiohttp_session: aiohttp.ClientSession | None = None
) -> dict:
    # TODO: Add reverse option
    if aiohttp_session_not_passed := (aiohttp_session is None):
        aiohttp_session = aiohttp.ClientSession()
    try:
        async with aiohttp_session.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params = {"address": location, "key": os.getenv("GOOGLE_API_KEY")}
        ) as resp:
            geocode_data = await resp.json()

        if geocode_data["status"] == "ZERO_RESULTS":
            raise ValueError("Address/Location not found")

        if geocode_data["status"] != "OK":
            raise UnitOutputError()
            # TODO: error descriptions?

        return geocode_data["results"][0]
    finally:
        if aiohttp_session_not_passed:
            await aiohttp_session.close()


async def get_timezone_data(
    location = None, latitude = None, longitude = None, aiohttp_session = None
):
    if not aiohttp_session:
        raise UnitExecutionError("aiohttp session required")
        # TODO: Default aiohttp session?

    if not (latitude and longitude):
        if not location:
            raise TypeError("location or latitude and longitude required")

        geocode_data = await get_geocode_data(
            location, aiohttp_session = aiohttp_session
        )
        latitude = geocode_data["geometry"]["location"]["lat"]
        longitude = geocode_data["geometry"]["location"]["lng"]

    async with aiohttp_session.get(
        "https://maps.googleapis.com/maps/api/timezone/json",
        params = {
            "location": f"{latitude}, {longitude}",
            "timestamp": str(datetime.datetime.utcnow().timestamp()),
            "key": os.getenv("GOOGLE_API_KEY")
        }
    ) as resp:
        timezone_data = await resp.json()

    if timezone_data["status"] == "ZERO_RESULTS":
        raise UnitOutputError("Timezone data not found")

    if timezone_data["status"] != "OK":
        error_message = timezone_data.get(
            "errorMessage", timezone_data["status"]
        )
        raise UnitOutputError(f"Error: {error_message}")

    return timezone_data


DEGREES_RANGES_TO_DIRECTIONS = {
    (0, 11.25): 'N',
    (11.25, 33.75): "NNE",
    (33.75, 56.25): "NE",
    (56.25, 78.75): "ENE",
    (78.75, 101.25): 'E',
    (101.25, 123.75): "ESE",
    (123.75, 146.25): "SE",
    (146.25, 168.75): "SSE",
    (168.75, 191.25): 'S',
    (191.25, 213.75): "SSW",
    (213.75, 236.25): "SW",
    (236.25, 258.75): "WSW",
    (258.75, 281.25): 'W',
    (281.25, 303.75): "WNW",
    (303.75, 326.25): "NW",
    (326.25, 348.75): "NNW",
    (348.75, 360): 'N'
}
# http://snowfence.umn.edu/Components/winddirectionanddegreeswithouttable3.htm

def wind_degrees_to_direction(degrees: int | float) -> str:
    if not isinstance(degrees, (int, float)):
        raise TypeError("degrees must be a number")
    if degrees < 0:
        raise ValueError("degrees must be greater than zero")
    if degrees > 360:
        raise ValueError("degrees must be less than 360")

    for degrees_range, direction in DEGREES_RANGES_TO_DIRECTIONS.items():
        if degrees_range[0] <= degrees <= degrees_range[1]:
            return direction

