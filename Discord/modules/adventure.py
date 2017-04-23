
import math
import json
import random
import time
import types

from modules import utilities

initial_data = {"xp": {"woodcutting": 0, "mining": 0, "fishing": 0, "foraging": 0}, "inventory": {}, "last_action": None, "last_action_time": None, "time_started": None}
skills = ["woodcutting", "mining", "fishing", "foraging"]
forageables = {"rock": ("stone", "boulder"), "stick": ("branch", "trunk"), "plant": ("shrub", "bush")}
craftables = {("rock", "stick"): "rock attached to stick"}
wood_types = ["cuipo", "balsa", "eastern white pine", "basswood", "western white pine", "hemlock", "chestnut", "larch", "red alder", "western juniper", "douglas fir", "southern yellow pine", "silver maple", "radiata pine", "shedua", "box elder", "sycamore", "parana", "honduran mahogany", "african mahogany", "lacewood", "eastern red cedar", "paper birch", "boire", "red maple", "imbusia", "cherry", "black walnut", "boreal", "peruvian walnut", "siberian larch", "makore", "english oak", "rose gum", "teak", "larch", "carapa guianensis", "heart pine", "movingui", "yellow birch", "caribbean heart pine", "red oak", "american beech", "ash", "ribbon gum", "tasmanian oak", "white oak", "australian cypress", "bamboo", "kentucky coffeetree", "caribbean walnut", "hard maple", "sweet birch", "curupixa", "sapele", "peroba", "true pine", "zebrawood", "tualang", "wenge", "highland beech", "black locust", "kempas", "merbau", "blackwood", "african padauk", "rosewood", "bangkirai", "afzelia", "hickory", "tigerwood", "purpleheart", "jarrah", "amendoim", "merbau", "tallowwood", "cameron", "bubinga", "sydney blue gum", "karri", "osage orange", "brushbox", "brazilian koa", "pradoo", "bocote", "balfourodendron riedelianum", "golden teak", "mesquite", "jatoba", "spotted gum", "southern chestnut", "live oak", "turpentine", "bloodwood", "cocobolo", "yvyraro", "massaranduba", "ebony", "ironwood", "sucupira", "cumaru", "lapacho", "bolivian cherry", "grey ironbark", "moabi", "lapacho", "brazilian ebony", "brazilian olivewood", "snakewood", "piptadenia macrocarpa", "lignum vitae", "schinopsis balansae", "schinopsis brasiliensis", "australian buloke"]
# https://en.wikipedia.org/wiki/Janka_hardness_test
minerals = {"talc": (1), "graphite": (1.5), "putnisite": (1.75, 1), "bauxite": (2, 10), "gypsum": (2), "halite": (2.25), "galena": (2.625), "chalcocite": (2.75), "copper": (3), "celestine": (3.25), "chalcopyrite": (3.5), "strontianite": (3.5), "azurite": (3.75), "cuprite": (3.75), "malachite": (3.75), "cassiterite": (6.5), "pollucite": (6.75), "qingsongite": (9.5, 1), "quartz": (7, 10)}
# https://en.wikipedia.org/wiki/Mohs_scale_of_mineral_hardness
examine_messages = {"rock": "it's a rock..", "stone": "it's a bigger rock..", "boulder": "wow, that's a big rock", "stick": "pointy", "rock attached to stick": "it must have taken you a long time to make this"}

def xp_to_lvl(xp):
	return math.ceil((xp / 12.5 + 1.08) ** 0.5 / 2 - 0.5)

def xp_left_to_next_lvl(xp):
	lvl = xp_to_lvl(xp)
	return (lvl ** 2 + lvl + 2) * 50 - 100 - xp

def lvl_to_xp(lvl):
	return (lvl ** 2 - lvl + 2) * 50 - 100

def lvl_to_rate(lvl):
	return math.log10(lvl + 10)

def xp_to_rate(xp):
	return lvl_to_rate(xp_to_lvl(xp))

def wood_lvl(wood_type):
	return wood_types.index(wood_type) + 1

class AdventurePlayer:
	
	'''Adventure Player'''
	
	def __init__(self, user_id):
		self.user_id = user_id
		_initial_data = initial_data.copy()
		_initial_data["time_started"] = time.time()
		utilities.create_file("adventure_players/" + user_id, content = _initial_data)
		with open("data/adventure_players/{}.json".format(user_id), 'r') as player_file:
			self.data = json.load(player_file)
			
	def write_data(self):
		with open("data/adventure_players/{}.json".format(self.user_id), 'w') as player_file:
			json.dump(self.data, player_file, indent = 4)
	
	def wood_rate(self, wood_type):
		return max(0, math.log10(self.woodcutting_lvl / wood_lvl(wood_type)) + 1)
	
	def start_foraging(self, item):
		if self.last_action is not None:
			return self.last_action[0]
		elif item.lower() in forageables:
			self.last_action = ("foraging", item)
			self.last_action_time = time.time()
			self.write_data()
			return True
		else:
			return False
	
	def stop_foraging(self):
		if self.last_action and self.last_action[0] == "foraging":
			item = self.last_action[1]
			time_spent = math.ceil(time.time() - self.last_action_time) / 60
			self.last_action = None
			self.last_action_time = None
			item_amount = math.floor(time_spent * self.foraging_rate)
			self.inventory[item] = self.inventory.get(item, 0) + item_amount
			if self.inventory[item] == 0:
				del self.inventory[item]
			self.foraging_xp += item_amount
			secondary_item = forageables[item][0]
			tertiary_item = forageables[item][1]
			secondary_amount = random.randint(0, item_amount)
			tertiary_amount = math.floor(random.randint(0, item_amount) / 100)
			self.inventory[secondary_item] = self.inventory.get(secondary_item, 0) + secondary_amount
			if self.inventory[secondary_item] == 0:
				del self.inventory[secondary_item]
			self.inventory[tertiary_item] = self.inventory.get(tertiary_item, 0) + tertiary_amount
			if self.inventory[tertiary_item] == 0:
				del self.inventory[tertiary_item]
			self.write_data()
			return item, time_spent, item_amount, secondary_amount, tertiary_amount
		else:
			return False, self.last_action
	
	def create_item(self, items):
		'''Create/Craft an item'''
		for item in items:
			if item not in self.inventory:
				return None
		sorted_items = tuple(sorted(items))
		if sorted_items not in craftables:
			return False
		crafted_item = craftables[sorted_items]
		for item in items:
			self.inventory[item] -= 1
			if self.inventory[item] == 0:
				del self.inventory[item]
		self.inventory[crafted_item] = self.inventory.get(crafted_item, 0) + 1
		return crafted_item
	
	def start_woodcutting(self, wood_type):
		if self.last_action is not None:
			return self.last_action[0]
		elif wood_type.lower() in wood_types:
			self.last_action = ("woodcutting", wood_type)
			self.last_action_time = time.time()
			self.write_data()
			return True
		else:
			return False
	
	def stop_woodcutting(self):
		if self.last_action and self.last_action[0] == "woodcutting":
			wood_type = self.last_action[1]
			time_spent = math.ceil(time.time() - self.last_action_time) / 60
			self.last_action = None
			self.last_action = None
			current_wood_lvl = wood_lvl(wood_type)
			wood_amount = math.floor(time_spent * self.wood_rate(wood_type) * self.woodcutting_rate)
			xp_amount = current_wood_lvl * wood_amount
			self.inventory[wood_type] = self.inventory.get(wood_type, 0) + wood_amount
			if self.inventory[wood_type] == 0:
				del self.inventory[wood_type]
			self.woodcutting_xp += xp_amount
			self.write_data()
			return wood_type, time_spent, wood_amount, xp_amount
		else:
			return False, self.last_action
	
	def chop_once(self, wood_type):
		'''Chop a tree once'''
		wood = self.inventory[wood_type] = self.inventory.get(wood_type, 0) + 1
		xp = self.woodcutting_xp = self.woodcutting_xp + wood_lvl(wood_type)
		self.write_data()
		return wood, xp

for info in initial_data:
	def set_info(self, value, info = info): self.data[info] = value # write_data?
	setattr(AdventurePlayer, info, property(lambda self, info = info: self.data[info], set_info))

for skill in skills:
	def set_xp(self, value, skill = skill): self.data["xp"][skill] = value # write data?
	setattr(AdventurePlayer, skill + "_xp", property(lambda self, skill = skill: self.data["xp"][skill], set_xp))
	setattr(AdventurePlayer, skill + "_lvl", property(lambda self, skill = skill: xp_to_lvl(self.data["xp"][skill])))
	setattr(AdventurePlayer, skill + "_rate", property(lambda self, skill = skill: xp_to_rate(self.data["xp"][skill])))

