
import discord
from discord.ext import commands

from utilities import errors

class Context(commands.Context):
	
	def embed_reply(self, *args, **kwargs):
		return self.embed_say(*args, author_name = self.author.display_name, author_icon_url = self.author.avatar_url, **kwargs)
	
	# TODO: optimize/improve clarity
	async def embed_say(self, description = None, *args, title = discord.Embed.Empty, title_url = discord.Embed.Empty, 
	author_name = "", author_url = discord.Embed.Empty, author_icon_url = discord.Embed.Empty, 
	image_url = None, thumbnail_url = None, footer_text = discord.Embed.Empty, footer_icon_url = discord.Embed.Empty, 
	timestamp = discord.Embed.Empty, fields = [], in_response_to = True, attempt_delete = True, **kwargs):
		embed = discord.Embed(title = title, url = title_url, timestamp = timestamp, color = self.bot.bot_color)
		embed.description = str(description) if description else discord.Embed.Empty
		if author_name: embed.set_author(name = author_name, url = author_url, icon_url = author_icon_url)
		if image_url: embed.set_image(url = image_url)
		if thumbnail_url: embed.set_thumbnail(url = thumbnail_url)
		embed.set_footer(text = footer_text, icon_url = footer_icon_url)
		if footer_text == discord.Embed.Empty and in_response_to: embed.set_footer(text = "In response to: {}".format(self.message.clean_content), icon_url = footer_icon_url)
		elif in_response_to and not args: args = ("In response to: `{}`".format(self.message.clean_content),)
		for field in fields:
			if len(field) >= 3:
				embed.add_field(name = field[0], value = field[1], inline = field[2])
			else:
				embed.add_field(name = field[0], value = field[1])
		if isinstance(self.channel, discord.DMChannel) or getattr(self.channel.permissions_for(self.channel.guild.me), "embed_links", None):
			message = await self.send(*args, embed = embed, **kwargs)
		elif not (title or title_url or image_url or thumbnail_url or footer_text or footer_icon_url or timestamp or fields):
			message = await self.reply(description)
			# TODO: Check for everyone/here mentions
		else:
			raise errors.MissingCapability(["embed_links"])
		if attempt_delete: await self.bot.attempt_delete_message(self.message)
		return message
	
	def reply(self, content, *args, **kwargs):
		return self.send("{0.display_name}: {1}".format(self.author, content), **kwargs)
	
	def whisper(self, *args, **kwargs):
		return self.author.send(*args, **kwargs)

