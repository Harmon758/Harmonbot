
import discord
from discord.ext import commands

from utilities import checks

async def setup(bot):
	await bot.add_cog(Pokemon(bot))

class Pokemon(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	# TODO: Cache API responses
	
	@commands.group(aliases = ["pokémon"], invoke_without_command = True, case_insensitive = True)
	async def pokemon(self, ctx, id_or_name : str):
		'''WIP'''
		# TODO: colors?, egg groups?, forms?, genders?, habitats?, 
		#		pokeathlon stats?, shapes?, stats?, version groups?
		await ctx.send_help(ctx.command)
	
	@pokemon.command()
	async def ability(self, ctx, id_or_name: str):
		'''
		WIP
		Abilities provide passive effects for Pokémon in battle or in the overworld
		Pokémon have multiple possible abilities but can have only one ability at a time
		Check out [Bulbapedia](https://bulbapedia.bulbagarden.net/wiki/Ability) for greater detail
		'''
		async with ctx.bot.aiohttp_session.get(
			"https://pokeapi.co/api/v2/ability/" + id_or_name
		) as resp:
			if resp.status == 404:
				await ctx.embed_reply(
					f"{ctx.bot.error_emoji} Error: {await resp.text()}"
				)
				return
			ability_data = await resp.json()
		
		ability_name = ability_data['name'].capitalize()
		for name_data in ability_data["names"]:
			if name_data["language"]["name"] == "en":
				ability_name = name_data["name"]
				break
		
		fields = []
		
		for effect_entry in ability_data["effect_entries"]:
			if effect_entry["language"]["name"] == "en":
				fields.append(("Effect", effect_entry["effect"], False))
				break
		
		# TODO: Flavor Text?
		
		async with ctx.bot.aiohttp_session.get(
			ability_data["generation"]["url"]
		) as resp:
			generation_data = await resp.json()
		
		for generation_name_data in generation_data["names"]:
			if generation_name_data["language"]["name"] == "en":
				fields.append(("Generation", generation_name_data["name"]))
				break
		
		fields.append((
			"Pokémon",
			", ".join(
				pokemon_data["pokemon"]["name"].capitalize()
				for pokemon_data in ability_data["pokemon"]
			),
			False
		))  # TODO: Handle -gmax and -hisui suffixes
		
		await ctx.embed_reply(
			title = f"{ability_name} ({ability_data['id']})",
			fields = fields
		)
	
	@pokemon.command()
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
	async def characteristic(self, ctx, id : int):
		'''WIP'''
		...
	
	@pokemon.group(invoke_without_command = True, case_insensitive = True)
	async def contest(self, ctx):
		'''WIP'''
		# TODO: contest effects?, super contest effects?
		...
	
	@contest.command(name = "condition", aliases = ["type"])
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
	
	@pokemon.group(invoke_without_command = True, case_insensitive = True)
	async def encounter(self, ctx):
		'''WIP'''
		# TODO: conditions?/condition values?
		...
	
	@encounter.command(name = "method")
	async def encounter_method(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.group(invoke_without_command = True, case_insensitive = True)
	async def evolution(self, ctx):
		'''WIP'''
		...
	
	@evolution.command(name = "chain")
	async def evolution_chain(self, ctx, id : int):
		'''WIP'''
		...
	
	@evolution.command(name = "trigger")
	async def evolution_trigger(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.command()
	async def generation(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.command(aliases = ["rate", "growthrate", "growth_rate"])
	async def growth(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.group(case_insensitive = True)
	async def item(self, ctx, id_or_name : str):
		'''WIP'''
		# TODO: fling effect?
		...
	
	@item.command(name = "attribute")
	async def item_attribute(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@item.command(name = "category")
	async def item_category(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@item.command(name = "pocket")
	async def item_pocket(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.group(case_insensitive = True)
	async def location(self, ctx, id : int):
		'''WIP'''
		# TODO: pal park areas?
		...
	
	@location.command(name = "area")
	async def location_area(self, ctx, id : int):
		'''WIP'''
		...
	
	@pokemon.command()
	async def machine(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.group(case_insensitive = True)
	async def move(self, ctx, id_or_name : str):
		'''WIP'''
		# TODO: damage classes?, learn methods?, targets?
		...
	
	@move.command(name = "ailment")
	async def move_ailment(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@move.command(name = "category")
	async def move_category(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.command()
	async def nature(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.command()
	async def pokedex(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.command()
	async def region(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.command()
	async def species(self, ctx, id_or_name : str):
		'''WIP'''
		...
	
	@pokemon.command()
	async def type(self, ctx, id_or_name : str):
		'''WIP'''
		...

