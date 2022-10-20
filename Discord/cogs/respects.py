
import discord
from discord import app_commands
from discord.ext import commands

import io
import math

## import astropy.modeling
import matplotlib
import numpy
## import scipy

from utilities import checks

async def setup(bot):
	await bot.add_cog(Respects(bot))

class Respects(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
	
	async def cog_load(self):
		await self.bot.connect_to_database()
		await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS respects")
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS respects.stats (
				stat	TEXT PRIMARY KEY, 
				value	BIGINT
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS respects.users (
				user_id		BIGINT PRIMARY KEY, 
				respects	BIGINT
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS respects.guilds (
				guild_id	BIGINT PRIMARY KEY, 
				respects	BIGINT
			)
			"""
		)
		await self.bot.db.execute(
			"""
			INSERT INTO respects.stats (stat, value)
			VALUES ('total', 0)
			ON CONFLICT (stat) DO NOTHING
			"""
		)
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.group(
		aliases = ["respect"],
		case_insensitive = True, invoke_without_command = True
	)
	async def respects(self, ctx):
		"""
		Press F to Pay Respects
		https://knowyourmeme.com/memes/press-f-to-pay-respects
		"""
		await ctx.send_help(ctx.command)
	
	@respects.command()
	async def paid(self, ctx):
		"""
		Respects paid
		Record of respects paid by each user began on 2016-12-20
		Record of respects paid by each server began on 2018-09-04
		"""
		user_respects = await ctx.bot.db.fetchval(
			"SELECT respects FROM respects.users WHERE user_id = $1",
			ctx.author.id
		) or 0
		if ctx.guild:
			guild_respects = await ctx.bot.db.fetchval(
				"SELECT respects FROM respects.guilds WHERE guild_id = $1",
				ctx.guild.id
			) or 0
		total_respects = await ctx.bot.db.fetchval(
			"SELECT value FROM respects.stats WHERE stat = 'total'"
		)
		response = f"You have paid {user_respects:,} respects\n"
		if ctx.guild:
			response += f"This server has paid {guild_respects:,} respects\n"
		response += f"A total of {total_respects:,} respects have been paid"
		await ctx.embed_reply(response)
	
	@respects.command()
	async def pay(self, ctx):
		'''
		Pay Respects
		Can also be triggered with 'f' or 'F'
		'''
		total_respects = await ctx.bot.db.fetchval(
			"""
			UPDATE respects.stats
			SET value = value + 1
			WHERE stat = 'total'
			RETURNING value
			"""
		)
		if ctx.guild:
			guild_respects = await ctx.bot.db.fetchval(
				"""
				INSERT INTO respects.guilds (guild_id, respects)
				VALUES ($1, 1)
				ON CONFLICT (guild_id) DO
				UPDATE SET respects = guilds.respects + 1
				RETURNING respects
				""", 
				ctx.guild.id
			)
		user_respects = await ctx.bot.db.fetchval(
			"""
			INSERT INTO respects.users (user_id, respects)
			VALUES ($1, 1)
			ON CONFLICT (user_id) DO
			UPDATE SET respects = users.respects + 1
			RETURNING respects
			""", 
			ctx.author.id
		)
		suffix = ctx.bot.inflect_engine.ordinal(user_respects)[len(str(user_respects)):]
		response = f"{ctx.author.mention} has paid their respects for the {user_respects:,}{suffix} time\n"
		if ctx.guild:
			response += f"Total respects paid in this server: {guild_respects:,}\n"
		response += f"Total respects paid so far: {total_respects:,}"
		await ctx.embed_reply(response)
	
	@app_commands.command(name = 'f')
	async def slash_f(self, interaction):
		"""Pay Respects"""
		ctx = await interaction.client.get_context(interaction)
		await self.pay(ctx)
	
	@respects.command(aliases = ["statistics"])
	async def stats(self, ctx):
		'''Statistics'''
		total_respects = await ctx.bot.db.fetchval("SELECT value FROM respects.stats WHERE stat = 'total'")
		respects_paid = []
		async with ctx.bot.database_connection_pool.acquire() as connection:
			async with connection.transaction():
				# Postgres requires non-scrollable cursors to be created
				# and used in a transaction.
				async for record in connection.cursor("SELECT * FROM respects.users"):
					respects_paid.append(record["respects"])
		# TODO: Optimize
		# TODO: Fit curve
		## n, bins, _ = matplotlib.pyplot.hist(respects_paid, log = True, 
		figure = matplotlib.figure.Figure()
		axes = figure.add_subplot(xscale = "log", xlabel = "Respects Paid", ylabel = "People")
		last_power_of_10 = math.ceil(numpy.log10(max(respects_paid)))
		bins = (10 ** numpy.arange(last_power_of_10))[:, numpy.newaxis] * numpy.arange(1, 10)
		axes.hist(respects_paid, bins = bins.flatten(), log = True, ec = "black")
		## bin_centers = bins[:-1] + numpy.diff(bins) / 2
		## def func(x, a, b, c):
		##	return a * numpy.exp(-b * x) + c
		## popt, _ = scipy.optimize.curve_fit(func, bin_centers[1:], n[1:], p0 = (1000, 1, 1), maxfev = 100000)
		## t_init = astropy.modeling.models.Gaussian1D()
		## fit_t = astropy.modeling.fitting.LevMarLSQFitter()
		## t = fit_t(t_init, bin_centers, n)
		## x_interval_for_fit = numpy.linspace(bins[0], bins[-1], 10000)
		## matplotlib.pyplot.plot(x_interval_for_fit, func(x_interval_for_fit, *popt), color = "red")
		## axes.set_ylim(0.8)
		formatter = matplotlib.ticker.ScalarFormatter()
		formatter.set_scientific(False)
		axes.get_xaxis().set_major_formatter(formatter)
		axes.get_yaxis().set_major_formatter(formatter)
		# Remove minor ticks < 1
		axes.set_xticks([tick for tick in axes.get_xticks(minor = True) if tick >= 1], minor = True)
		axes.set_yticks([tick for tick in axes.get_yticks(minor = True) if tick >= 1], minor = True)
		axes.autoscale(enable = True)
		buffer = io.BytesIO()
		figure.savefig(buffer, format = "PNG")
		buffer.seek(0)
		await ctx.embed_reply(fields = (("Total respects paid", f"{total_respects:,}"), 
										("People who paid respects", f"{len(respects_paid):,}")),
								image_url = "attachment://respects.png", 
								file = discord.File(buffer, filename = "respects.png"))
	
	@respects.command(aliases = ["most"])
	async def top(self, ctx, number: int = 10):
		'''Top respects paid'''
		if number > 10:
			number = 10
		fields = []
		async with ctx.bot.database_connection_pool.acquire() as connection:
			async with connection.transaction():
				# Postgres requires non-scrollable cursors to be created
				# and used in a transaction.
				async for record in connection.cursor("SELECT * FROM respects.users ORDER BY respects DESC LIMIT $1", number):
					user = ctx.bot.get_user(record["user_id"])
					if not user:
						user = await ctx.bot.fetch_user(record["user_id"])
					fields.append((str(user), f"{record['respects']:,}"))
		await ctx.embed_reply(title = "Top Respects Paid", fields = fields)

