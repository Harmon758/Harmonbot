
import discord
from discord.ext import commands

#import builtins
import datetime
import json
import subprocess

import credentials
from modules import documentation
from modules import permissions
from modules import utilities
from modules import voice
from utilities import checks
from client import online_time

def setup(bot):
	bot.add_cog(Meta(bot))

class Meta:
	
	def __init__(self, bot):
		self.bot = bot
	
	'''
	@self.bot.command(hidden = True)
	@checks.is_owner()
	async def eval(*code : str):
		await self.bot.reply("\n```" + str(builtins.eval(' '.join(code))) + "```")
	
	@self.bot.command(hidden = True)
	@checks.is_owner()
	async def exec(*code : str):
		builtins.exec('' '.join(code))
		await self.bot.reply("Successfully executed.")
	'''
	
	@commands.group(invoke_without_command = True)
	@checks.is_server_owner()
	async def setpermission(self):
		await self.bot.reply("Invalid input.")
	
	@setpermission.command(name = "everyone", pass_context = True)
	@checks.is_server_owner()
	async def setpermission_everyone(self, ctx, permission : str, setting : bool):
		permission.set_permission(ctx.message, "everyone", None, permission, setting)
		await self.bot.reply("Permission updated")
	
	@setpermission.command(name = "role", pass_context = True)
	@checks.is_server_owner()
	async def setpermission_role(self, ctx, role : str, permission : str, setting : bool):
		role_names = []
		for role in ctx.message.server.roles:
			role_names.append(remove_symbols(role.name))
		if role_names.count(role) > 1:
			await self.bot.reply("Error: multiple roles with this name")
			return
		elif role_names.count(role) == 0:
			await self.bot.reply("Error: role with this name not found")
			return
		else:
			to_set = discord.utils.find(lambda r: remove_symbols(r.name) == role, ctx.message.server.roles).id
		permissions.set_permission(ctx.message, "role", to_set, permission, setting)
		await self.bot.reply("Permission updated")
	
	@setpermission.command(name = "user", pass_context = True)
	@checks.is_server_owner()
	async def setpermission_user(self, ctx, user : str, permission : str, setting : bool):
		if re.match(r"^(\w+)#(\d{4})", user):
			user_info = re.match(r"^(\w+)#(\d{4})", user)
			user_name = user_info.group(1)
			user_discriminator = user_info.group(2)
			to_set = discord.utils.find(lambda m: m.name == user_name and str(m.discriminator) == user_discriminator, ctx.message.server.members).id
			if not to_set:
				await self.bot.reply("Error: user not found")
				return
		else:
			user_names = []
			for member in ctx.message.server.members:
				user_names.append(member.name)
			if user_names.count(user) > 1:
				await self.bot.reply("Error: multiple users with this name; please include discriminator")
				return
			elif user_names.count(user) == 0:
				await self.bot.reply("Error: user with this name not found")
				return
			else:
				to_set = discord.utils.get(ctx.message.server.members, name = user).id
		permissions.set_permission(ctx.message, "user", to_set, permission, setting)
		await self.bot.reply("Permission updated")
	
	@commands.group(invoke_without_command = True)
	@checks.is_server_owner()
	async def getpermission(self):
		await self.bot.reply("Invalid input.")
	
	@getpermission.command(name = "everyone", pass_context = True)
	@checks.is_server_owner()
	async def getpermission_everyone(self, ctx, permission : str):
		permissions.get_permission(ctx.message, "everyone", None, permission)
	
	@getpermission.command(name = "role", pass_context = True)
	@checks.is_server_owner()
	async def getpermission_role(self, ctx, role : str, permission : str):
		role_names = []
		for role in ctx.message.server.roles:
			role_names.append(remove_symbols(role.name))
		if role_names.count(role) > 1:
			await self.bot.reply("Error: multiple roles with this name")
		elif role_names.count(role) == 0:
			await self.bot.reply("Error: role with this name not found")
		else:
			to_find = discord.utils.get(ctx.message.server.roles, name = role).id
		permissions.get_permission(ctx.message, "role", to_find, permission)
	
	@getpermission.command(name = "user", pass_context = True)
	@checks.is_server_owner()
	async def getpermission_user(self, ctx, user : str, permission : str):
		return
	
	@commands.command(hidden = True, pass_context = True)
	@checks.is_owner()
	async def allcommands(self, ctx):
		'''All the commands'''
		formatter = commands.HelpFormatter(show_check_failure = True, show_hidden = True)
		formatter.format_help_for(ctx, self.bot)
		_commands = formatter.filter_command_list()
		_allcommands = ""
		for name, _command in _commands:
			_allcommands += name + ' '
		await self.bot.whisper(_allcommands[:-1])
	
	@commands.command()
	async def changelog(self):
		'''Link to changelog'''
		await self.bot.reply("https://discord.gg/0oyodN94Y3CgCT6I")
	
	@commands.command(name = "commands")
	async def _commands(self):
		'''Some additional commands and information'''
		await self.bot.whisper(documentation.commands)
		await self.bot.reply("Check your DMs for some of my additional commands.")
	
	@commands.command(hidden = True)
	async def discordlibraryversion(self):
		'''The discord.py library version I'm currently using'''
		await self.bot.reply(discord.__version__)
	
	@commands.command(aliases = ["oauth"], hidden = True)
	async def invite(self):
		'''Link to invite me to a server'''
		application_info = await self.bot.application_info()
		await self.bot.reply(discord.utils.oauth_url(application_info.id))
	
	@commands.command(hidden = True)
	async def ping(self):
		'''Basic ping - pong command'''
		await self.bot.say("pong")
	
	@commands.command(hidden = True)
	@checks.is_owner()
	async def servers(self):
		'''Every server I'm in'''
		for server in self.bot.servers:
			server_info = "```Name: " + server.name + "\n"
			server_info += "ID: " + server.id + "\n"
			server_info += "Owner: " + server.owner.name + "\n"
			server_info += "Server Region: " + str(server.region) + "\n"
			server_info += "Members: " + str(server.member_count) + "\n"
			server_info += "Created at: " + str(server.created_at) + "\n```"
			server_info += "Icon: " + server.icon_url
			await self.bot.whisper(server_info)
	
	# Public Stats
	
	@commands.command()
	async def stats(self, *option : str):
		'''Bot stats'''
		with open("data/stats.json", "r") as stats_file:
			stats = json.load(stats_file)
		if not option:
			uptime = utilities.duration_to_letter_format(utilities.secs_to_duration(int(stats["uptime"])))
			restarts = str(stats["restarts"])
			cogs_reloaded = str(stats["cogs_reloaded"])
			commands_executed = str(stats["commands_executed"])
			await self.bot.reply("\n"
			"Total Recorded Uptime: {}\n"
			"Total Recorded Restarts: {}\n"
			"Total Cogs Reloaded: {}\n"
			"Total Recorded Commands Executed: {}".format(uptime, restarts, cogs_reloaded, commands_executed))
		elif option[0] == "uptime": # since 4/17/16, fixed 5/10/16
			uptime = utilities.duration_to_letter_format(utilities.secs_to_duration(int(stats["uptime"])))
			await self.bot.reply("Total Recorded Uptime: {}".format(uptime))
		elif option[0] == "restarts": # since 4/17/16, fixed 5/10/16
			restarts = str(stats["restarts"])
			await self.bot.reply("Total Recorded Restarts: {}".format(restarts))
		elif ' '.join(option[:2]) == "cogs reloaded": # since 6/10/16 - implemented cog reloading
			cogs_reloaded = str(stats["cogs_reloaded"])
			await self.bot.reply("Total Cogs Reloaded: {}".format(cogs_reloaded))
		elif ' '.join(option[:2]) == "commands executed": # since 6/10/16 (cog commands)
			commands_executed = str(stats["commands_executed"])
			await self.bot.reply("Total Record Commands Executed".format(commands_executed))
	
	@commands.command()
	async def uptime(self):
		'''Bot uptime'''
		now = datetime.datetime.utcnow()
		uptime = now - online_time
		await self.bot.reply(utilities.duration_to_letter_format(utilities.secs_to_duration(int(uptime.total_seconds()))))
	
	# Update Bot Stuff
	
	@commands.command(pass_context = True, hidden = True)
	@checks.is_owner()
	async def changenickname(self, ctx, *, nickname : str):
		'''Update my nickname'''
		await self.bot.change_nickname(ctx.message.server.me, nickname)
	
	@commands.command(hidden = True)
	@checks.is_owner()
	async def updateavatar(self):
		'''Update my avatar'''
		with open("data/discord_harmonbot_icon.png", "rb") as avatar_file:
			await self.bot.edit_profile(avatar = avatar_file.read())
		await self.bot.reply("Avatar updated.")
	
	@commands.command(hidden = True)
	async def randomgame(self):
		'''Update to a random playing/game status message'''
		await utilities.random_game_status()
		# await self.bot.reply("I changed to a random game status.")
	
	@commands.command(pass_context = True, aliases = ["updateplaying", "updategame", "changeplaying", "changegame", "setplaying"], hidden = True)
	@checks.is_owner()
	async def setgame(self, ctx, *, name : str):
		'''Set my playing/game status message'''
		updated_game = ctx.message.server.me.game
		if not updated_game:
			updated_game = discord.Game(name = name)
		else:
			updated_game.name = name
		await self.bot.change_status(game = updated_game)
		await self.bot.reply("Game updated.")
	
	@commands.command(pass_context = True, hidden = True)
	@checks.is_owner()
	async def setstreaming(self, ctx, option : str, *url : str):
		'''Set my streaming status'''
		if option == "on" or option == "true":
			if not url:
				await utilities.set_streaming_status()
				return
			else:
				updated_game = ctx.message.server.me.game
				if not updated_game:
					updated_game = discord.Game(url = url[0], type = 1)
				else:
					updated_game.url = url[0]
					updated_game.type = 1
		else:
			updated_game = ctx.message.server.me.game
			updated_game.type = 0
		await self.bot.change_status(game = updated_game)
	
	@commands.command(pass_context = True, aliases = ["!clearplaying"], hidden = True)
	@checks.is_owner()
	async def cleargame(self, ctx):
		'''Clear my playing/game status message'''
		updated_game = ctx.message.server.me.game
		if updated_game and updated_game.name:
			updated_game.name = None
			await self.bot.change_status(game = updated_game)
			await self.bot.reply("Game status cleared.")
		else:
			await self.bot.reply("There is no game status to clear.")
	
	@commands.command(pass_context = True, hidden = True)
	@checks.is_owner()
	async def clearstreaming(self, ctx, *option : str):
		'''Clear my streaming status'''
		updated_game = ctx.message.server.me.game
		if updated_game and (updated_game.url or updated_game.type):
			updated_game.url = None
			if option and option[0] == "url":
				await self.bot.change_status(game = updated_game)
				await self.bot.reply("Streaming url cleared.")
				return
			updated_game.type = 0
			await self.bot.change_status(game = updated_game)
			await self.bot.reply("Streaming status and url cleared.")
		else:
			await self.bot.reply("There is no streaming status or url to clear.")
	
	# Restart/Shutdown
	
	@commands.command(pass_context = True, hidden = True)
	@checks.is_owner()
	async def restart(self, ctx):
		'''Restart me'''
		await self.bot.say(":ok_hand::skin-tone-2: Restarting...")
		print("Shutting down Harmonbot...")
		voice_channels = [[voice_client.channel.id, voice.get_player(voice_client.server)["text"]] for voice_client in self.bot.voice_clients]
		with open("data/restart_channel.json", "x+") as restart_channel_file:
			json.dump({"restart_channel" : ctx.message.channel.id, "voice_channels" : voice_channels}, restart_channel_file)
		#raise KeyboardInterrupt
		await utilities.restart_tasks()
		await self.bot.logout()
	
	@commands.command(aliases = ["crash", "panic"], hidden = True)
	@checks.is_owner()
	async def shutdown(self):
		'''Shut me down'''
		await self.bot.say(":scream: Shutting down.")
		print("Forcing Shutdown...")
		await utilities.shutdown_tasks()
		subprocess.call(["taskkill", "/f", "/im", "cmd.exe"])
		subprocess.call(["taskkill", "/f", "/im", "python.exe"])
	
	# Testing
	
	@commands.command(hidden = True)
	async def test(self):
		'''Basic test command'''
		await self.bot.say("Hello, World!")
	
	@commands.command(hidden = True)
	@checks.is_owner()
	async def echo(self, *, message):
		'''Echoes the message'''
		await self.bot.say(message)
	
	@commands.command(hidden = True)
	@checks.is_owner()
	async def deletetest(self):
		'''Sends 100 messages'''
		for i in range(1, 101):
			await self.bot.say(str(i))
	
	@commands.command(hidden = True)
	async def loading_bar(self):
		'''
		Just for fun loading bar
		Currently does nothing.. or does it?
		'''
		counter = 0
		bar = chr(9633) * 10
		loading_message = await self.bot.say("Loading: [" + bar + "]")
		while counter <= 10:
			counter += 1
			bar = chr(9632) + bar[:-1] #9608
			await asyncio.sleep(1)
			await self.bot.edit_message(loading_message, "Loading: [" + bar + "]")

