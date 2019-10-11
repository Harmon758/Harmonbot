
import discord
from discord.ext import commands

from modules import utilities
from utilities import checks

def setup(bot):
	bot.add_cog(Permissions(bot))

class Permissions(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		
		self.bot.loop.create_task(self.initialize_database())
	
	async def initialize_database(self):
		await self.bot.connect_to_database()
		await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS permissions")
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS permissions.everyone (
				guild_id		BIGINT, 
				permission		TEXT, 
				setting			BOOL, 
				PRIMARY KEY		(guild_id, permission)
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS permissions.roles (
				guild_id		BIGINT, 
				role_id			BIGINT, 
				permission		TEXT, 
				setting			BOOL, 
				PRIMARY KEY		(guild_id, role_id, permission)
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS permissions.users (
				guild_id		BIGINT, 
				user_id			BIGINT, 
				permission		TEXT, 
				setting			BOOL, 
				PRIMARY KEY		(guild_id, user_id, permission)
			)
			"""
		)
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.is_permitted()
	async def setpermission(self, ctx):
		'''Set a permission'''
		await ctx.send_help(ctx.command)
	
	@setpermission.command(name = "everyone")
	@commands.guild_only()
	@checks.is_permitted()
	async def setpermission_everyone(self, ctx, permission: str, setting: bool = None):
		if permission not in self.bot.all_commands:
			return await ctx.embed_reply(f"Error: {permission} is not a command")
		await self.bot.db.execute(
			"""
			INSERT INTO permissions.everyone (guild_id, permission, setting)
			VALUES ($1, $2, $3)
			ON CONFLICT (guild_id, permission) DO
			UPDATE SET setting = $3
			""", 
			ctx.guild.id, self.bot.all_commands[permission].name, setting
		)
		await ctx.embed_reply("Permission updated\n"
								f"{permission} set to {setting} for everyone")
	
	@setpermission.command(name = "role")
	@commands.guild_only()
	@checks.is_permitted()
	async def setpermission_role(self, ctx, role: discord.Role, permission: str, setting: bool = None):
		if permission not in self.bot.all_commands:
			return await ctx.embed_reply(f"Error: {permission} is not a command")
		await self.bot.db.execute(
			"""
			INSERT INTO permissions.roles (guild_id, role_id, permission, setting)
			VALUES ($1, $2, $3, $4)
			ON CONFLICT (guild_id, role_id, permission) DO
			UPDATE SET setting = $4
			""", 
			ctx.guild.id, role.id, self.bot.all_commands[permission].name, setting
		)
		await ctx.embed_reply("Permission updated\n"
								f"{permission} set to {setting} for the {role.name} role")
	
	@setpermission.command(name = "user")
	@commands.guild_only()
	@checks.is_permitted()
	async def setpermission_user(self, ctx, user: str, permission: str, setting: bool = None):
		if permission not in self.bot.all_commands:
			return await ctx.embed_reply(f"Error: {permission} is not a command")
		_user = await utilities.get_user(ctx, user)
		if not _user:
			return await ctx.embed_reply("Error: user not found")
		await self.bot.db.execute(
			"""
			INSERT INTO permissions.users (guild_id, user_id, permission, setting)
			VALUES ($1, $2, $3, $4)
			ON CONFLICT (guild_id, user_id, permission) DO
			UPDATE SET setting = $4
			""", 
			ctx.guild.id, _user.id, self.bot.all_commands[permission].name, setting
		)
		await ctx.embed_reply("Permission updated\n"
								f"{permission} set to {setting} for {_user}")
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@commands.guild_only()
	@checks.is_permitted()
	async def getpermission(self, ctx, *options : str):
		'''Get a permission'''
		if len(options) == 2:
			if options[1] not in self.bot.all_commands: return (await ctx.embed_reply("Error: {} is not a command".format(options[1])))
			command = self.bot.all_commands[options[1]].name
			user = await utilities.get_user(ctx, options[0])
			if not user: return (await ctx.embed_reply("Error: user not found"))
			setting = await ctx.get_permission(command, id = user.id)
			await ctx.embed_reply("{} is set to {} for {}".format(options[1], setting, user))
		else:
			await ctx.embed_reply(":no_entry: Invalid input\ngetpermission everyone|role|user or <user> <permission>") #options
	
	@getpermission.command(name = "everyone")
	@commands.guild_only()
	@checks.is_permitted()
	async def getpermission_everyone(self, ctx, permission : str):
		if permission not in self.bot.all_commands: return (await ctx.embed_reply("Error: {} is not a command".format(permission)))
		command = self.bot.all_commands[permission].name
		setting = await ctx.get_permission(command, type = "everyone")
		await ctx.embed_reply("{} is set to {} for everyone".format(permission, setting))
	
	@getpermission.command(name = "role")
	@commands.guild_only()
	@checks.is_permitted()
	async def getpermission_role(self, ctx, role : str, permission : str):
		if permission not in self.bot.all_commands: return (await ctx.embed_reply("Error: {} is not a command".format(permission)))
		command = self.bot.all_commands[permission].name
		matches = [_role for _role in ctx.guild.roles if _role.name == role]
		if len(matches) > 1: return (await ctx.embed_reply("Error: multiple roles with the name, {}".format(role)))
		elif len(matches) == 0: return (await ctx.embed_reply('Error: role with name, "{}", not found'.format(role)))
		else: _role = matches[0]
		setting = await ctx.get_permission(command, type = "role", id = _role.id)
		await ctx.embed_reply("{} is set to {} for the {} role".format(permission, setting, _role.name))
	
	@getpermission.command(name = "user")
	@commands.guild_only()
	@checks.is_permitted()
	async def getpermission_user(self, ctx, user : str, permission : str):
		if permission not in self.bot.all_commands: return (await ctx.embed_reply("Error: {} is not a command".format(permission)))
		command = self.bot.all_commands[permission].name
		_user = await utilities.get_user(ctx, user)
		if not _user: return (await ctx.embed_reply("Error: user not found"))
		setting = await ctx.get_permission(command, id = _user.id)
		await ctx.embed_reply("{} is set to {} for {}".format(permission, setting, _user))
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.is_permitted()
	async def getpermissions(self, ctx):
		await ctx.send_help(ctx.command)
	
	@getpermissions.command(name = "everyone")
	@commands.guild_only()
	@checks.is_permitted()
	async def getpermissions_everyone(self, ctx):
		records = await ctx.bot.db.fetch(
			"""
			SELECT permission, setting FROM permissions.everyone
			WHERE guild_id = $1
			""", 
			ctx.guild.id
		)
		output = "__Permissions for everyone__\n"
		for record in records:
			output += "{}: {}\n".format(record["permission"], str(record["setting"]))
		await ctx.send(output)
	
	@getpermissions.command(name = "role")
	@commands.guild_only()
	@checks.is_permitted()
	async def getpermissions_role(self, ctx, role : str):
		matches = [_role for _role in ctx.guild.roles if _role.name == role]
		if len(matches) > 1: return (await ctx.embed_reply("Error: multiple roles with the name, {}".format(role)))
		elif len(matches) == 0: return (await ctx.embed_reply('Error: role with name, "{}", not found'.format(role)))
		else: _role = matches[0]
		records = await ctx.bot.db.fetch(
			"""
			SELECT permission, setting FROM permissions.roles
			WHERE guild_id = $1 AND role_id = $2
			""", 
			ctx.guild.id, _role.id
		)
		output = "__Permissions for {}__\n".format(_role.name)
		for record in records:
			output += "{}: {}\n".format(record["permission"], str(record["setting"]))
		await ctx.send(output)
	
	@getpermissions.command(name = "user")
	@commands.guild_only()
	@checks.is_permitted()
	async def getpermissions_user(self, ctx, user : str):
		_user = await utilities.get_user(ctx, user)
		if not _user: return (await ctx.embed_reply("Error: user not found"))
		records = await ctx.bot.db.fetch(
			"""
			SELECT permission, setting FROM permissions.users
			WHERE guild_id = $1 AND user_id = $2
			""", 
			ctx.guild.id, _user.id
		)
		output = "__Permissions for {}__\n".format(_user.name)
		for record in records:
			output += "{}: {}\n".format(record["permission"], str(record["setting"]))
		await ctx.send(output)
	
	@getpermissions.command(name = "command")
	@commands.guild_only()
	@checks.is_permitted()
	async def getpermissions_command(self, ctx, command : str):
		if command not in self.bot.all_commands: return (await ctx.embed_reply("Error: {} is not a command".format(command)))
		output = "__Permissions for {}__\n".format(command)
		setting = await ctx.bot.db.fetchval(
			"""
			SELECT setting FROM permissions.everyone
			WHERE guild_id = $1 AND permission = $2
			""", 
			ctx.guild.id, command
		)
		output += "**Everyone**: {}\n".format(setting)
		output += "**Roles**\n"
		records = await ctx.bot.db.fetch(
			"""
			SELECT role_id, setting FROM permissions.roles
			WHERE guild_id = $1 AND permission = $2
			""", 
			ctx.guild.id, command
		)
		for record in records:
			output += "{}: {}\n".format(ctx.guild.get_role(record["role_id"]), str(record["setting"]))
			# TODO: Handle role no longer existing
		output += "**Users**\n"
		records = await ctx.bot.db.fetch(
			"""
			SELECT user_id, setting FROM permissions.users
			WHERE guild_id = $1 AND permission = $2
			""", 
			ctx.guild.id, command
		)
		for record in records:
			output += "{}: {}\n".format(ctx.bot.get_user(record["user_id"]), str(record["setting"]))
			# TODO: Handle user no longer visible
		await ctx.send(output)

