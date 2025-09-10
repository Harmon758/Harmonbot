
from twitchio.ext import commands

import random

class Context(commands.Context):
	
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.channel_command = None
	
	def random_viewer(self):
		return random.choice(self.channel.chatters)

