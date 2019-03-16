
import discord
from discord.ext.commands.formatter import HelpFormatter, Paginator
from discord.ext.commands import Command, Group

import inspect
import itertools

import clients

class CustomHelpFormatter(HelpFormatter):
	
	'''Custom Help Formatter'''
	
	def __init__(self, embed_color):
		self.embed_color = embed_color
		self.embed_total_limit = 6000
		self.embed_description_limit = 2048
		self.embed_field_limit = 1024
		self.embed_codeblock_row_limit = 55
		self.embed_fields_limit = 25
		super().__init__()
	
	async def format(self):
		'''Format'''
		description_paginator = Paginator(max_size = self.embed_description_limit)
		max_width = self.max_name_size
		if not isinstance(self.command, Command) or self.has_subcommands():
			filtered_command_list = await self.filter_command_list()
		if self.is_bot():
			def category(tup):
				cog = tup[1].cog_name
				# we insert the zero width space there to give it approximate last place sorting position
				return cog if cog is not None else "\u200bNo Category"
			data = sorted(filtered_command_list, key = lambda c: category(c).lower())
			embeds = [discord.Embed(title = "My Commands", color = self.embed_color)]
			for category, commands in itertools.groupby(data, key = category):
				commands = sorted(commands, key = lambda c: c[0])
				if len(commands) > 0:
					field_paginator = Paginator(max_size = self.embed_field_limit)
					self._add_subcommands_to_page(max_width, commands, field_paginator)
					# Embed Limit
					total_paginator_characters = len(field_paginator.pages) * len(category + " (coninued)") 
					for page in field_paginator.pages:
						total_paginator_characters += len(page)
					if len(embeds[-1]) + total_paginator_characters > self.embed_total_limit:
						embeds.append(discord.Embed(color = self.embed_color))
					# 
					if len(embeds[-1].fields) <= self.embed_fields_limit - len(field_paginator.pages):
						embeds[-1].add_field(name = category, value = field_paginator.pages[0], inline = False)
					else:
						embeds.append(discord.Embed(color = self.embed_color).add_field(name = category, value = field_paginator.pages[0], inline = False))
					for page in field_paginator.pages[1:]:
						embeds[-1].add_field(name = "{} (continued)".format(category), value = page, inline = False)
			return embeds
		elif isinstance(self.command, Command):
			# <signature portion>
			title = self.get_command_signature()
			# <long doc> section
			if self.command.help:
				description_paginator.add_line(self.command.help, empty = True)
			# end it here if it's just a regular command
			if not self.has_subcommands() or not list(filtered_command_list):
				description_paginator.close_page()
				if not self.command.help:
					return [discord.Embed(title = title, description = self.command.description, color = self.embed_color)]
				elif len(self.command.help) <= self.embed_description_limit:
					description = clients.code_block.format(self.command.help) if "  " in self.command.help else self.command.help
					description += "\n" + self.command.description
					return [discord.Embed(title = title, description = description, color = self.embed_color)]
				return self.embeds(title, description_paginator)
			subcommands = sorted(filtered_command_list, key = lambda c: c[0])
			subcommand_lines = self.generate_subcommand_lines(max_width, subcommands)
			if (not self.command.help or len(self.command.help) <= self.embed_description_limit) and len('\n'.join(subcommand_lines)) <= self.embed_field_limit - 8:
			# 8: len("```\n") * 2
				embed = discord.Embed(color = self.embed_color)
				value = "{}\n".format(description_paginator.pages[0]) if description_paginator.pages else ""
				value += self.command.description
				if not value:
					embed.title = title
				else:
					embed.add_field(name = title, value = value, inline = False)
				embed.add_field(name = "Subcommands for {}".format(self.command), value = clients.code_block.format('\n'.join(subcommand_lines)), inline = False)
				return [embed]
			description_paginator.add_line("Subcommands for {}:".format(self.command))
			self._add_subcommands_to_page(max_width, subcommands, description_paginator)
		else: # cog
			description = inspect.getdoc(self.command)
			if description:
				# <description> portion
				description_paginator.add_line(description, empty = True)
			title = "{} Commands".format(type(self.command).__name__)
			subcommands = sorted(filtered_command_list, key = lambda c: c[0])
			self._add_subcommands_to_page(max_width, subcommands, description_paginator)
		return self.embeds(title, description_paginator)
	
	@property
	def max_name_size(self):
		"""int: Returns the largest name length of a command or if it has subcommands
		the largest subcommand name."""
		try:
			commands = self.command.all_commands.copy() if not self.is_cog() else self.context.bot.all_commands.copy()
			if commands:
				# Include subcommands of subcommands
				for _, command in commands.copy().items():
					if isinstance(command, Group):
						commands.update(command.all_commands)
				return max(map(lambda c: len(c.name) if self.show_hidden or not c.hidden else 0, commands.values()))
			return 0
		except AttributeError:
			return len(self.command.name)
	
	def _add_subcommands_to_page(self, max_width, commands, paginator):
		for line in self.generate_subcommand_lines(max_width, commands):
			paginator.add_line(line)
	
	def generate_subcommand_lines(self, max_width, commands):
		lines = []
		# Add 3 for "┣ "/"┗ "
		for _, command in commands:
			if isinstance(command, Group) and command.commands:
				max_width += 3
				break
		for name, command in commands:
			if name in command.aliases: # skip aliases
				continue
			prefix = "┃ " if isinstance(command, Group) and command.commands else " "
			buffer = 2 if isinstance(command, Group) and command.commands else 0
			line = "{0:<{width}}  {1}".format(name, command.short_doc, width = max_width)
			lines = self.append_subcommand_line(lines, line, max_width, prefix, buffer)
			# Add subcommands of subcommands
			if isinstance(command, Group) and command.commands:
				subcommands = sorted(command.commands, key = lambda c: c.name)
				for subcommand in subcommands[:-1]:
					line = "┣ {0:<{width}}  {1}".format(subcommand.name, subcommand.short_doc, width = max_width - 2)
					lines = self.append_subcommand_line(lines, line, max_width, "┃ ", 1)
				line = "┗ {0:<{width}}  {1}".format(subcommands[-1].name, subcommands[-1].short_doc, width = max_width - 2)
				lines = self.append_subcommand_line(lines, line, max_width, "  ", 0)
		return lines
	
	def append_subcommand_line(self, lines, line, max_width, prefix, buffer):
		limit = self.embed_codeblock_row_limit
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
	
	def embeds(self, title, paginator):
		embeds = [discord.Embed(title = title, description = paginator.pages[0] if paginator.pages else None, color = self.embed_color)]
		for page in paginator.pages[1:]:
			embeds.append(discord.Embed(description = page, color = self.embed_color))
		return embeds

