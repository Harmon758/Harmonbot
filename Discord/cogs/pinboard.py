
import discord
from discord.ext import commands

from typing import Optional

from utilities import checks

def setup(bot):
	bot.add_cog(Pinboard(bot))

class Pinboard(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.default_threshold = 3
		self.pin_emotes = ("\N{PUSHPIN}", "\N{ROUND PUSHPIN}", 
							"\N{WHITE MEDIUM STAR}", "\N{GLOWING STAR}", "\N{SHOOTING STAR}")
	
	async def cog_load(self):
		await self.bot.connect_to_database()
		await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS pinboard")
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS pinboard.pinboards (
				guild_id			BIGINT PRIMARY KEY, 
				channel_id			BIGINT, 
				threshold			INT, 
				private_channels	BOOL
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS pinboard.pins (
				message_id			BIGINT PRIMARY KEY, 
				guild_id			BIGINT, 
				channel_id			BIGINT, 
				pinboard_message_id BIGINT
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS pinboard.pinners (
				message_id	BIGINT REFERENCES pinboard.pins (message_id) ON DELETE CASCADE, 
				pinner_id	BIGINT, 
				PRIMARY KEY (message_id, pinner_id)
			)
			"""
		)
	
	@commands.group(aliases = ["starboard"], invoke_without_command = True, case_insensitive = True)
	@commands.is_owner()
	async def pinboard(self, ctx):
		'''
		WIP
		Pinboard/Starboard
		Inspired by Rapptz/Danny's Robo/R. Danny's starboard
		'''
		await ctx.send_help(ctx.command)
	
	@pinboard.command()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	@commands.guild_only()
	async def backfill(self, ctx):
		'''
		Backfill pins into current pinboard channel
		This can take a while depending on how many missing pinned messages there are
		'''
		record = await ctx.bot.db.fetchrow(
			"""
			SELECT channel_id, threshold, private_channels
			FROM pinboard.pinboards
			WHERE guild_id = $1
			""", 
			ctx.guild.id
		)
		pinboard_channel_id = record["channel_id"]
		threshold = record["threshold"] or self.default_threshold
		private_channels_setting = record["private_channels"]
		if not pinboard_channel_id:
			return await ctx.embed_reply(":no_entry: Error: Pinboard channel not set")
		response = await ctx.embed_reply("Backfilling...")
		pinboard_channel = self.bot.get_channel(pinboard_channel_id)
		async with ctx.bot.database_connection_pool.acquire() as connection:
			async with connection.transaction():
				# Postgres requires non-scrollable cursors to be created
				# and used in a transaction.
				async for record in connection.cursor("SELECT * FROM pinboard.pins WHERE guild_id = $1 ORDER BY message_id", 
														ctx.guild.id):
					try:
						await pinboard_channel.fetch_message(record["pinboard_message_id"])
					except (discord.NotFound, discord.HTTPException):
						pin_count = await self.bot.db.fetchval("SELECT COUNT(*) FROM pinboard.pinners WHERE message_id = $1",
																record["message_id"])
						if pin_count < threshold:
							continue
						pinned_message_channel = self.bot.get_channel(record["channel_id"])
						if not private_channels_setting and pinned_message_channel.overwrites_for(ctx.guild.default_role).read_messages == False:
							continue
						pinned_message = await pinned_message_channel.fetch_message(record["message_id"])
						pinboard_message = await self.send_pinboard_message(pinboard_channel, pinned_message, pin_count)
						await self.bot.db.execute("UPDATE pinboard.pins SET pinboard_message_id = $1 WHERE message_id = $2",
													pinboard_message.id, record["message_id"])
		if ctx.channel.id == pinboard_channel_id:
			await ctx.bot.attempt_delete_message(response)
		else:
			embed = response.embeds[0]
			embed.description = "Backfill complete"
			await response.edit(embed = embed)
	
	# TODO: pinboard off option
	@pinboard.command()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	@commands.guild_only()
	async def channel(self, ctx, channel : discord.TextChannel = None):
		'''Set/get channel'''
		channel_id = await ctx.bot.db.fetchval("SELECT channel_id FROM pinboard.pinboards WHERE guild_id = $1", 
												ctx.guild.id)
		if not channel_id:
			if not channel:
				channel = ctx.channel
			await ctx.bot.db.execute("INSERT INTO pinboard.pinboards (guild_id, channel_id) VALUES ($1, $2)",
										ctx.guild.id, channel.id)
			await ctx.embed_reply(f":thumbsup:{ctx.bot.emoji_skin_tone} Pinboard channel set to {channel.mention}")
		elif not channel:
			pinboard_channel = ctx.guild.get_channel(channel_id)
			await ctx.embed_reply(f"Current pinboard channel: {pinboard_channel.mention}")
		else:
			await ctx.bot.db.execute("UPDATE pinboard.pinboards SET channel_id = $1 WHERE guild_id = $2",
										channel.id, ctx.guild.id)
			await ctx.embed_reply(f":thumbsup:{ctx.bot.emoji_skin_tone} Changed pinboard channel to {channel.mention}")
	
	@pinboard.command(aliases = ["starrers", "who", "pinner", "starrer"])
	@checks.not_forbidden()
	async def pinners(self, ctx, message: discord.Message):
		'''
		Show who pinned a message
		message input can be the pinned message or the message in the pinboard channel
		'''
		records = await ctx.bot.db.fetch(
			"""
			SELECT pinboard.pinners.pinner_id
			FROM pinboard.pinners
			INNER JOIN pinboard.pins
			ON pinboard.pinners.message_id = pinboard.pins.message_id
			WHERE pinboard.pins.message_id = $1 OR pinboard.pins.pinboard_message_id = $1
			""", 
			message.id
		)
		if not records:
			return await ctx.embed_reply("No one has pinned this message or this is not a valid message ID")
		pinners = []
		for record in records:
			pinner = ctx.bot.get_user(record[0])
			if not pinner:
				pinner = await ctx.bot.fetch_user(record[0])
			pinners.append(pinner)
		await ctx.embed_reply(' '.join(pinner.mention for pinner in pinners), 
								title = f"{len(records)} {ctx.bot.inflect_engine.plural('pinner', len(records))} of {message.jump_url}")
	
	@pinboard.command(aliases = ["private"])
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	@commands.guild_only()
	async def private_channels(self, ctx, setting: Optional[bool]):
		'''
		Set/get whether to include pins from private channels
		Default: False
		A channel is considered private if the "Read Messages" permission is off for the everyone role
		'''
		# TODO: Handle case where guild-level "Read Messages" permission is off for @everyone?
		if setting is None:
			setting = await ctx.bot.db.fetchval(
				"""
				SELECT private_channels
				FROM pinboard.pinboards
				WHERE guild_id = $1
				""", 
				ctx.guild.id
			)
			if setting is None:
				await ctx.embed_reply(f"Current pinboard setting: Ignore private channels (Default)")
			elif setting:
				await ctx.embed_reply(f"Current pinboard setting: Include private channels")
			else:
				await ctx.embed_reply(f"Current pinboard setting: Ignore private channels")
		else:
			await ctx.bot.db.execute(
				"""
				UPDATE pinboard.pinboards
				SET private_channels = $1
				WHERE guild_id = $2
				""", 
				setting, ctx.guild.id
			)
			await ctx.embed_reply(f":thumbsup:{ctx.bot.emoji_skin_tone} Changed pinboard private channels setting to {setting}")
	
	@pinboard.command()
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	@commands.guild_only()
	async def threshold(self, ctx, threshold_number : int = None):
		'''
		Set/get the number of reactions needed to pin message
		Default: 3
		'''
		if threshold_number:
			await ctx.bot.db.execute("UPDATE pinboard.pinboards SET threshold = $1 WHERE guild_id = $2",
										threshold_number, ctx.guild.id)
			await ctx.embed_reply(f":thumbsup:{ctx.bot.emoji_skin_tone} Changed pinboard threshold to {threshold_number}")
		else:
			threshold_number = await ctx.bot.db.fetchval("SELECT threshold FROM pinboard.pinboards WHERE guild_id = $1", 
															ctx.guild.id)
			if threshold_number:
				await ctx.embed_reply(f"Current pinboard threshold: {threshold_number}")
			else:
				await ctx.embed_reply(f"The current pinboard threshold is the default of 3")
	
	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		if str(payload.emoji) not in self.pin_emotes:
			# Reaction is not for pinboard
			return
		if not payload.guild_id:
			# Reaction is not in a guild
			return
		record = await self.bot.db.fetchrow(
			"""
			SELECT channel_id, threshold, private_channels
			FROM pinboard.pinboards
			WHERE guild_id = $1
			""", 
			payload.guild_id
		)
		if not record:
			# Guild doesn't have a pinboard
			return
		pinboard_channel_id = record["channel_id"]
		threshold = record["threshold"] or self.default_threshold
		private_channels_setting = record["private_channels"]
		if payload.channel_id == pinboard_channel_id and (
			record := await self.bot.db.fetchrow(
				"""
				SELECT message_id, channel_id
				FROM pinboard.pins WHERE pinboard_message_id = $1
				""", 
				(pinboard_message_id := payload.message_id)
			)
		):
			# Message being reacted to is on the pinboard
			message_id = record["message_id"]
			channel_id = record["channel_id"]
		else:
			message_id = payload.message_id
			channel_id = payload.channel_id
			pinboard_message_id = await self.bot.db.fetchval(
				"""
				INSERT INTO pinboard.pins (message_id, guild_id, channel_id)
				VALUES ($1, $2, $3)
				ON CONFLICT (message_id) DO UPDATE SET guild_id = $2
				RETURNING pinboard_message_id
				""", 
				message_id, payload.guild_id, payload.channel_id
			)
		# Add user as pinner
		inserted = await self.bot.db.fetchrow(
			"""
			INSERT INTO pinboard.pinners (message_id, pinner_id)
			VALUES ($1, $2)
			ON CONFLICT DO NOTHING
			RETURNING *
			""", 
			message_id, payload.user_id
		)
		if not inserted:
			# User has already pinned this message
			return
		pin_count = await self.bot.db.fetchval("SELECT COUNT(*) FROM pinboard.pinners WHERE message_id = $1",
												message_id)
		if pin_count < threshold:
			# Pin count has not reached threshold yet
			return
		pinboard_channel = self.bot.get_channel(pinboard_channel_id)
		pinned_message_channel = self.bot.get_channel(channel_id)
		if not private_channels_setting and pinned_message_channel.overwrites_for(payload.member.guild.default_role).read_messages is False:
			# Set to ignore private channels and message is in private channel
			return
		pinned_message = await pinned_message_channel.fetch_message(message_id)
		if pinboard_message_id:
			# Pinboard message already exists
			pinboard_message = await pinboard_channel.fetch_message(pinboard_message_id)
			embed = pinboard_message.embeds[0]
			embed.clear_fields()
			embed.add_field(name = f"**{pin_count}** \N{PUSHPIN}", value = f"[Message Link]({pinned_message.jump_url})")
			await pinboard_message.edit(embed = embed)
		else:
			pinboard_message = await self.send_pinboard_message(pinboard_channel, pinned_message, pin_count)
			await self.bot.db.execute("UPDATE pinboard.pins SET pinboard_message_id = $1 WHERE message_id = $2",
										pinboard_message.id, message_id)
	
	async def send_pinboard_message(self, pinboard_channel, pinned_message, pin_count):
		# TODO: custom emote
		embed = discord.Embed(timestamp = pinned_message.created_at, color = 0xdd2e44)
		# TODO: color dependent on custom emote
		# alternate color: 0xbe1931
		# star: 0xffac33
		embed.set_author(name = pinned_message.author.display_name, icon_url = pinned_message.author.avatar.url)
		content = pinned_message.content
		if pinned_message.embeds:
			if pinned_message.embeds[0].type == "image":
				embed.set_image(url = pinned_message.embeds[0].thumbnail.url)
			else:
				content += '\n' + self.bot.CODE_BLOCK.format(pinned_message.embeds[0].to_dict())
		embed.description = content
		if pinned_message.attachments:
			embed.set_image(url = pinned_message.attachments[0].url)
		# TODO: Handle non-image attachments
		# TODO: Handle both attachments and image embed?
		embed.add_field(name = f"**{pin_count}** \N{PUSHPIN}", value = f"[Message Link]({pinned_message.jump_url})")
		embed.set_footer(text = f"In #{pinned_message.channel}")
		return await pinboard_channel.send(embed = embed)

