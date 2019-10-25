
import discord
from discord.ext import commands

import copy
# import inspect
import math
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

def secs_to_duration(secs, limit = 0):
	duration = []
	time_in_secs = [31536000, 604800, 86400, 3600, 60]
	# years, weeks, days, hours, minutes
	for length_of_time in time_in_secs:
		if (limit and length_of_time > limit) or secs < length_of_time:
			duration.append(0)
		else:
			duration.append(int(math.floor(secs / length_of_time)))
			secs -= math.floor(secs / length_of_time) * length_of_time
	duration.append(int(secs))
	return duration

def duration_to_letter_format(duration):
	return ' '.join(filter(None, ["{}{}".format(duration[i], letter) if duration[i] else "" for i, letter in enumerate(['y', 'w', 'd', 'h', 'm', 's'])])) or "0s"

def duration_to_colon_format(duration):
	return ':'.join([str(unit).rjust(2, '0') if unit else "00" for unit in duration]).lstrip("0:").rjust(2, '0').rjust(3, ':').rjust(4, '0')

def secs_to_letter_format(secs, limit = 0):
	return duration_to_letter_format(secs_to_duration(secs, limit = limit))

def secs_to_colon_format(secs, limit = 0):
	return duration_to_colon_format(secs_to_duration(secs, limit = limit))

def remove_symbols(string):
	plain_string = ""
	for character in string:
		if 0 <= ord(character) <= 127:
			plain_string += character
	if plain_string.startswith(' '):
		plain_string = plain_string[1:]
	return plain_string

# https://en.wikipedia.org/wiki/Unicode_subscripts_and_superscripts#Superscripts_and_subscripts_block

def superscript(string):
	superscripts = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹', '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾', 'i': 'ⁱ	', 'n': 'ⁿ'}
	return "".join(superscripts.get(c, c) for c in str(string))

def subscript(string):
	subscripts = {'0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉', '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎', 'a': 'ₐ', 'e': 'ₑ', 'o': 'ₒ', 'x': 'ₓ', 'ə': 'ₔ', 'h': 'ₕ', 'k': 'ₖ', 'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ', 'p': 'ₚ', 's': 'ₛ', 't': 'ₜ'}
	return "".join(subscripts.get(c, c) for c in str(string))

# Discord

async def get_user(ctx, name):
	# check if mention
	mention = re.match(r"<@\!?([0-9]+)>", name)
	if mention:
		user_id = mention.group(1)
		user = await ctx.bot.fetch_user(user_id)
		if user: return user
	if ctx.guild:
		# check if exact match
		matches = [member for member in ctx.guild.members if member.name == name or member.nick == name]
		if len(matches) == 1:
			return matches[0]
		elif len(matches) > 1:
			members = ""
			for index, member in enumerate(matches, 1):
				members += "{}: {}".format(str(index), str(member))
				if member.nick: members += " ({})".format(member.nick)
				members += '\n'
			await ctx.embed_reply("Multiple users with the name, {}. Which one did you mean?\n"
			"**Enter the number it is in the list.**\n".format(name) + members)
			message = await ctx.bot.wait_for("message", check = lambda m: m.author == ctx.author and m.content.isdigit() and 1 <= int(m.content) <= len(matches))
			return matches[int(message.content) - 1]
		# check if beginning match
		start_matches = [member for member in ctx.guild.members if member.name.startswith(name) or member.nick and member.nick.startswith(name)]
		if len(start_matches) == 1:
			return start_matches[0]
		elif len(start_matches) > 1:
			members = ""
			for index, member in enumerate(start_matches, 1):
				members += "{}: {}".format(str(index), str(member))
				if member.nick: members += " ({})".format(member.nick)
				members += '\n'
			await ctx.embed_reply("Multiple users with names starting with {}. Which one did you mean? **Enter the number.**\n".format(name) + members)
			message = await ctx.bot.wait_for("message", check = lambda m: m.author == ctx.author and m.content.isdigit() and 1 <= int(m.content) <= len(start_matches))
			return start_matches[int(message.content) - 1]
	# check if with discriminator
	user_info = re.match(r"^(.+)#(\d{4})", name)
	if user_info:
		user_name = user_info.group(1)
		user_discriminator = user_info.group(2)
		user = discord.utils.find(lambda m: m.name == user_name and str(m.discriminator) == user_discriminator, ctx.bot.get_all_members())
		if user: return user
	return None

# Commands

def add_as_subcommand(cog, command, parent_name, subcommand_name, *, aliases = []):
	if isinstance(parent_name, commands.Command):
		parent = parent_name
		# parent_cog = cog.bot.get_cog(parent.cog_name)
		parent_cog = parent.cog
		parent_command_name = parent.name
	else:
		parent_cog_name, parent_command_name = parent_name.split('.')
		parent_cog = cog.bot.get_cog(parent_cog_name)
		parent = getattr(parent_cog, parent_command_name, None)
		if not parent: return
	subcommand = copy.copy(command)
	subcommand.name = subcommand_name
	subcommand.aliases = aliases
	subcommand.parent = parent
	subcommand.cog = parent_cog
	if isinstance(subcommand, commands.Group):
		for subsubcommand in subcommand.commands:
			subsubcommand.parent = subcommand
	# async def wrapper(*args, **kwargs):
	# async def wrapper(*args, command = command, **kwargs):
	# 	await command.callback(cog, *args, **kwargs)
	# subcommand.callback = wrapper
	# subcommand.params = inspect.signature(subcommand.callback).parameters.copy()
	setattr(parent_cog, "{}_{}".format(parent_command_name, subcommand_name), subcommand)
	parent.add_command(subcommand)

def remove_as_subcommand(cog, parent_name, subcommand_name):
	parent_cog_name, parent_command_name = parent_name.split('.')
	parent = getattr(cog.bot.get_cog(parent_cog_name), parent_command_name, None)
	if parent: parent.remove_command(subcommand_name)

