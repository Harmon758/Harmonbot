
import discord

# import aiohttp
from collections import OrderedDict
import json
import math
import os
import re

# Utility

def is_number(characters):
	try:
		float(characters)
		return True
	except ValueError:
		return False

def is_hex(characters):
    try:
        int(characters, 16)
        return True
    except ValueError:
        return False

'''
import string
def is_hex(s):
     hex_digits = set(string.hexdigits)
     # if s is long, then it is faster to check against a set
     return all(c in hex_digits for c in s)
'''

def message_is_digit_gtz(m):
	return m.content.isdigit() and m.content != '0'

def is_digit_gtz(s):
	return s.isdigit() and s != '0'

def secs_to_duration(secs):
	duration = []
	time_in_secs = [31536000, 604800, 86400, 3600, 60]
	# years, weeks, days, hours, minutes
	for length_of_time in time_in_secs:
		if secs > length_of_time:
			duration.append(int(math.floor(secs / length_of_time)))
			secs -= math.floor(secs / length_of_time) * length_of_time
		else:
			duration.append(0)
	duration.append(int(secs))
	return duration

def duration_to_letter_format(duration):
	output = ""
	letters = ["y", "w", "d", "h", "m", "s"]
	for i in range(6):
		if duration[i]:
			output += str(duration[i]) + letters[i] + ' '
	return output[:-1]

def duration_to_colon_format(duration):
	output = ""
	started = False
	for i in range(6):
		if duration[i]:
			started = True
			output += str(duration[i]) + ":"
		elif started:
			output += "00:"
	return output[:-1]

def secs_to_letter_format(secs):
	return duration_to_letter_format(secs_to_duration(secs))

def secs_to_colon_format(secs):
	return duration_to_colon_format(secs_to_duration(secs))

def add_commas(number):
	try:
		return "{:,}".format(number)
	except:
		return number

def remove_symbols(string):
	plain_string = ""
	for character in string:
		if 0 <= ord(character) <= 127:
			plain_string += character
	if plain_string.startswith(' '):
		plain_string = plain_string[1:]
	return plain_string

def create_file(filename, *, content = {}):
	try:
		with open("data/{}.json".format(filename), "x") as file:
			json.dump(content, file)
	except FileExistsError:
		pass

def create_folder(folder):
	if not os.path.exists(folder):
		os.makedirs(folder)

# Discord

def get_permission(ctx, permission, *, type = "user", id = None):
	try:
		with open("data/permissions/{}.json".format(ctx.message.server.id), "x+") as permissions_file:
			json.dump({"name" : ctx.message.server.name}, permissions_file, indent = 4)
	except FileExistsError:
		pass
	else:
		return None
	with open("data/permissions/{}.json".format(ctx.message.server.id), "r") as permissions_file:
		permissions_data = json.load(permissions_file)
	if type == "everyone":
		return permissions_data.get("everyone", {}).get(permission)
	elif type == "role":
		role_setting = permissions_data.get("roles", {}).get(id, {}).get(permission)
		return role_setting if role_setting is not None else permissions_data.get("everyone", {}).get(permission)
	elif type == "user":
		user_setting = permissions_data.get("users", {}).get(id, {}).get(permission)
		if user_setting is not None: return user_setting
		user = discord.utils.get(ctx.message.server.members, id = id)
		role_positions = {}
		for role in user.roles:
			role_positions[role.position] = role
		sorted_role_positions = OrderedDict(sorted(role_positions.items(), reverse = True))
		for role_position, role in sorted_role_positions.items():
			role_setting = permissions_data.get("roles", {}).get(role.id, {}).get(permission)
			if role_setting is not None: return role_setting
		return permissions_data.get("everyone", {}).get(permission)

async def get_user(ctx, name):
	# check if mention
	mention = re.match(r"<@\!?([0-9]+)>", name)
	if mention:
		user_id = mention.group(1)
		user = ctx.message.server.get_member(user_id)
		if user: return user
	if ctx.message.server:
		# check if exact match
		matches = [member for member in ctx.message.server.members if member.name == name or member.nick == name]
		if len(matches) == 1:
			return matches[0]
		elif len(matches) > 1:
			members = ""
			for index, member in enumerate(matches, 1):
				members += "{}: {}".format(str(index), str(member))
				if member.nick: members += " ({})".format(member.nick)
				members += '\n'
			await ctx.bot.say("Multiple users with the name, {}. Which one did you mean?\n"
			"**Enter the number it is in the list.**".format(name))
			await ctx.bot.say(members)
			message = await ctx.bot.wait_for_message(author = ctx.message.author, check = lambda m: m.content.isdigit() and 1 <= int(m.content) <= len(matches))
			return matches[int(message.content) - 1]
		# check if beginning match
		start_matches = [member for member in ctx.message.server.members if member.name.startswith(name) or member.nick and member.nick.startswith(name)]
		if len(start_matches) == 1:
			return start_matches[0]
		elif len(start_matches) > 1:
			members = ""
			for index, member in enumerate(start_matches, 1):
				members += "{}: {}".format(str(index), str(member))
				if member.nick: members += " ({})".format(member.nick)
				members += '\n'
			await ctx.bot.reply("Multiple users with names starting with {}. Which one did you mean? **Enter the number.**".format(name))
			await ctx.bot.say(members)
			message = await ctx.bot.wait_for_message(author = ctx.message.author, check = lambda m: m.content.isdigit() and 1 <= int(m.content) <= len(start_matches))
			return start_matches[int(message.content) - 1]
	# check if with discriminator
	user_info = re.match(r"^(.+)#(\d{4})", name)
	if user_info:
		user_name = user_info.group(1)
		user_discriminator = user_info.group(2)
		user = discord.utils.find(lambda m: m.name == user_name and str(m.discriminator) == user_discriminator, ctx.bot.get_all_members())
		if user: return user
	return None

