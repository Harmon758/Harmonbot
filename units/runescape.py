
from .errors import UnitExecutionError, UnitOutputError

async def get_item_id(item, aiohttp_session = None):
	if not aiohttp_session:
		raise UnitExecutionError("aiohttp session required")
		# TODO: Default aiohttp session?
	# https://runescape.wiki/w/Application_programming_interface#Grand_Exchange_Database_API
	# https://www.mediawiki.org/wiki/API:Opensearch
	# TODO: Handle redirects?
	url = "https://runescape.wiki/api.php"
	params = {"action": "opensearch", "search": item}
	async with aiohttp_session.get(url, params = params) as resp:
		data = await resp.json()
	if not data[1]:
		raise UnitOutputError("Item not found")
	for item in data[1]:
		# https://www.semantic-mediawiki.org/wiki/Help:Ask
		# https://www.semantic-mediawiki.org/wiki/Help:Inline_queries
		params = {"action": "ask", "query": f"[[{item}]]|?Item_ID", "format": "json"}
		async with aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		item_id = list(data["query"]["results"].values())[0]["printouts"]["Item ID"]
		if item_id:
			return item_id[0]
	raise UnitOutputError(f"{item} is not an item")

async def get_ge_data(item, item_id = None, aiohttp_session = None):
	if not aiohttp_session:
		raise UnitExecutionError("aiohttp session required")
		# TODO: Default aiohttp session?
	if not item_id:
		item_id = await get_item_id(item, aiohttp_session = aiohttp_session)
	url = "https://services.runescape.com/m=itemdb_rs/api/catalogue/detail.json"
	params = {"item": item_id}
	async with aiohttp_session.get(url, params = params) as resp:
		if resp.status == 404:
			raise UnitOutputError(f"{item} not found on the Grand Exchange")
		data = await resp.json(content_type = "text/html")
	return data["item"]

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

