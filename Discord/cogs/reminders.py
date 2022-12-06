
import discord
from discord.ext import commands, menus, tasks

import asyncio
import datetime
from typing import Optional

from parsedatetime import Calendar, VERSION_CONTEXT_STYLE

from utilities import checks
from utilities.paginators import ButtonPaginator

async def setup(bot):
	await bot.add_cog(Reminders(bot))

class Reminders(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		
		self.calendar = Calendar(version = VERSION_CONTEXT_STYLE)
		# Add mo as valid abbreviation for month
		self.calendar.ptc.units["months"].append("mo")
		
		self.current_timer = None
		self.new_reminder = asyncio.Event()
		self.restarting_timer = False
		self.timer.start().set_name("Reminders")
	
	def cog_unload(self):
		self.timer.cancel()
	
	async def initialize_database(self):
		await self.bot.connect_to_database()
		await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS reminders")
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS reminders.reminders (
				id				INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY, 
				user_id			BIGINT, 
				channel_id		BIGINT, 
				message_id		BIGINT, 
				created_time	TIMESTAMPTZ DEFAULT NOW(), 
				remind_time		TIMESTAMPTZ, 
				reminder		TEXT, 
				reminded		BOOL DEFAULT FALSE, 
				cancelled 		BOOL DEFAULT FALSE, 
				failed			BOOL DEFAULT FALSE
			)
			"""
		)
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	# TODO: Allow setting timezone (+ for time command as well)
	
	@commands.group(
		name = "reminder",
		aliases = ["remind", "reminders", "timer", "timers"],
		case_insensitive = True, invoke_without_command = True
	)
	async def reminder_command(
		self, ctx, *, reminder: Optional[commands.clean_content]
	):
		"""
		See and set reminders
		Times are in UTC
		"""
		# Invoke list subcommand for reminders and timers invocations
		if ctx.invoked_with in ("reminders", "timers"):
			offset = 0
			count = 10
			try:
				inputs = reminder.split()
				offset = int(inputs[0])
				count = int(inputs[1])
			except (AttributeError, IndexError, ValueError):
				pass
			return await ctx.invoke(self.list_reminders, offset, count)
		elif not reminder:
			raise commands.BadArgument("Time not specified")
		# Clean reminder input
		for prefix in ("me about ", "me to ", "me "):
			if reminder.startswith(prefix):
				reminder = reminder[len(prefix):]
		reminder = reminder.replace("from now", "")
		# Parse reminder
		now = datetime.datetime.now(datetime.timezone.utc)
		if not (matches := self.calendar.nlp(reminder, sourceTime = now)):
			raise commands.BadArgument("Time not specified")
		parsed_datetime, context, start_pos, end_pos, matched_text = matches[0]
		if not context.hasTime:
			parsed_datetime = parsed_datetime.replace(
				hour = now.hour, minute = now.minute,
				second = now.second, microsecond = now.microsecond
			)
		parsed_datetime = parsed_datetime.replace(tzinfo = datetime.timezone.utc)
		if parsed_datetime < now:
			raise commands.BadArgument("Time is in the past")
		# Respond
		reminder = reminder[:start_pos] + reminder[end_pos + 1:]
		reminder = reminder.strip()
		response = await ctx.embed_reply(
			fields = (("Reminder", reminder or ctx.bot.ZWS),),
			footer_text = f"Set for {parsed_datetime.isoformat(timespec = 'seconds').replace('+00:00', 'Z')}",
			timestamp = parsed_datetime
		)
		# Insert into database
		created_time = ctx.message.created_at.replace(tzinfo = datetime.timezone.utc)
		await self.bot.db.execute(
			"""
			INSERT INTO reminders.reminders (user_id, channel_id, message_id, created_time, remind_time, reminder)
			VALUES ($1, $2, $3, $4, $5, $6)
			""", 
			ctx.author.id, ctx.channel.id, response.id, created_time,
			parsed_datetime, reminder
		)
		# Update timer
		if self.current_timer and parsed_datetime < self.current_timer["remind_time"]:
			self.restarting_timer = True
			self.timer.restart()
			self.timer.get_task().set_name("Reminders")
		else:
			self.new_reminder.set()
	
	@reminder_command.command(aliases = ["delete", "remove"])
	async def cancel(self, ctx, reminder_id: int):
		'''Cancel a reminder'''
		cancelled = await ctx.bot.db.fetchrow(
			"""
			UPDATE reminders.reminders
			SET cancelled = TRUE
			WHERE id = $1 AND user_id = $2 AND reminded = FALSE AND failed = FALSE
			RETURNING *
			""", 
			reminder_id, ctx.author.id
		)
		if not cancelled:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: Unable to find and cancel reminder")
		if self.current_timer and self.current_timer["id"] == reminder_id:
			self.restarting_timer = True
			self.timer.restart()
			self.timer.get_task().set_name("Reminders")
		await ctx.embed_reply(fields = (("Cancelled Reminder", cancelled["reminder"] or ctx.bot.ZWS),), 
								footer_text = f"Set for {cancelled['remind_time'].isoformat(timespec = 'seconds').replace('+00:00', 'Z')}", 
								timestamp = cancelled["remind_time"])
	
	@reminder_command.command(name = "list")
	async def list_reminders(
		self, ctx, per_page: Optional[commands.Range[int, 1, 10]] = 10
	):
		"""
		List reminders
		Max per_page is 10
		"""
		records = await ctx.bot.db.fetch(
			"""
			SELECT id, channel_id, message_id, remind_time, reminder
			FROM reminders.reminders
			WHERE user_id = $1 AND reminded = FALSE AND cancelled = FALSE AND failed = FALSE
			ORDER BY remind_time
			""", 
			ctx.author.id
		)
		paginator = ButtonPaginator(
			ctx, RemindersSource(records, per_page = per_page)
		)
		await paginator.start()
		ctx.bot.views.append(paginator)
	
	# TODO: clear subcommand
	
	# R/PT0S
	@tasks.loop()
	async def timer(self):
		record = await self.bot.db.fetchrow(
			"""
			SELECT * FROM reminders.reminders
			WHERE reminded = FALSE AND cancelled = FALSE AND failed = FALSE
			ORDER BY remind_time
			LIMIT 1
			"""
		)
		if not record:
			self.new_reminder.clear()
			return await self.new_reminder.wait()
		self.current_timer = record
		await discord.utils.sleep_until(record["remind_time"])
		if not (channel := self.bot.get_channel(record["channel_id"])):
			# TODO: Attempt to fetch channel?
			return await self.bot.db.execute("UPDATE reminders.reminders SET failed = TRUE WHERE id = $1", record["id"])
		user = self.bot.get_user(record["user_id"]) or await self.bot.fetch_user(record["user_id"])
		# TODO: Handle user not found?
		embed = discord.Embed(color = self.bot.bot_color)
		try:
			message = await channel.fetch_message(record["message_id"])
			embed.description = f"[{record['reminder'] or 'Reminder'}]({message.jump_url})"
		except discord.NotFound:
			embed.description = record["reminder"] or "Reminder"
		embed.set_footer(text = "Reminder set")
		embed.timestamp = record["created_time"]
		try:
			await channel.send(user.mention, embed = embed)
		except discord.Forbidden:
			# TODO: Attempt to send without embed
			# TODO: Fall back to DM
			await self.bot.db.execute("UPDATE reminders.reminders SET failed = TRUE WHERE id = $1", record["id"])
		else:
			await self.bot.db.execute("UPDATE reminders.reminders SET reminded = TRUE WHERE id = $1", record["id"])
	
	@timer.before_loop
	async def before_timer(self):
		await self.initialize_database()
		await self.bot.wait_until_ready()
	
	@timer.after_loop
	async def after_timer(self):
		if self.restarting_timer:
			self.restarting_timer = False
		else:
			self.bot.print("Reminders task cancelled")

class RemindersSource(menus.ListPageSource):
	
	def __init__(self, records, per_page):
		super().__init__(records, per_page = per_page)
	
	async def format_page(self, menu, records):
		embed = discord.Embed(title = "Reminders", color = menu.bot.bot_color)
		embed.set_author(name = menu.ctx.author.display_name, icon_url = menu.ctx.author.avatar.url)
		if self.per_page == 1:
			records = [records]
		for record in records:
			value = record["reminder"] or "Reminder"
			if channel := menu.bot.get_channel(record["channel_id"]):
				message = channel.get_partial_message(record["message_id"])
				value = (
					f"[{value}]({message.jump_url})\n"
					f"In {getattr(channel, 'mention', 'DMs')}"
				)
			# TODO: Attempt to fetch channel?
			value += f"\nAt {record['remind_time'].isoformat(timespec = 'seconds').replace('+00:00', 'Z')}"
			embed.add_field(name = f"ID: {record['id']}", value = value)
		offset = menu.current_page * self.per_page
		start = offset + 1
		end = min(offset + self.per_page, len(self.entries))
		if start < end:
			embed.set_footer(text = f"Reminders {start} - {end} of {len(self.entries)}")
		elif start == end:
			embed.set_footer(text = f"Reminder {start} of {len(self.entries)}")
		else:
			return embed.set_footer(text = f"In response to: {menu.ctx.message.clean_content}")
		return {"content": f"In response to: `{menu.ctx.message.clean_content}`", "embed": embed}

