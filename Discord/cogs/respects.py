
from discord.ext import commands

from utilities import checks

def setup(bot):
	bot.add_cog(Respects(bot))

class Respects:
	
	def __init__(self, bot):
		self.bot = bot
		self.bot.loop.create_task(self.initialize_database())
	
	async def initialize_database(self):
		await self.bot.connect_to_database()
		await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS respect")
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS respect.stats (
				stat	TEXT PRIMARY KEY, 
				value	BIGINT
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS respect.users (
				user_id		BIGINT PRIMARY KEY, 
				respects	BIGINT
			)
			"""
		)
		# TODO: guilds table
		await self.bot.db.execute(
			"""
			INSERT INTO respect.stats (stat, value)
			VALUES ('total', 0)
			ON CONFLICT (stat) DO NOTHING
			"""
		)
	
	def __local_check(self, ctx):
		return checks.not_forbidden_predicate(ctx)
	
	@commands.group(aliases = ["respect"], invoke_without_command = True)
	async def respects(self, ctx):
		'''
		Press F to Pay Respects
		https://knowyourmeme.com/memes/press-f-to-pay-respects
		'''
		await ctx.invoke(ctx.bot.get_command("help"), ctx.invoked_with)
	
	@respects.command()
	async def paid(self, ctx):
		'''
		Respects paid
		Record of respects paid by each user began on 2016-12-20
		'''
		user_respects = await ctx.bot.db.fetchval("SELECT respects FROM respect.users WHERE user_id = $1", 
													ctx.author.id)
		total_respects = await ctx.bot.db.fetchval("SELECT value FROM respect.stats WHERE stat = 'total'")
		await ctx.embed_reply(f"You have paid {user_respects:,} respects\n"
								f"A total of {total_respects:,} respects have been paid")
	
	@respects.command()
	async def pay(self, ctx):
		'''
		Pay Respects
		Can also be triggered with 'f' or 'F'
		'''
		total_respects = await ctx.bot.db.fetchval(
								"""
								UPDATE respect.stats
								SET value = value + 1
								WHERE stat = 'total'
								RETURNING value
								"""
							)
		user_respects = await ctx.bot.db.fetchval(
							"""
							INSERT INTO respect.users (user_id, respects)
							VALUES ($1, 1)
							ON CONFLICT (user_id) DO
							UPDATE SET respects = users.respects + 1
							RETURNING respects
							""", 
							ctx.author.id
						)
		suffix = ctx.bot.inflect_engine.ordinal(user_respects)[len(str(user_respects)):]
		await ctx.embed_reply(f"{ctx.author.mention} has paid their respects for the {user_respects:,}{suffix} time\n"
								f"Total respects paid so far: {total_respects:,}")

