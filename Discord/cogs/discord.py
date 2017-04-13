
import discord
from discord.ext import commands

import asyncio
import datetime

import credentials
from modules import conversions
from modules import utilities
from utilities import checks
import clients

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
	async def delete(self, ctx, number : int, *, user : str = ""):
		'''
		Delete messages
		If used in a DM, delete <number> deletes <number> of Harmonbot's messages
		'''
		if ctx.message.channel.is_private:
			await self.bot.delete_number(ctx, number, check = lambda m: m.author == self.bot.user, delete_command = False)
		elif not user:
			await self.bot.delete_message(ctx.message)
			await self.bot.purge_from(ctx.message.channel, limit = number)
		elif user:
			await self.delete_number(ctx, number, check = lambda m: m.author.name == user)
	
	@delete.command(name = "attachments", aliases = ["images"], pass_context = True)
	@checks.has_permissions_and_capability(manage_messages = True)
	async def delete_attachments(self, ctx, number : int):
		'''Deletes the <number> most recent messages with attachments'''
		await self.delete_number(ctx, number, check = lambda m: m.attachments)
	
	@delete.command(name = "contains", pass_context = True)
	@checks.has_permissions_and_capability(manage_messages = True)
	async def delete_contains(self, ctx, string : str, number : int):
		'''Deletes the <number> most recent messages with <string> in them'''
		await self.delete_number(ctx, number, check = lambda m: string in m.content)
	
	@delete.command(name = "embeds", pass_context = True)
	@checks.has_permissions_and_capability(manage_messages = True)
	async def delete_embeds(self, ctx, number: int):
		'''Deletes the <number> most recent messages with embeds'''
		await self.delete_number(ctx, number, check = lambda m: m.embeds)
	
	@delete.command(name = "time", pass_context = True)
	@checks.has_permissions_and_capability(manage_messages = True)
	async def delete_time(self, ctx, minutes : int):
		'''Deletes messages in the past <minutes> minutes'''
		await self.bot.delete_message(ctx.message)
		await self.bot.purge_from(ctx.message.channel, limit = clients.delete_limit, after = datetime.datetime.utcnow() - datetime.timedelta(minutes = minutes))
	
	# TODO: delete mentions, invites?
	
	async def delete_number(self, ctx, number, check, delete_command = True):
		if number <= 0:
			await self.bot.embed_reply(":no_entry: Syntax error")
			return
		to_delete = []
		count = 0
		if delete_command: await self.bot.delete_message(ctx.message)
		async for message in self.bot.logs_from(ctx.message.channel, limit = clients.delete_limit):
			if check(message):
				to_delete.append(message)
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
	
	@commands.command(aliases = ["mycolour", "my_color", "my_colour"], pass_context = True, no_pm = True)
	@checks.not_forbidden()
	async def mycolor(self, ctx, color : str = ""):
		'''
		Return or change your color
		Currently only accepts hex color input
		'''
		# TODO: Rework
		if not color:
			color_value = ctx.message.author.color.value
			await self.bot.embed_reply("#{}".format(conversions.inttohex(color_value)))
			return
		# check color
		try:
			color_value = int(color.strip('#'), 16)
		except ValueError:
			await self.bot.embed_reply(":no_entry: Please enter a valid hex color")
			return
		role_to_change = discord.utils.get(ctx.message.server.roles, name = ctx.message.author.name)
		if not role_to_change:
			new_role = await self.bot.create_role(ctx.message.server, name = ctx.message.author.name, hoist = False)
			await self.bot.add_roles(ctx.message.author, new_role)
			new_colour = new_role.colour
			new_colour.value = color_value
			await self.bot.edit_role(ctx.message.server, new_role, name = ctx.message.author.name, colour = new_colour)
			await self.bot.embed_reply("Created your role with the color, {}".format(color))
		else:
			new_colour = role_to_change.colour
			new_colour.value = color_value
			await self.bot.edit_role(ctx.message.server, role_to_change, colour = new_colour)
			await self.bot.embed_reply("Changed your role color to {}".format(color))
	
	@commands.group(pass_context = True, invoke_without_command = True)
	@checks.has_permissions_and_capability(manage_messages = True)
	async def pin(self, ctx, message_id : int):
		'''Pin message by message ID'''
		message = await self.bot.get_message(ctx.message.channel, str(message_id))
		await self.bot.pin_message(message)
		await self.bot.embed_reply(":pushpin: Pinned message")
	
	@pin.command(name = "first", pass_context = True)
	@checks.has_permissions_and_capability(manage_messages = True)
	async def pin_first(self, ctx):
		'''Pin first message'''
		message = await self.bot.logs_from(ctx.message.channel, after = ctx.message.channel, limit = 1).iterate()
		await self.bot.pin_message(message)
		await self.bot.embed_reply(":pushpin: Pinned first message in this channel")
	
	@commands.command(pass_context = True)
	@checks.has_permissions_and_capability(manage_messages = True)
	async def unpin(self, ctx, message_id : int):
		'''Unpin message by message ID'''
		message = await self.bot.get_message(ctx.message.channel, str(message_id))
		await self.bot.unpin_message(message)
		await self.bot.embed_reply(":wastebasket: Unpinned message")
	
	@commands.command(aliases = ["rolecolour", "role_color", "role_colour"], pass_context = True, no_pm = True)
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
				await self.bot.embed_reply(":no_entry: Role not found")
				return
			color = selected_role.colour
			color_value = color.value
			await self.bot.embed_reply(conversions.inttohex(color_value))
		elif ctx.message.channel.permissions_for(ctx.message.author).manage_roles or ctx.message.author.id == credentials.myid:
			for _role in ctx.message.server.roles:
				if _role.name.startswith((' ').join(role.split('_'))):
					role_to_change = _role
					break
			if not role_to_change:
				await self.bot.embed_reply(":no_entry: Role not found")
				return
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
				await self.bot.embed_reply(":no_entry: User not found")
			voice_channel_permissions = discord.Permissions.none()
			voice_channel_permissions.connect = True
			voice_channel_permissions.speak = True
			voice_channel_permissions.use_voice_activation = True
			await self.bot.edit_channel_permissions(temp_voice_channel, to_allow, allow = voice_channel_permissions)
			text_channel_permissions = discord.Permissions.text()
			text_channel_permissions.manage_messages = False
			await self.bot.edit_channel_permissions(temp_text_channel, to_allow, allow = text_channel_permissions)
			await self.bot.embed_reply("You have allowed " + to_allow.display_name + " to join your temporary voice and text channel")
			return
		if temp_voice_channel:
			await self.bot.embed_reply(":no_entry: You already have a temporary voice and text channel")
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
			await self.bot.embed_reply(":no_entry: I can't move you to the new temporary voice channel")
		await self.bot.embed_reply("Temporary voice and text channel created")
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
		if not name:
			avatar = ctx.message.author.avatar_url or ctx.message.author.default_avatar_url
			await self.bot.embed_reply(None, title = "Your avatar", image_url = avatar)
			return
		if not ctx.message.server:
			await self.bot.embed_reply(":no_entry: Please use that command in a server")
			return
		user = await utilities.get_user(ctx, name)
		if not user:
			await self.bot.embed_reply(":no_entry: {} was not found on this server".format(name))
			return
		avatar = user.avatar_url or user.default_avatar_url
		await self.bot.embed_reply(None, title = "{}'s avatar".format(user), image_url = avatar)
	
	@commands.command(pass_context = True)
	@checks.not_forbidden()
	async def discriminator(self, ctx, *, name : str = ""):
		'''
		Get a discriminator
		Your own or someone else's discriminator
		'''
		if not name:
			await self.bot.embed_reply("Your discriminator: #" + ctx.message.author.discriminator)
			return
		if not ctx.message.server:
			await self.bot.embed_reply(":no_entry: Please use that command in a server")
			return
		flag = True
		for member in ctx.message.server.members:
			if member.name == name:
				embed = discord.Embed(description = name + "'s discriminator: #" + member.discriminator, color = clients.bot_color)
				avatar = member.default_avatar_url if not member.avatar else member.avatar_url
				embed.set_author(name = str(member), icon_url = avatar)
				await self.bot.reply("", embed = embed)
				flag = False
		if flag and name:
			await self.bot.embed_reply(name + " was not found on this server")
	
	@commands.command(aliases = ["role_id"], pass_context = True, no_pm = True)
	@checks.not_forbidden()
	async def roleid(self, ctx, *, name : str):
		'''Get the ID of a role'''
		for role in ctx.message.server.roles:
			if utilities.remove_symbols(role.name).startswith(name):
				await self.bot.embed_reply(role.id)
	
	@commands.command(aliases = ["role_positions"], pass_context = True, hidden = True)
	@checks.is_owner()
	async def rolepositions(self, ctx):
		'''WIP'''
		await self.bot.embed_reply(', '.join([role.name + ": " + str(role.position) for role in ctx.message.server.roles[1:]]))
	
	@commands.command(aliases = ["server_icon"], pass_context = True, no_pm = True)
	@checks.not_forbidden()
	async def servericon(self, ctx):
		'''See a bigger version of the server icon'''
		if not ctx.message.server.icon:
			await self.bot.embed_reply(":no_entry: This server doesn't have an icon")
		await self.bot.embed_reply("This server's icon:", image_url = ctx.message.server.icon_url)
	
	@commands.command(aliases = ["serverinformation", "server_info", "server_information"], pass_context = True, no_pm = True)
	@checks.not_forbidden()
	async def serverinfo(self, ctx):
		'''Information about a server'''
		server = ctx.message.server
		embed = discord.Embed(title = server.name, url = server.icon_url, timestamp = server.created_at, color = clients.bot_color)
		avatar = ctx.message.author.avatar_url or ctx.message.author.default_avatar_url
		embed.set_author(name = ctx.message.author.display_name, icon_url = avatar)
		embed.set_thumbnail(url = server.icon_url)
		embed.add_field(name = "Owner", value = server.owner.mention)
		embed.add_field(name = "ID", value = server.id)
		embed.add_field(name = "Region", value = str(server.region))
		embed.add_field(name = "Roles", value = len(server.roles))
		channel_types = [c.type for c in server.channels]
		text_count = channel_types.count(discord.ChannelType.text)
		voice_count = channel_types.count(discord.ChannelType.voice)
		embed.add_field(name = "Channels", value = "{} text\n{} voice".format(text_count, voice_count))
		embed.add_field(name = "Members", value = "{}\n({} bots)".format(server.member_count, sum(m.bot for m in server.members)))
		embed.add_field(name = "AFK Timeout", value = "{:g} min.".format(server.afk_timeout / 60))
		embed.add_field(name = "AFK Channel", value = str(server.afk_channel))
		embed.add_field(name = "Verification Level", value = str(server.verification_level).capitalize())
		embed.add_field(name = "2FA Requirement", value = bool(server.mfa_level))
		embed.add_field(name = "Default Channel", value = server.default_channel.mention)
		if server.emojis:
			emojis = [str(emoji) for emoji in server.emojis]
			if len(' '.join(emojis)) <= 1024:
				embed.add_field(name = "Emojis", value = ' '.join(emojis), inline = False)
			else:
				embed.add_field(name = "Emojis", value = ' '.join(emojis[:len(emojis) // 2]), inline = False)
				embed.add_field(name = "Emojis", value = ' '.join(emojis[len(emojis) // 2:]), inline = False)
		embed.set_footer(text = "Created")
		await self.bot.say(embed = embed)
	
	@commands.command(aliases = ["server_owner"], pass_context = True, no_pm = True)
	@checks.not_forbidden()
	async def serverowner(self, ctx):
		'''The owner of the server'''
		owner = ctx.message.server.owner
		await self.bot.embed_reply("The owner of this server is {}".format(owner.mention), footer_text = str(owner), footer_icon_url = owner.avatar_url or owner.default_avatar_url)
	
	@commands.command(aliases = ["user_info"], pass_context = True)
	@checks.not_forbidden()
	async def userinfo(self, ctx):
		'''Information about a user'''
		user = ctx.message.author
		avatar = user.avatar_url or user.default_avatar_url
		await self.bot.embed_reply(None, title = str(user), title_url = avatar, thumbnail_url = avatar, footer_text = "Created", timestamp = user.created_at, fields = [("User", user.mention), ("ID", user.id), ("Bot", user.bot)])
		# member info, status, game, roles, color, etc.
	
	# Convert Attributes
	
	@commands.command(aliases = ["id_to_name"])
	@checks.not_forbidden()
	async def idtoname(self, id : str):
		'''Convert user id to name'''
		user = await self.bot.get_user_info(id)
		if not user:
			await self.bot.embed_reply(":no_entry: User with that id not found")
			return
		embed = discord.Embed(color = clients.bot_color)
		embed.set_author(name = str(user), icon_url = user.avatar_url or user.default_avatar_url)
		# Include mention?
		await self.bot.reply("", embed = embed)
	
	@commands.command(aliases = ["usertoid", "usernametoid", "name_to_id", "user_to_id", "username_to_id"], no_pm = True, pass_context = True)
	@checks.not_forbidden()
	async def nametoid(self, ctx, *, name : str):
		'''Convert username to id'''
		user = await utilities.get_user(ctx, name)
		if not user:
			await self.bot.embed_reply(":no_entry: {} was not found on this server".format(name))
			return
		embed = discord.Embed(description = user.id, color = clients.bot_color)
		embed.set_author(name = str(user), icon_url = user.avatar_url or user.default_avatar_url)
		# Include mention?
		await self.bot.reply("", embed = embed)
	
	# Checks
	
	@commands.command(aliases = ["here"], pass_context = True)
	@checks.not_forbidden()
	async def everyone(self, ctx):
		'''
		Check if you can mention everyone/here
		For the channel you execute the command in
		'''
		able = "" if ctx.message.author.permissions_in(ctx.message.channel).mention_everyone else "not "
		await self.bot.embed_reply("You are {}able to mention everyone/here in this channel".format(able))

