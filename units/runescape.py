
from .errors import UnitExecutionError, UnitOutputError

async def get_monster_data(monster, aiohttp_session = None):
	if not aiohttp_session:
		raise UnitExecutionError("aiohttp session required")
		# TODO: Default aiohttp session?
	url = "http://services.runescape.com/m=itemdb_rs/bestiary/beastSearch.json"
	params = {"term": monster}
	async with aiohttp_session.get(url, params = params) as resp:
		data = await resp.json(content_type = "text/html")
	if "value" not in data[0]:
		raise UnitOutputError("Monster not found")
	url = "http://services.runescape.com/m=itemdb_rs/bestiary/beastData.json"
	params = {"beastid": data[0]["value"]}
	async with aiohttp_session.get(url, params = params) as resp:
		data = await resp.json(content_type = "text/html")
	return data

