
import twitchio

import random

class Context(twitchio.Context):
	
	def random_viewer(self):
		return random.choice(self.channel.chatters)

