
import discord
from discord.ext import commands
from discord.ext.commands import Group, Paginator

import difflib
import itertools

# Use DefaultHelpCommand?
class HelpCommand(commands.HelpCommand):
	
	'''Custom Help Command'''
	
	def __init__(self, **options):
		attrs = options.setdefault("command_attrs", {})
		attrs.setdefault("help", "Shows this message\n"
									"Inputs in angle brackets, <>, are required\n"
									"Inputs in square brackets, [], are optional\n"
									"If you are not currently able to use a command in the channel where you executed help, "
									"it will not be displayed in the corresponding help message")
		super().__init__(**options)
	
	# TODO: Mitigate code block cutoff issue
	
	def command_not_found(self, string):
		return f"No command called `{string}` found"
	
	def get_max_size(self, commands):
		# Include subcommands
		commands = commands.copy()
		for command in commands.copy():
			if isinstance(command, Group):
				commands.extend(command.commands)
		return super().get_max_size(commands)
	
	async def send_bot_help(self, mapping):
		ctx = self.context
		description = "  ".join(f"`{category}`" for category in sorted(ctx.bot.cogs, key = str.lower))
		fields = (("For more info:", f"`{ctx.prefix}{ctx.invoked_with} [category]`\n"
										f"`{ctx.prefix}{ctx.invoked_with} [command]`\n"
										f"`{ctx.prefix}{ctx.invoked_with} [command] [subcommand]`"), 
					("Also see:", f"`{ctx.prefix}about`\n`"
									f"{ctx.prefix}{ctx.invoked_with} help`\n"
									f"`{ctx.prefix}{ctx.invoked_with} other`"),  # TODO: Include stats?
					("For all commands:", f"`{ctx.prefix}{ctx.invoked_with} all`", False))
		await ctx.embed_reply(description, title = "Categories", fields = fields)
	
	async def send_cog_help(self, cog):
		ctx = self.context
		paginator = Paginator(max_size = ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT)
		if cog.description:
			paginator.add_line(cog.description, empty = True)
		filtered_commands = await self.filter_commands(cog.get_commands(), sort = True)
		self._add_subcommands_to_page(self.get_max_size(filtered_commands), filtered_commands, paginator)
		if not paginator.pages:
			return await ctx.embed_reply(title = f"{cog.qualified_name} Commands")
			# TODO: Response when no description or permitted commands in cog?
		if len(paginator.pages) == 1:
			return await ctx.embed_reply(title = f"{cog.qualified_name} Commands", description = paginator.pages[0])
		await ctx.author.send(embed = discord.Embed(title = f"{cog.qualified_name} Commands", description = paginator.pages[0], color = ctx.bot.bot_color))
		for page in paginator.pages[1:]:
			await ctx.author.send(embed = discord.Embed(description = page, color = ctx.bot.bot_color))
		if not isinstance(ctx.channel, discord.DMChannel):
			await ctx.embed_reply("Check your DMs")
	
	async def send_group_help(self, group):
		subcommands = await self.filter_commands(group.commands, sort = True)
		if not subcommands:
			return await self.send_command_help(group)
		
		ctx = self.context
		title = self.get_command_signature(group)
		if not group.help:
			description = group.description
		else:
			description = group.help
			if "  " in group.help:
				description = ctx.bot.CODE_BLOCK.format(description)
			description += '\n' + group.description
		if len(description) <= ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT:
			embeds = [discord.Embed(title = title, description = description, color = ctx.bot.bot_color)]
		else:
			paginator = Paginator(max_size = ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT)
			paginator.add_line(group.help, empty = True)
			paginator.close_page()  # Necessary?
			embeds = [discord.Embed(title = title, description = paginator.pages[0], color = ctx.bot.bot_color)]
			for page in paginator.pages[1:-1]:
				embeds.append(discord.Embed(description = page, color = ctx.bot.bot_color))
			if len(paginator.pages[-1] + group.description) + 1 > ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT:
				embeds.append(discord.Embed(description = paginator.pages[-1], color = ctx.bot.bot_color))
				embeds.append(discord.Embed(description = command.description, color = ctx.bot.bot_color))
			else:
				embeds.append(embed = discord.Embed(description = f"{paginator.pages[-1]}\n{command.description}", 
														color = ctx.bot.bot_color))
		
		max_width = self.get_max_size(subcommands)
		subcommand_lines = self.generate_subcommand_lines(max_width, subcommands)
		if len('\n'.join(subcommand_lines)) + 8 <= ctx.bot.EMBED_FIELD_VALUE_CHARACTER_LIMIT:
		# 8 = len("```\n") * 2
			embeds[-1].add_field(name = f"Subcommands for {group}", value = ctx.bot.CODE_BLOCK.format('\n'.join(subcommand_lines)), inline = False)
		else:
			paginator = Paginator(max_size = ctx.bot.EMBED_FIELD_VALUE_CHARACTER_LIMIT)
			self._add_subcommands_to_page(max_width, subcommands, paginator)
			embeds[-1].add_field(name = f"Subcommands for {group}", value = paginator.pages[0])
			for page in paginator.pages[1:]:
				embeds[-1].add_field(name = ctx.bot.ZERO_WIDTH_SPACE, value = page)
				if len(embeds[-1]) > ctx.bot.EMBED_TOTAL_CHARACTER_LIMIT:
					embeds[-1].remove_field(-1)
					embeds.append(discord.Embed(description = page, color = ctx.bot.bot_color))
		
		if len(embeds) == 1:
			await ctx.channel.send(embed = embeds[0].set_author(name = ctx.author.display_name, 
																icon_url = ctx.author.avatar_url))
		else:
			for embed in embeds:
				await ctx.author.send(embed = embed)
			if not isinstance(ctx.channel, discord.DMChannel):
				await ctx.embed_reply("Check your DMs")
	
	async def send_command_help(self, command):
		ctx = self.context
		title = self.get_command_signature(command)
		if not command.help:
			return await ctx.embed_reply(title = title, description = command.description)
		description = command.help
		if "  " in command.help:
			description = ctx.bot.CODE_BLOCK.format(description)
		description += '\n' + command.description
		if len(description) <= ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT:
			return await ctx.embed_reply(title = title, description = description)
		paginator = Paginator(max_size = ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT)
		paginator.add_line(command.help, empty = True)
		paginator.close_page()  # Necessary?
		await ctx.whisper(embed = discord.Embed(title = title, 
												description = paginator.pages[0], color = ctx.bot.bot_color))
		for page in paginator.pages[1:-1]:
			await ctx.whisper(embed = discord.Embed(description = page, color = ctx.bot.bot_color))
		if len(paginator.pages[-1] + command.description) + 1 > ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT:
			await ctx.whisper(embed = discord.Embed(description = paginator.pages[-1], color = ctx.bot.bot_color))
			await ctx.whisper(embed = discord.Embed(description = command.description, color = ctx.bot.bot_color))
		else:
			await ctx.whisper(embed = discord.Embed(description = f"{paginator.pages[-1]}\n{command.description}", 
													color = ctx.bot.bot_color))
		if not isinstance(ctx.channel, discord.DMChannel):
			await ctx.embed_reply("Check your DMs")
	
	async def send_all_help(self):
		ctx = self.context
		def get_category(command):
			return command.cog_name or f"{ctx.bot.ZERO_WIDTH_SPACE}No Category"
			# Zero width space to position as last category when sorted
		filtered_commands = await self.filter_commands(ctx.bot.commands, sort = True, key = lambda c: get_category(c).lower())
		embed = discord.Embed(title = "My Commands", color = ctx.bot.bot_color)
		for category, commands in itertools.groupby(filtered_commands, key = get_category):
			commands = sorted(commands, key = lambda c: c.name)
			paginator = Paginator(max_size = ctx.bot.EMBED_FIELD_VALUE_CHARACTER_LIMIT)
			self._add_subcommands_to_page(self.get_max_size(filtered_commands), commands, paginator)
			total_category_characters = (len(category) + len(paginator.pages) - 1
											+ sum(len(page) for page in paginator.pages))
			if (len(embed) + total_category_characters > ctx.bot.EMBED_TOTAL_CHARACTER_LIMIT or 
				len(embed.fields) + len(paginator.pages) > ctx.bot.EMBED_FIELD_AMOUNT_LIMIT):
				await ctx.whisper(embed = embed)
				embed = discord.Embed(color = ctx.bot.bot_color)
			embed.add_field(name = category, value = paginator.pages[0], inline = False)
			for page in paginator.pages[1:]:
				embed.add_field(name = ctx.bot.ZERO_WIDTH_SPACE, value = page, inline = False)
		await ctx.whisper(embed = embed)
		if not isinstance(ctx.channel, discord.DMChannel):
			await ctx.embed_reply("Check your DMs")
	
	def _add_subcommands_to_page(self, max_width, commands, paginator):
		for line in self.generate_subcommand_lines(max_width, commands):
			paginator.add_line(line)
	
	def generate_subcommand_lines(self, max_width, commands):
		lines = []
		# Add 3 for "┣ "/"┗ "
		for command in commands:
			if isinstance(command, Group) and command.commands:
				max_width += 3
				break
		for command in commands:
			prefix = "┃ " if isinstance(command, Group) and command.commands else " "
			buffer = 2 if isinstance(command, Group) and command.commands else 0
			line = f"{command.name:<{max_width}}  {command.short_doc}"
			lines = self.append_subcommand_line(lines, line, max_width, prefix, buffer)
			# Add subcommands of subcommands
			if isinstance(command, Group) and command.commands:
				subcommands = sorted(command.commands, key = lambda c: c.name)
				for subcommand in subcommands[:-1]:
					line = f"┣ {subcommand.name:<{max_width - 2}}  {subcommand.short_doc}"
					lines = self.append_subcommand_line(lines, line, max_width, "┃ ", 1)
				line = f"┗ {subcommands[-1].name:<{max_width - 2}}  {subcommands[-1].short_doc}"
				lines = self.append_subcommand_line(lines, line, max_width, "  ", 0)
		return lines
	
	def append_subcommand_line(self, lines, line, max_width, prefix, buffer):
		ctx = self.context
		limit = ctx.bot.EMBED_CODE_BLOCK_ROW_CHARACTER_LIMIT
		if '┣' in prefix + line or '┗' in prefix + line:
			limit -= 1
		if len(line) <= limit:
			lines.append(line)
		else:
			cutoff = line[:limit].rfind(' ')
			lines.append(line[:cutoff])
			while len(prefix) + max_width + 2 - buffer + len(line[cutoff + 1:]) >= limit:
				new_cutoff = line[:cutoff + limit - len(prefix) - max_width - 2 + buffer].rfind(' ')
				lines.append(prefix + ' ' * (max_width + 2 - buffer) + line[cutoff + 1:new_cutoff])
				cutoff = new_cutoff
			lines.append(prefix + ' ' * (max_width + 2 - buffer) + line[cutoff + 1:])
		return lines
	
	# @checks.dm_or_has_capability("embed_links")
	async def command_callback(self, ctx, *commands : str):
		self.context = ctx
		if len(commands) == 1:
			if commands[0] == "all":
				'''All commands'''
				return await self.send_all_help()
			if commands[0] == "other":
				'''Additional commands and information'''
				# TODO: Update
				# TODO: Add last updated date?
				fields = (("Conversion Commands", f"see `{ctx.prefix}conversions`", False), 
							("In Progress", "gofish redditsearch roleposition rolepositions taboo userlimit webmtogif whatis", False), 
							("Misc", "invite randomgame test test_on_message", False), 
							("Owner Only", "allcommands changenickname deletetest cleargame clearstreaming echo eval exec load reload repl restart servers setgame setstreaming shutdown unload updateavatar", False), 
							("No Prefix", "@Harmonbot :8ball: (exactly: f|F) (anywhere in message: getprefix)", False))
				return await ctx.embed_reply(f"See `{ctx.prefix}help` for the main commands", 
												title = f"Commands not in {ctx.prefix}help", fields = fields)
		# TODO: Pass alias used to help formatter?
		if not commands:
			return await super().command_callback(ctx)
		name = self.remove_mentions(commands[0])
		if len(commands) == 1:
			if name in ctx.bot.cogs:
				cog = ctx.bot.cogs[name]
				return await self.send_cog_help(cog)
			if name.lower() in ctx.bot.all_commands:
				command = ctx.bot.all_commands[name.lower()]
				if isinstance(command, Group):
					return await self.send_group_help(command)
				else:
					return await self.send_command_help(command)
			cog = discord.utils.find(lambda c: c[0].lower() == name.lower(), ctx.bot.cogs.items())
			if cog:
				cog = cog[1]
				return await self.send_cog_help(cog)
			output = self.command_not_found(name)
			close_matches = difflib.get_close_matches(name, ctx.bot.all_commands.keys(), n = 1)
			if close_matches:
				output += f"\nDid you mean `{close_matches[0]}`?"
			return await ctx.embed_reply(output)
		else:
			command = ctx.bot.all_commands.get(name)
			if command is None:
				return await ctx.embed_reply(self.command_not_found(name))
			for key in commands[1:]:
				try:
					key = self.remove_mentions(key)
					command = command.all_commands.get(key)
					if command is None:
						return await ctx.embed_reply(self.command_not_found(key))
				except AttributeError:
					return await ctx.embed_reply(f"`{command.name}` command has no subcommands")
			if isinstance(command, Group):
				return await self.send_group_help(command)
			else:
				return await self.send_command_help(command)

