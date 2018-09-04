
from discord.ext import commands

from utilities import checks

def setup(bot):
	bot.add_cog(Respects())

class Respects:
	
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
	async def pay(self, ctx):
		'''
		Pay Respects
		Can also be triggered with 'f' or 'F'
		Record of respects paid by each user began on 2016-12-20
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

