
import discord
from discord.ext import commands

import asyncio

import keys
from modules import conversions
from modules import utilities
from client import client

def setup(bot):
	bot.add_cog(Discord())

class Discord:

	# Do Stuff
	
	@commands.command(pass_context = True)
	async def addrole(self, ctx, name : str, role_to_add : str):
		'''
		Gives a user a role
		
		addrole <name> <role>
		Underscores for spaces
		'''
		if ctx.message.server and (ctx.message.channel.permissions_for(ctx.message.author).manage_roles or ctx.message.author.id == keys.myid):
			for member in ctx.message.server.members:
				if member.name == ' '.join(name.split('_')):
					selected_member = member
					break
			for role in ctx.message.server.roles:
				if utilities.remove_symbols(role.name).startswith(' '.join(role_to_add.split('_'))):
					selected_role = role
					break
			await client.add_roles(selected_member, selected_role)
			await client.reply("I gave the role, {0}, to {1}".format(selected_role, selected_member))
	
	@commands.command(pass_context = True)
	async def channel(self, ctx, *options : str):
		'''
		Create a channel
		
		channel <type/name> <name>
		type: text or voice
		'''
		if ctx.message.channel.permissions_for(ctx.message.author).manage_channels and options:
			if options[0] == "voice":
				await client.create_channel(message.server, options[1], type = "voice")
			elif options[1] == "text":
				await client.create_channel(message.server, options[1], type = "text")
			else:
				await client.create_channel(message.server, options[0], type = "text")
	
	@commands.command(pass_context = True, aliases = ["purge", "clean"])
	async def delete(self, ctx, *options : str):
		'''
		Delete messages
		
		delete <number> or delete <user> <number>
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
							to_delete = []
							await asyncio.sleep(1)
				if len(to_delete) == 1:
					await client.delete_message(to_delete[0])
				elif len(to_delete) > 1:
					await client.delete_messages(to_delete)
			else:
				await client.reply("Syntax error.")
	
	@commands.command(pass_context = True, aliases = ["mycolour"])
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
	
	@commands.command(pass_context = True, aliases = ["rolecolour"])
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
	
	# Get Attributes
	
	@commands.command(pass_context = True)
	async def avatar(self, ctx, *name : str):
		'''Returns avatars'''
		if name:
			name = " ".join(name)
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
	async def discriminator(self, ctx, *name : str):
		'''Returns discriminators'''
		if name:
			name = " ".join(name)
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
	
	@commands.command(pass_context = True) # no_pm = True
	async def servericon(self, ctx):
		'''Returns the server icon'''
		if ctx.message.server:
			# await client.reply("This server's icon: https://cdn.discordapp.com/icons/" + ctx.message.server.id + "/" + ctx.message.server.icon + ".jpg")
			if ctx.message.server.icon:
				await client.reply("This server's icon: " + ctx.message.server.icon_url)
			else:
				await client.reply("This server doesn't have an icon.")
		else:
			await client.reply("Please use that command in a server.")
	
	@commands.command(pass_context = True) # no_pm = True
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
	
	@commands.command(pass_context = True) # no_pm = True
	async def serverowner(self, ctx):
		'''Returns the server owner'''
		if ctx.message.server:
			await client.reply("The owner of this server is " + ctx.message.server.owner.name + "#" + str(ctx.message.server.owner.discriminator))
		else:
			await client.reply("Please use that command in a server.")
	
	@commands.command(pass_context = True) # no_pm = True
	async def roleid(self, ctx, *rolename : str):
		'''Returns role id's'''
		for role in ctx.message.server.roles:
			if utilities.remove_symbols(role.name).startswith(' '.join(rolename)):
				await client.reply(role.id)
	
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
	async def nametoid(self, ctx, *name : str):
		'''Convert user name to id'''
		name = ' '.join(name)
		member = discord.utils.get(ctx.message.server.members, name = name)
		await client.reply(member.id)
	
	# Checks
	
	@commands.command(pass_context = True)
	async def everyone(self, ctx):
		'''Check if you can mention everyone'''
		if ctx.message.author.permissions_in(ctx.message.channel).mention_everyone:
			await client.reply("You are able to mention everyone in this channel.")
		else:
			await client.reply("You are not able to mention everyone in this channel.")

