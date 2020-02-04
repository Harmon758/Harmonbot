
from discord.ext import commands

import difflib
import textwrap

from utilities import checks

def setup(bot):
	bot.add_cog(Blobs(bot))

class Blobs(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.bot.loop.create_task(self.initialize_database(), name = "Initialize database")
	
	async def initialize_database(self):
		await self.bot.connect_to_database()
		await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS blobs")
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS blobs.blobs (
				blob	TEXT PRIMARY KEY, 
				image	TEXT
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS blobs.aliases (
				alias	TEXT PRIMARY KEY, 
				blob	TEXT REFERENCES blobs.blobs(blob) ON DELETE CASCADE
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS blobs.stats (
				blob			TEXT REFERENCES blobs.blobs(blob) ON DELETE CASCADE, 
				user_id			BIGINT, 
				count			BIGINT, 
				PRIMARY KEY		(blob, user_id)
			)
			"""
		)
	
	@commands.group(aliases = ["blob"], invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def blobs(self, ctx, *, blob : str):
		'''Blob/Google Emoji'''
		records = await ctx.bot.db.fetch(
			"""
			SELECT blob, NULL as unaliased, image
			FROM blobs.blobs
			UNION
			SELECT blobs.aliases.alias, blobs.blobs.blob, blobs.blobs.image
			FROM blobs.aliases
			INNER JOIN blobs.blobs
			ON blobs.aliases.blob = blobs.blobs.blob
			"""
		)
		blob_data = {}
		for record in records:
			blob_data[record["blob"]] = {"image": record["image"], "unaliased": record["unaliased"]}
		close_match = difflib.get_close_matches(blob, blob_data, n = 1)
		if not close_match:
			return await ctx.embed_reply(":no_entry: Blob not found")
		blob = close_match[0]
		await ctx.embed_reply(title = blob, image_url = blob_data[blob]["image"])
		await ctx.bot.db.execute(
			"""
			INSERT INTO blobs.stats (blob, user_id, count)
			VALUES ($1, $2, 1)
			ON CONFLICT (blob, user_id) DO
			UPDATE SET count = stats.count + 1
			""", 
			blob_data[blob]["unaliased"] or blob, ctx.author.id
		)
	
	@blobs.command(aliases = ["edit"])
	@commands.is_owner()
	async def add(self, ctx, name : str, image_url : str, *aliases : str):
		'''Add or edit a blob'''
		await ctx.bot.db.execute(
			"""
			INSERT INTO blobs.blobs (blob, image)
			VALUES ($1, $2)
			ON CONFLICT (blob) DO
			UPDATE SET image = $2
			""", 
			name, image_url
		)
		await ctx.bot.db.execute("DELETE FROM blobs.aliases WHERE blob = $1", name)
		for alias in aliases:
			inserted = await ctx.bot.db.fetchrow(
				"""
				INSERT INTO blobs.aliases (alias, blob)
				VALUES ($1, $2)
				ON CONFLICT DO NOTHING
				RETURNING *
				""", 
				alias, name
			)
			if not inserted:
				await ctx.embed_reply(f"Failed to add already existing alias: {alias}")
		await ctx.embed_reply("Blob added/edited")
	
	@blobs.command(aliases = ["details"])
	@commands.is_owner()
	async def info(self, ctx, name : str):
		'''Information about a blob'''
		image_url = await ctx.bot.db.fetchval("SELECT image FROM blobs.blobs WHERE blob = $1", name)
		if not image_url:
			name = await ctx.bot.db.fetchval("SELECT blob FROM blobs.aliases WHERE alias = $1", name)
			if not name:
				return await ctx.embed_reply(f":no_entry: Blob not found")
			image_url = await ctx.bot.db.fetchval("SELECT image FROM blobs.blobs WHERE blob = $1", name)
		records = await ctx.bot.db.fetch("SELECT alias FROM blobs.aliases WHERE blob = $1", name)
		aliases = [record["alias"] for record in records]
		await ctx.embed_reply(image_url, title = name, fields = (("Aliases", ", ".join(aliases) or "None"),))
	
	@blobs.command(name = "list")
	@checks.not_forbidden()
	async def list_command(self, ctx, offset: int = 0):
		'''List blobs'''
		records = await ctx.bot.db.fetch("SELECT blob FROM blobs.blobs")
		blob_names = [record["blob"] for record in records]
		await ctx.embed_reply(textwrap.shorten(", ".join(sorted(blob_names)[offset:]), 
												width = ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT, 
												placeholder = " ..."))
	
	@blobs.command(aliases = ["delete"])
	@commands.is_owner()
	async def remove(self, ctx, name : str):
		'''Remove a blob'''
		await ctx.bot.db.execute("DELETE FROM blobs.blobs WHERE blob = $1", name)
		await ctx.embed_reply("Blob removed")
	
	@blobs.command()
	@checks.not_forbidden()
	async def stats(self, ctx, *, blob : str):
		'''Blob emoji stats'''
		records = await ctx.bot.db.fetch("SELECT blob FROM blobs.blobs UNION SELECT alias FROM blobs.aliases")
		blob_names = [record["blob"] for record in records]
		close_match = difflib.get_close_matches(blob, blob_names, n = 1)
		if not close_match:
			return await ctx.embed_reply(":no_entry: Blob not found")
		blob = close_match[0]
		records = await ctx.bot.db.fetch("SELECT user_id, count FROM blobs.stats WHERE blob = $1", blob)
		if not records:
			blob = await ctx.bot.db.fetchval("SELECT blob FROM blobs.aliases WHERE alias = $1", blob)
			records = await ctx.bot.db.fetch("SELECT user_id, count FROM blobs.stats WHERE blob = $1", blob)
		personal = 0
		total = 0
		for record in records:
			if record["user_id"] == ctx.author.id:
				personal = record["count"]
			total += record["count"]
		await ctx.embed_reply(f"Personal: {personal}\nTotal: {total}")
	
	@blobs.command()
	@checks.not_forbidden()
	async def top(self, ctx):
		'''Top blob emoji'''
		records = await ctx.bot.db.fetch(
			"""
			SELECT blob, count
			FROM blobs.stats
			WHERE user_id = $1
			ORDER BY count
			DESC LIMIT 5
			""", 
			ctx.author.id
		)
		personal = [f"{count}. {record['blob']} ({record['count']})" for count, record in enumerate(records, start = 1)]
		records = await ctx.bot.db.fetch(
			"""
			SELECT blob, SUM(count) as count
			FROM blobs.stats
			GROUP BY blob
			ORDER BY SUM(count)
			DESC LIMIT 5
			"""
		)
		total = [f"{count}. {record['blob']} ({record['count']})" for count, record in enumerate(records, start = 1)]
		await ctx.embed_reply(fields = (("Personal", '\n'.join(personal)), ("Total", '\n'.join(total))))

