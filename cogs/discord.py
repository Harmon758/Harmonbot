
import discord
from discord.ext import commands

import asyncio
import datetime

import credentials
from modules import conversions
from modules import utilities
from utilities import checks

def setup(bot):
	bot.add_cog(Discord(bot))

class Discord:
	
	def __init__(self, bot):
		self.bot = bot
	
	# Do Stuff
	
	@commands.command(pass_context = True, no_pm = True)
	@checks.has_permissions_and_capability(manage_roles = True)
	async def addrole(self, ctx, member : str, *, role : str): # member : discord.Member
		'''
		Gives a user a role
		Replace spaces in usernames with underscores or put the username in qoutes
		'''
		member = await utilities.get_user(ctx, member)
		if not member:
			await self.bot.embed_reply(":no_entry: Member not found")
			return
		role = discord.utils.find(lambda r: utilities.remove_symbols(r.name).startswith(role), ctx.message.server.roles)
		if not role:
			await self.bot.embed_reply(":no_entry: Role not found")
			return
		await self.bot.add_roles(member, role)
		await self.bot.embed_reply("I gave the role, {0}, to {1}".format(role, member))
	
	@commands.command(pass_context = True, no_pm = True)
	@checks.has_permissions_and_capability(manage_channels = True)
	async def channel(self, ctx, *options : str):
		'''
		Create a channel
		channel <type/name> <name>
		type: text or voice, default: text
		'''
		if options:
			if options[0] == "voice":
				await self.bot.create_channel(ctx.message.server, options[1], type = "voice")
			elif options[0] == "text":
				await self.bot.create_channel(ctx.message.server, options[1], type = "text")
			else:
				await self.bot.create_channel(ctx.message.server, options[0], type = "text")
	
	@commands.command(pass_context = True, no_pm = True)
	@checks.has_permissions_and_capability(manage_roles = True)
	async def createrole(self, ctx, *, name : str = ""):
		'''Creates a role'''
		await self.bot.create_role(ctx.message.server, name = name)
	
	@commands.group(pass_context = True, aliases = ["purge", "clean"], invoke_without_command = True)
	@checks.dm_or_has_permissions_and_capability(manage_messages = True)
	async def delete(self, ctx, *options : str):
		'''
		Delete messages
		delete <number> or delete <user> <number>
		If used in a DM, delete <number> deletes <number> of Harmonbot's messages
		'''
		if ctx.message.channel.is_private:
			if options and options[0].isdigit():
				number = int(options[0])
				count = 0
				async for client_message in self.bot.logs_from(ctx.message.channel, limit = 10000):
					if client_message.author == self.bot.user:
						await self.bot.delete_message(client_message)
						await asyncio.sleep(0.2)
						count += 1
						if count == number:
							break
			else:
				await self.bot.reply("Syntax error.")
		elif options and options[0].isdigit():
			number = int(options[0])
			await self.bot.delete_message(ctx.message)
			await self.bot.purge_from(ctx.message.channel, limit = number)
		elif len(options) > 1 and options[1].isdigit():
			def check(message):
				return message.author.name == options[0]
			await self.delete_number(ctx, int(options[1]), check)
		else:
			await self.bot.reply("Syntax error.")
	
	@delete.command(name = "attachments", aliases = ["images"], pass_context = True)
	@checks.has_permissions_and_capability(manage_messages = True)
	async def delete_attachments(self, ctx, number : int):
		'''Deletes the <number> most recent messages with attachments'''
		def check(message):
			return message.attachments
		await self.delete_number(ctx, number, check)
	
	@delete.command(name = "contains", pass_context = True)
	@checks.has_permissions_and_capability(manage_messages = True)
	async def delete_contains(self, ctx, string : str, number : int):
		'''Deletes the <number> most recent messages with <string> in them'''
		def check(message):
			return string in message.content
		await self.delete_number(ctx, number, check)
	
	@delete.command(name = "embeds", pass_context = True)
	@checks.has_permissions_and_capability(manage_messages = True)
	async def delete_embeds(self, ctx, number: int):
		'''Deletes the <number> most recent messages with embeds'''
		def check(message):
			return message.embeds
		await self.delete_number(ctx, number, check)
	
	@delete.command(name = "time", hidden = True, pass_context = True)
	@checks.is_owner()
	@checks.has_permissions_and_capability(manage_messages = True)
	async def delete_time(self, ctx, minutes : int):
		'''WIP'''
		await self.bot.delete_message(ctx.message)
		await self.bot.purge_from(ctx.message.channel, limit = 10000, after = datetime.datetime.utcnow() - datetime.timedelta(minutes = minutes))
	
	async def delete_number(self, ctx, number, check):
		if number <= 0:
			await self.bot.reply("Syntax Error.")
			return
		to_delete = []
		count = 0
		await self.bot.delete_message(ctx.message)
		async for client_message in self.bot.logs_from(ctx.message.channel, limit = 10000):
			if check(client_message):
				to_delete.append(client_message)
				count += 1
				if count == number:
					break
				elif len(to_delete) == 100:
					await self.bot.delete_messages(to_delete)
					to_delete.clear()
					await asyncio.sleep(1)
		if len(to_delete) == 1:
			await self.bot.delete_message(to_delete[0])
		elif len(to_delete) > 1:
			await self.bot.delete_messages(to_delete)
	
	@commands.command(pass_context = True, aliases = ["mycolour"], no_pm = True)
	@checks.not_forbidden()
	async def mycolor(self, ctx, *color : str): #rework
		'''
		Return or change your color
		Currently only accepts hex color input
		'''
		if not color:
			color_value = ctx.message.author.color.value
			await self.bot.reply("#{}".format(conversions.inttohex(color_value)))
		else: # check color
			try:
				color_value = int(color[0], 16)
			except ValueError:
				await self.bot.reply(":no_entry: Please enter a valid hex color")
				return
			if not discord.utils.get(ctx.message.server.roles, name = ctx.message.author.name):
				new_role = await self.bot.create_role(ctx.message.server, name = ctx.message.author.name, hoist = False)
				await self.bot.add_roles(ctx.message.author, new_role)
				new_colour = new_role.colour
				new_colour.value = color_value
				await self.bot.edit_role(ctx.message.server, new_role, name = ctx.message.author.name, colour = new_colour)
			else:
				role_to_change = discord.utils.get(ctx.message.server.roles, name = ctx.message.author.name)
				new_colour = role_to_change.colour
				new_colour.value = color_value
				await self.bot.edit_role(ctx.message.server, role_to_change, colour = new_colour)
	
	@commands.command(pass_context = True)
	@checks.has_permissions_and_capability(manage_messages = True)
	async def pin(self, ctx, message_id : int):
		'''Pin message by message ID'''
		message = await self.bot.get_message(ctx.message.channel, str(message_id))
		await self.bot.pin_message(message)
		await self.bot.reply("Message pinned.")
	
	@commands.command(pass_context = True)
	@checks.has_permissions_and_capability(manage_messages = True)
	async def unpin(self, ctx, message_id : int):
		'''Unpin message by message ID'''
		message = await self.bot.get_message(ctx.message.channel, str(message_id))
		await self.bot.unpin_message(message)
		await self.bot.reply("Message unpinned.")
	
	@commands.command(pass_context = True, aliases = ["rolecolour"], no_pm = True)
	@checks.not_forbidden()
	async def rolecolor(self, ctx, role : str, *color : str):
		'''
		Returns or changes role colors
		Replace spaces in role names with underscores or put the role name in qoutes
		Currently only accepts hex color input
		'''
		if not color:
			selected_role = None
			for _role in ctx.message.server.roles:
				if _role.name.startswith((' ').join(role.split('_'))):
					selected_role = _role
					break
			if not selected_role:
				await self.bot.reply("Role not found.")
				return
			color = selected_role.colour
			color_value = color.value
			await self.bot.reply(str(conversions.inttohex(color_value)))
		elif ctx.message.channel.permissions_for(ctx.message.author).manage_roles or ctx.message.author.id == credentials.myid:
			for _role in ctx.message.server.roles:
				if _role.name.startswith((' ').join(role.split('_'))):
					role_to_change = _role
					break
			new_colour = role_to_change.colour
			new_colour.value = conversions.hextoint(color[0])
			await self.bot.edit_role(ctx.message.server, role_to_change, colour = new_colour)
	
	@commands.command(pass_context = True, hidden = True)
	@checks.is_owner()
	async def roleposition(self, ctx, role : str, position : int):
		'''WIP'''
		for _role in ctx.message.server.roles:
			if _role.name.startswith((' ').join(role.split('_'))):
				selected_role = _role
				break
		await self.bot.move_role(ctx.message.server, selected_role, position)
	
	@commands.command(pass_context = True, no_pm = True)
	@checks.not_forbidden()
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
				await self.bot.reply("User not found.")
			voice_channel_permissions = discord.Permissions.none()
			voice_channel_permissions.connect = True
			voice_channel_permissions.speak = True
			voice_channel_permissions.use_voice_activation = True
			await self.bot.edit_channel_permissions(temp_voice_channel, to_allow, allow = voice_channel_permissions)
			text_channel_permissions = discord.Permissions.text()
			text_channel_permissions.manage_messages = False
			await self.bot.edit_channel_permissions(temp_text_channel, to_allow, allow = text_channel_permissions)
			await self.bot.reply("You have allowed " + to_allow.display_name + " to join your temporary voice and text channel.")
			return
		if temp_voice_channel:
			await self.bot.reply("You already have a temporary voice and text channel.")
			return
		temp_voice_channel = await self.bot.create_channel(ctx.message.server, ctx.message.author.display_name + "'s Temp Channel", type = discord.ChannelType.voice)
		temp_text_channel = await self.bot.create_channel(ctx.message.server, ctx.message.author.display_name + "s_Temp_Channel", type = discord.ChannelType.text)
		await self.bot.edit_channel_permissions(temp_voice_channel, ctx.message.server.me, allow = discord.Permissions.all())
		await self.bot.edit_channel_permissions(temp_text_channel, ctx.message.server.me, allow = discord.Permissions.all())
		await self.bot.edit_channel_permissions(temp_voice_channel, ctx.message.author.roles[0], deny = discord.Permissions.all())
		await self.bot.edit_channel_permissions(temp_text_channel, ctx.message.author.roles[0], deny = discord.Permissions.all())
		await self.bot.edit_channel_permissions(temp_voice_channel, ctx.message.author, allow = discord.Permissions.all())
		await self.bot.edit_channel_permissions(temp_text_channel, ctx.message.author, allow = discord.Permissions.all())
		try:
			await self.bot.move_member(ctx.message.author, temp_voice_channel)
		except discord.errors.Forbidden:
			await self.bot.reply("I can not move you to the new temporary voice channel.")
		await self.bot.reply("Temporary voice and text channel created")
		while True:
			await asyncio.sleep(15)
			temp_voice_channel = discord.utils.get(ctx.message.server.channels, id = temp_voice_channel.id)
			if len(temp_voice_channel.voice_members) == 0:
				await self.bot.edit_channel_permissions(temp_voice_channel, ctx.message.server.me, allow = discord.Permissions.all())
				await self.bot.edit_channel_permissions(temp_text_channel, ctx.message.server.me, allow = discord.Permissions.all())
				await self.bot.delete_channel(temp_voice_channel)
				await self.bot.delete_channel(temp_text_channel)
				return
	
	@commands.command(hidden = True, pass_context = True, no_pm = True)
	@checks.is_owner()
	async def userlimit(self, ctx, limit : int):
		'''WIP'''
		if ctx.message.author.voice_channel:
			voice_channel = ctx.message.author.voice_channel
		await self.bot.edit_channel(voice_channel, user_limit = limit)
	
	# Get Attributes
	
	@commands.command(pass_context = True)
	@checks.not_forbidden()
	async def avatar(self, ctx, *, name : str = ""):
		'''
		See a bigger version of an avatar
		Your own or someone else's avatar
		'''
		if name:
			if ctx.message.server:
				user = await utilities.get_user(ctx, name)
				if user and user.avatar_url:
					await self.bot.reply(name + "'s avatar: " + user.avatar_url)
				elif user:
					await self.bot.reply(name + "'s avatar: " + user.default_avatar_url)
				else:
					await self.bot.reply(name + " was not found on this server.")
			else:
				await self.bot.reply("Please use that command in a server.")
		else:
			if ctx.message.author.avatar_url:
				await self.bot.reply("Your avatar: " + ctx.message.author.avatar_url)
			else:
				await self.bot.reply("Your avatar: " + ctx.message.author.default_avatar_url)
	
	@commands.command(pass_context = True)
	@checks.not_forbidden()
	async def discriminator(self, ctx, *, name : str = ""):
		'''
		Get a discriminator
		Your own or someone else's discriminator
		'''
		if name:
			flag = True
			if ctx.message.server:
				for member in ctx.message.server.members:
					if member.name == name:
						await self.bot.reply(name + "'s discriminator: #" + member.discriminator)
						flag = False
				if flag and name:
					await self.bot.reply(name + " was not found on this server.")
			else:
				await self.bot.reply("Please use that command in a server.")
		else:
			await self.bot.reply("Your discriminator: #" + ctx.message.author.discriminator)
	
	@commands.command(pass_context = True, no_pm = True)
	@checks.not_forbidden()
	async def roleid(self, ctx, *, name : str):
		'''Get the ID of a role'''
		for role in ctx.message.server.roles:
			if utilities.remove_symbols(role.name).startswith(name):
				await self.bot.reply(role.id)
	
	@commands.command(pass_context = True, hidden = True)
	@checks.is_owner()
	async def rolepositions(self, ctx):
		'''WIP'''
		await self.bot.reply(', '.join([role.name + ": " + str(role.position) for role in ctx.message.server.roles[1:]]))
	
	@commands.command(pass_context = True, no_pm = True)
	@checks.not_forbidden()
	async def servericon(self, ctx):
		'''See a bigger version of the server icon'''
		# await self.bot.reply("This server's icon: https://cdn.discordapp.com/icons/" + ctx.message.server.id + "/" + ctx.message.server.icon + ".jpg")
		if ctx.message.server.icon:
			await self.bot.reply("This server's icon: " + ctx.message.server.icon_url)
		else:
			await self.bot.reply("This server doesn't have an icon.")
	
	@commands.command(aliases = ["serverinformation"], pass_context = True, no_pm = True)
	@checks.not_forbidden()
	async def serverinfo(self, ctx):
		'''Information about a server'''
		server = ctx.message.server
		embed = discord.Embed(title = server.name, url = server.icon_url, timestamp = server.created_at, color = clients.bot_color)
		avatar = ctx.message.author.default_avatar_url if not ctx.message.author.avatar else ctx.message.author.avatar_url
		embed.set_author(name = ctx.message.author.display_name, icon_url = avatar)
		embed.set_thumbnail(url = server.icon_url)
		embed.add_field(name = "Owner", value = server.owner.mention)
		embed.add_field(name = "ID", value = server.id)
		embed.add_field(name = "Region", value = str(server.region))
		channel_types = [c.type for c in server.channels]
		text_count = channel_types.count(discord.ChannelType.text)
		voice_count = channel_types.count(discord.ChannelType.voice)
		embed.add_field(name = "Channels", value = "{} text\n{} voice".format(text_count, voice_count))
		embed.add_field(name = "Members", value = server.member_count)
		embed.add_field(name = "Roles", value = len(server.roles))
		embed.add_field(name = "Default Channel", value = server.default_channel.mention)
		embed.add_field(name = "AFK Timeout", value = "{:g} min.".format(server.afk_timeout / 60))
		embed.add_field(name = "AFK Channel", value = str(server.afk_channel))
		embed.add_field(name = "Verification Level", value = str(server.verification_level).capitalize())
		embed.add_field(name = "2FA Requirement", value = bool(server.mfa_level))
		if server.emojis: embed.add_field(name = "Emojis", value = ' '.join([str(emoji) for emoji in server.emojis]), inline = False)
		embed.set_footer(text = "Created")
		await self.bot.say(embed = embed)
	
	@commands.command(pass_context = True, no_pm = True)
	@checks.not_forbidden()
	async def serverowner(self, ctx):
		'''The owner of the server'''
		await self.bot.reply("The owner of this server is " + ctx.message.server.owner.name + "#" + str(ctx.message.server.owner.discriminator))
	
	@commands.command(pass_context = True)
	@checks.not_forbidden()
	async def userinfo(self, ctx):
		'''Information about a user'''
		user = ctx.message.author
		avatar_url = user.default_avatar_url if not user.avatar else user.avatar_url
		embed = discord.Embed(title = str(user), url = avatar_url, timestamp = user.created_at, color = clients.bot_color)
		avatar = ctx.message.author.default_avatar_url if not ctx.message.author.avatar else ctx.message.author.avatar_url
		embed.set_author(name = ctx.message.author.display_name, icon_url = avatar)
		embed.set_thumbnail(url = avatar_url)
		embed.add_field(name = "User", value = user.mention)
		embed.add_field(name = "ID", value = user.id)
		embed.add_field(name = "Bot", value = user.bot)
		embed.set_footer(text = "Created")
		await self.bot.say(embed = embed)
		# member info, status, game, roles, color, etc.
	
	# Convert Attributes
	
	@commands.command()
	@checks.not_forbidden()
	async def idtoname(self, id : str):
		'''Convert user id to name'''
		user = await self.bot.get_user_info(id)
		if user:
			await self.bot.reply(user)
		else:
			await self.bot.reply("User with that id not found")
	
	@commands.command(pass_context = True)
	@checks.not_forbidden()
	async def nametoid(self, ctx, *, name : str):
		'''Convert user name to id'''
		if ctx.message.server:
			user = await utilities.get_user(ctx, name)
			if user:
				await self.bot.reply(user.id)
			else:
				await self.bot.reply(name + " was not found on this server.")
		else:
			await self.bot.reply("Please use that command in a server.")
	
	# Checks
	
	@commands.command(pass_context = True)
	@checks.not_forbidden()
	async def everyone(self, ctx):
		'''
		Check if you can mention everyone
		For the channel you execute the command in
		'''
		if ctx.message.author.permissions_in(ctx.message.channel).mention_everyone:
			await self.bot.reply("You are able to mention everyone in this channel.")
		else:
			await self.bot.reply("You are not able to mention everyone in this channel.")

