
from discord.ext import commands

import difflib
import json

import clients
from utilities import checks

def setup(bot):
	'''
	def blob_wrapper(name, image_url, aliases = []):
		@commands.command(name = name, help = name.capitalize() + " blob", aliases = aliases)
		@checks.not_forbidden()
		async def blob_command(self, ctx):
			await ctx.embed_reply(None, image_url = image_url)
		return blob_command
	
	with open(clients.data_path + "/blobs.json", 'r') as blobs_file:
		blobs_data = json.load(blobs_file)
	
	for name, data in blobs_data.items():
		setattr(Blobs, name, blob_wrapper(name, data[0], data[1]))

	for name, command in inspect.getmembers(Blobs):
		if isinstance(command, commands.Command) and command.parent is None and name != "blobs":
			Blobs.blobs.add_command(command)
	'''
	bot.add_cog(Blobs(bot))

class Blobs:
	
	def __init__(self, bot):
		self.bot = bot
		clients.create_file("blobs", content = {})
		clients.create_file("blob_stats", content = {})
		with open(clients.data_path + "/blob_stats.json", 'r') as stats_file:
			self.stats = json.load(stats_file)
		with open(clients.data_path + "/blobs.json", 'r') as blobs_file:
			self.data = json.load(blobs_file)
		self.generate_reference()
		self.bot.loop.create_task(self.initialize_database())
	
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
				blob	TEXT REFERENCES blobs.blobs(blob)
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS blobs.stats (
				blob			TEXT REFERENCES blobs.blobs(blob), 
				user_id			BIGINT, 
				count			BIGINT, 
				PRIMARY KEY		(blob, user_id)
			)
			"""
		)
		# Migrate existing data
		for blob, data in self.data.items():
			await self.bot.db.execute(
				"""
				INSERT INTO blobs.blobs (blob, image)
				VALUES ($1, $2)
				ON CONFLICT (blob) DO UPDATE SET image = $2
				""", 
				blob, data[0]
			)
			for alias in data[1]:
				await self.bot.db.execute(
					"""
					INSERT INTO blobs.aliases (alias, blob)
					VALUES ($1, $2)
					ON CONFLICT (alias) DO UPDATE SET blob = $2
					""", 
					alias, blob
				)
		for blob, data in self.stats.items():
			name = await self.bot.db.fetchval("SELECT EXISTS (SELECT 1 FROM blobs.blobs WHERE blob = $1)", 
												blob)
			if not name:
				blob = await self.bot.db.fetchval("SELECT blob from blobs.aliases WHERE alias = $1", blob)
			for user_id, count in data.items():
				await self.bot.db.execute(
					"""
					INSERT INTO blobs.stats (blob, user_id, count)
					VALUES ($1, $2, $3)
					ON CONFLICT (blob, user_id) DO UPDATE SET count = stats.count + $3
					""", 
					blob, int(user_id), count
				)
	
	def generate_reference(self):
		self.reference = {}
		for name, data in self.data.items():
			self.reference[name] = data[0]
			for alias in data[1]:
				self.reference[alias] = data[0]

	@commands.group(aliases = ["blob"], invoke_without_command = True)
	@checks.not_forbidden()
	async def blobs(self, ctx, *, blob : str):
		'''Blob/Google Emoji'''
		'''
		subcommand = self.blobs.get_command(ctx.message.content.lstrip(ctx.prefix + ctx.invoked_with).replace(' ', ""))
		if subcommand: await subcommand.invoke(ctx)
		else: await ctx.embed_reply(":no_entry: Blob not found")
		'''
		close_match = difflib.get_close_matches(blob, self.reference.keys(), n = 1)
		if not close_match:
			return await ctx.embed_reply(":no_entry: Blob not found")
		blob = close_match[0]
		await ctx.embed_reply(title = blob, image_url = self.reference[blob])
		if blob not in self.stats: self.stats[blob] = {}
		self.stats[blob][str(ctx.author.id)] = self.stats[blob].get(str(ctx.author.id), 0) + 1
		with open(clients.data_path + "/blob_stats.json", 'w') as stats_file:
			json.dump(self.stats, stats_file, indent = 4)
	
	@blobs.command(aliases = ["edit"])
	@commands.is_owner()
	async def add(self, ctx, name : str, image_url : str, *aliases : str):
		'''Add or edit a blob'''
		self.data[name] = [image_url, aliases]
		self.generate_reference()
		with open(clients.data_path + "/blobs.json", 'w') as blobs_file:
			json.dump(self.data, blobs_file, indent = 4)
		await ctx.embed_reply("Blob added/edited")
	
	@blobs.command(aliases = ["details"])
	@commands.is_owner()
	async def info(self, ctx, name : str):
		'''Information about a blob'''
		await ctx.embed_reply(self.data[name][0], title = name, fields = (("Aliases", ", ".join(self.data[name][1]) or "None"),))
	
	@blobs.command()
	@checks.not_forbidden()
	async def list(self, ctx):
		'''List blobs'''
		await ctx.embed_reply(", ".join(sorted(self.data.keys())))
	
	@blobs.command(aliases = ["delete"])
	@commands.is_owner()
	async def remove(self, ctx, name : str):
		'''Remove a blob'''
		del self.data[name]
		self.generate_reference()
		with open(clients.data_path + "/blobs.json", 'w') as blobs_file:
			json.dump(self.data, blobs_file, indent = 4)
		await ctx.embed_reply("Blob removed")
	
	@blobs.command(name = "stats")
	@checks.not_forbidden()
	async def blobs_stats(self, ctx, *, blob : str):
		'''Blob emoji stats'''
		close_match = difflib.get_close_matches(blob, self.reference.keys(), n = 1)
		# subcommand = self.blobs.get_command(blob.replace(' ', ""))
		if not close_match:
			return await ctx.embed_reply(":no_entry: Blob not found")
		blob = close_match[0]
		if blob not in self.stats:
			return await ctx.embed_reply("Personal: 0\nTotal: 0")
		personal = self.stats[blob].get(str(ctx.author.id), 0)
		total = sum(self.stats[blob].values())
		await ctx.embed_reply(f"Personal: {personal}\nTotal: {total}")
	
	@blobs.command()
	@checks.not_forbidden()
	async def top(self, ctx):
		'''Top blob emoji'''
		personal = sorted(self.stats.items(), key = lambda subcommand: subcommand[1].get(str(ctx.author.id), 0), reverse = True)
		top_personal = '\n'.join(f"{i + 1}. {personal[i][0]} ({personal[i][1].get(str(ctx.author.id), 0)})" for i in range(min(5, len(personal))))
		total = sorted(self.stats.items(), key = lambda subcommand: sum(subcommand[1].values()), reverse = True)
		top_total = '\n'.join(f"{i + 1}. {total[i][0]} ({sum(total[i][1].values())})" for i in range(min(5, len(total))))
		await ctx.embed_reply(fields = (("Personal", top_personal), ("Total", top_total)))

