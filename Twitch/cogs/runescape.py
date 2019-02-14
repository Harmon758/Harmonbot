
from twitchio.ext import commands

import bisect

@commands.cog()
class Runescape:
	
	def __init__(self, bot):
		self.bot = bot
		
		self.ehp_data = {"attack": [(0, 15000), (37224, 38000), (100000, 55000), (1000000, 65000), 
									(1986068, 80000), (3000000, 90000), (5346332, 105000), (13034431, 120000)], 
						"defence": [(0, 15000), (37224, 38000), (100000, 55000), (1000000, 65000), 
									(1986068, 80000), (3000000, 90000), (5346332, 105000), (13034431, 120000)], 
						"strength": [(0, 15000), (37224, 38000), (100000, 55000), (1000000, 65000), 
									(1986068, 80000), (3000000, 90000), (5346332, 105000), (13034431, 120000)], 
						"ranged": [(0, 250000), (6517253, 330000), (13034431, 350000)], 
						"cooking": [(0, 40000), (7842, 130000), (37224, 175000), (1986068, 275000), 
									(5346332, 340000), (7944614, 360000)], 
						"woodcutting": [(0, 7000), (2411, 16000), (13363, 35000), (41171, 49000), 
										(302288, 58000), (500000, 68000), (1000000, 73000), 
										(2000000, 80000), (4000000, 86000), (8000000, 92000)], 
						"fletching": [(0, 30000), (7842, 45000), (22406, 72000), (166636, 135000), 
										(737627, 184000), (3258594, 225000)], 
						"fishing": [(0, 14000), (4470, 30000), (13363, 40000), (273742, 44000), 
									(737627, 52000), (2500000, 56500), (6000000, 59000), 
									(11000000, 61000), (13034431, 63000)], 
						"firemaking": [(0, 45000), (13363, 130500), (61512, 195750), 
										(273742, 293625), (1210421, 445000)], 
						"crafting": [(0, 57000), (300000, 170000), (362000, 285000)], 
						"smithing": [(0, 40000), (37224, 103000)], 
						"mining": [(0, 8000), (14883, 20000), (41171, 44000), (302288, 47000), 
									(547953, 54000), (1986068, 58000), (6000000, 63000)], 
						"herblore": [(0, 60000), (27473, 200000), (2192818, 310000)], 
						"agility": [(0, 6000), (13363, 15000), (41171, 44000), (449428, 50000), 
									(2192818, 55000), (6000000, 59000), (11000000, 62000)], 
						"thieving": [(0, 15000), (61512, 60000), (166636, 100000), (449428, 220000), 
										(5902831, 255000), (13034431, 265000)], 
						"slayer": [(0, 5000), (37224, 12000), (100000, 17000), (1000000, 25000), 
									(1986068, 30000), (3000000, 32500), (7195629, 35000), (13034431, 37000)], 
						"farming": [(0, 10000), (2411, 50000), (13363, 80000), (61512, 150000), 
									(273742, 350000), (1210421, 700000)], 
						"runecrafting": [(0, 8000), (2107, 20000), (1210421, 24500), 
											(2421087, 30000), (5902831, 26250)], 
						"hunter": [(0, 5000), (12031, 40000), (247886, 80000), (1986068, 110000), 
									(3972294, 135000), (13034431, 155000)], 
						"construction": [(0, 20000), (18247, 100000), (101333, 230000), (1096278, 410000)]}
		
		self.skill_aliases = {"att": "attack", "def": "defence", "defense": "defence", "str": "strength", 
								"range": "ranged", "cook": "cooking", "wc": "woodcutting", "fletch": "fletching", 
								"fish": "fishing", "fm": "firemaking", "craft": "crafting", "smith": "smithing", 
								"mine": "mining", "herb": "herblore", "thief": "thieving", "thieve": "thieving", 
								"slay": "slayer", "farm": "farming", "rc": "runecrafting", "hunt": "hunter", 
								"con": "construction"}
	
	@commands.command()
	async def ehp(self, ctx, skill, xp : int):
		# TODO: Handle negative xp input
		if xp > 200000000:
			return await ctx.send(f"You can't have that much xp, {ctx.author.name.capitalize()}! Reported.")
		skill = self.skill_aliases.get(skill, skill)
		if skill in self.ehp_data:
			index = bisect.bisect([boundary[0] for boundary in self.ehp_data[skill]], xp) - 1
			await ctx.send(f"At {xp} {skill.capitalize()} xp: 1 ehp = {self.ehp_data[skill][index][1]:,} xp/h")
		elif skill in ("hp", "hitpoints"):
			# TODO: Add constitution as alias?
			await ctx.send("None.")
		elif skill in ("pray", "prayer"):
			await ctx.send("For Prayer: 1 ehp = 500,000 xp/h")
		elif skill in ("mage", "magic"):
			await ctx.send("For Magic: 1 ehp = 250,000 xp/h")
		# TODO: Handle skill not found

