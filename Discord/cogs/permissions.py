
import discord
from discord.ext import commands

from typing import Optional, Union

from utilities import checks

async def setup(bot):
	await bot.add_cog(Permissions(bot))

class Permissions(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
	
	async def cog_load(self):
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
	@checks.not_forbidden()
	async def setpermission(self, ctx):
		'''Set a permission'''
		await ctx.send_help(ctx.command)
	
	@setpermission.command(name = "everyone")
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	@commands.guild_only()
	async def setpermission_everyone(self, ctx, permission: str, setting: Optional[bool]):
		'''Set a permission for everyone'''
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
		await ctx.embed_reply(f"{permission} set to {setting} for everyone", 
								title = "Permission Updated")
	
	@setpermission.command(name = "role")
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	@commands.guild_only()
	async def setpermission_role(self, ctx, role: discord.Role, permission: str, setting: Optional[bool]):
		'''Set a permission for a role'''
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
		await ctx.embed_reply(f"{permission} set to {setting} for the role, {role.mention}", 
								title = "Permission Updated")
	
	@setpermission.command(name = "user", aliases = ["member"])
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	@commands.guild_only()
	async def setpermission_user(self, ctx, user: discord.Member, permission: str, setting: Optional[bool]):
		'''Set a permission for a user'''
		if permission not in self.bot.all_commands:
			return await ctx.embed_reply(f"Error: {permission} is not a command")
		await self.bot.db.execute(
			"""
			INSERT INTO permissions.users (guild_id, user_id, permission, setting)
			VALUES ($1, $2, $3, $4)
			ON CONFLICT (guild_id, user_id, permission) DO
			UPDATE SET setting = $4
			""", 
			ctx.guild.id, user.id, self.bot.all_commands[permission].name, setting
		)
		await ctx.embed_reply(f"{permission} set to {setting} for {user.mention}", 
								title = "Permission Updated")
	
	@commands.command()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	@commands.guild_only()
	async def getpermission(self, ctx, permission, users: Optional[Union[discord.Member, discord.Role]]):
		'''
		Get a permission for a user, role, or everyone
		Defaults to everyone if no user or role is specified
		'''
		if permission not in self.bot.all_commands:
			return await ctx.embed_reply(f"Error: {permission} is not a command")
		if not users:
			setting = await ctx.get_permission(self.bot.all_commands[permission].name, type = "everyone")
			return await ctx.embed_reply(f"{permission} is set to {setting} for everyone")
		if isinstance(users, discord.Member):
			setting = await ctx.get_permission(self.bot.all_commands[permission].name, user = users)
			return await ctx.embed_reply(f"{permission} is set to {setting} for {users.mention}")
		if isinstance(users, discord.Role):
			setting = await ctx.get_permission(self.bot.all_commands[permission].name, 
												type = "role", id = users.id)
			return await ctx.embed_reply(f"{permission} is set to {setting} for the role, {users.mention}")
	
	@commands.command()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	@commands.guild_only()
	async def getpermissions(self, ctx, subject: Optional[Union[discord.Member, discord.Role, str]]):
		'''
		Get permissions for a user, role, command, or everyone
		Defaults to everyone if no user, role, or command is specified or found
		'''
		if isinstance(subject, (discord.Member, discord.Role)):
			subject_type = type(subject).__name__.lower().replace("member", "user")
			records = await ctx.bot.db.fetch(
				f"""
				SELECT permission, setting FROM permissions.{subject_type}s
				WHERE guild_id = $1 AND {subject_type}_id = $2
				""", 
				ctx.guild.id, subject.id
			)
			return await ctx.embed_reply('\n'.join(f"{record['permission']}: `{record['setting']}`" for record in records), 
											title = f"Permissions for {subject_type}: {subject}")
		if subject and subject in self.bot.all_commands:
			setting = await ctx.bot.db.fetchval(
				"""
				SELECT setting FROM permissions.everyone
				WHERE guild_id = $1 AND permission = $2
				""", 
				ctx.guild.id, subject
			)
			fields = [("Everyone", f"`{setting}`")]
			for permission_type in ("role", "user"):
				records = await ctx.bot.db.fetch(
					f"""
					SELECT {permission_type}_id, setting FROM permissions.{permission_type}s
					WHERE guild_id = $1 AND permission = $2
					""", 
					ctx.guild.id, subject
				)
				getter = {"role": ctx.guild.get_role, "user": ctx.bot.get_user}[permission_type]
				fields.append((f"{permission_type.capitalize()}s", 
								'\n'.join(f"{getter(record[f'{permission_type}_id']).mention}: `{record['setting']}`"
											for record in records)))
				# TODO: Handle role/user no longer existing
			return await ctx.embed_reply(title = f"Permissions for command: {subject}", fields = fields)
		records = await ctx.bot.db.fetch(
			"""
			SELECT permission, setting FROM permissions.everyone
			WHERE guild_id = $1
			""", 
			ctx.guild.id
		)
		await ctx.embed_reply('\n'.join(f"{record['permission']}: `{record['setting']}`" for record in records), 
										title = "Permissions for everyone")

