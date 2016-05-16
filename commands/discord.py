
import discord
from discord.ext import commands

import keys
from modules import utilities
from client import client

def setup(bot):
	bot.add_cog(Discord())

class Discord:

	# Do Stuff
	
	@commands.command(pass_context = True)
	async def addrole(self, ctx, name : str, role_to_add : str):
		'''Gives a user a role
		
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
		'''Create a channel
		
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

