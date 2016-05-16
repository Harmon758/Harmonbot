
import pyowm

import keys

owm = pyowm.OWM(keys.owm_api_key)

def wunderground():
	pass

def location(loc):
	pass

def tempc(search):
	observation = owm.weather_at_place(search)
	location = observation.get_location()
	weather = observation.get_weather()
	return location.get_name() + ": " + str(weather.get_temperature(unit = "celsius")["temp"])
	# weather.get_temperature(unit = "fahrenheit")
