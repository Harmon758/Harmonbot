
import math
import sys

def hextoint(hex):
	if hex.startswith('#'):
		hex = hex[1:]
	return int(hex, 16)

def inttohex(integer):
	return hex(integer)[2:]

# degrees Celsius (°C) to degrees Fahrenheit (°F) [exact]
def ctof(celsius):
	return celsius * 9.0 / 5.0 + 32.0

# degrees Celsius (°C) to Kelvin (K) [exact]
def ctok(celsius):
	return celsius + 273.15

# degrees Celsius (°C) to degrees Rankine (°R) [exact]
def ctor(celsius):
	return (celsius + 273.15) * 9.0 / 5.0

# degrees Celsius (°C) to degrees Delisle (°De) [exact]
def ctode(celsius):
	return (100 - celsius) * 3.0 / 2.0

# degrees Celsius (°C) to degrees Newton (°N) [exact]
def cton(celsius):
	return celsius * 33.0 / 100.0

# degrees Celsius (°C) to degrees Réaumur (°Ré) [exact]
def ctore(celsius):
	return celsius * 4.0 / 5.0

# degrees Celsius (°C) to degrees Rømer (°Rø) [exact]
def ctoro(celsius):
	return celsius * 21.0 / 40.0 + 7.5

# degrees Fahrenheit (°F) to degrees Celsius (°C) [exact]
def ftoc(fahrenheit):
	return (fahrenheit - 32.0) * 5.0 / 9.0

# degrees Fahrenheit (°F) to Kelvin (K) [exact]
def ftok(fahrenheit):
	return (fahrenheit + 459.67) * 5.0 / 9.0

# degrees Fahrenheit (°F) to degrees Rankine (°R) [exact]
def ftor(fahrenheit):
	return fahrenheit + 459.67

# degrees Fahrenheit (°F) to degrees Delisle (°De) [exact]
def ftode(fahrenheit):
	return (212 - fahrenheit) * 5.0 / 6.0

# degrees Fahrenheit (°F) to degrees Newton (°N) [exact]
def fton(fahrenheit):
	return (fahrenheit - 32) * 11.0 / 60.0

# degrees Fahrenheit (°F) to degrees Réaumur (°Ré) [exact]
def ftore(fahrenheit):
	return (fahrenheit - 32) * 4.0 / 9.0

# degrees Fahrenheit (°F) to degrees Rømer (°Rø) [exact]
def ftoro(fahrenheit):
	return (fahrenheit - 32) * 7.0 / 24.0 + 7.5

# Kelvin (K) to degrees Celsius (°C) [exact]
def ktoc(kelvin):
	return kelvin - 273.15

# Kelvin (K) to degrees Fahrenheit (°F) [exact]
def ktof(kelvin):
	return kelvin * 9.0 / 5.0 - 459.67

# Kelvin (K) to degrees Rankine (°R) [exact]
def ktor(kelvin):
	return (373.15 - kelvin) * 9.0 / 5.0

# Kelvin (K) to degrees Delisle (°De) [exact]
def ktode(kelvin):
	return (373.15 - kelvin) * 3.0 / 2.0

# Kelvin (K) to degrees Newton (°N) [exact]
def kton(kelvin):
	return (kelvin - 273.15) * 33.0 / 100.0

# Kelvin (K) to degrees Réaumur (°Ré) [exact]
def ktore(kelvin):
	return (kelvin - 273.15) * 4.0 / 5.0

# Kelvin (K) to degrees Rømer (°Rø) [exact]
def ktoro(kelvin):
	return (kelvin - 273.15) * 21.0 / 40.0 + 7.5

# degrees Rankine (°R) to degrees Celsius (°C) [exact]
def rtoc(rankine):
	return (rankine - 491.67) * 5.0 / 9.0

# degrees Rankine (°R) to degrees Fahrenheit (°F) [exact]
def rtof(rankine):
	return rankine - 459.67

# degrees Rankine (°R) to Kelvin (K) [exact]
def rtok(rankine):
	return rankine * 5.0 / 9.0

# degrees Rankine (°R) to degrees Delisle (°De) [exact]
def rtode(rankine):
	return (671.67 - rankine) * 5.0 / 6.0

# degrees Rankine (°R) to degrees Netwon (°N) [exact]
def rton(rankine):
	return (rankine - 491.67) * 11.0 / 60.0

# degrees Rankine (°R) to degrees Réaumur (°Ré) [exact]
def rtore(rankine):
	return (rankine - 491.67) * 4.0 / 9.0

# degrees Rankine (°R) to degrees Rømer (°Rø) [exact]
def rtoro(rankine):
	return (rankine - 491.67) * 7.0 / 24.0 + 7.5

# degrees Delisle (°De) to degrees Celsius (°C) [exact]
def detoc(delisle):
	return 100 - delisle * 2.0 / 3.0

# degrees Delisle (°De) to degrees Fahrenheit (°F) [exact]
def detof(delisle):
	return 212 - delisle * 6.0 / 5.0

# degrees Delisle (°De) to Kelvin (K) [exact]
def detok(delisle):
	return 373.15 - delisle * 2.0 / 3.0

# degrees Delisle (°De) to degrees Rankine (°R) [exact]
def detor(delisle):
	return 671.67 - delisle * 6.0 / 5.0

# degrees Delisle (°De) to degrees Newton (°N) [exact]
def deton(delisle):
	return 33 - delisle * 11.0 / 50.0

# degrees Delisle (°De) to degrees Réaumur (°Ré) [exact]
def detore(delisle):
	return 80 - delisle * 8.0 / 15.0

# degrees Delisle (°De) to degrees Rømer (°Rø) [exact]
def detoro(delisle):
	return 60 - delisle * 7.0 / 20.0

# degrees Newton (°N) to degrees Celsius (°C) [exact]
def ntoc(newton):
	return newton * 100.0 / 33.0

# degrees Newton (°N) to degrees Fahrenheit (°F) [exact]
def ntof(newton):
	return newton * 60.0 / 11.0 + 32

# degrees Newton (°N) to Kelvin (K) [exact]
def ntok(newton):
	return newton * 100.0 / 33.0 + 273.15

# degrees Newton (°N) to degrees Rankine (°R) [exact]
def ntor(newton):
	return newton * 60.0 / 11.0 + 491.67

# degrees Newton (°N) to degrees Delisle (°De) [exact]
def ntode(newton):
	return (33 - newton) * 50.0 / 11.0

# degrees Newton (°N) to degrees Réaumur (°Ré) [exact]
def ntore(newton):
	return newton * 80.0 / 33.0

# degrees Newton (°N) to degrees Rømer (°Rø) [exact]
def ntoro(newton):
	return newton * 35.0 / 22.0 + 7.5

# degrees Réaumur (°Ré) to degrees Celsius (°C) [exact]
def retoc(reaumur):
	return reaumur * 5.0 / 4.0

# degrees Réaumur (°Ré) to degrees Fahrenheit (°F) [exact]
def retof(reaumur):
	return reaumur * 9.0 / 4.0 + 32

# degrees Réaumur (°Ré) to Kelvin (K) [exact]
def retok(reaumur):
	return reaumur * 5.0 / 4.0 + 273.15

# degrees Réaumur (°Ré) to degrees Rankine (°R) [exact]
def retor(reaumur):
	return reaumur * 9.0 / 4.0 + 491.67

# degrees Réaumur (°Ré) to degrees Delisle (°De) [exact]
def retode(reaumur):
	return (80 - reaumur) * 15.0 / 8.0

# degrees Réaumur (°Ré) to degrees Newton (°N) [exact]
def reton(reaumur):
	return reaumur * 33.0 / 80.0

# degrees Réaumur (°Ré) to degrees Rømer (°Rø) [exact]
def retoro(reaumur):
	return reaumur * 21.0 / 32.0 + 7.5

# degrees Rømer (°Rø) to degrees Celsius (°C) [exact]
def rotoc(romer):
	return (romer - 7.5) * 40.0 / 21.0

# degrees Rømer (°Rø) to degrees Fahrenheit (°F) [exact]
def rotof(romer):
	return (romer - 7.5) * 24.0 / 7.0 + 32

# degrees Rømer (°Rø) to Kelvin (K) [exact]
def rotok(romer):
	return (romer - 7.5) * 40.0 / 21.0 + 273.15

# degrees Rømer (°Rø) to degrees Rankine (°R) [exact]
def rotor(romer):
	return (romer - 7.5) * 24.0 / 7.0 + 491.67

# degrees Rømer (°Rø) to degrees Delisle (°De) [exact]
def rotode(romer):
	return (60 - romer) * 20.0 / 7.0

# degrees Rømer (°Rø) to degrees Newton (°N) [exact]
def roton(romer):
	return (romer - 7.5) * 22.0 / 35.0

# degrees Rømer (°Rø) to degrees Réaumur (°Ré) [exact]
def rotore(romer):
	return (romer - 7.5) * 32.0 / 21.0

temperatures = ['f', 'c', 'k', 'r', "de", 'n', "re", "ro"]
temperatures_formatted = {'f' : "°F", 'c': "°C", 'k' : 'K', 'r' : "°R" , "de" : "°De", 'n' : "°N", "re" : "°Ré", "ro" : "°Rø"}

def temperatureconversion(value, unit1, unit2):
	if unit1 in temperatures and unit2 in temperatures:
		conversion = getattr(sys.modules[__name__], f"{unit1}to{unit2}")
		return conversion(value), temperatures_formatted[unit1], temperatures_formatted[unit2]
	else:
		return None, unit1, unit2

# https://en.wikipedia.org/wiki/Conversion_of_units#Mass
masses = {
	"amu" : 1.6605390666 * 10 ** -27, "me" : 9.1093837015 * 10 ** -31, "bagc" : 60, 
	"bagpc" : 42.63768278, "barge" : 20411.65665, "kt" : 0.0002051965483, "ct" : 0.0002, 
	"clove" : 3.62873896, "crith" : 8.99349 * 10 ** -5, "da" : 1.66053904 * 10 ** -27, 
	"drt" : 0.0038879346, "drav" : 0.0017718451953125, "ev" : 1.78266184 * 10 ** -36, 
	"gamma" : 1 * 10 ** -9, "gr" : 6.479891, "gv" : 1, "longcwt" : 50.80234544,	
	"cwt" : 50.80234544, "shcwt" : 45.359237, "kg" : 1, "kip" : 453.59237, "mark" : 0.2488278144, 
	"mite" : 3.2399455 * 10 ** -6, "mitem" : 5 * 10 ** -5, "ozt" : 0.0311034768, 
	"ozav" : 0.028349523125, "oz" : 0.028, "dwt" : 0.0015551738, "pwt" : 0.0015551738, 
	"point" : 2 * 10 ** -6, "lb" : 0.45359237, "lbav" : 0.45359237, "lbm" : 0.5, 
	"lbt" : 0.3732417216, "quarterimp" : 12.70058636, "quarterinf" : 226.796185, 
	"quarterlinf" : 254.0117272, "q" : 100, "sap" : 0.0012959782, "sheet" : 0.0006479891, 
	"slug" : 14.593903, "st" : 6.35029318, "atl" : 32.6, "ats" : 29.16, "longtn" : 1016.0469088, 
	"ton" : 1016.0469088, "shtn" : 907.18474, "t" : 1000, "wey" : 114.30527724, "g" : 0.001
}

def massconversion(value, unit1, unit2):
	if unit1 in masses and unit2 in masses:
		return value * masses[unit1] / masses[unit2]
	else:
		return None

def fttom(feet):
	return feet * 0.3048

def mtoft(meters):
	return meters * 3.2808

def fitom(feet, inches):
	return (feet + inches / 12.0) * 0.3048

def mtofi(meters):
	return math.floor(meters * 39.370 / 12.0), meters * 39.370 - math.floor(meters * 39.370 / 12.0) * 12.0

def mitokm(miles):
	return miles * 1.60934

def kmtomi(kilometers):
	return kilometers * 0.621371

