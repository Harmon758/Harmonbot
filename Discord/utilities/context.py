
import discord
from discord.ext import commands

from operator import attrgetter

class Context(commands.Context):
	
	async def embed_reply(
		self, *args, in_response_to = True, attempt_delete = True, **kwargs
	):
		if not self.interaction:
			if not (
				author_used := (
					"author_name" in kwargs or "author_icon_url" in kwargs
				)
			):
				kwargs["author_name"] = self.author.display_name
				kwargs["author_icon_url"] = self.author.display_avatar.url
			
			if in_response_to:
				in_response_to_text = "In response to"
				
				if "footer_text" not in kwargs:
					if author_used:
						in_response_to_text += (
							f" {self.author} ({self.author.id})"
						)
					
					kwargs["footer_text"] = (
						f"{in_response_to_text}: {self.message.clean_content}"
					)
				elif len(args) < 2 and "content" not in kwargs:
					if author_used:
						in_response_to_text += f" {self.author.mention}"
						if "allowed_mentions" not in kwargs:
							kwargs["allowed_mentions"] = (
								discord.AllowedMentions.none()
							)
					
					args = (
						next(iter(args), kwargs.pop("description", None)),
						f"{in_response_to_text}: "
						f"`{self.message.clean_content}`"
					)
				elif "content" in kwargs:
					if author_used:
						in_response_to_text += f" {self.author.mention}"
						if "allowed_mentions" not in kwargs:
							kwargs["allowed_mentions"] = (
								discord.AllowedMentions.none()
							)
					
					kwargs["content"] = (
						f"{in_response_to_text}: "
						f"`{self.message.clean_content}`\n"
						f"{kwargs['content']}"
					)
		
		message = await self.embed_send(*args, **kwargs)
		
		if attempt_delete and not self.interaction:
			await self.bot.attempt_delete_message(self.message)
		
		return message
	
	# TODO: optimize/improve clarity
	async def embed_send(
		self, description = None, *args, title = None, title_url = None,
		author_name = "", author_url = None, author_icon_url = None,
		image_url = None, thumbnail_url = None, footer_text = None,
		footer_icon_url = None, timestamp = None, fields = [], color = None,
		embeds = [], **kwargs
	):
		embed = discord.Embed(
			title = title, url = title_url, timestamp = timestamp,
			color = color or self.bot.bot_color
		)
		embed.description = str(description) if description else None
		if author_name:
			embed.set_author(
				name = author_name, url = author_url,
				icon_url = author_icon_url
			)
		if image_url:
			embed.set_image(url = image_url)
		if thumbnail_url:
			embed.set_thumbnail(url = thumbnail_url)
		embed.set_footer(text = footer_text, icon_url = footer_icon_url)
		for field in fields:
			if len(field) >= 3:
				embed.add_field(
					name = field[0], value = field[1], inline = field[2]
				)
			else:
				embed.add_field(name = field[0], value = field[1])
		if (
			self.channel.type is discord.ChannelType.private or
			getattr(
				self.channel.permissions_for(self.channel.guild.me),
				"embed_links", None
			)
		):
			if embeds:
				embeds.insert(0, embed)
				return await self.send(*args, embeds = embeds, **kwargs)
			else:
				return await self.send(*args, embed = embed, **kwargs)
		elif (
			not (
				title or title_url or image_url or thumbnail_url or
				footer_icon_url or timestamp or fields or embeds
			) and (
				not footer_text or footer_text.startswith("In response to")
			)
		):
			return await self.reply(
				str(description),
				allowed_mentions = discord.AllowedMentions.none()
			)
		else:
			raise commands.BotMissingPermissions(["embed_links"])
	
	async def reply(self, content, *args, **kwargs):
		if self.interaction:
			return await self.send(content, **kwargs)
		else:
			if "allowed_mentions" not in kwargs:
				kwargs["allowed_mentions"] = discord.AllowedMentions.none()
			message = await self.send(
				f"In response to {self.author.mention}: "
				f"`{self.message.clean_content}`\n{content}",
				**kwargs
			)
			await self.bot.attempt_delete_message(self.message)
			return message
	
	def whisper(self, *args, **kwargs):
		return self.author.send(*args, **kwargs)
	
	# TODO: Improve
	async def get_permission(self, permission, *, type = "user", user = None, id = None):
		if not self.guild:
			return True
		role_ids = []
		if type == "user":
			if user:
				id = user.id
			user_setting  = await self.bot.db.fetchval(
				"""
				SELECT setting FROM permissions.users
				WHERE guild_id = $1 AND user_id = $2 AND permission = $3
				""", 
				self.guild.id, id, permission
			)
			if user_setting is not None:
				return user_setting
			if not user:
				user = self.guild.get_member(id)
			role_ids.extend(role.id for role in sorted(user.roles, key = attrgetter("position"), reverse = True))
		elif type == "role":
			role_ids.append(id)
		for role_id in role_ids:
			role_setting = await self.bot.db.fetchval(
				"""
				SELECT setting FROM permissions.roles
				WHERE guild_id = $1 AND role_id = $2 AND permission = $3
				""", 
				self.guild.id, role_id, permission
			)
			if role_setting is not None:
				return role_setting
		return await self.bot.db.fetchval(
			"""
			SELECT setting FROM permissions.everyone
			WHERE guild_id = $1 AND permission = $2
			""", 
			self.guild.id, permission
		)

