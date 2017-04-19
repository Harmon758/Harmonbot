
import discord
from discord.ext.commands.formatter import HelpFormatter, Paginator
from discord.ext.commands import Command

import inspect
import itertools
from modules import utilities

import clients

class CustomHelpFormatter(HelpFormatter):
	
	def format(self):
		description_paginator = Paginator(max_size = 2048)
		max_width = self.max_name_size
		if self.is_bot():
			def category(tup):
				cog = tup[1].cog_name
				# we insert the zero width space there to give it approximate last place sorting position
				return cog if cog is not None else "\u200bNo Category"
			## data = sorted(self.filter_command_list(), key = category)
			data = sorted(self.filter_command_list(), key = lambda c: category(c).lower())
			embeds = [discord.Embed(title = "My Commands", color = clients.bot_color)]
			for category, commands in itertools.groupby(data, key = category):
				commands = sorted(commands, key = lambda c: c[0])
				if len(commands) > 0:
					field_paginator = Paginator(max_size = 1024)
					self._add_subcommands_to_page(max_width, commands, field_paginator)
					# Embed Limit
					total_paginator_characters = len(field_paginator.pages) * len(category + " (coninued)") 
					for page in field_paginator.pages:
						total_paginator_characters += len(page)
					if utilities.embed_total_characters(embeds[-1]) + total_paginator_characters > 4000:
						embeds.append(discord.Embed(color = clients.bot_color))
					# 
					if len(embeds[-1].fields) <= 25 - len(field_paginator.pages):
						embeds[-1].add_field(name = category, value = field_paginator.pages[0], inline = False)
					else:
						embeds.append(discord.Embed(color = clients.bot_color).add_field(name = category, value = field_paginator.pages[0], inline = False))
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
			if not self.has_subcommands() or not list(self.filter_command_list()):
				description_paginator.close_page()
				if not self.command.help:
					return [discord.Embed(title = title, description = self.command.description, color = clients.bot_color)]
				elif len(self.command.help) <= 2048:
					description = clients.code_block.format(self.command.help) if "  " in self.command.help else self.command.help
					description += "\n" + self.command.description
					return [discord.Embed(title = title, description = description, color = clients.bot_color)]
				return self.embeds(title, description_paginator)
			subcommands = sorted(self.filter_command_list(), key = lambda c: c[0])
			subcommands_lines = self._subcommands_lines(max_width, subcommands)
			if (not self.command.help or len(self.command.help) <= 2048) and len('\n'.join(subcommands_lines)) <= 1016:
				# 1024 - 4 * 2
				embed = discord.Embed(color = clients.bot_color)
				value = "{}\n".format(description_paginator.pages[0]) if description_paginator.pages else ""
				value += self.command.description
				if not value:
					embed.title = title
				else:
					embed.add_field(name = title, value = value, inline = False)
				embed.add_field(name = "Subcommands for {}".format(self.command), value = clients.code_block.format('\n'.join(subcommands_lines)), inline = False)
				return [embed]
			description_paginator.add_line("Subcommands for {}:".format(self.command))
			self._add_subcommands_to_page(max_width, subcommands, description_paginator)
		else: # cog
			description = inspect.getdoc(self.command)
			if description:
				# <description> portion
				description_paginator.add_line(description, empty = True)
			title = "{} Commands".format(type(self.command).__name__)
			subcommands = sorted(self.filter_command_list(), key = lambda c: c[0])
			self._add_subcommands_to_page(max_width, subcommands, description_paginator)
		return self.embeds(title, description_paginator)
	
	def embeds(self, title, paginator):
		embeds = [discord.Embed(title = title, description = paginator.pages[0] if paginator.pages else None, color = clients.bot_color)]
		for page in paginator.pages[1:]:
			embeds.append(discord.Embed(description = page, color = clients.bot_color))
		return embeds
	
	def _add_subcommands_to_page(self, max_width, commands, paginator):
		for line in self._subcommands_lines(max_width, commands):
			paginator.add_line(line)
	
	def _subcommands_lines(self, max_width, commands):
	# def _subcommands_lines(self, max_width, commands, indent = True):
		lines = []
		for name, command in commands:
			if name in command.aliases: # skip aliases
				continue
			line = '{0:<{width}}  {1}'.format(name, command.short_doc, width = max_width)
			# line = '{indent}{0:<{width}}  {1}'.format(name, command.short_doc, width = max_width, indent = "  " if indent else "")
			if len(line) <= 55:
				lines.append(line)
			else:
				cutoff = line[:55].rfind(' ')
				lines.append(line[:cutoff])
				while cutoff + 55 < len(line):
					new_cutoff = line[:cutoff + 55].rfind(' ')
					lines.append(' ' * (max_width + 2) + line[cutoff + 1:new_cutoff])
					cutoff = new_cutoff
				lines.append(' ' * (max_width + 2) + line[cutoff + 1:])
		return lines

