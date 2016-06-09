
import discord
from discord.ext import commands

import asyncio
import datetime

import keys
from modules import conversions
from modules import utilities
from utilities import checks
from client import client

def setup(bot):
	bot.add_cog(Discord())

class Discord:

	# Do Stuff
	
	@commands.command(pass_context = True, no_pm = True)
	async def addrole(self, ctx, name : str, role : str):
		'''
		Gives a user a role
		Replace spaces in role names with underscores or put the role name in qoutes
		'''
		if ctx.message.server and (ctx.message.channel.permissions_for(ctx.message.author).manage_roles or ctx.message.author.id == keys.myid):
			for member in ctx.message.server.members:
				if member.name == ' '.join(name.split('_')):
					selected_member = member
					break
			for _role in ctx.message.server.roles:
				if utilities.remove_symbols(_role.name).startswith(' '.join(role.split('_'))):
					selected_role = _role
					break
			await client.add_roles(selected_member, selected_role)
			await client.reply("I gave the role, {0}, to {1}".format(selected_role, selected_member))
	
	@commands.command(pass_context = True, no_pm = True)
	async def channel(self, ctx, *options : str):
		'''
		Create a channel
		channel <type/name> <name>
		type: text or voice, default: text
		'''
		if ctx.message.channel.permissions_for(ctx.message.author).manage_channels and options:
			if options[0] == "voice":
				await client.create_channel(message.server, options[1], type = "voice")
			elif options[1] == "text":
				await client.create_channel(message.server, options[1], type = "text")
			else:
				await client.create_channel(message.server, options[0], type = "text")
	
	@commands.command(pass_context = True, no_pm = True)
	async def createrole(self, ctx, *, name : str):
		'''Creates a role'''
		await client.create_role(ctx.message.server, name = name)
	
	@commands.group(pass_context = True, aliases = ["purge", "clean"], invoke_without_command = True)
	async def delete(self, ctx, *options : str):
		'''
		Delete messages
		delete <number> or delete <user> <number> or delete images <number>
		If used in a DM, delete <number> deletes <number> of Harmonbot's messages
		'''
		if ctx.message.channel.is_private:
			if options[0].isdigit():
				number = int(options[0])
				count = 0
				async for client_message in client.logs_from(ctx.message.channel, limit = 10000):
					if client_message.author == client.user:
						await client.delete_message(client_message)
						await asyncio.sleep(0.2)
						count += 1
						if count == number:
							break
			else:
				await client.reply("Syntax error.")
		elif not ctx.message.server.me.permissions_in(ctx.message.channel).manage_messages:
			await client.reply("I don't have permission to do that here. I need the \"Manage Messages\" permission to delete messages.")
		elif ctx.message.channel.permissions_for(ctx.message.author).manage_messages or ctx.message.author.id == keys.myid:
			if options[0].isdigit():
				number = int(options[0])
				await client.delete_message(ctx.message)
				await client.purge_from(ctx.message.channel, limit = number)
			elif options[0] in ["images", "attachments"] and options[1].isdigit():
				number = int(options[1])
				to_delete = []
				count = 0
				await client.delete_message(ctx.message)
				async for client_message in client.logs_from(ctx.message.channel, limit = 10000):
					if client_message.attachments:
						to_delete.append(client_message)
						count += 1
						if count == number:
							break
						elif len(to_delete) == 100:
							await client.delete_messages(to_delete)
							to_delete.clear()
							await asyncio.sleep(1)
				if len(to_delete) == 1:
					await client.delete_message(to_delete[0])
				elif len(to_delete) > 1:
					await client.delete_messages(to_delete)
			elif len(options) > 1 and options[1].isdigit():
				number = int(options[1])
				to_delete = []
				count = 0
				await client.delete_message(ctx.message)
				async for client_message in client.logs_from(ctx.message.channel, limit = 10000):
					if client_message.author.name == options[0]:
						to_delete.append(client_message)
						count += 1
						if count == number:
							break
						elif len(to_delete) == 100:
							await client.delete_messages(to_delete)
							to_delete.clear()
							await asyncio.sleep(1)
				if len(to_delete) == 1:
					await client.delete_message(to_delete[0])
				elif len(to_delete) > 1:
					await client.delete_messages(to_delete)
			else:
				await client.reply("Syntax error.")
	
	@delete.command(hidden = True, pass_context = True)
	@checks.is_owner()
	async def time(self, ctx, minutes : int):
		'''WIP'''
		await client.delete_message(ctx.message)
		await client.purge_from(ctx.message.channel, limit = 10000, after = datetime.datetime.utcnow() - datetime.timedelta(minutes = minutes))
	
	@commands.command(pass_context = True, aliases = ["mycolour"], no_pm = True)
	async def mycolor(self, ctx, *color : str): #rework
		'''
		Return or change your color
		Currently only accepts hex color input
		'''
		if not color:
			_color = ctx.message.author.color
			color_value = _color.value
			await client.reply(str(conversions.inttohex(color_value)))
		else: # check color
			if not discord.utils.get(ctx.message.server.roles, name = ctx.message.author.name):
				new_role = await client.create_role(ctx.message.server, name = ctx.message.author.name, hoist = False)
				await client.add_roles(ctx.message.author, new_role)
				new_colour = new_role.colour
				new_colour.value = int(color[0], 16)
				await client.edit_role(ctx.message.server, new_role, name = ctx.message.author.name, colour = new_colour)
			else:
				role_to_change = discord.utils.get(ctx.message.server.roles, name = ctx.message.author.name)
				new_colour = role_to_change.colour
				new_colour.value = int(color[0], 16)
				await client.edit_role(ctx.message.server, role_to_change, colour = new_colour)
	
	@commands.command(pass_context = True, aliases = ["rolecolour"], no_pm = True)
	async def rolecolor(self, ctx, role : str, *color : str):
		'''
		Returns or changes role colors
		Replace spaces in role names with underscores or put the role name in qoutes
		Currently only accepts hex color input
		'''
		if not color:
			for _role in ctx.message.server.roles:
				if _role.name.startswith((' ').join(role.split('_'))):
					selected_role = _role
					break
			color = selected_role.colour
			color_value = color.value
			await client.reply(str(conversions.inttohex(color_value)))
		elif ctx.message.channel.permissions_for(ctx.message.author).manage_roles or ctx.message.author.id == keys.myid:
			for _role in ctx.message.server.roles:
				if _role.name.startswith((' ').join(role.split('_'))):
					role_to_change = _role
					break
			new_colour = role_to_change.colour
			new_colour.value = conversions.hextoint(color[0])
			await client.edit_role(ctx.message.server, role_to_change, colour = new_colour)
	
	@commands.command(pass_context = True)
	@checks.is_owner()
	async def roleposition(self, ctx, role : str, position : int):
		'''WIP'''
		for _role in ctx.message.server.roles:
			if _role.name.startswith((' ').join(role.split('_'))):
				selected_role = _role
				break
		await client.move_role(ctx.message.server, selected_role, position)
	
	@commands.command(pass_context = True, no_pm = True)
	async def tempchannel(self, ctx, *options : str):
		'''
		Create temporary voice and text channels
		options: allow <friend>
		'''
		temp_voice_channel = discord.utils.get(ctx.message.server.channels, name = ctx.message.author.display_name + "'s Temp Channel")
		temp_text_channel = discord.utils.get(ctx.message.server.channels, name = ctx.message.author.display_name.lower() + "s_temp_channel")
		if temp_voice_channel and options and options[0] == "allow":
			to_allow = discord.utils.get(ctx.message.server.members, name = options[1])
			if not to_allow:
				await client.reply("User not found.")
			voice_channel_permissions = discord.Permissions.none()
			voice_channel_permissions.connect = True
			voice_channel_permissions.speak = True
			voice_channel_permissions.use_voice_activation = True
			await client.edit_channel_permissions(temp_voice_channel, to_allow, allow = voice_channel_permissions)
			text_channel_permissions = discord.Permissions.text()
			text_channel_permissions.manage_messages = False
			await client.edit_channel_permissions(temp_text_channel, to_allow, allow = text_channel_permissions)
			await client.reply("You have allowed " + to_allow.display_name + " to join your temporary voice and text channel.")
			return
		if temp_voice_channel:
			await client.reply("You already have a temporary voice and text channel.")
			return
		temp_voice_channel = await client.create_channel(ctx.message.server, ctx.message.author.display_name + "'s Temp Channel", type = discord.ChannelType.voice)
		temp_text_channel = await client.create_channel(ctx.message.server, ctx.message.author.display_name + "s_Temp_Channel", type = discord.ChannelType.text)
		await client.edit_channel_permissions(temp_voice_channel, ctx.message.server.me, allow = discord.Permissions.all())
		await client.edit_channel_permissions(temp_text_channel, ctx.message.server.me, allow = discord.Permissions.all())
		await client.edit_channel_permissions(temp_voice_channel, ctx.message.author.roles[0], deny = discord.Permissions.all())
		await client.edit_channel_permissions(temp_text_channel, ctx.message.author.roles[0], deny = discord.Permissions.all())
		await client.edit_channel_permissions(temp_voice_channel, ctx.message.author, allow = discord.Permissions.all())
		await client.edit_channel_permissions(temp_text_channel, ctx.message.author, allow = discord.Permissions.all())
		try:
			await client.move_member(ctx.message.author, temp_voice_channel)
		except discord.errors.Forbidden:
			await client.reply("I can not move you to the new temporary voice channel.")
		await client.reply("Temporary voice and text channel created")
		while True:
			await asyncio.sleep(15)
			temp_voice_channel = discord.utils.get(ctx.message.server.channels, id = temp_voice_channel.id)
			if len(temp_voice_channel.voice_members) == 0:
				await client.edit_channel_permissions(temp_voice_channel, ctx.message.server.me, allow = discord.Permissions.all())
				await client.edit_channel_permissions(temp_text_channel, ctx.message.server.me, allow = discord.Permissions.all())
				await client.delete_channel(temp_voice_channel)
				await client.delete_channel(temp_text_channel)
				return
	
	@commands.command(hidden = True, pass_context = True, no_pm = True)
	@checks.is_owner()
	async def userlimit(self, ctx, limit : int):
		'''WIP'''
		if ctx.message.author.voice_channel:
			voice_channel = ctx.message.author.voice_channel
		await client.edit_channel(voice_channel, user_limit = limit)
	
	# Get Attributes
	
	@commands.command(pass_context = True)
	async def avatar(self, ctx, *, name : str):
		'''See a bigger version of your own or someone else's avatar'''
		if name:
			flag = True
			if ctx.message.server:
				for member in ctx.message.server.members:
					if member.name == name:
						if member.avatar_url:
							await client.reply(name + "'s avatar: " + member.avatar_url)
						else:
							await client.reply(name + "'s avatar: " + member.default_avatar_url)
						flag = False
				if flag and name:
					await client.reply(name + " was not found on this server.")
			else:
				await client.reply("Please use that command in a server.")
		else:
			if ctx.message.author.avatar_url:
				await client.reply("Your avatar: " + ctx.message.author.avatar_url)
			else:
				await client.reply("Your avatar: " + ctx.message.author.default_avatar_url)
	
	@commands.command(pass_context = True)
	async def discriminator(self, ctx, *, name : str):
		'''Get your own or someone else's discriminator'''
		if name:
			flag = True
			if ctx.message.server:
				for member in ctx.message.server.members:
					if member.name == name:
						await client.reply(name + "'s discriminator: #" + member.discriminator)
						flag = False
				if flag and name:
					await client.reply(name + " was not found on this server.")
			else:
				await client.reply("Please use that command in a server.")
		else:
			await client.reply("Your discriminator: #" + ctx.message.author.discriminator)
	
	@commands.command(pass_context = True, no_pm = True)
	async def roleid(self, ctx, *, name : str):
		'''Get the ID of a role'''
		for role in ctx.message.server.roles:
			if utilities.remove_symbols(role.name).startswith(name):
				await client.reply(role.id)
	
	@commands.command(pass_context = True)
	@checks.is_owner()
	async def rolepositions(self, ctx):
		'''WIP'''
		await client.reply(', '.join([role.name + ": " + str(role.position) for role in ctx.message.server.roles[1:]]))
	
	@commands.command(pass_context = True, no_pm = True)
	async def servericon(self, ctx):
		'''See a bigger version of the server icon'''
		# await client.reply("This server's icon: https://cdn.discordapp.com/icons/" + ctx.message.server.id + "/" + ctx.message.server.icon + ".jpg")
		if ctx.message.server.icon:
			await client.reply("This server's icon: " + ctx.message.server.icon_url)
		else:
			await client.reply("This server doesn't have an icon.")
	
	@commands.command(pass_context = True, no_pm = True)
	async def serverinfo(self, ctx):
		'''Information about a server'''
		server = ctx.message.server
		server_info = "```Name: " + server.name + "\n"
		server_info += "ID: " + server.id + "\n"
		server_info += "Owner: " + server.owner.name + "\n"
		server_info += "Server Region: " + str(server.region) + "\n"
		server_info += "Members: " + str(server.member_count) + "\n"
		server_info += "Created at: " + str(server.created_at) + "\n```"
		server_info += "Icon: " + server.icon_url
		await client.reply(server_info)
	
	@commands.command(pass_context = True, no_pm = True)
	async def serverowner(self, ctx):
		'''The owner of the server'''
		await client.reply("The owner of this server is " + ctx.message.server.owner.name + "#" + str(ctx.message.server.owner.discriminator))
	
	@commands.command(pass_context = True)
	async def userinfo(self, ctx):
		'''Information about a user'''
		user = ctx.message.author
		user_info = "```" + str(user) + "\n"
		user_info += "ID: " + user.id + "\n"
		user_info += "Joined: " + str(user.created_at)
		user_info += "```"
		await client.reply(user_info)
	
	# Convert Attributes
	
	@commands.command()
	async def idtoname(self, id : str):
		'''Convert user id to name'''
		if id.isdigit():
			await client.reply("<@" + id + ">")
	
	@commands.command(pass_context = True)
	async def nametoid(self, ctx, *, name : str):
		'''Convert user name to id'''
		member = discord.utils.get(ctx.message.server.members, name = name)
		await client.reply(member.id)
	
	# Checks
	
	@commands.command(pass_context = True)
	async def everyone(self, ctx):
		'''Check if you can mention everyone in the channel'''
		if ctx.message.author.permissions_in(ctx.message.channel).mention_everyone:
			await client.reply("You are able to mention everyone in this channel.")
		else:
			await client.reply("You are not able to mention everyone in this channel.")

