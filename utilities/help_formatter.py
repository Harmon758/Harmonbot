
from discord.ext.commands.formatter import HelpFormatter
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
		
		self._pages = []
		self._count = 4 # ``` + '\n'
		self._current_page = ['```']
		
		# we need a padding of ~80 or so
		
		description = self.command.description if not self.is_cog() else inspect.getdoc(self.command)
		
		if description:
			# <description> portion
			self._current_page.append(description)
			self._current_page.append('')
			self._count += len(description)
		
		if isinstance(self.command, Command):
			# <signature portion>
			signature = self.get_command_signature()
			self._count += 2 + len(signature) # '\n' sig '\n'
			self._current_page.append(signature)
			self._current_page.append('')
		
			# <long doc> section
			if self.command.help:
				self._count += 2 + len(self.command.help)
				self._current_page.append(self.command.help)
				self._current_page.append('')
				self._check_new_page()
		
			# end it here if it's just a regular command
			if not self.has_subcommands():
				self._current_page.append('```')
				self._pages.append('\n'.join(self._current_page))
				return self._pages
		
		
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
					self._current_page.append(category)
					self._count += len(category)
					self._check_new_page()
				
				self._add_subcommands_to_page(max_width, commands)
		else:
			self._current_page.append('Commands:')
			self._count += 1 + len(self._current_page[-1])
			self._add_subcommands_to_page(max_width, self.filter_command_list())
		
		# add the ending note
		self._current_page.append('')
		ending_note = self.get_ending_note()
		self._count += len(ending_note)
		self._check_new_page()
		self._current_page.append(ending_note)
		
		if len(self._current_page) > 1:
			self._current_page.append('```')
			self._pages.append('\n'.join(self._current_page))
		
		return self._pages

