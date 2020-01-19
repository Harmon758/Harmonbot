
from discord.ext import menus

class Menu(menus.Menu):
	
	async def update(self, payload):
		await super().update(payload)
		await self.bot.increment_menu_reactions_count()

