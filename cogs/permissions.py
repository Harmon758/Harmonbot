
import discord
from discord.ext import commands

import json

from modules import utilities
from utilities import checks

def setup(bot):
	bot.add_cog(Permissions(bot))

class Permissions:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.group(invoke_without_command = True)
	@checks.is_permitted()
	async def setpermission(self):
		'''Set a permission'''
		await self.bot.reply("Invalid input. setpermission everyone|role|user")
	
	@setpermission.command(name = "everyone", pass_context = True)
	@checks.is_server_owner() #or permitted
	async def setpermission_everyone(self, ctx, permission : str, setting : bool = None):
		if permission not in self.bot.commands: return (await self.bot.reply("Error: {} is not a command.".format(permission)))
		command = self.bot.commands[permission].name
		with open("data/permissions/{}.json".format(ctx.message.server.id), "r") as permissions_file:
			permissions_data = json.load(permissions_file)
		permissions_data.setdefault("everyone", {})
		permissions_data["everyone"][command] = setting
		with open("data/permissions/{}.json".format(ctx.message.server.id), "w") as permissions_file:
			json.dump(permissions_data, permissions_file, indent = 4)		
		await self.bot.reply("Permission updated. {} set to {} for everyone".format(permission, setting))
	
	@setpermission.command(name = "role", pass_context = True)
	@checks.is_server_owner() #or permitted
	async def setpermission_role(self, ctx, role : str, permission : str, setting : bool = None):
		if permission not in self.bot.commands: return (await self.bot.reply("Error: {} is not a command.".format(permission)))
		command = self.bot.commands[permission].name
		matches = [_role for _role in ctx.message.server.roles if _role.name == role]
		if len(matches) > 1: return (await self.bot.reply("Error: multiple roles with the name, {}.".format(role)))
		elif len(matches) == 0: return (await self.bot.reply('Error: role with name, "{}", not found'.format(role)))
		else: _role = matches[0]
		with open("data/permissions/{}.json".format(ctx.message.server.id), "r") as permissions_file:
			permissions_data = json.load(permissions_file)
		permissions_data.setdefault("roles", {})
		permissions_data["roles"].setdefault(_role.id, {"name" : _role.name})
		permissions_data["roles"][_role.id][command] = setting
		with open("data/permissions/{}.json".format(ctx.message.server.id), "w") as permissions_file:
			json.dump(permissions_data, permissions_file, indent = 4)		
		await self.bot.reply("Permission updated. {} set to {} for the {} role".format(permission, setting, _role.name))
	
	@setpermission.command(name = "user", pass_context = True)
	@checks.is_server_owner() #or permitted
	async def setpermission_user(self, ctx, user : str, permission : str, setting : bool = None):
		if permission not in self.bot.commands: return (await self.bot.reply("Error: {} is not a command.".format(permission)))
		command = self.bot.commands[permission].name
		_user = await utilities.get_user(ctx, user)
		if not _user: return (await self.bot.reply("Error: user not found."))
		with open("data/permissions/{}.json".format(ctx.message.server.id), "r") as permissions_file:
			permissions_data = json.load(permissions_file)
		permissions_data.setdefault("users", {})
		permissions_data["users"].setdefault(_user.id, {"name" : _user.name})
		permissions_data["users"][_user.id][command] = setting
		with open("data/permissions/{}.json".format(ctx.message.server.id), "w") as permissions_file:
			json.dump(permissions_data, permissions_file, indent = 4)
		await self.bot.reply("Permission updated. {} set to {} for {}".format(permission, setting, _user))
	
	@commands.group(invoke_without_command = True, pass_context = True)
	@checks.is_permitted()
	async def getpermission(self, ctx, *options : str):
		'''Get a permission'''
		if len(options) == 2:
			if options[1] not in self.bot.commands: return (await self.bot.reply("Error: {} is not a command.".format(options[1])))
			command = self.bot.commands[options[1]].name
			user = await utilities.get_user(ctx, options[0])
			if not user: return (await self.bot.reply("Error: user not found."))
			setting = utilities.get_permission(ctx, command, id = user.id)
			await self.bot.reply("{} is set to {} for {}".format(options[1], setting, user))
		else:
			await self.bot.reply("Invalid input. getpermission everyone|role|user or <user> <permission>") #options
	
	@getpermission.command(name = "everyone", pass_context = True)
	@checks.is_server_owner()
	async def getpermission_everyone(self, ctx, permission : str):
		if permission not in self.bot.commands: return (await self.bot.reply("Error: {} is not a command.".format(permission)))
		command = self.bot.commands[permission].name
		setting = utilities.get_permission(ctx, command, type = "everyone")
		await self.bot.reply("{} is set to {} for everyone".format(permission, setting))
	
	@getpermission.command(name = "role", pass_context = True)
	@checks.is_server_owner()
	async def getpermission_role(self, ctx, role : str, permission : str):
		if permission not in self.bot.commands: return (await self.bot.reply("Error: {} is not a command.".format(permission)))
		command = self.bot.commands[permission].name
		matches = [_role for _role in ctx.message.server.roles if _role.name == role]
		if len(matches) > 1: return (await self.bot.reply("Error: multiple roles with the name, {}.".format(role)))
		elif len(matches) == 0: return (await self.bot.reply('Error: role with name, "{}", not found'.format(role)))
		else: _role = matches[0]
		setting = utilities.get_permission(ctx, command, type = "role", id = _role.id)
		await self.bot.reply("{} is set to {} for the {} role".format(permission, setting, _role.name))
	
	@getpermission.command(name = "user", pass_context = True)
	@checks.is_server_owner()
	async def getpermission_user(self, ctx, user : str, permission : str):
		if permission not in self.bot.commands: return (await self.bot.reply("Error: {} is not a command.".format(permission)))
		command = self.bot.commands[permission].name
		_user = await utilities.get_user(ctx, user)
		if not _user: return (await self.bot.reply("Error: user not found."))
		setting = utilities.get_permission(ctx, command, id = _user.id)
		await self.bot.reply("{} is set to {} for {}".format(permission, setting, _user))
	
	@commands.group(invoke_without_command = True)
	@checks.is_permitted()
	async def getpermissions(self):
		return
	
	@getpermissions.command(name = "everyone", pass_context = True)
	@checks.is_server_owner()
	async def getpermissions_everyone(self, ctx):
		with open("data/permissions/{}.json".format(ctx.message.server.id), "r") as permissions_file:
			permissions_data = json.load(permissions_file)
		everyone_settings = permissions_data.get("everyone", {})
		output = "__Permissions for everyone__\n"
		for permission, setting in everyone_settings.items():
			output += "{}: {}\n".format(permission, str(setting))
		await self.bot.say(output)
	
	@getpermissions.command(name = "role", pass_context = True)
	@checks.is_server_owner()
	async def getpermissions_role(self, ctx, role : str):
		matches = [_role for _role in ctx.message.server.roles if _role.name == role]
		if len(matches) > 1: return (await self.bot.reply("Error: multiple roles with the name, {}.".format(role)))
		elif len(matches) == 0: return (await self.bot.reply('Error: role with name, "{}", not found'.format(role)))
		else: _role = matches[0]
		with open("data/permissions/{}.json".format(ctx.message.server.id), "r") as permissions_file:
			permissions_data = json.load(permissions_file)
		role_settings = permissions_data.get("roles", {}).get(_role.id, {})
		output = "__Permissions for {}__\n".format(_role.name)
		role_settings.pop("name", None)
		for permission, setting in role_settings.items():
			output += "{}: {}\n".format(permission, str(setting))
		await self.bot.say(output)
	
	@getpermissions.command(name = "user", pass_context = True)
	@checks.is_server_owner()
	async def getpermissions_user(self, ctx, user : str):
		_user = await utilities.get_user(ctx, user)
		if not _user: return (await self.bot.reply("Error: user not found."))
		with open("data/permissions/{}.json".format(ctx.message.server.id), "r") as permissions_file:
			permissions_data = json.load(permissions_file)
		user_settings = permissions_data.get("users", {}).get(_user.id, {})
		output = "__Permissions for {}__\n".format(_user.name)
		user_settings.pop("name", None)
		for permission, setting in user_settings.items():
			output += "{}: {}\n".format(permission, str(setting))
		await self.bot.say(output)
	
	@getpermissions.command(name = "command", pass_context = True)
	@checks.is_server_owner()
	async def getpermissions_command(self, ctx, command : str):
		if command not in self.bot.commands: return (await self.bot.reply("Error: {} is not a command.".format(command)))
		with open("data/permissions/{}.json".format(ctx.message.server.id), "r") as permissions_file:
			permissions_data = json.load(permissions_file)
		output = "__Permissions for {}__\n".format(command)
		permissions_data.pop("name", None)
		if command in permissions_data.get("everyone", {}):
			output += "**Everyone**: {}\n".format(permissions_data.pop("everyone")[command])
		for type, objects in permissions_data.items():
			output += "**{}**\n".format(type.capitalize())
			for id, settings in objects.items():
				if command in settings:
					output += "{}: {}\n".format(settings["name"], str(settings[command]))
		await self.bot.say(output)

