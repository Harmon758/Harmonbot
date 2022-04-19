
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
		ctx = self.context
		output = f"No command called `{string}` found"
		close_matches = difflib.get_close_matches(string, ctx.bot.all_commands.keys(), n = 1)
		if close_matches:
			output += f"\nDid you mean `{close_matches[0]}`?"
		return output
	
	def subcommand_not_found(self, command, string):
		if isinstance(command, Group) and command.all_commands:
			return f"`{command.qualified_name}` command has no subcommand named {string}"
		return f"`{command.qualified_name}` command has no subcommands"
	
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
		fields = (("For more info:", f"`{ctx.prefix}{self.invoked_with} [category]`\n"
										f"`{ctx.prefix}{self.invoked_with} [command]`\n"
										f"`{ctx.prefix}{self.invoked_with} [command] [subcommand]`"), 
					("Also see:", f"`{ctx.prefix}about`\n`"
									f"{ctx.prefix}{self.invoked_with} help`\n"
									f"`{ctx.prefix}{self.invoked_with} other`"),  # TODO: Include stats?
					("For all commands:", f"`{ctx.prefix}{self.invoked_with} all`", False))
		await ctx.embed_reply(description, title = "Categories", fields = fields)
	
	async def send_cog_help(self, cog):
		ctx = self.context
		paginator = Paginator(max_size = ctx.bot.EMBED_DESCRIPTION_CHARACTER_LIMIT)
		if cog.description:
			paginator.add_line(cog.description, empty = True)
		filtered_commands = await self.filter_commands(cog.get_commands(), sort = True)
		self.add_commands(self.get_max_size(filtered_commands), ctx.bot.EMBED_DESCRIPTION_CODE_BLOCK_ROW_CHARACTER_LIMIT, 
							filtered_commands, paginator)
		if not paginator.pages:
			return await ctx.embed_reply(title = f"{cog.qualified_name} Commands")
			# TODO: Response when no description or permitted commands in cog?
		if len(paginator.pages) == 1:
			return await ctx.embed_reply(title = f"{cog.qualified_name} Commands", description = paginator.pages[0])
		await ctx.whisper(embed = discord.Embed(title = f"{cog.qualified_name} Commands", description = paginator.pages[0], color = ctx.bot.bot_color))
		for page in paginator.pages[1:]:
			await ctx.whisper(embed = discord.Embed(description = page, color = ctx.bot.bot_color))
		if ctx.channel.type is not discord.ChannelType.private:
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
				embeds.append(discord.Embed(description = group.description, color = ctx.bot.bot_color))
			else:
				embeds.append(embed = discord.Embed(description = f"{paginator.pages[-1]}\n{group.description}", 
														color = ctx.bot.bot_color))
		
		max_width = self.get_max_size(subcommands)
		paginator = Paginator(max_size = ctx.bot.EMBED_FIELD_VALUE_CHARACTER_LIMIT)
		self.add_commands(max_width, ctx.bot.EMBED_FIELD_VALUE_CODE_BLOCK_ROW_CHARACTER_LIMIT, 
							subcommands, paginator)
		embeds[-1].add_field(name = f"Subcommands for {group}", value = paginator.pages[0], inline = False)
		for page in paginator.pages[1:]:
			if len(embeds[-1]) > ctx.bot.EMBED_TOTAL_CHARACTER_LIMIT:
				embeds.append(discord.Embed(color = ctx.bot.bot_color))
			embeds[-1].add_field(name = ctx.bot.ZERO_WIDTH_SPACE, value = page, inline = False)
		
		if len(embeds) == 1:
			embed = embeds[0]
			embed.set_author(
				name = ctx.author.display_name,
				icon_url = ctx.author.display_avatar.url
			)
			await ctx.channel.send(embed = embed)
		else:
			for embed in embeds:
				await ctx.whisper(embed = embed)
			if ctx.channel.type is not discord.ChannelType.private:
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
		if ctx.channel.type is not discord.ChannelType.private:
			await ctx.embed_reply("Check your DMs")
	
	async def send_all_help(self):
		ctx = self.context
		def get_category(command):
			return command.cog_name or f"{ctx.bot.ZERO_WIDTH_SPACE}No Category"
			# Zero width space to position as last category when sorted
		filtered_commands = await self.filter_commands(ctx.bot.commands, sort = True, 
														key = lambda c: get_category(c).lower())
		embed = discord.Embed(title = "My Commands", color = ctx.bot.bot_color)
		for category, commands in itertools.groupby(filtered_commands, key = get_category):
			commands = sorted(commands, key = lambda c: c.name)
			paginator = Paginator(max_size = ctx.bot.EMBED_FIELD_VALUE_CHARACTER_LIMIT)
			self.add_commands(self.get_max_size(filtered_commands), ctx.bot.EMBED_FIELD_VALUE_CODE_BLOCK_ROW_CHARACTER_LIMIT, 
								commands, paginator)
			total_category_characters = len(category) + len(paginator.pages) - 1 + len(paginator)
			if (len(embed) + total_category_characters > ctx.bot.EMBED_TOTAL_CHARACTER_LIMIT or 
				len(embed.fields) + len(paginator.pages) > ctx.bot.EMBED_FIELD_AMOUNT_LIMIT):
				await ctx.whisper(embed = embed)
				embed = discord.Embed(color = ctx.bot.bot_color)
			embed.add_field(name = category, value = paginator.pages[0], inline = False)
			for page in paginator.pages[1:]:
				embed.add_field(name = ctx.bot.ZERO_WIDTH_SPACE, value = page, inline = False)
		await ctx.whisper(embed = embed)
		if ctx.channel.type is not discord.ChannelType.private:
			await ctx.embed_reply("Check your DMs")
	
	def add_commands(self, max_width, line_limit, commands, paginator):
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
			lines.extend(self.wrap_line(line, max_width, line_limit, prefix, buffer))
			# Add subcommands of commands
			if isinstance(command, Group) and command.commands:
				subcommands = sorted(command.commands, key = lambda c: c.name)
				for subcommand in subcommands[:-1]:
					line = f"┣ {subcommand.name:<{max_width - 2}}  {subcommand.short_doc}"
					lines.extend(self.wrap_line(line, max_width, line_limit, "┃ ", 1))
				line = f"┗ {subcommands[-1].name:<{max_width - 2}}  {subcommands[-1].short_doc}"
				lines.extend(self.wrap_line(line, max_width, line_limit, "  ", 0))
		for line in lines:
			paginator.add_line(line)
	
	def wrap_line(self, line, max_width, limit, prefix, buffer):
		ctx = self.context
		if '┣' in prefix + line or '┗' in prefix + line:
			limit -= 1
		if len(line) <= limit:
			return [line]
		cutoff = line[:limit].rfind(' ')
		lines = [line[:cutoff]]
		while len(prefix) + max_width + 2 - buffer + len(line[cutoff + 1:]) >= limit:
			new_cutoff = line[:cutoff + limit - len(prefix) - max_width - 2 + buffer].rfind(' ')
			lines.append(prefix + ' ' * (max_width + 2 - buffer) + line[cutoff + 1:new_cutoff])
			cutoff = new_cutoff
		lines.append(prefix + ' ' * (max_width + 2 - buffer) + line[cutoff + 1:])
		return lines
	
	# @commands.bot_has_permissions(embed_links = True)
	async def command_callback(self, ctx, *, command : str = None):
		await self.prepare_help_command(ctx, command)
		
		if command == "all":
			'''All commands'''
			return await self.send_all_help()
			
		if command == "other":
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
		
		if not command:
			mapping = self.get_bot_mapping()
			return await self.send_bot_help(mapping)
		
		cog = ctx.bot.get_cog(command)
		if cog:
			return await self.send_cog_help(cog)
		
		keys = command.split()
		command = ctx.bot.all_commands.get(keys[0])
		if not command:
			# TODO: Use entire input?
			cog = discord.utils.find(lambda c: c[0].lower() == keys[0].lower(), ctx.bot.cogs.items())
			if cog:
				cog = cog[1]
				return await self.send_cog_help(cog)
			
			return await ctx.embed_reply(self.command_not_found(self.remove_mentions(keys[0])))
		
		for key in keys[1:]:
			if not isinstance(command, Group) or key not in command.all_commands:
				# TODO: Pass aliases used?
				return await ctx.embed_reply(self.subcommand_not_found(command, self.remove_mentions(key)))
			command = command.all_commands[key]
		
		# TODO: Pass alias used?
		if isinstance(command, Group):
			return await self.send_group_help(command)
		else:
			return await self.send_command_help(command)

