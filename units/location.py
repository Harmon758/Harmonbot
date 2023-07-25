
import datetime
import os

from .errors import UnitExecutionError, UnitOutputError


async def get_geocode_data(location, aiohttp_session = None):
    # TODO: Add reverse option
    if not aiohttp_session:
        raise UnitExecutionError("aiohttp session required")
        # TODO: Default aiohttp session?

    async with aiohttp_session.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params = {"address": location, "key": os.getenv("GOOGLE_API_KEY")}
    ) as resp:
        geocode_data = await resp.json()

    if geocode_data["status"] == "ZERO_RESULTS":
        raise UnitOutputError("Address/Location not found")

    if geocode_data["status"] != "OK":
        raise UnitOutputError()
        # TODO: error descriptions?

    return geocode_data["results"][0]


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


def wind_degrees_to_direction(degrees):
    # http://snowfence.umn.edu/Components/winddirectionanddegreeswithouttable3.htm
    if not isinstance(degrees, (int, float)):
        raise TypeError("degrees must be a number")
    if degrees < 0:
        raise ValueError("degrees must be greater than zero")
    if degrees > 360:
        raise ValueError("degrees must be less than 360")
    if degrees <= 11.25 or 348.75 <= degrees: return 'N'
    if 11.25 <= degrees <= 33.75: return "NNE"
    if 33.75 <= degrees <= 56.25: return "NE"
    if 56.25 <= degrees <= 78.75: return "ENE"
    if 78.75 <= degrees <= 101.25: return 'E'
    if 101.25 <= degrees <= 123.75: return "ESE"
    if 123.75 <= degrees <= 146.25: return "SE"
    if 146.25 <= degrees <= 168.75: return "SSE"
    if 168.75 <= degrees <= 191.25: return 'S'
    if 191.25 <= degrees <= 213.75: return "SSW"
    if 213.75 <= degrees <= 236.25: return "SW"
    if 236.25 <= degrees <= 258.75: return "WSW"
    if 258.75 <= degrees <= 281.25: return 'W'
    if 281.25 <= degrees <= 303.75: return "WNW"
    if 303.75 <= degrees <= 326.25: return "NW"
    if 326.25 <= degrees <= 348.75: return "NNW"

