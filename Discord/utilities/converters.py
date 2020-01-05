
from discord.ext import commands

class Maptype(commands.Converter):
	
	'''
	For Google Maps Static API parameter
	https://developers.google.com/maps/documentation/maps-static/dev-guide
	'''

	async def convert(self, ctx, argument):
		if argument not in ("roadmap", "satellite", "hybrid", "terrain"):
			raise commands.BadArgument("Invalid map type")
		return argument

