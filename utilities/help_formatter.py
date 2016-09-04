
from discord.ext.commands.formatter import HelpFormatter, Paginator
from discord.ext.commands import Command
import inspect
import itertools

class CustomHelpFormatter(HelpFormatter):
	def format(self):
		'''
		Handles the actual behaviour involved with formatting.
		To change the behaviour, this method should be overridden.
		Returns
		--------
		list
			A paginated output of the help command.
		'''
		
		self._paginator = Paginator()
		
		# we need a padding of ~80 or so
		
		# description = self.command.description if not self.is_cog() else inspect.getdoc(self.command)
		if self.command == "categories":
			description = "Categories:"
		elif self.is_bot():
			description = "My Commands:"
		elif self.is_cog():
			description = inspect.getdoc(self.command)
		else:
			description = self.command.description
		
		if description:
			# <description> portion
			self._paginator.add_line(description, empty=True)
		
		if isinstance(self.command, Command):
			# <signature portion>
			signature = self.get_command_signature()
			self._paginator.add_line(signature, empty=True)
		
			# <long doc> section
			if self.command.help:
				self._paginator.add_line(self.command.help, empty=True)
		
			# end it here if it's just a regular command
			if not self.has_subcommands():
				self._paginator.close_page()
				return self._paginator.pages
		
		max_width = self.max_name_size
		
		def category(tup):
			cog = tup[1].cog_name
			# we insert the zero width space there to give it approximate
			# last place sorting position.
			return cog + ':' if cog is not None else '\u200bNo Category:'
		
		if self.is_bot():
			data = sorted(self.filter_command_list(), key=category)
			for category, commands in itertools.groupby(data, key=category):
				# there simply is no prettier way of doing this.
				# commands = list(commands)
				commands = sorted(commands, key = lambda c: c[0])
				if len(commands) > 0:
					self._paginator.add_line(category)
				
				self._add_subcommands_to_page(max_width, commands)
		elif self.command == "categories":
			categories = sorted(self.context.bot.cogs, key = str.lower)
			for category in categories:
				self._paginator.add_line(category)
			self._paginator.add_line()
			ending_note = ("{0}{1} [command] or {0}{1} [category] for more info\n"
			"{0}{1} all for all commands\n"
			"Also see {0}othercommands").format(self.clean_prefix, self.context.invoked_with)
			self._paginator.add_line(ending_note)
		else:
			# self._paginator.add_line('Commands:')
			if isinstance(self.command, Command):
				self._paginator.add_line("{} Commands:".format(self.command))
			else:
				self._paginator.add_line("{} Commands:".format(type(self.command).__name__))
			# self._add_subcommands_to_page(max_width, self.filter_command_list())
			subcommands = sorted(self.filter_command_list(), key = lambda c: c[0])
			self._add_subcommands_to_page(max_width, subcommands)
		
		# add the ending note
		# self._paginator.add_line()
		# ending_note = self.get_ending_note()
		# self._paginator.add_line(ending_note)
		return self._paginator.pages

