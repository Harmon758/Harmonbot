
import datetime

from . import credentials
from .errors import UnitExecutionError, UnitOutputError

async def get_geocode_data(location, aiohttp_session = None):
	# TODO: Add reverse option
	if not aiohttp_session:
		raise UnitExecutionError("aiohttp session required")
		# TODO: Default aiohttp session?
	url = "https://maps.googleapis.com/maps/api/geocode/json"
	params = {"address": location, "key": credentials.google_apikey}
	async with aiohttp_session.get(url, params = params) as resp:
		geocode_data = await resp.json()
	if geocode_data["status"] == "ZERO_RESULTS":
		raise UnitOutputError("Address/Location not found")
	if geocode_data["status"] != "OK":
		raise UnitOutputError()
		# TODO: error descriptions?
	return geocode_data["results"][0]

async def get_timezone_data(location = None, latitude = None, longitude = None, aiohttp_session = None):
	if not aiohttp_session:
		raise UnitExecutionError("aiohttp session required")
		# TODO: Default aiohttp session?
	if not (latitude and longitude):
		if not location:
			raise UnitExecutionError("location or latitude and longitude required")
		geocode_data = await get_geocode_data(location, aiohttp_session = aiohttp_session)
		latitude = geocode_data["geometry"]["location"]["lat"]
		longitude = geocode_data["geometry"]["location"]["lng"]
	current_utc_timestamp = datetime.datetime.utcnow().timestamp()
	url = "https://maps.googleapis.com/maps/api/timezone/json"
	params = {"location": f"{latitude}, {longitude}", 
				"timestamp": str(current_utc_timestamp), "key": credentials.google_apikey}
	async with aiohttp_session.get(url, params = params) as resp:
		timezone_data = await resp.json()
	if timezone_data["status"] == "ZERO_RESULTS":
		raise UnitOutputError("Timezone data not found")
	if timezone_data["status"] != "OK":
		error_message = timezone_data.get("errorMessage", timezone_data["status"])
		raise UnitOutputError(f"Error: {error_message}")
	return timezone_data

