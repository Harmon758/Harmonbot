
from twitchio.ext import commands

import bisect

@commands.cog()
class Runescape:
	
	def __init__(self, bot):
		self.bot = bot
		
		self.ehp_data = {"attack": ((0, 15000), (37224, 38000), (100000, 55000), (1000000, 65000), (1986068, 82000), 
									(3000000, 95000), (5346332, 115000), (13034431, 180000)), 
						"strength": ((0, 15000), (37224, 38000), (100000, 55000), (1000000, 65000), (1986068, 82000), 
										(3000000, 95000), (5346332, 115000), (13034431, 180000)), 
						"ranged": ((0, 250000), (6517253, 330000), (13034431, 900000)), 
						"prayer": ((0, 850000), (737627, 1600000)), 
						"cooking": ((0, 40000), (7842, 130000), (37224, 175000), (737627, 490000), (1986068, 950000)), 
						"woodcutting": ((0, 7000), (2411, 16000), (13363, 35000), (41171, 49000), (302288, 126515), 
										(737627, 137626), (1986068, 149906), (5902831, 160366), (13034431, 200000)), 
						"fletching": ((0, 30000), (969, 45000), (33648, 150000), (50339, 250000), (150872, 500000), 
										(302288, 700000), (13034431, 4000000)), 
						"fishing": ((0, 14000), (4470, 30000), (13363, 40000), (273742, 65000), (737627, 87000), 
									(2421087, 96403), (5902831, 103105), (10692629, 106619), (13034431, 110000)), 
						"firemaking": ((0, 45000), (13363, 132660), (61512, 198990), (273742, 298485), (1210421, 447801), 
										(5346332, 528797)), 
						"crafting": ((0, 57000), (300000, 170000), (362000, 285000), (496254, 336875), (2951373, 440000)), 
						"smithing": ((0, 40000), (37224, 380000), (13034431, 400000)), 
						"mining": ((0, 8000), (14833, 20000), (41171, 44000), (302288, 78150), (547953, 88861), 
									(1986068, 100830), (5902831, 110151), (13034431, 123000)), 
						"herblore": ((0, 60000), (27473, 200000), (2192818, 450000)), 
						"agility": ((0, 6000), (13363, 15000), (41171, 44000), (449428, 50000), (2192818, 55000), 
									(6000000, 59000), (11000000, 62300), (13034431, 70000)), 
						"thieving": ((0, 15000), (61512, 60000), (166636, 100000), (449428, 220000), (5902831, 255000), 
										(13034431, 275000)), 
						"slayer": ((0, 5000), (37224, 12000), (100000, 17000), (1000000, 25000), (1986068, 50000), 
									(3000000, 55000), (7195629, 60000), (13034431, 90000)), 
						"farming": ((0, 10000), (2411, 50000), (13363, 80000), (61512, 150000), (273742, 350000), 
									(1210421, 1900000)), 
						"runecrafting": ((0, 8000), (2107, 20000), (101333, 45000), (1210421, 68500), (13034431, 145000)), 
						"hunter": ((0, 5000), (12031, 40000), (247886, 85000), (1986068, 115000), (3972294, 135000), 
									(6517253, 150000), (13034431, 240000)), 
						"construction": ((0, 20000), (18247, 100000), (123660, 900000))}
		# TODO: Use database?
		self.ehp_responses = {"defence": "For Defence: 1 ehp = 350,000 xp/h", "hitpoints": "None", 
								"magic": "For Magic: 1 ehp = 250,000 xp/h"}
		
		self.skill_aliases = {"att": "attack", "con": "construction", "cook": "cooking", "craft": "crafting", 
								"def": "defence", "defense": "defence", "farm": "farming", "fish": "fishing", 
								"fletch": "fletching", "fm": "firemaking", "herb": "herblore", "hp": "hitpoints", 
								"hunt": "hunter", "mage": "magic", "mine": "mining", "pray": "prayer", 
								"range": "ranged", "rc": "runecrafting", "slay": "slayer", "smith": "smithing", 
								"str": "strength", "thief": "thieving", "thieve": "thieving", "wc": "woodcutting"}
		# TODO: Add constitution as alias?
	
	@commands.command()
	async def ehp(self, ctx, skill, xp : int):
		# TODO: Handle negative xp input
		if xp > 200000000:
			return await ctx.send(f"You can't have that much xp, {ctx.author.name.capitalize()}! Reported.")
		skill = self.skill_aliases.get(skill, skill)
		if skill in self.ehp_responses:
			await ctx.send(self.ehp_responses[skill])
		elif skill in self.ehp_data:
			index = bisect.bisect([boundary[0] for boundary in self.ehp_data[skill]], xp) - 1
			await ctx.send(f"At {xp} {skill.capitalize()} xp: 1 ehp = {self.ehp_data[skill][index][1]:,} xp/h")
		# TODO: Handle skill not found
	
	@commands.command()
	async def level(self, ctx, level : int):
		if 1 <= level <= 126:
			xp = sum(int(i + 300 * 2 ** (i / 7)) for i in range(1, level)) // 4
			await ctx.send(f"Runescape Level {level} = {xp:,} xp")
		elif 126 < level < 9000:
			await ctx.send(f"I was gonna calculate xp at Level {level}. Then I took an arrow to the knee.")
		elif level == 9000:
			await ctx.send("Almost there.")
		elif level > 9000:
			await ctx.send("It's over 9000!")
		else:
			await ctx.send(f"Level {level} does not exist.")
	
	@commands.command()
	async def monster(self, ctx, *monster):
		url = "http://services.runescape.com/m=itemdb_rs/bestiary/beastSearch.json?term="
		url += '+'.join(monster)
		async with self.bot.aiohttp_session.get(url) as resp:
			data = await resp.json(content_type = "text/html")
		if "value" in data[0]:
			monster_id = data[0]["value"]
			url = "http://services.runescape.com/m=itemdb_rs/bestiary/beastData.json"
			params = {"beastid": monster_id}
			async with self.bot.aiohttp_session.get(url, params = params) as resp:
				data = await resp.json(content_type = "text/html")
			level = data.get("level", "N/A")
			weakness = data.get("weakness", "N/A")
			hp = data.get("lifepoints", "N/A")
			await ctx.send(f"{data['name']}: {data['description']}, Level: {level}, Weakness: {weakness}, XP/Kill: {data['xp']}, HP: {hp}, Members: {data['members']}, Aggressive: {data['aggressive']}")
		else:
			await ctx.send("Monster not found.")
	
	@commands.command()
	async def xpbetween(self, ctx, start_level : int, end_level : int):
		start_xp = sum(int(level + 300 * 2 ** (level / 7)) for level in range(1, start_level))
		end_xp = (start_xp + sum(int(level + 300 * 2 ** (level / 7)) for level in range(start_level, end_level))) // 4
		start_xp //= 4
		await ctx.send(f"{end_xp - start_xp:,} xp between level {start_level} and level {end_level}")

