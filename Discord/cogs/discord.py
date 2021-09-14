
import discord
from discord.ext import commands

import asyncio
import datetime
import time
from typing import Optional, Union

from parsedatetime import Calendar, VERSION_CONTEXT_STYLE

from modules import conversions
from utilities import checks

ACTIVITES = {
	"Betrayal.io": 773336526917861400,
	"Chess In The Park": 832012774040141894,
	"Fishington.io": 814288819477020702,
	"Poker Night": 755827207812677713,
	"YouTube Together": 755600276941176913
}

def setup(bot):
	bot.add_cog(Discord(bot))

class Discord(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		
		self.calendar = Calendar(version = VERSION_CONTEXT_STYLE)
		# Add mo as valid abbreviation for month
		self.calendar.ptc.units["months"].append("mo")
		
		def activity_wrapper(activity):
			async def activity_command(
				ctx, *, channel: Optional[discord.VoiceChannel]
			):
				if not channel and (
					not ctx.author.voice or not (
						channel := ctx.author.voice.channel
					)
				):
					await ctx.embed_reply(
						f"{ctx.bot.error_emoji} Voice channel not found"
					)
					return
				invite = await channel.create_invite(
					reason = f"{activity} activity",
					target_type = discord.InviteTarget.embedded_application,
					target_application_id = ACTIVITES[activity]
				)
				await ctx.embed_reply(
					title = activity,
					footer_text = discord.Embed.Empty,
					view = ActivityView(ctx, invite)
				)
			return activity_command
		
		for activity, name, aliases in (
			("Betrayal.io", "betrayal", ["betrayal.io"]),
			("Chess In The Park", "chess", []),
			("Fishington.io", "fishington", ["fishing", "fishington.io"]),
			("Poker Night", "poker", []),
			("YouTube Together", "youtube", ["yt"]),
		):
			command = commands.Command(
				activity_wrapper(activity),
				name = name,
				aliases = aliases,
				help = "Create an invite for " + activity,
				checks = [
					commands.guild_only().predicate,
					checks.not_forbidden().predicate,
					commands.bot_has_permissions(
						create_instant_invite = True
					).predicate,
					commands.check_any(
						commands.has_permissions(create_instant_invite = True),
						commands.is_owner()
					).predicate
				]
			)
			setattr(self, name, command)
			self.activity.add_command(command)
	
	# TODO: Include spaces in quotes explanation (in help)
	
	@commands.group(case_insensitive = True, invoke_without_command = True)
	@checks.not_forbidden()
	async def activity(self, ctx):
		'''Create an invite for a voice channel activity'''
		await ctx.send_help(ctx.command)
	
	# TODO: Merge with quote command?
	@commands.command()
	@checks.not_forbidden()
	async def archive(self, ctx, message: discord.Message):
		'''Archive messages'''
		# TODO: Add option to delete message?
		# TODO: Handle rich presence messages?
		# TODO: Use system_content?
		fields = []
		for embed in message.embeds:
			fields.append(("Embed", ctx.bot.CODE_BLOCK.format(embed.to_dict()), False))
		reactions = ""
		for reaction in message.reactions:
			users = await reaction.users(limit = 3).flatten()
			users_message = ", ".join(user.mention for user in sorted(users, key = str))
			if reaction.count > 3:
				users_message += ", etc."
			reaction_string = f"{reaction.emoji}: {reaction.count} ({users_message})"
			if len(reactions) + len(reaction_string) > ctx.bot.EMBED_FIELD_VALUE_CHARACTER_LIMIT:
				break
				# TODO: Handle too long for field value
			reactions += reaction_string + '\n'
		if reactions:
			fields.append(("Reactions", reactions[:-1]))
		image_url = discord.Embed.Empty
		if message.attachments:
			image_url = message.attachments[0].url
		# TODO: Handle non-image attachments
		# TODO: Handle multiple attachments
		await ctx.embed_reply(message.content, 
								author_name = message.author.display_name, author_icon_url = message.author.avatar.url, 
								fields = fields, image_url = image_url, 
								footer_text = f"In #{message.channel}", timestamp = message.created_at)
		# TODO: Include message author ID/username#discriminator
		# TODO: Mention channel or include channel ID
		# TODO: Include message.edited_at
	
	@commands.group(aliases = ["purge", "clean"], invoke_without_command = True, case_insensitive = True)
	async def delete(self, ctx, number : int, *, user : discord.Member = None):
		'''
		Delete messages
		If used in a DM, delete <number> deletes <number> of Harmonbot's messages
		'''
		if ctx.channel.type is discord.ChannelType.private:
			return await self.delete_number(ctx, number, check = lambda m: m.author == self.bot.user, delete_command = False)
		await commands.check_any(commands.has_permissions(manage_messages = True), commands.is_owner()).predicate(ctx)
		await commands.bot_has_permissions(manage_messages = True).predicate(ctx)
		if user:
			await self.delete_number(ctx, number, check = lambda m: m.author.id == user.id)
		else:
			await self.bot.attempt_delete_message(ctx.message)
			try:
				await ctx.channel.purge(limit = number)
			except discord.NotFound:
				# TODO: Better handling
				return
	
	@delete.command(name = "attachments", aliases = ["images"])
	@commands.bot_has_permissions(manage_messages = True)
	@commands.check_any(commands.has_permissions(manage_messages = True), commands.is_owner())
	@commands.guild_only()
	# TODO: Handle in DMs
	async def delete_attachments(self, ctx, number : int):
		'''Deletes the <number> most recent messages with attachments'''
		await self.delete_number(ctx, number, check = lambda m: m.attachments)
	
	@delete.command(name = "contains")
	@commands.bot_has_permissions(manage_messages = True)
	@commands.check_any(commands.has_permissions(manage_messages = True), commands.is_owner())
	@commands.guild_only()
	# TODO: Handle in DMs
	async def delete_contains(self, ctx, string : str, number : int):
		'''Deletes the <number> most recent messages with <string> in them'''
		await self.delete_number(ctx, number, check = lambda m: string in m.content)
	
	@delete.command(name = "embeds")
	@commands.bot_has_permissions(manage_messages = True)
	@commands.check_any(commands.has_permissions(manage_messages = True), commands.is_owner())
	@commands.guild_only()
	# TODO: Handle in DMs
	async def delete_embeds(self, ctx, number: int):
		'''Deletes the <number> most recent messages with embeds'''
		await self.delete_number(ctx, number, check = lambda m: m.embeds)
	
	@delete.command(name = "time")
	@commands.bot_has_permissions(manage_messages = True)
	@commands.check_any(commands.has_permissions(manage_messages = True), commands.is_owner())
	@commands.guild_only()
	# TODO: Handle in DMs
	async def delete_time(self, ctx, minutes : int):
		'''Deletes messages in the past <minutes> minutes'''
		await self.bot.attempt_delete_message(ctx.message)
		await ctx.channel.purge(after = datetime.datetime.utcnow() - datetime.timedelta(minutes = minutes), 
								limit = None, oldest_first = False)
	
	# TODO: delete mentions, invites?
	# TODO: server settings/options:
	#       in progress + count summary for command
	#       case-insensitive
	#       include embed text
	
	# TODO: make Bot method?
	# TODO: use purge with no limit?, increment count in check?
	async def delete_number(self, ctx, number, check, delete_command = True):
		if number <= 0:
			return await ctx.embed_reply(":no_entry: Error: Number of messages to delete must be greater than 0")
		to_delete = []
		count = 0
		if delete_command:
			await ctx.bot.attempt_delete_message(ctx.message)
		async for message in ctx.history(limit = None).filter(check):
			if (message.id < int((time.time() - 14 * 24 * 60 * 60) * 1000 - discord.utils.DISCORD_EPOCH) << 22 or 
				ctx.channel.type is discord.ChannelType.private):
				# Too old (older than 14 days) to bulk delete or in DM
				await ctx.bot.attempt_delete_message(message)
			else:
				to_delete.append(message)
			count += 1
			if count == number:
				break
			elif len(to_delete) == 100:
				await ctx.channel.delete_messages(to_delete)
				to_delete.clear()
				await asyncio.sleep(1)  # Necessary?
		if len(to_delete) == 1:
			await ctx.bot.attempt_delete_message(to_delete[0])
		elif len(to_delete) > 1:
			await ctx.channel.delete_messages(to_delete)
	
	@commands.command(aliases = ["here"])
	@checks.not_forbidden()
	async def everyone(self, ctx):
		'''
		Check if you can mention everyone/here
		For the channel you execute the command in
		'''
		if ctx.channel.permissions_for(ctx.author).mention_everyone:
			await ctx.embed_reply("You are able to mention everyone/here in this channel")
		else:
			await ctx.embed_reply("You are not able to mention everyone/here in this channel")
	
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
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@commands.bot_has_permissions(manage_messages = True)
	@commands.check_any(commands.has_permissions(manage_messages = True), commands.is_owner())
	@commands.guild_only()
	# TODO: Handle in DMs
	async def pin(self, ctx, message: discord.Message):
		'''Pin message by message ID'''
		await message.pin()
		await ctx.embed_reply(":pushpin: Pinned message")
	
	@pin.command(name = "first")
	@commands.bot_has_permissions(manage_messages = True)
	@commands.check_any(commands.has_permissions(manage_messages = True), commands.is_owner())
	@commands.guild_only()
	# TODO: Handle in DMs
	async def pin_first(self, ctx):
		'''Pin first message'''
		message = await ctx.history(oldest_first = True, limit = 1).next()
		await message.pin()
		await ctx.embed_reply(":pushpin: Pinned first message in this channel")
	
	@commands.command()
	@commands.bot_has_permissions(manage_messages = True)
	@commands.check_any(commands.has_permissions(manage_messages = True), commands.is_owner())
	@commands.guild_only()
	# TODO: Handle in DMs
	async def unpin(self, ctx, message: discord.Message):
		'''Unpin message by message ID'''
		await message.unpin()
		await ctx.embed_reply(":wastebasket: Unpinned message")
	
	@commands.command()
	@commands.bot_has_permissions(manage_messages = True)
	@commands.check_any(commands.has_permissions(manage_messages = True), commands.is_owner())
	@commands.guild_only()
	# TODO: Handle own messages (in DMs)
	async def suppress(self, ctx, message: discord.Message):
		'''Suppress embeds in a message'''
		await message.edit(suppress = True)
		await ctx.embed_reply(f"\N{FACE WITH FINGER COVERING CLOSED LIPS} Suppressed embeds in [message]({message.jump_url})")
	
	@commands.command()
	@commands.bot_has_permissions(manage_messages = True)
	@commands.check_any(commands.has_permissions(manage_messages = True), commands.is_owner())
	@commands.guild_only()
	# TODO: Handle own messages (in DMs)
	async def unsuppress(self, ctx, message: discord.Message):
		'''Unsuppress embeds in a message'''
		await message.edit(suppress = False)
		await ctx.embed_reply(f"\N{SPEAKING HEAD IN SILHOUETTE} Unsuppressed embeds in [message]({message.jump_url})")
	
	@commands.command()
	@checks.not_forbidden()
	async def timestamp(
		self, ctx, ID: Optional[Union[discord.Message, discord.Object]],
		*, time: Optional[str]
	):
		'''
		Timestamp of a Discord ID or message or formatted markdown for a time
		'''
		if ID:
			ID = ID.id
			time = discord.utils.snowflake_time(ID).replace(
				tzinfo = datetime.timezone.utc
			)
			await ctx.embed_reply(
				f"{discord.utils.format_dt(time)}\n{time}"
			)
			return
		
		if time:
			time = time.replace("from now", "")
			now = datetime.datetime.now(datetime.timezone.utc)
			if not (matches := self.calendar.nlp(time, sourceTime = now)):
				raise commands.BadArgument("Invalid time")
			parsed_datetime, context, start_pos, end_pos, matched_text = matches[0]
			if not context.hasTime:
				parsed_datetime = parsed_datetime.replace(
					hour = now.hour, minute = now.minute, 
					second = now.second, microsecond = now.microsecond
				)
			time = parsed_datetime.replace(
				tzinfo = datetime.timezone.utc
			)
		else:
			time = datetime.datetime.now(datetime.timezone.utc)
		
		t = discord.utils.format_dt(time, style = 't')
		T = discord.utils.format_dt(time, style = 'T')
		d = discord.utils.format_dt(time, style = 'd')
		D = discord.utils.format_dt(time, style = 'D')
		f = discord.utils.format_dt(time, style = 'f')
		F = discord.utils.format_dt(time, style = 'F')
		R = discord.utils.format_dt(time, style = 'R')
		await ctx.embed_reply(
			f"Epoch/POSIX: {time.timestamp()}\n"
			f"{t} (`{t}`)\n"
			f"{T} (`{T}`)\n"
			f"{d} (`{d}`)\n"
			f"{D} (`{D}`)\n"
			f"{f} (`{f}`, `{discord.utils.format_dt(time)}`)\n"
			f"{F} (`{F}`)\n"
			f"{R} (`{R}`)"
		)
	
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

class ActivityView(discord.ui.View):
	
	def __init__(self, ctx, invite):
		super().__init__(timeout = None)
		self.ctx = ctx
		self.invite = invite
		
		self.clear_items()
		self.start = discord.ui.Button(
			label = "Start/Join", url = str(invite)
		)
		self.add_item(self.start)
		self.add_item(self.send)
		self.add_item(self.revoke)
	
	@discord.ui.button(
		label = "Send Invite", style = discord.ButtonStyle.blurple
	)
	async def send(self, button, interaction):
		await interaction.response.send_message(self.invite)
	
	@discord.ui.button(
		label = "Revoke Invite", style = discord.ButtonStyle.red
	)
	async def revoke(self, button, interaction):
		if (
			interaction.user.id not in (
				self.ctx.author.id, self.ctx.bot.owner_id
			)
		) and (
			not self.invite.channel.permissions_for(
				interaction.user
			).manage_channels
		):
			await interaction.response.send_message(
				"You don't have permission to do that.",
				ephemeral = True
			)
			return
		
		try:
			await self.invite.delete()
		except discord.Forbidden:
			await interaction.response.send_message(
				"I need the \"manage channel(s)\" permission to do that.",
				ephemeral = True
			)
			return
		except discord.NotFound:
			pass
		
		self.start.disabled = True
		self.send.disabled = True
		self.revoke.disabled = True
		self.revoke.label = "Invite Revoked"
		await interaction.response.edit_message(view = self)
		
		self.stop()

