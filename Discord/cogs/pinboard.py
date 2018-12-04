
import discord
from discord.ext import commands

import asyncpg

from utilities import checks

def setup(bot):
	bot.add_cog(Pinboard(bot))

class Pinboard:
	
	def __init__(self, bot):
		self.bot = bot
		self.pin_emotes = ("\N{PUSHPIN}", "\N{ROUND PUSHPIN}", 
							"\N{WHITE MEDIUM STAR}", "\N{GLOWING STAR}", "\N{SHOOTING STAR}")
		self.bot.loop.create_task(self.initialize_database())
	
	async def initialize_database(self):
		await self.bot.connect_to_database()
		await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS pinboard")
		await self.bot.db.execute("""CREATE TABLE IF NOT EXISTS pinboard.pinboards (
										guild_id	BIGINT PRIMARY KEY, 
										channel_id	BIGINT
										)""")
		await self.bot.db.execute("""CREATE TABLE IF NOT EXISTS pinboard.pins (
										message_id			BIGINT PRIMARY KEY, 
										guild_id			BIGINT, 
										channel_id			BIGINT, 
										pinboard_message_id BIGINT
										)""")
		await self.bot.db.execute("""CREATE TABLE IF NOT EXISTS pinboard.pinners (
										message_id	BIGINT REFERENCES pins (message_id) ON DELETE CASCADE, 
										pinner_id	BIGINT, 
										PRIMARY KEY (message_id, pinner_id)
										)""")
	
	@commands.group(aliases = ["starboard"], invoke_without_command = True)
	@commands.is_owner()
	async def pinboard(self, ctx):
		'''
		WIP
		Pinboard/Starboard
		Inspired by Rapptz/Danny's Robo/R. Danny's starboard
		'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	@pinboard.command()
	@checks.is_permitted()
	async def backfill(self, ctx):
		'''
		Backfill pins into current pinboard channel
		This can take a while depending on how many missing pinned messages there are
		'''
		pinboard_channel_id = await ctx.bot.db.fetchval("SELECT channel_id FROM pinboard.pinboards where guild_id = $1", 
															ctx.guild.id)
		if not pinboard_channel_id:
			return await ctx.embed_reply(":no_entry: Error: Pinboard channel not set")
		response = await ctx.embed_reply("Backfilling...")
		pinboard_channel = self.bot.get_channel(pinboard_channel_id)
		async with ctx.bot.database_connection_pool.acquire() as connection:
			async with connection.transaction():
				# Postgres requires non-scrollable cursors to be created
				# and used in a transaction.
				async for record in connection.cursor("SELECT * FROM pinboard.pins where guild_id = $1", ctx.guild.id):
					try:
						await pinboard_channel.get_message(record["pinboard_message_id"])
					except (discord.NotFound, discord.HTTPException):
						pin_count = await self.bot.db.fetchval("SELECT COUNT(*) FROM pinboard.pinners WHERE message_id = $1",
																record["message_id"])
						pinned_message_channel = self.bot.get_channel(record["channel_id"])
						pinned_message = await pinned_message_channel.get_message(record["message_id"])
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
	@checks.is_permitted()
	async def channel(self, ctx, channel : discord.TextChannel = None):
		'''Set/get channel'''
		channel_id = await ctx.bot.db.fetchval("SELECT channel_id FROM pinboard.pinboards where guild_id = $1", 
												ctx.guild.id)
		if not channel_id:
			if not channel:
				channel = ctx.channel
			await ctx.bot.db.execute("INSERT INTO pinboard.pinboards (guild_id, channel_id) VALUES ($1, $2)",
										ctx.guild.id, channel.id)
			await ctx.embed_reply(f":thumbsup::skin-tone-2: Pinboard channel set to {channel.mention}")
		elif not channel:
			pinboard_channel = ctx.guild.get_channel(channel_id)
			await ctx.embed_reply(f"Current pinboard channel: {pinboard_channel.mention}")
		else:
			await ctx.bot.db.execute("UPDATE pinboard.pinboards SET channel_id = $1 WHERE guild_id = $2",
										channel.id, ctx.guild.id)
			await ctx.embed_reply(f":thumbsup::skin-tone-2: Changed pinboard channel to {channel.mention}")
	
	async def on_raw_reaction_add(self, payload):
		if str(payload.emoji) not in self.pin_emotes:
			# Reaction is not for pinboard
			return
		if not payload.guild_id:
			# Reaction is not in a guild
			return
		pinboard_channel_id = await self.bot.db.fetchval("SELECT channel_id FROM pinboard.pinboards where guild_id = $1", 
															payload.guild_id)
		if not pinboard_channel_id:
			# Guild doesn't have a pinboard
			return
		if payload.channel_id == pinboard_channel_id:
			# Message being reacted to is on the pinboard
			pinboard_message_id = payload.message_id
			record = await self.bot.db.fetchrow("""SELECT message_id, channel_id
													FROM pinboard.pins where pinboard_message_id = $1""", 
													pinboard_message_id)
			message_id = record["message_id"]
			channel_id = record["channel_id"]
		else:
			message_id = payload.message_id
			channel_id = payload.channel_id
			pinboard_message_id = await self.bot.db.fetchval("""INSERT INTO pinboard.pins (message_id, guild_id, channel_id)
																VALUES ($1, $2, $3)
																ON CONFLICT (message_id) DO UPDATE SET guild_id = $2
																RETURNING pinboard_message_id""", 
																message_id, payload.guild_id, payload.channel_id)
		try:
			# Add user as pinner
			await self.bot.db.execute("""INSERT INTO pinboard.pinners (message_id, pinner_id)
											VALUES ($1, $2)""", 
											message_id, payload.user_id)
		except asyncpg.UniqueViolationError:
			# User has already pinned this message
			return
		pin_count = await self.bot.db.fetchval("SELECT COUNT(*) FROM pinboard.pinners WHERE message_id = $1",
												message_id)
		pinboard_channel = self.bot.get_channel(pinboard_channel_id)
		pinned_message_channel = self.bot.get_channel(channel_id)
		pinned_message = await pinned_message_channel.get_message(message_id)
		if pinboard_message_id:
			# Pinboard message already exists
			pinboard_message = await pinboard_channel.get_message(pinboard_message_id)
			embed = pinboard_message.embeds[0]
			embed.clear_fields()
			embed.add_field(name = f"**{pin_count}** \N{PUSHPIN}", value = f"[**Message Link**]({pinned_message.jump_url})")
			await pinboard_message.edit(embed = embed)
		else:
			pinboard_message = await self.send_pinboard_message(pinboard_channel, pinned_message, pin_count)
			await self.bot.db.execute("UPDATE pinboard.pins SET pinboard_message_id = $1 WHERE message_id = $2",
										pinboard_message.id, message_id)
	
	async def send_pinboard_message(self, pinboard_channel, pinned_message, pin_count):
		# TODO: custom emote
		content = pinned_message.content
		if pinned_message.embeds:
			content += '\n' + self.bot.CODE_BLOCK.format(pinned_message.embeds[0].to_dict())
		embed = discord.Embed(description = content, timestamp = pinned_message.created_at, color = 0xdd2e44)
		# TODO: color dependent on custom emote
		# alternate color: 0xbe1931
		# star: 0xffac33
		embed.set_author(name = pinned_message.author.display_name, icon_url = pinned_message.author.avatar_url)
		if pinned_message.attachments:
			embed.set_image(url = pinned_message.attachments[0].url)
		embed.add_field(name = f"**{pin_count}** \N{PUSHPIN}", value = f"[Message Link]({pinned_message.jump_url})")
		embed.set_footer(text = f"In #{pinned_message.channel}")
		return await pinboard_channel.send(embed = embed)

