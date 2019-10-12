
import discord
from discord.ext import commands, tasks

import aiohttp
import asyncio
import dateutil.parser
import logging
import sys
import traceback

from utilities import checks

errors_logger = logging.getLogger("errors")

def setup(bot):
	bot.add_cog(Twitch(bot))

class Twitch(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.check_twitch_streams.start()
	
	def cog_unload(self):
		self.check_twitch_streams.cancel()
	
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
				game			TEXT, 
				PRIMARY KEY		(channel_id, game)
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
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	@checks.is_permitted()
	async def twitch(self, ctx):
		'''Twitch'''
		await ctx.send_help(ctx.command)
	
	@twitch.group(name = "add", invoke_without_command = True, case_insensitive = True)
	@checks.is_permitted()
	async def twitch_add(self, ctx):
		'''Add Twitch games, keywords, or channels to follow'''
		await ctx.send_help(ctx.command)
	
	@twitch_add.command(name = "filter")
	@checks.is_permitted()
	async def twitch_add_filter(self, ctx, *, string : str):
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
			return await ctx.embed_reply(f"This text channel already has the filter, `{string}`")
		await ctx.embed_reply(f"Added the filter, `{string}`, to this text channel\n"
								"I will now filter all streams for this string in the title")
	
	@twitch_add.command(name = "game")
	@checks.is_permitted()
	async def twitch_add_game(self, ctx, *, game : str):
		'''Add a Twitch game to follow'''
		# TODO: Add documentation on 100 limit
		inserted = await ctx.bot.db.fetchrow(
			"""
			INSERT INTO twitch_notifications.games (channel_id, game)
			VALUES ($1, $2)
			ON CONFLICT DO NOTHING
			RETURNING *
			""", 
			ctx.channel.id, game
		)
		if not inserted:
			return await ctx.embed_reply(f"This text channel is already following the game, `{game}`")
		await ctx.embed_reply(f"Added the game, [`{game}`](https://www.twitch.tv/directory/game/{game}), to this text channel\n"
								"I will now announce here when Twitch streams playing this game go live")
	
	@twitch_add.command(name = "keyword", aliases = ["query", "search"])
	@checks.is_permitted()
	async def twitch_add_keyword(self, ctx, *, keyword : str):
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
	
	@twitch_add.command(name = "channel", aliases = ["stream"])
	@checks.is_permitted()
	async def twitch_add_channel(self, ctx, username : str):
		'''Add a Twitch channel to follow'''
		url = "https://api.twitch.tv/kraken/users"
		headers = {"Accept": "application/vnd.twitchtv.v5+json"}
		params = {"login": username, "client_id": ctx.bot.TWITCH_CLIENT_ID}
		async with ctx.bot.aiohttp_session.get(url, headers = headers, params = params) as resp:
			users_data = await resp.json()
		inserted = await ctx.bot.db.fetchrow(
			"""
			INSERT INTO twitch_notifications.channels (channel_id, user_name, user_id)
			VALUES ($1, $2, $3)
			ON CONFLICT DO NOTHING
			RETURNING *
			""", 
			ctx.channel.id, username, users_data["users"][0]["_id"]
		)
		if not inserted:
			return await ctx.embed_reply(f"This text channel is already following the channel, `{channel}`")
		await ctx.embed_reply(f"Added the Twitch channel, [`{username}`](https://www.twitch.tv/{username}), to this text channel\n"
								"I will now announce here when this Twitch channel goes live")
	
	@twitch.group(name = "remove", aliases = ["delete"], 
					invoke_without_command = True, case_insensitive = True)
	@checks.is_permitted()
	async def twitch_remove(self, ctx):
		'''Remove Twitch games, keywords, or channels being followed'''
		await ctx.send_help(ctx.command)
	
	@twitch_remove.command(name = "filter")
	@checks.is_permitted()
	async def twitch_remove_filter(self, ctx, *, string : str):
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
			return await ctx.embed_reply(":no_entry: This text channel doesn't have that filter")
		await ctx.embed_reply(f"Removed the filter, `{string}`, from this text channel")
	
	@twitch_remove.command(name = "game")
	@checks.is_permitted()
	async def twitch_remove_game(self, ctx, *, game : str):
		'''Remove a Twitch game being followed'''
		deleted = await ctx.bot.db.fetchval(
			"""
			DELETE FROM twitch_notifications.games
			WHERE channel_id = $1 AND game = $2
			RETURNING *
			""", 
			ctx.channel.id, game
		)
		if not deleted:
			return await ctx.embed_reply(":no_entry: This text channel isn't following that game")
		await ctx.embed_reply(f"Removed the game, [`{game}`](https://www.twitch.tv/directory/game/{game}), from this text channel")
	
	@twitch_remove.command(name = "keyword", aliases = ["query", "search"])
	@checks.is_permitted()
	async def twitch_remove_keyword(self, ctx, *, keyword : str):
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
			return await ctx.embed_reply(":no_entry: This text channel isn't following that keyword")
		await ctx.embed_reply(f"Removed the Twitch keyword search, `{keyword}`, from this text channel")
	
	@twitch_remove.command(name = "channel", aliases = ["stream"])
	@checks.is_permitted()
	async def twitch_remove_channel(self, ctx, username : str):
		'''Remove a Twitch channel being followed'''
		url = "https://api.twitch.tv/kraken/users"
		headers = {"Accept": "application/vnd.twitchtv.v5+json"}
		params = {"login": username, "client_id": ctx.bot.TWITCH_CLIENT_ID}
		async with ctx.bot.aiohttp_session.get(url, headers = headers, params = params) as resp:
			users_data = await resp.json()
		deleted = await ctx.bot.db.fetchval(
			"""
			DELETE FROM twitch_notifications.channels
			WHERE channel_id = $1 AND user_id = $2
			RETURNING *
			""", 
			ctx.channel.id, users_data["users"][0]["_id"]
		)
		if not deleted:
			return await ctx.embed_reply(":no_entry: This text channel isn't following that Twitch channel")
		await ctx.embed_reply(f"Removed the Twitch channel, [`{username}`](https://www.twitch.tv/{username}), from this text channel")
	
	@twitch.command(name = "filters")
	@checks.not_forbidden()
	async def twitch_filters(self, ctx):
		'''Show strings Twitch stream titles are being filtered by in this text channel'''
		records = await ctx.bot.db.fetch(
			"""
			SELECT filter FROM twitch_notifications.filters
			WHERE channel_id = $1
			""", 
			ctx.channel.id
		)
		await ctx.embed_reply('\n'.join(record["filter"] for record in records), 
								title = "Twitch stream title filters in this text channel")
	
	@twitch.command(name = "games")
	@checks.not_forbidden()
	async def twitch_games(self, ctx):
		'''Show Twitch games being followed in this text channel'''
		records = await ctx.bot.db.fetch(
			"""
			SELECT game FROM twitch_notifications.games
			WHERE channel_id = $1
			""", 
			ctx.channel.id
		)
		await ctx.embed_reply('\n'.join(record["game"] for record in records), 
								title = "Twitch games being followed in this text channel")
	
	@twitch.command(name = "keywords", aliases = ["queries", "searches"])
	@checks.not_forbidden()
	async def twitch_keywords(self, ctx):
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
	
	@twitch.command(name = "channels", aliases = ["streams"])
	@checks.not_forbidden()
	async def twitch_channels(self, ctx):
		'''Show Twitch channels being followed in this text channel'''
		records = await ctx.bot.db.fetch(
			"""
			SELECT user_name, user_id FROM twitch_notifications.channels
			WHERE channel_id = $1
			""", 
			ctx.channel.id
		)
		channels = []
		for record in records:
			url = f"https://api.twitch.tv/kraken/users/{record['user_id']}"
			headers = {"Accept": "application/vnd.twitchtv.v5+json"}
			params = {"client_id": self.bot.TWITCH_CLIENT_ID}
			async with self.bot.aiohttp_session.get(url, headers = headers, params = params) as resp:
				user_data = await resp.json()
			channels.append(user_data["display_name"])
			# TODO: Add note about name change to response
			#       user_data["name"] != record["user_name"]
		await ctx.embed_reply('\n'.join(f"[{channel}](https://www.twitch.tv/{channel})" for channel in channels), 
								title = "Twitch channels being followed in this text channel")
	
	@tasks.loop(seconds = 20)
	async def check_twitch_streams(self):
		headers = {"Accept": "application/vnd.twitchtv.v5+json"}  # Use Twitch API v5
		try:
			stream_ids = []
			# Games
			records = await self.bot.db.fetch("SELECT DISTINCT game FROM twitch_notifications.games")
			url = "https://api.twitch.tv/kraken/streams"
			for record in records:
				game = record["game"]
				params = {"game": game, "client_id": self.bot.TWITCH_CLIENT_ID, "limit": 100}
				async with self.bot.aiohttp_session.get(url, params = params, headers = headers) as resp:
					if resp.status in (421, 503):
						continue
					games_data = await resp.json()
				streams = games_data.get("streams", [])
				stream_ids += [str(stream["_id"]) for stream in streams]
				await self.process_twitch_streams(streams, "games", match = game)
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
				await self.process_twitch_streams(streams, "keywords", match = keyword)
				await asyncio.sleep(1)
			# Streams
			streams_data = {}
			records = await self.bot.db.fetch("SELECT DISTINCT user_id FROM twitch_notifications.channels")
			url = "https://api.twitch.tv/kraken/streams"
			params = {"channel": ','.join(record["user_id"] for record in records), 
						"client_id": self.bot.TWITCH_CLIENT_ID, "limit": 100}
			async with self.bot.aiohttp_session.get(url, params = params, headers = headers) as resp:
				if resp.status not in (503, 504):
					streams_data = await resp.json()
				# TODO: Handle >100 streams
			streams = streams_data.get("streams", [])
			stream_ids += [str(stream["_id"]) for stream in streams]
			await self.process_twitch_streams(streams, "streams")
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
			print(f"{self.bot.console_message_prefix}Twitch Task Connection Error: {type(e).__name__}: {e}")
			await asyncio.sleep(10)
		except asyncio.CancelledError:
			raise
		except Exception as e:
			print("Exception in Twitch Task", file = sys.stderr)
			traceback.print_exception(type(e), e, e.__traceback__, file = sys.stderr)
			errors_logger.error("Uncaught Twitch Task exception\n", exc_info = (type(e), e, e.__traceback__))
			await asyncio.sleep(60)
	
	@check_twitch_streams.before_loop
	async def before_check_twitch_streams(self):
		await self.initialize_database()
		await self.bot.wait_until_ready()
	
	@check_twitch_streams.after_loop
	async def after_check_twitch_streams(self):
		print(f"{self.bot.console_message_prefix}Twitch task cancelled")
	
	async def process_twitch_streams(self, streams, type, match = None):
		# TODO: use textwrap
		for stream in streams:
			records = await self.bot.db.fetch(
				"""
				SELECT channel_id, message_id, live
				FROM twitch_notifications.notifications
				WHERE stream_id = $1
				""", 
				str(stream["_id"])
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
						str(stream["_id"]), record["channel_id"]
					)
			if not records:
				# Construct embed
				if len(stream["channel"]["status"]) <= 256:
					title = stream["channel"]["status"]
				else:
					title = stream["channel"]["status"][:253] + "..."
				if stream["channel"]["game"]:
					description = f"{stream['channel']['display_name']} is playing {stream['game']}"
				else:
					description = discord.Embed.Empty
				embed = discord.Embed(title = title, url = stream["channel"]["url"], 
										description = description, 
										timestamp = dateutil.parser.parse(stream["created_at"]).replace(tzinfo = None), 
										color = self.bot.twitch_color)
				embed.set_author(name = f"{stream['channel']['display_name']} just went live on Twitch", 
									icon_url = self.bot.twitch_icon_url)
				if stream["channel"]["logo"]:
					embed.set_thumbnail(url = stream["channel"]["logo"])
				embed.add_field(name = "Followers", value = f"{stream['channel']['followers']:,}")
				embed.add_field(name = "Views", value = f"{stream['channel']['views']:,}")
				# Get text channel IDs
				if not match:
					records = await self.bot.db.fetch(
						"""
						SELECT channel_id FROM twitch_notifications.channels
						WHERE user_id = $1
						""", 
						str(stream["channel"]["_id"])
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
						if record["filter"] not in stream["channel"]["status"]:
							channel_ids.remove(channel_id)
							break
				# Send notifications
				for channel_id in channel_ids:
					text_channel = self.bot.get_channel(channel_id)
					if not text_channel:
						# TODO: Remove text channel data if now non-existent
						continue
					message = await text_channel.send(embed = embed)
					await self.bot.db.execute(
						"""
						INSERT INTO twitch_notifications.notifications (stream_id, channel_id, message_id, live)
						VALUES ($1, $2, $3, TRUE)
						""", 
						str(stream["_id"]), channel_id, message.id
					)

