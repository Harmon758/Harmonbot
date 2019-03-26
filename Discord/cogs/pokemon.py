
import discord
from discord.ext import commands

from utilities import checks

def setup(bot):
	bot.add_cog(Pokemon(bot))

class Pokemon(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.group(aliases = ["pokémon"], invoke_without_command = True)
	@checks.not_forbidden()
	async def pokemon(self, ctx, id_or_name : str):
		'''WIP'''
		# TODO: colors?, egg groups?, forms?, genders?, habitats?, 
		#		pokeathlon stats?, shapes?, stats?, version groups?
		await ctx.send_help(ctx.command)
	
	@pokemon.command()
	@checks.not_forbidden()
	async def ability(self, ctx, id_or_name : str):
		'''
		WIP
		Abilities provide passive effects for Pokémon in battle or in the overworld
		Pokémon have multiple possible abilities but can have only one ability at a time
		Check out [Bulbapedia](https://bulbapedia.bulbagarden.net/wiki/Ability) for greater detail
		'''
		async with ctx.bot.aiohttp_session.get("https://pokeapi.co/api/v2/ability/" + id_or_name) as resp:
			data = await resp.json()
			if resp.status == 404:
				return await ctx.embed_reply(f":no_entry: Error: {data['detail']}")
		await ctx.embed_reply(title = f"{data['name'].capitalize()} ({data['id']})", 
								fields = (("Generation", data["generation"]["name"]),))
	
	@pokemon.command()
	@checks.not_forbidden()
	async def berry(self, ctx, id_or_name : str):
		'''
		Berries
		Small fruits that can provide HP and status condition restoration, stat enhancement, and even damage negation when eaten by Pokémon
		Check out [Bulbapedia](https://bulbapedia.bulbagarden.net/wiki/Berry) for greater detail
		'''
		async with ctx.bot.aiohttp_session.get("https://pokeapi.co/api/v2/berry/" + id_or_name) as resp:
			data = await resp.json()
			if resp.status == 404:
				return await ctx.embed_reply(f":no_entry: Error: {data['detail']}")
		await ctx.embed_reply(title = f"{data['name'].capitalize()} ({data['id']})", 
								fields = (("Item Name", data["item"]["name"].capitalize()), 
											("Growth Time", f"{data['growth_time']}h*4"), ("Max Harvest", data["max_harvest"]), 
											("Size", f"{data['size']} mm"), ("Smoothness", data["smoothness"]), 
											("Soil Dryness", data["soil_dryness"]), ("Firmness", data["firmness"]["name"]), 
											("Natural Gift Power", data["natural_gift_power"]), 
											("Natural Gift Type", data["natural_gift_type"]["name"]), 
											("Flavors (Potency)", ", ".join(f"{f['flavor']['name']} ({f['potency']})" for f in data["flavors"]))))
	
	@pokemon.command()
	@checks.not_forbidden()
	async def characteristic(self, ctx, id : int):
		'''WIP'''
		...
	
	@pokemon.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def contest(self, ctx):
		'''WIP'''
		# TODO: contest effects?, super contest effects?
		...
	
	@contest.command(name = "condition", aliases = ["type"])
	@checks.not_forbidden()
	async def contest_condition(self, ctx, id_or_name : str):
		'''
		Contest conditions
		Categories judges use to weigh a Pokémon's condition in Pokémon contests
		Check out [Bulbapedia](https://bulbapedia.bulbagarden.net/wiki/Contest_condition) for greater detail
		'''
		async with ctx.bot.aiohttp_session.get("https://pokeapi.co/api/v2/contest-type/" + id_or_name) as resp:
			data = await resp.json()
			if resp.status == 404:
				return await ctx.embed_reply(f":no_entry: Error: {data['detail']}")
		name = discord.utils.find(lambda n: n["language"]["name"] == "en", data["names"])
		color = name["color"]
		await ctx.embed_reply(title = f"{data['name'].capitalize()} ({data['id']})", 
								fields = (("Flavor", data["berry_flavor"]["name"]), ("Color", color)))
	
	@pokemon.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def encounter(self, ctx):
		'''WIP'''
		# TODO: conditions?/condition values?
		...
	
	@encounter.command(name = "method")
	@checks.not_forbidden()
	async def encounter_method(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.group(invoke_without_command = True)
	@checks.not_forbidden()
	async def evolution(self, ctx):
		'''WIP'''
		...
	
	@evolution.command(name = "chain")
	@checks.not_forbidden()
	async def evolution_chain(self, ctx, id : int):
		'''WIP'''
		...
	
	@evolution.command(name = "trigger")
	@checks.not_forbidden()
	async def evolution_trigger(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.command()
	@checks.not_forbidden()
	async def generation(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.command(aliases = ["rate", "growthrate", "growth_rate"])
	@checks.not_forbidden()
	async def growth(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.group()
	@checks.not_forbidden()
	async def item(self, ctx, id_or_name : str):
		'''WIP'''
		# TODO: fling effect?
		...
	
	@item.command(name = "attribute")
	@checks.not_forbidden()
	async def item_attribute(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@item.command(name = "category")
	@checks.not_forbidden()
	async def item_category(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@item.command(name = "pocket")
	@checks.not_forbidden()
	async def item_pocket(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.group()
	@checks.not_forbidden()
	async def location(self, ctx, id : int):
		'''WIP'''
		# TODO: pal park areas?
		...
	
	@location.command(name = "area")
	@checks.not_forbidden()
	async def location_area(self, ctx, id : int):
		'''WIP'''
		...
	
	@pokemon.command()
	@checks.not_forbidden()
	async def machine(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.group()
	@checks.not_forbidden()
	async def move(self, ctx, id_or_name : str):
		'''WIP'''
		# TODO: damage classes?, learn methods?, targets?
		...
	
	@move.command(name = "ailment")
	@checks.not_forbidden()
	async def move_ailment(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@move.command(name = "category")
	@checks.not_forbidden()
	async def move_category(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.command()
	@checks.not_forbidden()
	async def nature(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.command()
	@checks.not_forbidden()
	async def pokedex(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.command()
	@checks.not_forbidden()
	async def region(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.command()
	@checks.not_forbidden()
	async def species(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.command()
	@checks.not_forbidden()
	async def type(self, ctx, id_or_name : str):
		'''WIP'''
		...

