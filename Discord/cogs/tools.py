
import discord
from discord.ext import commands

import difflib
import io
import re
import textwrap

import imageio
import matplotlib
import numexpr
import numpy
import pandas
from PIL import Image, ImageDraw, ImageFont
import seaborn

from utilities import checks
from utilities.paginators import Paginator

async def setup(bot):
	await bot.add_cog(Tools(bot))

class Tools(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
	
	async def cog_load(self):
		await self.bot.connect_to_database()
		await self.bot.db.execute("CREATE SCHEMA IF NOT EXISTS tags")
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS tags.global (
				tag			TEXT PRIMARY KEY, 
				content		TEXT, 
				created_at	TIMESTAMPTZ, 
				owner_id	BIGINT, 
				uses		INT
			)
			"""
		)
		await self.bot.db.execute(
			"""
			CREATE TABLE IF NOT EXISTS tags.individual (
				user_id			BIGINT, 
				tag				TEXT, 
				content			TEXT, 
				PRIMARY KEY		(user_id, tag)
			)
			"""
		)
	
	@commands.hybrid_command(aliases = ["plot"])
	@checks.not_forbidden()
	async def graph(
		self, ctx, lower_limit: int, upper_limit: int, *, equation: str
	):
		"""
		Generate a graph
		
		Parameters
		----------
		lower_limit
			The lower limit of x for the graph
		upper_limit
			The upper limit of x for the graph
		equation
			The equation/expression y = in terms of x
		"""
		equation = equation.lstrip("y =")
		
		try:
			equation = self.string_to_equation(equation)
		except SyntaxError as e:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")
			return
		
		x = numpy.linspace(lower_limit, upper_limit, 250)
		
		try:
			y = numexpr.evaluate(equation)
		except Exception as e:
			await ctx.reply(
				ctx.bot.PY_CODE_BLOCK.format(f"{type(e).__name__}: {e}")
			)
			return
		
		figure = matplotlib.figure.Figure()
		axes = figure.add_subplot()
		try:
			axes.plot(x, y)
		except ValueError as e:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")
			return
		
		buffer = io.BytesIO()
		figure.savefig(buffer, format = "PNG")
		buffer.seek(0)
		await ctx.embed_reply(
			image_url = "attachment://graph.png", 
			file = discord.File(buffer, filename = "graph.png")
		)
	
	def string_to_equation(self, string):
		replacements = {'^': "**"}
		allowed_words = (
			'x', "sin", "cos", "tan", "arcsin", "arccos", "arctan", "arctan2",
			"sinh", "cosh", "tanh", "arcsinh", "arccosh", "arctanh", "log",
			"log10", "log1p", "exp", "expm1", "sqrt", "abs", "conj", "complex"
		)
		for word in re.findall("[a-zA-Z_]+", string):
			if word not in allowed_words:
				raise SyntaxError(f"`{word}` is not supported")
		for old, new in replacements.items():
			string = string.replace(old, new)
		return string
	
	@commands.command(aliases = ["graph_alt", "graph_complex"])
	@commands.is_owner()
	async def graph_alternative(self, ctx, *, data : str):
		'''WIP'''
		buffer = io.BytesIO()
		seaborn.jointplot(**eval(data)).savefig(buffer, format = "PNG")
		buffer.seek(0)
		await ctx.embed_reply(image_url = "attachment://graph.png", 
								file = discord.File(buffer, filename = "graph.png"))
	
	@commands.command(aliases = ["spoil"], hidden = True)
	@checks.not_forbidden()
	async def spoiler(self, ctx, name: str, *, text: str):
		'''
		Spoiler GIF
		This command is now deprecated, as Discord now has native [spoiler tags](https://support.discordapp.com/hc/en-us/articles/360022320632-Spoiler-Tags-)
		Make sure you have the "Automatically play GIFs when Discord is focused." setting off
		Otherwise, the spoiler will automatically be displayed
		This setting is under User Settings -> Text & Images
		'''
		response = await ctx.embed_reply("Generating spoiler", in_response_to = False)
		# TODO: add border?, adjust fonts?
		# Constants
		content_font = "pala.ttf"
		guide_font = "verdana.ttf"
		margin_size = 10
		avatar_size = 40
		content_font_size = 20
		guide_font_size = 10
		text_vertical_margin = 20
		text_opacity = 180  # 0-255, 180 = ~70%
		character_wrap = 55
		# Initialize values
		spoiler_text = textwrap.fill(text, character_wrap)
		spoiler_title = textwrap.fill(f"{ctx.author.display_name}'s {name} spoiler", character_wrap)
		buffer = io.BytesIO()
		await ctx.author.display_avatar.save(buffer, seek_begin = True)
		avatar = Image.open(buffer)
		avatar.thumbnail((avatar_size, avatar_size))
		content_font = ImageFont.truetype(content_font, content_font_size)
		guide_font = ImageFont.truetype(guide_font, guide_font_size)
		# Determine font width + height
		draw = ImageDraw.Draw(Image.new("1", (1, 1), 1))
		text_width, text_height = map(max, zip(*[draw.textsize(t, font = content_font) for t in (spoiler_text, spoiler_title)]))
		## use functools.partial?
		## text_width, text_height = map(max, zip(*map(functools.partial(draw.textsize, font = content_font), (spoiler_text, spoiler_title))))
		## more optimal, but doesn't handle multiline
		## text_width, text_height = map(max, zip(*map(content_font.getsize, (spoiler_text, spoiler_title))))
		# Create frames
		frames = []
		for frame_text in (spoiler_title, spoiler_text):
			frame = Image.new("RGBA", 
								(text_width + (avatar_size + 2 * margin_size) * 2, text_height + text_vertical_margin * 2), 
								discord.Color(ctx.bot.dark_theme_background_color).to_rgb())
			try:
				frame.paste(avatar, (margin_size, margin_size), avatar)
			except ValueError:  # if bad transparency mask
				frame.paste(avatar, (margin_size, margin_size))
			transparent_text = Image.new("RGBA", frame.size, discord.Color(ctx.bot.white_color).to_rgb() + (0,))
			draw = ImageDraw.Draw(transparent_text)
			draw.text((avatar_size + 2 * margin_size, text_vertical_margin), frame_text, 
						fill = discord.Color(ctx.bot.white_color).to_rgb() + (text_opacity,), 
						font = content_font)
			if not frames:
				draw.text((avatar_size + 2 * margin_size, text_height + 2 * margin_size), 
							"(Hover to reveal spoiler)", font = guide_font, 
							fill = discord.Color(ctx.bot.white_color).to_rgb() + (text_opacity,))
			frame = Image.alpha_composite(frame, transparent_text)
			buffer = io.BytesIO()
			frame.save(buffer, "PNG")
			buffer.seek(0)
			frames.append(buffer)
		# Create + send .gif
		buffer = io.BytesIO()
		imageio.mimsave(buffer, [imageio.imread(frame) for frame in frames], "GIF", loop = 1, duration = 0.5)
		buffer.seek(0)
		await ctx.channel.send(file = discord.File(buffer, filename = "spoiler.gif"))
		await ctx.bot.attempt_delete_message(response)
	
	@commands.group(aliases = ["trigger", "note", "tags", "triggers", "notes"], 
					invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def tag(self, ctx, tag: str = ""):
		'''Tags/notes that you can trigger later'''
		if not tag:
			await ctx.embed_reply("Add a tag with `{0}tag add [tag] [content]`\nUse `{0}tag [tag]` to trigger the tag you added\n`{0}tag edit [tag] [content]` to edit it and `{0}tag delete [tag]` to delete it".format(ctx.prefix))
			return
		content = await ctx.bot.db.fetchval(
			"""
			SELECT content FROM tags.individual
			WHERE user_id = $1 AND tag = $2
			""", 
			ctx.author.id, tag
		)
		if content:
			return await ctx.reply(content)
		content = await ctx.bot.db.fetchval(
			"""
			SELECT content FROM tags.global
			WHERE tag = $1
			""", 
			tag
		)
		if content:
			await ctx.reply(content)
			await ctx.bot.db.execute(
				"""
				UPDATE tags.global SET uses = uses + 1
				WHERE tag = $1
				""", 
				tag
			)
			# TODO: Optimize into single query
			return
		individual_records = await ctx.bot.db.fetch(
			"""
			SELECT tag FROM tags.individual
			WHERE user_id = $1
			""", 
			ctx.author.id
		)
		global_records = await ctx.bot.db.fetch("SELECT tag FROM tags.global")
		# TODO Optimize into single query?
		tags = [record["tag"] for record in individual_records] + [record["tag"] for record in global_records]
		close_matches = difflib.get_close_matches(tag, tags)
		close_matches = "\nDid you mean:\n{}".format('\n'.join(close_matches)) if close_matches else ""
		await ctx.embed_reply("Tag not found{}".format(close_matches))
	
	@tag.command(name = "list", aliases = ["all", "mine"])
	async def tag_list(self, ctx):
		'''List your tags'''
		if (await self.check_no_tags(ctx)): return
		tags_paginator = Paginator(seperator = ", ")
		records = await ctx.bot.db.fetch(
			"""
			SELECT tag FROM tags.individual
			WHERE user_id = $1
			""", 
			ctx.author.id
		)
		for tag in sorted(record["tag"] for record in records):
			tags_paginator.add_section(tag)
		# DM
		for page in tags_paginator.pages:
			await ctx.embed_reply(page, title = "Your tags:")
	
	@tag.command(name = "add", aliases = ["make", "new", "create"])
	async def tag_add(self, ctx, tag: str, *, content: str):
		'''Add a tag'''
		inserted = await ctx.bot.db.fetchrow(
			"""
			INSERT INTO tags.individual (user_id, tag, content)
			VALUES ($1, $2, $3)
			ON CONFLICT DO NOTHING
			RETURNING *
			""", 
			ctx.author.id, tag, discord.utils.escape_mentions(content)
		)
		if not inserted:
			return await ctx.embed_reply("You already have that tag\nUse `{}tag edit <tag> <content>` to edit it".format(ctx.prefix))
		await ctx.embed_reply(f":thumbsup:{ctx.bot.emoji_skin_tone} Your tag has been added")
	
	@tag.command(name = "edit", aliases = ["update"])
	async def tag_edit(self, ctx, tag: str, *, content: str):
		'''Edit one of your tags'''
		if (await self.check_no_tags(ctx)): return
		if (await self.check_no_tag(ctx, tag)): return
		await ctx.bot.db.execute(
			"""
			UPDATE tags.individual SET content = $3
			WHERE user_id = $1 AND tag = $2
			""", 
			ctx.author.id, tag, discord.utils.escape_mentions(content)
		)
		await ctx.embed_reply(f":ok_hand:{ctx.bot.emoji_skin_tone} Your tag has been edited")
	
	@tag.command(name = "delete", aliases = ["remove", "destroy"])
	async def tag_delete(self, ctx, tag: str):
		'''Delete one of your tags'''
		if (await self.check_no_tags(ctx)): return
		if (await self.check_no_tag(ctx, tag)): return
		deleted = await ctx.bot.db.fetchrow(
			"""
			DELETE FROM tags.individual
			WHERE user_id = $1 AND tag = $2
			RETURNING *
			""", 
			ctx.author.id, tag
		)
		if not deleted:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Tag not found")
		await ctx.embed_reply(f":ok_hand:{ctx.bot.emoji_skin_tone} Your tag has been deleted")
	
	@tag.command(name = "expunge")
	@commands.is_owner()
	async def tag_expunge(self, ctx, owner: discord.Member, tag: str):
		'''Delete someone else's tags'''
		deleted = await ctx.bot.db.fetchrow(
			"""
			DELETE FROM tags.individual
			WHERE user_id = $1 AND tag = $2
			RETURNING *
			""", 
			owner.id, tag
		)
		if not deleted:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Tag not found")
			return
		await ctx.embed_reply(f":ok_hand:{ctx.bot.emoji_skin_tone} {owner.mention}'s tag has been deleted")
	
	@tag.command(name = "search", aliases = ["contains", "find"])
	async def tag_search(self, ctx, *, search: str):
		'''Search your tags'''
		if (await self.check_no_tags(ctx)): return
		records = await ctx.bot.db.fetch(
			"""
			SELECT tag FROM tags.individual
			WHERE user_id = $1
			""", 
			ctx.author.id
		)
		tags = [record["tag"] for record in records]
		if results := [tag for tag in tags if search in tag]:
			return await ctx.embed_reply(f"{len(results)} tags found: {', '.join(results)}")
		close_matches = difflib.get_close_matches(search, tags)
		close_matches = "\nDid you mean:\n" + '\n'.join(close_matches) if close_matches else ""
		await ctx.embed_reply(f"No tags found{close_matches}")
	
	@tag.command(name = "globalize", aliases = ["globalise"])
	async def tag_globalize(self, ctx, tag: str):
		'''Globalize a tag'''
		if (await self.check_no_tags(ctx)): return
		if (await self.check_no_tag(ctx, tag)): return
		exists = await ctx.bot.db.fetchval(
			"""
			SELECT EXISTS (
				SELECT FROM tags.global
				WHERE tag = $1
			)
			""", 
			tag
		)
		if exists:
			await ctx.embed_reply(f"That global tag already exists\nIf you own it, use `{ctx.prefix}tag global edit <tag> <content>` to edit it")
			return
		deleted = await ctx.bot.db.fetchrow(
			"""
			DELETE FROM tags.individual
			WHERE user_id = $1 AND tag = $2
			RETURNING *
			""", 
			ctx.author.id, tag
		)
		await ctx.bot.db.execute(
			"""
			INSERT INTO tags.global (tag, content, created_at, owner_id, uses)
			VALUES ($1, $2, NOW(), $3, 0)
			""", 
			tag, deleted["content"], ctx.author.id
		)
		# TODO: Optimize into single query
		await ctx.embed_reply(f":thumbsup:{ctx.bot.emoji_skin_tone} Your tag has been {ctx.invoked_with}d")
	
	# TODO: rename, aliases
	
	@tag.group(name = "global", invoke_without_command = True, case_insensitive = True)
	async def tag_global(self, ctx):
		'''Global tags'''
		await ctx.send_help(ctx.command)
	
	@tag_global.command(name = "add", aliases = ["make", "new", "create"])
	async def tag_global_add(self, ctx, tag: str, *, content: str):
		'''Add a global tag'''
		inserted = await ctx.bot.db.fetchrow(
			"""
			INSERT INTO tags.global (tag, content, created_at, owner_id, uses)
			VALUES ($1, $2, NOW(), $3, 0)
			ON CONFLICT DO NOTHING
			RETURNING *
			""", 
			tag, discord.utils.escape_mentions(content), ctx.author.id
		)
		if not inserted:
			await ctx.embed_reply(f"That global tag already exists\nIf you own it, use `{ctx.prefix}tag global edit <tag> <content>` to edit it")
			return
		await ctx.embed_reply(f":thumbsup:{ctx.bot.emoji_skin_tone} Your tag has been added")
	
	@tag_global.command(name = "edit", aliases = ["update"])
	async def tag_global_edit(self, ctx, tag: str, *, content: str):
		'''Edit one of your global tags'''
		owner_id = await ctx.bot.db.fetchval(
			"""
			SELECT owner_id FROM tags.global
			WHERE tag = $1
			""", 
			tag
		)
		if not owner_id:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} That global tag doesn't exist")
			return
		elif owner_id != ctx.author.id:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} You don't own that global tag")
			return
		await ctx.bot.db.execute(
			"""
			UPDATE tags.global SET content = $2
			WHERE tag = $1
			""", 
			tag, discord.utils.escape_mentions(content)
		)
		await ctx.embed_reply(f":ok_hand:{ctx.bot.emoji_skin_tone} Your tag has been edited")
	
	@tag_global.command(name = "delete", aliases = ["remove", "destroy"])
	async def tag_global_delete(self, ctx, tag: str):
		'''Delete one of your global tags'''
		owner_id = await ctx.bot.db.fetchval(
			"""
			SELECT owner_id FROM tags.global
			WHERE tag = $1
			""", 
			tag
		)
		if not owner_id:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} That global tag doesn't exist")
			return
		elif owner_id != ctx.author.id:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} You don't own that global tag")
			return
		await ctx.bot.db.execute("DELETE FROM tags.global WHERE tag = $1", tag)
		await ctx.embed_reply(f":ok_hand:{ctx.bot.emoji_skin_tone} Your tag has been deleted")
	
	# TODO: global expunge, search, list?
	
	async def check_no_tags(self, ctx):
		exists = await ctx.bot.db.fetchval(
			"""
			SELECT EXISTS (
				SELECT FROM tags.individual
				WHERE user_id = $1
			)
			""", 
			ctx.author.id
		)
		if not exists:
			await ctx.embed_reply("You don't have any tags :slight_frown:\nAdd one with `{}{} add <tag> <content>`".format(ctx.prefix, ctx.invoked_with))
			# TODO: Fix invoked_with for subcommands
		return not exists
	
	async def check_no_tag(self, ctx, tag):
		exists = await ctx.bot.db.fetchval(
			"""
			SELECT EXISTS (
				SELECT FROM tags.individual
				WHERE user_id = $1 AND tag = $2
			)
			""", 
			ctx.author.id, tag
		)
		if not exists:
			records = await ctx.bot.db.fetch(
				"""
				SELECT tag FROM tags.individual
				WHERE user_id = $1
				""", 
				ctx.author.id
			)
			tags = [record["tag"] for record in records]
			close_matches = difflib.get_close_matches(tag, tags)
			close_matches = "\nDid you mean:\n{}".format('\n'.join(close_matches)) if close_matches else ""
			await ctx.embed_reply("You don't have that tag{}".format(close_matches))
		return not exists
	
	@commands.command(hidden = True)
	@checks.not_forbidden()
	async def webmtogif(self, ctx):
		'''
		WebM to GIF
		This command has been deprecated
		See https://imgur.com/vidgif instead
		'''
		await ctx.embed_reply("See https://imgur.com/vidgif")

