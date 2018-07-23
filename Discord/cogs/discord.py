
import discord
from discord.ext import commands

import asyncio
import datetime

import clients
import credentials
from modules import conversions
from modules import utilities
from utilities import checks

def setup(bot):
	bot.add_cog(Discord(bot))

class Discord:
	
	def __init__(self, bot):
		self.bot = bot
	
	# TODO: Include spaces in quotes explanation (in help)
	
	
	@commands.group(aliases = ["purge", "clean"], invoke_without_command = True)
	@checks.dm_or_has_permissions_and_capability(manage_messages = True)
	async def delete(self, ctx, number : int, *, user : str = ""):
		'''
		Delete messages
		If used in a DM, delete <number> deletes <number> of Harmonbot's messages
		'''
		if isinstance(ctx.channel, discord.DMChannel):
			await self.bot.delete_number(ctx, number, check = lambda m: m.author == self.bot.user, delete_command = False)
		elif not user:
			await self.bot.attempt_delete_message(ctx.message)
			await ctx.channel.purge(limit = number)
		elif user:
			await self.delete_number(ctx, number, check = lambda m: m.author.name == user)
	
	@delete.command(name = "attachments", aliases = ["images"])
	@checks.has_permissions_and_capability(manage_messages = True)
	async def delete_attachments(self, ctx, number : int):
		'''Deletes the <number> most recent messages with attachments'''
		await self.delete_number(ctx, number, check = lambda m: m.attachments)
	
	@delete.command(name = "contains")
	@checks.has_permissions_and_capability(manage_messages = True)
	async def delete_contains(self, ctx, string : str, number : int):
		'''Deletes the <number> most recent messages with <string> in them'''
		await self.delete_number(ctx, number, check = lambda m: string in m.content)
	
	@delete.command(name = "embeds")
	@checks.has_permissions_and_capability(manage_messages = True)
	async def delete_embeds(self, ctx, number: int):
		'''Deletes the <number> most recent messages with embeds'''
		await self.delete_number(ctx, number, check = lambda m: m.embeds)
	
	@delete.command(name = "time")
	@checks.has_permissions_and_capability(manage_messages = True)
	async def delete_time(self, ctx, minutes : int):
		'''Deletes messages in the past <minutes> minutes'''
		await self.bot.attempt_delete_message(ctx.message)
		await ctx.channel.purge(limit = self.bot.delete_limit, after = datetime.datetime.utcnow() - datetime.timedelta(minutes = minutes))
	
	# TODO: delete mentions, invites?
	
	async def delete_number(self, ctx, number, check, delete_command = True):
		if number <= 0:
			await ctx.embed_reply(":no_entry: Syntax error")
			return
		to_delete = []
		count = 0
		if delete_command: await self.bot.attempt_delete_message(ctx.message)
		async for message in ctx.channel.history(limit = self.bot.delete_limit):
			if check(message):
				to_delete.append(message)
				count += 1
				if count == number:
					break
				elif len(to_delete) == 100:
					await ctx.channel.delete_messages(to_delete)
					to_delete.clear()
					await asyncio.sleep(1)
		if len(to_delete) == 1:
			await self.bot.attempt_delete_message(to_delete[0])
		elif len(to_delete) > 1:
			await ctx.channel.delete_messages(to_delete)
	
	@commands.command(aliases = ["mycolour", "my_color", "my_colour"])
	@commands.guild_only()
	@checks.not_forbidden()
	async def mycolor(self, ctx, color : str = ""):
		'''
		Return or change your color
		Currently only accepts hex color input
		'''
		# TODO: Rework
		if not color:
			color_value = ctx.author.color.value
			await ctx.embed_reply("#{}".format(conversions.inttohex(color_value)))
			return
		# check color
		try:
			color_value = int(color.strip('#'), 16)
		except ValueError:
			await ctx.embed_reply(":no_entry: Please enter a valid hex color")
			return
		role_to_change = discord.utils.get(ctx.guild.roles, name = ctx.author.name)
		if not role_to_change:
			new_role = await self.bot.create_role(ctx.guild, name = ctx.author.name, hoist = False)
			await self.bot.add_roles(ctx.author, new_role)
			new_colour = new_role.colour
			new_colour.value = color_value
			await self.bot.edit_role(ctx.guild, new_role, name = ctx.author.name, colour = new_colour)
			await ctx.embed_reply("Created your role with the color, {}".format(color))
		else:
			new_colour = role_to_change.colour
			new_colour.value = color_value
			await self.bot.edit_role(ctx.guild, role_to_change, colour = new_colour)
			await ctx.embed_reply("Changed your role color to {}".format(color))
	
	@commands.group(invoke_without_command = True)
	@checks.has_permissions_and_capability(manage_messages = True)
	async def pin(self, ctx, message_id : int):
		'''Pin message by message ID'''
		message = await ctx.channel.get_message(message_id)
		await message.pin()
		await ctx.embed_reply(":pushpin: Pinned message")
	
	@pin.command(name = "first")
	@checks.has_permissions_and_capability(manage_messages = True)
	async def pin_first(self, ctx):
		'''Pin first message'''
		message = await ctx.channel.history(after = ctx.channel, limit = 1).iterate()
		await message.pin()
		await ctx.embed_reply(":pushpin: Pinned first message in this channel")
	
	@commands.command()
	@checks.has_permissions_and_capability(manage_messages = True)
	async def unpin(self, ctx, message_id : int):
		'''Unpin message by message ID'''
		message = await ctx.channel.get_message(message_id)
		await message.unpin()
		await ctx.embed_reply(":wastebasket: Unpinned message")
	
	@commands.command()
	@commands.guild_only()
	@checks.not_forbidden()
	async def tempchannel(self, ctx, *options : str):
		'''
		Create temporary voice and text channels
		options: allow <friend>
		'''
		temp_voice_channel = discord.utils.get(ctx.guild.channels, name = ctx.author.display_name + "'s Temp Channel")
		temp_text_channel = discord.utils.get(ctx.guild.channels, name = ctx.author.display_name.lower() + "s_temp_channel")
		if temp_voice_channel and options and options[0] == "allow":
			to_allow = discord.utils.get(ctx.guild.members, name = options[1])
			if not to_allow:
				await ctx.embed_reply(":no_entry: User not found")
			voice_channel_permissions = discord.Permissions.none()
			voice_channel_permissions.connect = True
			voice_channel_permissions.speak = True
			voice_channel_permissions.use_voice_activation = True
			await self.bot.edit_channel_permissions(temp_voice_channel, to_allow, allow = voice_channel_permissions)
			text_channel_permissions = discord.Permissions.text()
			text_channel_permissions.manage_messages = False
			await self.bot.edit_channel_permissions(temp_text_channel, to_allow, allow = text_channel_permissions)
			await ctx.embed_reply("You have allowed " + to_allow.display_name + " to join your temporary voice and text channel")
			return
		if temp_voice_channel:
			await ctx.embed_reply(":no_entry: You already have a temporary voice and text channel")
			return
		temp_voice_channel = await self.bot.create_channel(ctx.guild, ctx.author.display_name + "'s Temp Channel", type = discord.ChannelType.voice)
		temp_text_channel = await self.bot.create_channel(ctx.guild, ctx.author.display_name + "s_Temp_Channel", type = discord.ChannelType.text)
		await self.bot.edit_channel_permissions(temp_voice_channel, ctx.me, allow = discord.Permissions.all())
		await self.bot.edit_channel_permissions(temp_text_channel, ctx.me, allow = discord.Permissions.all())
		await self.bot.edit_channel_permissions(temp_voice_channel, ctx.author.roles[0], deny = discord.Permissions.all())
		await self.bot.edit_channel_permissions(temp_text_channel, ctx.author.roles[0], deny = discord.Permissions.all())
		await self.bot.edit_channel_permissions(temp_voice_channel, ctx.author, allow = discord.Permissions.all())
		await self.bot.edit_channel_permissions(temp_text_channel, ctx.author, allow = discord.Permissions.all())
		try:
			await self.bot.move_member(ctx.author, temp_voice_channel)
		except discord.Forbidden:
			await ctx.embed_reply(":no_entry: I can't move you to the new temporary voice channel")
		await ctx.embed_reply("Temporary voice and text channel created")
		while True:
			await asyncio.sleep(15)
			temp_voice_channel = discord.utils.get(ctx.guild.channels, id = temp_voice_channel.id)
			if len(temp_voice_channel.voice_members) == 0:
				await self.bot.edit_channel_permissions(temp_voice_channel, ctx.me, allow = discord.Permissions.all())
				await self.bot.edit_channel_permissions(temp_text_channel, ctx.me, allow = discord.Permissions.all())
				await self.bot.delete_channel(temp_voice_channel)
				await self.bot.delete_channel(temp_text_channel)
				return
	
	# User
	# TODO: create cog, add commands
	# TODO: role removal
	
	@commands.group(aliases = ["member"], invoke_without_command = True)
	@checks.not_forbidden()
	async def user(self, ctx):
		'''User'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	@user.command(name = "add_role", aliases = ["addrole"])
	@commands.guild_only()
	@checks.has_permissions_and_capability(manage_roles = True)
	async def user_add_role(self, ctx, member : discord.Member, *, role : discord.Role):
		'''Gives a user a role'''
		await member.add_roles(role)
		await ctx.embed_reply("I gave the role, {}, to {}".format(role, member))
	
	@commands.command()
	@checks.not_forbidden()
	async def avatar(self, ctx, *, name : str = ""):
		'''
		See a bigger version of an avatar
		Your own or someone else's avatar
		'''
		if not name:
			await ctx.embed_reply(title = "Your avatar", image_url = ctx.author.avatar_url)
		elif not ctx.guild:
			await ctx.embed_reply(":no_entry: Error: Please use that command in a server")
		else:
			user = await utilities.get_user(ctx, name)
			if not user:
				await ctx.embed_reply(":no_entry: Error: {} was not found on this server".format(name))
			else:
				await ctx.embed_reply(title = "{}'s avatar".format(user), image_url = user.avatar_url)
	
	@commands.command()
	@checks.not_forbidden()
	async def discriminator(self, ctx, *, name : str = ""):
		'''
		Get a discriminator
		Your own or someone else's discriminator
		'''
		if not name:
			await self.bot.embed_reply("Your discriminator: #" + ctx.author.discriminator)
			return
		if not ctx.guild:
			await self.bot.embed_reply(":no_entry: Please use that command in a server")
			return
		flag = True
		for member in ctx.guild.members:
			if member.name == name:
				embed = discord.Embed(description = name + "'s discriminator: #" + member.discriminator, color = clients.bot_color)
				avatar = member.default_avatar_url if not member.avatar else member.avatar_url
				embed.set_author(name = str(member), icon_url = avatar)
				await self.bot.reply("", embed = embed)
				flag = False
		if flag and name:
			await self.bot.embed_reply(name + " was not found on this server")
	
	# Convert Attributes
	
	@user.command(name = "name")
	@checks.not_forbidden()
	async def user_name(self, ctx, *, user : discord.Member):
		'''The name of a user'''
		# Include mention?
		await ctx.embed_reply(user.mention, footer_text = str(user), footer_icon_url = user.avatar_url)
	
	@commands.command(aliases = ["usertoid", "usernametoid", "name_to_id", "user_to_id", "username_to_id"])
	@commands.guild_only()
	@checks.not_forbidden()
	async def nametoid(self, ctx, *, name : str):
		'''Convert username to id'''
		user = await utilities.get_user(ctx, name)
		if not user:
			await ctx.embed_reply(":no_entry: Error: {} was not found on this server".format(name))
		else:
			# Include mention?
			await ctx.embed_reply(user.id, footer_text = str(user), footer_icon_url = user.avatar_url)
	
	# Checks
	
	@commands.command(aliases = ["here"])
	@checks.not_forbidden()
	async def everyone(self, ctx):
		'''
		Check if you can mention everyone/here
		For the channel you execute the command in
		'''
		able = "" if ctx.author.permissions_in(ctx.channel).mention_everyone else "not "
		await ctx.embed_reply("You are {}able to mention everyone/here in this channel".format(able))

