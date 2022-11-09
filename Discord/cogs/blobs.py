
import discord
from discord.ext import commands, menus

import difflib
import textwrap

from utilities import checks
from utilities.menu import Menu

async def setup(bot):
	await bot.add_cog(Blobs(bot))

class Blobs(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		self.menus = []
	
	async def cog_load(self):
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
		
	def cog_unload(self):
		for menu in self.menus:
			menu.stop()
	
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
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Blob not found")
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
		if not (image_url := await ctx.bot.db.fetchval("SELECT image FROM blobs.blobs WHERE blob = $1", name)):
			if not (name := await ctx.bot.db.fetchval("SELECT blob FROM blobs.aliases WHERE alias = $1", name)):
				return await ctx.embed_reply(f"{ctx.bot.error_emoji} Blob not found")
			image_url = await ctx.bot.db.fetchval("SELECT image FROM blobs.blobs WHERE blob = $1", name)
		records = await ctx.bot.db.fetch("SELECT alias FROM blobs.aliases WHERE blob = $1", name)
		aliases = [record["alias"] for record in records]
		await ctx.embed_reply(image_url, title = name, fields = (("Aliases", ", ".join(aliases) or "None"),))
	
	@blobs.command(name = "list")
	@checks.not_forbidden()
	async def list_command(self, ctx, offset: int = 0):
		'''List blobs'''
		records = await ctx.bot.db.fetch("SELECT blob FROM blobs.blobs ORDER BY blob")
		blob_names = [record["blob"] for record in records]
		await ctx.embed_reply(textwrap.shorten(", ".join(blob_names[offset:]), 
												width = ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT, 
												placeholder = " ..."))
	
	@blobs.command(name = "menu", aliases = ['m', "menus", 'r', "reaction", "reactions"])
	@checks.not_forbidden()
	async def menu_command(self, ctx, number: int = 1):
		'''Blobs menu'''
		records = await ctx.bot.db.fetch("SELECT * FROM blobs.blobs ORDER BY blob")
		menu = BlobsMenu(records, number)
		self.menus.append(menu)
		await menu.start(ctx, wait = True)
		self.menus.remove(menu)
	
	@blobs.command()
	@checks.not_forbidden()
	async def random(self, ctx):
		'''Random blob emoji'''
		# Note: random blob command invokes this command
		record = await ctx.bot.db.fetchrow("SELECT * FROM blobs.blobs TABLESAMPLE BERNOULLI (1) LIMIT 1")
		await ctx.embed_reply(title = record["blob"], image_url = record["image"])
	
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
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Blob not found")
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

class BlobsSource(menus.ListPageSource):
	
	def __init__(self, records):
		super().__init__(records, per_page = 1)
	
	async def format_page(self, menu, record):
		embed = discord.Embed(title = record["blob"], color = menu.bot.bot_color)
		embed.set_author(name = menu.ctx.author.display_name, icon_url = menu.ctx.author.avatar.url)
		embed.set_image(url = record["image"])
		embed.set_footer(text = f"Blob {menu.current_page + 1} of {self.get_max_pages()}")
		return {"content": f"In response to: `{menu.ctx.message.clean_content}`", "embed": embed}

class BlobsMenu(Menu, menus.MenuPages):
	
	def __init__(self, records, number):
		super().__init__(BlobsSource(records), timeout = None, clear_reactions_after = True, check_embeds = True)
		self.initial_offset = number - 1
	
	async def send_initial_message(self, ctx, channel):
		page = await self.source.get_page(self.initial_offset)
		self.current_page = self.initial_offset
		kwargs = await self.source.format_page(self, page)
		message = await channel.send(**kwargs)
		await ctx.bot.attempt_delete_message(ctx.message)
		return message

