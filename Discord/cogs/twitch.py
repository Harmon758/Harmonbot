
import discord
from discord.ext import commands, tasks

import asyncio
from itertools import zip_longest
import logging
import sys
import traceback

import aiohttp
import dateutil.parser

from utilities import checks

errors_logger = logging.getLogger("errors")

def setup(bot):
	bot.add_cog(Twitch(bot))

class Twitch(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.check_streams.start().set_name("Twitch")
	
	def cog_unload(self):
		self.check_streams.cancel()
	
	async def initialize_database(self):
		await self.bot.connect_to_database()
		await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS twitch_notifications")
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS twitch_notifications.channels (
				channel_id		BIGINT, 
				user_name		TEXT, 
				user_id			TEXT, 
				PRIMARY KEY		(channel_id, user_id)
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS twitch_notifications.filters (
				channel_id		BIGINT, 
				filter			TEXT, 
				PRIMARY KEY		(channel_id, filter)
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS twitch_notifications.games (
				channel_id		BIGINT, 
				game_id			TEXT, 
				game_name		TEXT, 
				PRIMARY KEY		(channel_id, game_id)
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS twitch_notifications.keywords (
				channel_id		BIGINT, 
				keyword			TEXT, 
				PRIMARY KEY		(channel_id, keyword)
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS twitch_notifications.notifications (
				stream_id		TEXT, 
				channel_id		BIGINT, 
				message_id		BIGINT, 
				live			BOOL, 
				PRIMARY KEY		(stream_id, channel_id)
			)
			"""
		)
	
	@commands.group(case_insensitive = True, invoke_without_command = True)
	@checks.not_forbidden()
	async def twitch(self, ctx):
		'''Twitch'''
		await ctx.send_help(ctx.command)
	
	@twitch.group(case_insensitive = True, invoke_without_command = True)
	@checks.not_forbidden()
	async def add(self, ctx):
		'''Add Twitch channels, games, or keywords to follow'''
		await ctx.send_help(ctx.command)
	
	@add.command(name = "channel", aliases = ["stream"])
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def add_channel(self, ctx, username: str):
		'''Add a Twitch channel to follow'''
		if not (users_data := await ctx.bot.twitch_client.get_users(username)):
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Channel not found")
			return
		
		user = users_data[0]
		inserted = await ctx.bot.db.fetchrow(
			"""
			INSERT INTO twitch_notifications.channels (channel_id, user_name, user_id)
			VALUES ($1, $2, $3)
			ON CONFLICT DO NOTHING
			RETURNING *
			""", 
			ctx.channel.id, username, user.id
		)
		if not inserted:
			await ctx.embed_reply(
				f"This text channel is already following the channel, `{user.display_name}`"
			)
			return
		await ctx.embed_reply(
			f"Added the Twitch channel, [`{user.display_name}`](https://www.twitch.tv/{user.login}), to this text channel\n"
			"I will now announce here when this Twitch channel goes live"
		)
	
	@add.command(name = "filter")
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def add_filter(self, ctx, *, string: str):
		'''Add string to filter Twitch stream titles by'''
		inserted = await ctx.bot.db.fetchrow(
			"""
			INSERT INTO twitch_notifications.filters (channel_id, filter)
			VALUES ($1, $2)
			ON CONFLICT DO NOTHING
			RETURNING *
			""", 
			ctx.channel.id, string
		)
		if not inserted:
			await ctx.embed_reply(
				f"This text channel already has the filter, `{string}`"
			)
			return
		await ctx.embed_reply(
			f"Added the filter, `{string}`, to this text channel\n"
			"I will now filter all streams for this string in the title"
		)
	
	@add.command(name = "game")
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def add_game(self, ctx, *, game: str):
		'''Add a Twitch game to follow'''
		# TODO: Add documentation on 100 limit
		if not (games := await ctx.bot.twitch_client.get_games(game)):
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Game not found")
			return

		game = games[0]
		inserted = await ctx.bot.db.fetchrow(
			"""
			INSERT INTO twitch_notifications.games (channel_id, game_id, game_name)
			VALUES ($1, $2, $3)
			ON CONFLICT DO NOTHING
			RETURNING *
			""", 
			ctx.channel.id, game["id"], game["name"]
		)
		if not inserted:
			await ctx.embed_reply(
				f"This text channel is already following the game, `{game['name']}`"
			)
			return
		await ctx.embed_reply(
			f"Added the game, [`{game['name']}`](https://www.twitch.tv/directory/game/{game['name']}), to this text channel\n"
			"I will now announce here when Twitch streams playing this game go live"
		)
	
	@add.command(name = "keyword", aliases = ["query", "search"])
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def add_keyword(self, ctx, *, keyword: str):
		'''Add a Twitch keyword(s) search to follow'''
		# TODO: Add documentation on 100 limit
		inserted = await ctx.bot.db.fetchrow(
			"""
			INSERT INTO twitch_notifications.keywords (channel_id, keyword)
			VALUES ($1, $2)
			ON CONFLICT DO NOTHING
			RETURNING *
			""", 
			ctx.channel.id, keyword
		)
		if not inserted:
			return await ctx.embed_reply(f"This text channel is already following the keyword, `{keyword}`")
		await ctx.embed_reply(f"Added the keyword search, `{keyword}`, to this text channel\n"
								"I will now announce here when Twitch streams with this keyword go live")
	
	@twitch.command(aliases = ["streams"])
	@checks.not_forbidden()
	async def channels(self, ctx):
		'''Show Twitch channels being followed in this text channel'''
		records = await ctx.bot.db.fetch(
			"""
			SELECT user_name, user_id FROM twitch_notifications.channels
			WHERE channel_id = $1
			""", 
			ctx.channel.id
		)
		description = ""
		for record in records:
			user_data = await ctx.bot.twitch_client.get_users(record["user_id"])
			# TODO: Add note about name change to response
			#       user_data["name"] != record["user_name"]
			user = user_data[0]
			link = f"[{user.display_name}](https://www.twitch.tv/{user.login})"
			if len(description + link) > self.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT:
				await ctx.embed_reply(description[:-1], title = "Twitch channels being followed in this text channel")
				description = ""
			description += link + '\n'
		await ctx.embed_reply(description[:-1], title = "Twitch channels being followed in this text channel")
	
	@twitch.command()
	@checks.not_forbidden()
	async def filters(self, ctx):
		'''Show strings Twitch stream titles are being filtered by in this text channel'''
		records = await ctx.bot.db.fetch(
			"""
			SELECT filter FROM twitch_notifications.filters
			WHERE channel_id = $1
			""", 
			ctx.channel.id
		)
		await ctx.embed_reply(
			title = "Twitch stream title filters in this text channel",
			description = '\n'.join(record["filter"] for record in records)
		)
	
	@twitch.command()
	@checks.not_forbidden()
	async def games(self, ctx):
		'''Show Twitch games being followed in this text channel'''
		records = await ctx.bot.db.fetch(
			"""
			SELECT game_name FROM twitch_notifications.games
			WHERE channel_id = $1
			""", 
			ctx.channel.id
		)
		await ctx.embed_reply(
			title = "Twitch games being followed in this text channel",
			description = '\n'.join(record["game_name"] for record in records)
		)
	
	@twitch.command(aliases = ["queries", "searches"])
	@checks.not_forbidden()
	async def keywords(self, ctx):
		'''Show Twitch keywords being followed in this text channel'''
		records = await ctx.bot.db.fetch(
			"""
			SELECT keyword FROM twitch_notifications.keywords
			WHERE channel_id = $1
			""", 
			ctx.channel.id
		)
		await ctx.embed_reply('\n'.join(record["keyword"] for record in records), 
								title = "Twitch keywords being followed in this text channel")
	
	@twitch.group(
		aliases = ["delete"],
		case_insensitive = True, invoke_without_command = True
	)
	@checks.not_forbidden()
	async def remove(self, ctx):
		'''Remove Twitch channels, games, or keywords being followed'''
		await ctx.send_help(ctx.command)
	
	@remove.command(name = "channel", aliases = ["stream"])
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def remove_channel(self, ctx, username: str):
		'''Remove a Twitch channel being followed'''
		users_data = await ctx.bot.twitch_client.get_users(username)
		user = users_data[0]
		deleted = await ctx.bot.db.fetchval(
			"""
			DELETE FROM twitch_notifications.channels
			WHERE channel_id = $1 AND user_id = $2
			RETURNING *
			""", 
			ctx.channel.id, user.id
		)
		
		if not deleted:
			await ctx.embed_reply(
				f"{ctx.bot.error_emoji} "
				"This text channel isn't following that Twitch channel"
			)
			return
		
		await ctx.embed_reply(
			"Removed the Twitch channel, "
			f"[`{user.display_name}`](https://www.twitch.tv/{user.login}), "
			f"from this text channel"
		)
	
	@remove.command(name = "filter")
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def remove_filter(self, ctx, *, string: str):
		'''Remove a string Twitch stream titles are being filtered by'''
		deleted = await ctx.bot.db.fetchval(
			"""
			DELETE FROM twitch_notifications.filters
			WHERE channel_id = $1 AND filter = $2
			RETURNING *
			""", 
			ctx.channel.id, string
		)
		
		if not deleted:
			await ctx.embed_reply(
				f"{ctx.bot.error_emoji} "
				"This text channel doesn't have that filter"
			)
			return
		
		await ctx.embed_reply(
			f"Removed the filter, `{string}`, from this text channel"
		)
	
	@remove.command(name = "game")
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def remove_game(self, ctx, *, game: str):
		'''Remove a Twitch game being followed'''
		deleted = await ctx.bot.db.fetchval(
			"""
			DELETE FROM twitch_notifications.games
			WHERE channel_id = $1 AND game_name = $2
			RETURNING *
			""", 
			ctx.channel.id, game
		)
		if not deleted:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} This text channel isn't following that game")
		await ctx.embed_reply(f"Removed the game, [`{game}`](https://www.twitch.tv/directory/game/{game}), from this text channel")
	
	@remove.command(name = "keyword", aliases = ["query", "search"])
	@commands.check_any(checks.is_permitted(), checks.is_guild_owner())
	async def remove_keyword(self, ctx, *, keyword: str):
		'''Remove a Twitch keyword(s) search being followed'''
		deleted = await ctx.bot.db.fetchval(
			"""
			DELETE FROM twitch_notifications.keywords
			WHERE channel_id = $1 AND keyword = $2
			RETURNING *
			""", 
			ctx.channel.id, keyword
		)
		if not deleted:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} This text channel isn't following that keyword")
		await ctx.embed_reply(f"Removed the Twitch keyword search, `{keyword}`, from this text channel")
	
	# R/PT60S
	@tasks.loop(seconds = 60)
	async def check_streams(self):
		headers = {"Accept": "application/vnd.twitchtv.v5+json"}  # Use Twitch API v5
		try:
			stream_ids = []
			# Games
			records = await self.bot.db.fetch("SELECT DISTINCT game_id FROM twitch_notifications.games")
			for record in records:
				game_id = record["game_id"]
				streams = await self.bot.twitch_client.get_streams(game_id = game_id, limit = 100)
				stream_ids += [stream["id"] for stream in streams]
				await self.process_streams(streams, "games", game = record)
				await asyncio.sleep(1)
			# Keywords
			records = await self.bot.db.fetch("SELECT DISTINCT keyword FROM twitch_notifications.keywords")
			url = "https://api.twitch.tv/kraken/search/streams"
			for record in records:
				keyword = record["keyword"]
				params = {"query": keyword, "client_id": self.bot.TWITCH_CLIENT_ID, "limit": 100}
				async with self.bot.aiohttp_session.get(url, params = params, headers = headers) as resp:
					keywords_data = await resp.json()
				streams = keywords_data.get("streams", [])
				stream_ids += [str(stream["_id"]) for stream in streams]
				await self.process_streams(streams, "keywords", match = keyword)
				await asyncio.sleep(1)
			# Streams
			records = await self.bot.db.fetch("SELECT DISTINCT user_id FROM twitch_notifications.channels")
			for records_chunk in zip_longest(*[iter(records)] * 100):
				streams = await self.bot.twitch_client.get_streams(channels = [record["user_id"] for record in records_chunk if record], limit = 100)
				stream_ids += [stream["id"] for stream in streams]
				await self.process_streams(streams, "streams")
				await asyncio.sleep(1)
			# Update streams notified
			records = await self.bot.db.fetch(
				"""
				SELECT stream_id, channel_id, message_id
				FROM twitch_notifications.notifications
				WHERE live = TRUE
				"""
			)
			for record in records:
				if record["stream_id"] not in stream_ids:
					text_channel = self.bot.get_channel(record["channel_id"])
					# TODO: Handle text channel not existing anymore
					try:
						message = await text_channel.fetch_message(record["message_id"])
					except discord.Forbidden:
						# TODO: Handle can't access text channel anymore
						continue
					except discord.NotFound:
						# Notification was deleted
						continue
					embed = message.embeds[0]
					embed.set_author(name = embed.author.name.replace("just went", "was"), 
										url = embed.author.url, icon_url = embed.author.icon_url)
					try:
						await message.edit(embed = embed)
					except discord.Forbidden:
						# Missing permission to edit?
						pass
					await self.bot.db.execute(
						"""
						UPDATE twitch_notifications.notifications
						SET live = FALSE
						WHERE stream_id = $1 AND channel_id = $2
						""", 
						record["stream_id"], record["channel_id"]
					)
				# TODO: Handle no longer being followed?
		except aiohttp.ClientConnectionError as e:
			self.bot.print(f"Twitch Task Connection Error: {type(e).__name__}: {e}")
			await asyncio.sleep(10)
		except asyncio.TimeoutError as e:
			self.bot.print(f"Twitch Task Timeout Error: {type(e).__name__}: {e}")
			await asyncio.sleep(10)
		except discord.DiscordServerError as e:
			self.bot.print(f"Twitch Task Discord Server Error: {e}")
			await asyncio.sleep(60)
		except Exception as e:
			print("Exception in Twitch Task", file = sys.stderr)
			traceback.print_exception(type(e), e, e.__traceback__, file = sys.stderr)
			errors_logger.error("Uncaught Twitch Task exception\n", exc_info = (type(e), e, e.__traceback__))
			await asyncio.sleep(60)
	
	@check_streams.before_loop
	async def before_check_streams(self):
		await self.initialize_database()
		await self.bot.wait_until_ready()
	
	@check_streams.after_loop
	async def after_check_streams(self):
		self.bot.print("Twitch task cancelled")
	
	async def process_streams(self, streams, type, game = None, match = None):
		# TODO: use textwrap
		for stream in streams:
			records = await self.bot.db.fetch(
				"""
				SELECT channel_id, message_id, live
				FROM twitch_notifications.notifications
				WHERE stream_id = $1
				""", 
				stream["id"]
			)
			# TODO: Handle streams notified already, but followed by new channel
			for record in records:
				if not record["live"]:
					text_channel = self.bot.get_channel(record["channel_id"])
					# TODO: Handle text channel not existing anymore
					try:
						message = await text_channel.fetch_message(record["message_id"])
					except discord.NotFound:
						# Notification was deleted
						continue
					embed = message.embeds[0]
					embed.set_author(name = embed.author.name.replace("was", "just went"), 
										url = embed.author.url, icon_url = embed.author.icon_url)
					await message.edit(embed = embed)
					await self.bot.db.execute(
						"""
						UPDATE twitch_notifications.notifications
						SET live = TRUE
						WHERE stream_id = $1 AND channel_id = $2
						""", 
						stream["id"], record["channel_id"]
					)
			if not records:
				# Construct embed
				if len(stream["title"]) <= 256:
					title = stream["title"]
				else:
					title = stream["title"][:253] + "..."
				if stream["game_name"]:
					description = f"{stream['user_name']} is playing {stream['game_name']}"
				else:
					description = discord.Embed.Empty
				embed = discord.Embed(title = title, url = f"https://www.twitch.tv/{stream['user_login']}", 
										description = description, 
										timestamp = dateutil.parser.parse(stream["started_at"]), 
										color = self.bot.twitch_color)
				embed.set_author(name = f"{stream['user_name']} just went live on Twitch", 
									icon_url = self.bot.twitch_icon_url)
				# TODO: Include profile image (logo), follower count, viewer count?
				# Get text channel IDs
				if game:
					records = await self.bot.db.fetch(
						"""
						SELECT channel_id FROM twitch_notifications.games
						WHERE game_id = $1
						""", 
						game["game_id"]
					)
				elif not match:
					records = await self.bot.db.fetch(
						"""
						SELECT channel_id FROM twitch_notifications.channels
						WHERE user_id = $1
						""", 
						stream["user_id"]
					)
				else:
					records = await self.bot.db.fetch(
						f"""
						SELECT channel_id FROM twitch_notifications.{type}
						WHERE {type[:-1]} = $1
						""", 
						match
					)
				channel_ids = [record["channel_id"] for record in records]
				for channel_id in channel_ids.copy():
					records = await self.bot.db.fetch(
						"""
						SELECT filter FROM twitch_notifications.filters
						WHERE channel_id = $1
						""", 
						channel_id
					)
					for record in records:
						# TODO: Make filter case-insensitive?
						if record["filter"] not in stream["title"]:
							channel_ids.remove(channel_id)
							break
				# Send notifications
				for channel_id in channel_ids:
					if not (text_channel := self.bot.get_channel(channel_id)):
						# TODO: Remove text channel data if now non-existent
						continue
					try:
						message = await text_channel.send(embed = embed)
					except discord.Forbidden:
						if not (permissions := text_channel.permissions_for(text_channel.guild.me)).embed_links and permissions.send_messages:
							if game:
								await self.bot.db.execute(
									"""
									DELETE FROM twitch_notifications.games
									WHERE channel_id = $1 AND game_id = $2
									""", 
									channel_id, game["game_id"]
								)
								await text_channel.send("I am unable to send the embed notification in this text channel for "
														f"a stream going live on Twitch matching the game, {game['game_name']}, "
														f"so this text channel is no longer following that game for Twitch streams.")
							elif not match:
								await self.bot.db.execute(
									"""
									DELETE FROM twitch_notifications.channels
									WHERE channel_id = $1 AND user_id = $2
									""", 
									channel_id, stream["user_id"]
								)
								await text_channel.send("I am unable to send the embed notification in this text channel for "
														f"{stream['user_name']} going live on Twitch, "
														"so this text channel is no longer following that Twitch channel.")
							else:
								await self.bot.db.execute(
									f"""
									DELETE FROM twitch_notifications.{type}
									WHERE channel_id = $1 AND {type[:-1]} = $2
									""", 
									channel_id, match
								)
								await text_channel.send("I am unable to send the embed notification in this text channel for "
														f"a stream going live on Twitch matching the {type[:-1]}, {match}, "
														f"so this text channel is no longer following that {type[:-1]} for Twitch streams.")
						else:
							# TODO: Handle no longer able to send messages in text channel
							print(f"Twitch Task: Missing permissions to send message in #{text_channel.name} in {text_channel.guild.name}")
						continue
					await self.bot.db.execute(
						"""
						INSERT INTO twitch_notifications.notifications (stream_id, channel_id, message_id, live)
						VALUES ($1, $2, $3, TRUE)
						""", 
						stream["id"], channel_id, message.id
					)

