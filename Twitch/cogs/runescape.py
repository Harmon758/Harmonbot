
from twitchio.ext import commands

import bisect
import datetime
import time

from units.runescape import get_ge_data, get_monster_data
from units.time import duration_to_string

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
		
		self.osrs_skill_aliases = {"att": "attack", "atk": "attack", "con": "construction", "cook": "cooking", 
									"craft": "crafting", "def": "defence", "defense": "defence", "farm": "farming", 
									"fish": "fishing", "fletch": "fletching", "fm": "firemaking", "herb": "herblore", 
									"hp": "hitpoints", "hunt": "hunter", "mage": "magic", "mine": "mining", "pray": "prayer", 
									"range": "ranged", "rc": "runecrafting", "slay": "slayer", "smith": "smithing", 
									"str": "strength", "thief": "thieving", "thieve": "thieving", "wc": "woodcutting"}
		self.rs3_skill_aliases = self.osrs_skill_aliases
		self.rs3_skill_aliases.update({"hp": "constitution", "div": "divination", "dg": "dungeoneering", 
										"dung": "dungeoneering", "inventor": "invention", "invent": "invention"})
		self.skill_order = ("total", "attack", "defence", "strength", "constitution", "ranged", "prayer", 
							"magic", "cooking", "woodcutting", "fletching", "fishing", "firemaking", 
							"crafting", "smithing", "mining", "herblore", "agility", "thieving", "slayer", 
							"farming", "runecrafting", "hunter", "construction", "summoning", "dungeoneering", 
							"divination", "invention")
		
		self.hiscores_types = ("", "ironman", "hardcore_ironman", "oldschool", "oldschool_ironman", 
								"oldschool_ultimate", "oldschool_hardcore_ironman", "oldschool_deadman", 
								"oldschool_seasonal", "oldschool_tournament")
		self.hiscores_type_aliases = {"rs3": "", "runescape_3": "", "runescape3": "", 
										"07": "oldschool", "osrs": "oldschool", "os": "oldschool", 
										"hcim": "hardcore_ironman", "hc": "hardcore", "uim": "ultimate", 
										"tourny": "tournament"}
		self.hiscores_names = {"": "RS3", "ironman": "RS3 (Ironman)", "hardcore_ironman": "RS3 (Hardcore Ironman)", 
								"oldschool": "OSRS", "oldschool_ironman": "OSRS (Ironman)", 
								"oldschool_ultimate": "OSRS (Ultimate Ironman)", 
								"oldschool_hardcore_ironman": "OSRS (Hardcore Ironman)", 
								"oldschool_deadman": "OSRS (Deadman Mode)", "oldschool_seasonal": "OSRS (Seasonal)", 
								"oldschool_tournament": "OSRS (Tournament)"}
	
	@commands.command()
	async def cache(self, ctx):
		seconds = int(10800 - time.time() % 10800)
		# 10800 = seconds in 3 hours
		await ctx.send(f"{duration_to_string(datetime.timedelta(seconds = seconds))} until Guthixian Cache.")
	
	@commands.command()
	async def ehp(self, ctx, skill, xp : int):
		# TODO: Handle negative xp input
		if xp > 200000000:
			return await ctx.send(f"You can't have that much xp, {ctx.author.name.capitalize()}! Reported.")
		skill = self.osrs_skill_aliases.get(skill, skill)
		if skill in self.ehp_responses:
			await ctx.send(self.ehp_responses[skill])
		elif skill in self.ehp_data:
			index = bisect.bisect([boundary[0] for boundary in self.ehp_data[skill]], xp) - 1
			await ctx.send(f"At {xp} {skill.capitalize()} xp: 1 ehp = {self.ehp_data[skill][index][1]:,} xp/h")
		# TODO: Handle skill not found
	
	@commands.command()
	async def ge(self, ctx, *, item):
		try:
			data = await get_ge_data(item, aiohttp_session = self.bot.aiohttp_session)
		except ValueError as e:
			return await ctx.send(f"Error: {e}")
		await ctx.send(f"Price of {data['name']}: {data['current']['price']} gp")
	
	@commands.command(aliases = ("hiscore", "highscore", "highscores"))
	async def hiscores(self, ctx, username, skill_or_total = "total", hiscores_type = "", stat_type = "level"):
		# TODO: Document
		# TODO: Other RS3 hiscores?
		username = username.replace('_', ' ')
		skill = skill_or_total.lower()
		skill = self.rs3_skill_aliases.get(skill, skill)
		if skill not in self.skill_order:
			return await ctx.send("Invalid skill. Use _'s for spaces in usernames.")
		hiscores_type = hiscores_type.lower()
		for alias, name in self.hiscores_type_aliases.items():
			hiscores_type = hiscores_type.replace(alias, name)
		hiscores_type = hiscores_type.lstrip('_')
		if skill in ("dungeoneering", "divination", "invention") and hiscores_type.startswith("oldschool"):
			return await ctx.send("Invalid skill for OSRS.")
		if hiscores_type not in self.hiscores_types:
			valid_types = []
			for valid_type in self.hiscores_types:
				if not valid_type.startswith("oldschool"):
					valid_type = "runescape_3_" + valid_type
					valid_type = valid_type.rstrip('_')
				valid_types.append(valid_type)
			return await ctx.send(f"Invalid hiscores type. Valid types: {', '.join(valid_types)}")
		hiscores_name = self.hiscores_names[hiscores_type]
		if hiscores_type:
			hiscores_type = '_' + hiscores_type
		stat_types = ("rank", "level", "xp")
		stat_type_aliases = {"exp": "xp", "experience": "xp", "lvl": "level"}
		stat_type = stat_type.lower()
		stat_type = stat_type_aliases.get(stat_type, stat_type)
		if stat_type not in stat_types:
			stat_type = "level"
		hiscores_url = f"https://secure.runescape.com/m=hiscore{hiscores_type}/index_lite.ws"
		params = {"player": username}
		async with self.bot.aiohttp_session.get(hiscores_url, params = params) as resp:
			if resp.status == 404:
				return await ctx.send("Username not found.")
			data = await resp.text()
		data = data.split()
		skill_data = data[self.skill_order.index(skill)].split(',')
		stat = int(skill_data[stat_types.index(stat_type)])
		if stat_type == "rank":
			if skill == "total":
				stat_text = f" is rank {stat:,} overall"
			else:
				stat_text = f" is rank {stat:,} in {skill.capitalize()}"
		elif stat_type == "xp":
			if skill == "total":
				stat_text = f" has {stat:,} total XP"
			else:
				stat_text = f" has {stat:,} XP in {skill.capitalize()}"
		else:
			if skill != "total":
				skill = skill.capitalize()
			stat_text = f"'s {skill} level is {stat:,}"
		await ctx.send(f"{username.capitalize()}{stat_text} on {hiscores_name}.")
	
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
	async def monster(self, ctx, *, monster):
		try:
			data = await get_monster_data(monster, aiohttp_session = self.bot.aiohttp_session)
		except ValueError as e:
			return await ctx.send(f"Error: {e}")
		await ctx.send(f"{data['name']}: {data['description']}, "
						f"Level: {data.get('level', 'N/A')}, "
						f"Weakness: {data.get('weakness', 'N/A')}, "
						f"XP/Kill: {data['xp']}, "
						f"HP: {data.get('lifepoints', 'N/A')}, "
						f"Members: {data['members']}, "
						f"Aggressive: {data['aggressive']}")
	
	@commands.command(aliases = ("07rswiki", "rswiki07", "rswikios"))
	async def osrswiki(self, ctx, *search):
		await ctx.send("https://oldschool.runescape.wiki/w/" + '_'.join(search))
	
	@commands.command()
	async def reset(self, ctx):
		seconds = int(86400 - time.time() % 86400)
		# 86400 = seconds in 24 hours
		await ctx.send(f"{duration_to_string(datetime.timedelta(seconds = seconds))} until reset.")
	
	@commands.command()
	async def rswiki(self, ctx, *search):
		await ctx.send("https://runescape.wiki/w/" + '_'.join(search))
	
	@commands.command()
	async def warbands(self, ctx):
		seconds = int(25200 - time.time() % 25200)
		# 25200 = seconds in 7 hours
		await ctx.send(f"{duration_to_string(datetime.timedelta(seconds = seconds))} until Warbands.")
	
	@commands.command()
	async def xpat(self, ctx, xp : int):
		if not 0 <= xp <= 200000000:
			return await ctx.send("You can't have that much xp!")
		level = 0
		level_xp = 0
		while xp >= level_xp // 4:
			level += 1
			level_xp += int(level + 300 * 2 ** (level / 7))
		await ctx.send(f"{xp:,} xp = level {level}")
	
	@commands.command()
	async def xpbetween(self, ctx, start_level : int, end_level : int):
		start_xp = sum(int(level + 300 * 2 ** (level / 7)) for level in range(1, start_level))
		end_xp = (start_xp + sum(int(level + 300 * 2 ** (level / 7)) for level in range(start_level, end_level))) // 4
		start_xp //= 4
		await ctx.send(f"{end_xp - start_xp:,} xp between level {start_level} and level {end_level}")
	
	@commands.command()
	async def zybez(self, ctx):
		return await ctx.send("See https://forums.zybez.net/topic/1783583-exit-post-the-end/")

