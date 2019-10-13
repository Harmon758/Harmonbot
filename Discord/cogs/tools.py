
import discord
from discord.ext import commands

import asyncio
import difflib
import imageio
import json
import matplotlib
import numexpr
import numpy
import pandas
from PIL import Image, ImageDraw, ImageFont
import re
import seaborn
import textwrap
import time

import clients
from modules import utilities
from utilities import checks
from utilities import paginator

def setup(bot):
	bot.add_cog(Tools(bot))

class Tools(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		clients.create_file("tags", content = {"global": {}})
		with open(clients.data_path + "/tags.json", 'r') as tags_file:
			self.tags_data = json.load(tags_file)
	
	@commands.group(aliases = ["plot"], invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def graph(self, ctx, lower_limit : int, upper_limit : int, *, equation : str):
		'''WIP'''
		filename = clients.data_path + "/temp/graph.png"
		try:
			equation = self.string_to_equation(equation)
		except SyntaxError as e:
			await ctx.embed_reply(":no_entry: Error: {}".format(e))
			return
		x = numpy.linspace(lower_limit, upper_limit, 250)
		try:
			y = numexpr.evaluate(equation)
		except Exception as e:
			await ctx.reply(ctx.bot.PY_CODE_BLOCK.format("{}: {}".format(type(e).__name__, e)))
			return
		try:
			matplotlib.pyplot.plot(x, y)
		except ValueError as e:
			await ctx.embed_reply(":no_entry: Error: {}".format(e))
			return
		matplotlib.pyplot.savefig(filename)
		matplotlib.pyplot.clf()
		await ctx.embed_reply(image_url = "attachment://graph.png", file = discord.File(filename))
	
	def string_to_equation(self, string):
		replacements = {'^': "**"}
		allowed_words = ('x', "sin", "cos", "tan", "arcsin", "arccos", "arctan", "arctan2", "sinh", "cosh", "tanh", "arcsinh", "arccosh", "arctanh", "log", "log10", "log1p", "exp", "expm1", "sqrt", "abs", "conj", "complex")
		for word in re.findall("[a-zA-Z_]+", string):
			if word not in allowed_words:
				raise SyntaxError("`{}` is not supported".format(word))
		for old, new in replacements.items():
			string = string.replace(old, new)
		return string
	
	@graph.command(name = "alternative", aliases = ["alt", "complex"])
	@commands.is_owner()
	async def graph_alternative(self, ctx, *, data : str):
		'''WIP'''
		filename = clients.data_path + "/temp/graph_alternative.png"
		seaborn.jointplot(**eval(data)).savefig(filename)
		await ctx.channel.send(file = discord.File(filename), content = ctx.author.display_name + ':')
	
	@commands.command(aliases = ["spoil"], hidden = True)
	@checks.not_forbidden()
	async def spoiler(self, ctx, name : str, *, text : str):
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
		await ctx.author.avatar_url.save(self.bot.data_path + "/temp/spoiler_avatar.png")
		avatar = Image.open(self.bot.data_path + "/temp/spoiler_avatar.png")
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
		for frame_number, frame_text in zip(range(1, 3), (spoiler_title, spoiler_text)):
			frame = Image.new("RGBA", 
								(text_width + (avatar_size + 2 * margin_size) * 2, text_height + text_vertical_margin * 2), 
								discord.Color(self.bot.dark_theme_background_color).to_rgb())
			try:
				frame.paste(avatar, (margin_size, margin_size), avatar)
			except ValueError:  # if bad transparency mask
				frame.paste(avatar, (margin_size, margin_size))
			transparent_text = Image.new("RGBA", frame.size, discord.Color(self.bot.white_color).to_rgb() + (0,))
			draw = ImageDraw.Draw(transparent_text)
			draw.text((avatar_size + 2 * margin_size, text_vertical_margin), frame_text, 
						fill = discord.Color(self.bot.white_color).to_rgb() + (text_opacity,), 
						font = content_font)
			if frame_number == 1:
				draw.text((avatar_size + 2 * margin_size, text_height + 2 * margin_size), 
							"(Hover to reveal spoiler)", font = guide_font, 
							fill = discord.Color(self.bot.white_color).to_rgb() + (text_opacity,))
			frame = Image.alpha_composite(frame, transparent_text)
			frame.save(f"{self.bot.data_path}/temp/spoiler_frame_{frame_number}.png")
		# Create + send .gif
		images = [imageio.imread(f) for f in [f"{self.bot.data_path}/temp/spoiler_frame_{i}.png" for i in range(1, 3)]]
		imageio.mimsave(self.bot.data_path + "/temp/spoiler.gif", images, loop = 1, duration = 0.5)
		await ctx.channel.send(file = discord.File(self.bot.data_path + "/temp/spoiler.gif"))
		await self.bot.attempt_delete_message(response)
	
	@commands.group(aliases = ["trigger", "note", "tags", "triggers", "notes"], 
					invoke_without_command = True, case_insensitive = True)
	@checks.not_forbidden()
	async def tag(self, ctx, tag : str = ""):
		'''Tags/notes that you can trigger later'''
		if not tag:
			await ctx.embed_reply("Add a tag with `{0}tag add [tag] [content]`\nUse `{0}tag [tag]` to trigger the tag you added\n`{0}tag edit [tag] [content]` to edit it and `{0}tag delete [tag]` to delete it".format(ctx.prefix))
			return
		if tag in self.tags_data.get(str(ctx.author.id), {}).get("tags", []):
			await ctx.reply(self.tags_data[str(ctx.author.id)]["tags"][tag])
		elif tag in self.tags_data["global"]:
			await ctx.reply(self.tags_data["global"][tag]["response"])
			self.tags_data["global"][tag]["usage_counter"] += 1
			with open(clients.data_path + "/tags.json", 'w') as tags_file:
				json.dump(self.tags_data, tags_file, indent = 4)
		else:
			close_matches = difflib.get_close_matches(tag, list(self.tags_data.get(str(ctx.author.id), {}).get("tags", {}).keys()) + list(self.tags_data["global"].keys()))
			close_matches = "\nDid you mean:\n{}".format('\n'.join(close_matches)) if close_matches else ""
			await ctx.embed_reply("Tag not found{}".format(close_matches))
	
	@tag.command(name = "list", aliases = ["all", "mine"])
	async def tag_list(self, ctx):
		'''List your tags'''
		if (await self.check_no_tags(ctx)): return
		tags_paginator = paginator.CustomPaginator(seperator = ", ")
		for tag in sorted(self.tags_data[str(ctx.author.id)]["tags"].keys()):
			tags_paginator.add_section(tag)
		# DM
		for page in tags_paginator.pages:
			await ctx.embed_reply(page, title = "Your tags:")
	
	@tag.command(name = "add", aliases = ["make", "new", "create"])
	async def tag_add(self, ctx, tag : str, *, content : str):
		'''Add a tag'''
		if not str(ctx.author.id) in self.tags_data:
			self.tags_data[str(ctx.author.id)] = {"name" : ctx.author.name, "tags" : {}}
		tags = self.tags_data[str(ctx.author.id)]["tags"]
		if tag in tags:
			await ctx.embed_reply("You already have that tag\nUse `{}tag edit <tag> <content>` to edit it".format(ctx.prefix))
			return
		tags[tag] = utilities.clean_content(content)
		with open(clients.data_path + "/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await ctx.embed_reply(":thumbsup::skin-tone-2: Your tag has been added")
	
	@tag.command(name = "edit", aliases = ["update"])
	async def tag_edit(self, ctx, tag : str, *, content : str):
		'''Edit one of your tags'''
		if (await self.check_no_tags(ctx)): return
		if (await self.check_no_tag(ctx, tag)): return
		self.tags_data[str(ctx.author.id)]["tags"][tag] = utilities.clean_content(content)
		with open(clients.data_path + "/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await ctx.embed_reply(":ok_hand::skin-tone-2: Your tag has been edited")
	
	@tag.command(name = "delete", aliases = ["remove", "destroy"])
	async def tag_delete(self, ctx, tag : str):
		'''Delete one of your tags'''
		if (await self.check_no_tags(ctx)): return
		if (await self.check_no_tag(ctx, tag)): return
		try:
			del self.tags_data[str(ctx.author.id)]["tags"][tag]
		except KeyError:
			await ctx.embed_reply(":no_entry: Tag not found")
			return
		with open(clients.data_path + "/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await ctx.embed_reply(":ok_hand::skin-tone-2: Your tag has been deleted")
	
	@tag.command(name = "expunge")
	@commands.is_owner()
	async def tag_expunge(self, ctx, owner : discord.Member, tag : str):
		'''Delete someone else's tags'''
		try:
			del self.tags_data[str(owner.id)]["tags"][tag]
		except KeyError:
			await ctx.embed_reply(":no_entry: Tag not found")
			return
		with open(clients.data_path + "/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await ctx.embed_reply(":ok_hand::skin-tone-2: {}'s tag has been deleted".format(owner.mention))
	
	@tag.command(name = "search", aliases = ["contains", "find"])
	async def tag_search(self, ctx, *, search : str):
		'''Search your tags'''
		if (await self.check_no_tags(ctx)): return
		tags = self.tags_data[str(ctx.author.id)]["tags"]
		results = [t for t in tags.keys() if search in t]
		if results:
			await ctx.embed_reply("{} tags found: {}".format(len(results), ", ".join(results)))
			return
		close_matches = difflib.get_close_matches(search, tags.keys())
		close_matches = "\nDid you mean:\n{}".format('\n'.join(close_matches)) if close_matches else ""
		await ctx.embed_reply("No tags found{}".format(close_matches))
	
	@tag.command(name = "globalize", aliases = ["globalise"])
	async def tag_globalize(self, ctx, tag : str):
		'''Globalize a tag'''
		if (await self.check_no_tags(ctx)): return
		if (await self.check_no_tag(ctx, tag)): return
		if tag in self.tags_data["global"]:
			await ctx.embed_reply("That global tag already exists\nIf you own it, use `{}tag global edit <tag> <content>` to edit it".format(ctx.prefix))
			return
		self.tags_data["global"][tag] = {"response": self.tags_data[str(ctx.author.id)]["tags"][tag], "owner": str(ctx.author.id), "created_at": time.time(), "usage_counter": 0}
		del self.tags_data[str(ctx.author.id)]["tags"][tag]
		with open(clients.data_path + "/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await ctx.embed_reply(":thumbsup::skin-tone-2: Your tag has been {}d".format(ctx.invoked_with))
	
	# TODO: rename, aliases
	
	@tag.group(name = "global", invoke_without_command = True, case_insensitive = True)
	async def tag_global(self, ctx):
		'''Global tags'''
		await ctx.send_help(ctx.command)
	
	@tag_global.command(name = "add", aliases = ["make", "new", "create"])
	async def tag_global_add(self, ctx, tag : str, *, content : str):
		'''Add a global tag'''
		tags = self.tags_data["global"]
		if tag in tags:
			await ctx.embed_reply("That global tag already exists\nIf you own it, use `{}tag global edit <tag> <content>` to edit it".format(ctx.prefix))
			return
		tags[tag] = {"response": utilities.clean_content(content), "owner": str(ctx.author.id), "created_at": time.time(), "usage_counter": 0}
		with open(clients.data_path + "/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await ctx.embed_reply(":thumbsup::skin-tone-2: Your tag has been added")
	
	@tag_global.command(name = "edit", aliases = ["update"])
	async def tag_global_edit(self, ctx, tag : str, *, content : str):
		'''Edit one of your global tags'''
		if tag not in self.tags_data["global"]:
			await ctx.embed_reply(":no_entry: That global tag doesn't exist")
			return
		elif self.tags_data["global"][tag]["owner"] != str(ctx.author.id):
			await ctx.embed_reply(":no_entry: You don't own that global tag")
			return
		self.tags_data["global"][tag]["response"] = utilities.clean_content(content)
		with open(clients.data_path + "/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await ctx.embed_reply(":ok_hand::skin-tone-2: Your tag has been edited")
	
	@tag_global.command(name = "delete", aliases = ["remove", "destroy"])
	async def tag_global_delete(self, ctx, tag : str):
		'''Delete one of your global tags'''
		if tag not in self.tags_data["global"]:
			await ctx.embed_reply(":no_entry: That global tag doesn't exist")
			return
		elif self.tags_data["global"][tag]["owner"] != str(ctx.author.id):
			await ctx.embed_reply(":no_entry: You don't own that global tag")
			return
		del self.tags_data["global"][tag]
		with open(clients.data_path + "/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await ctx.embed_reply(":ok_hand::skin-tone-2: Your tag has been deleted")
	
	# TODO: global search, list?
	
	async def check_no_tags(self, ctx):
		no_tags = str(ctx.author.id) not in self.tags_data or not self.tags_data[str(ctx.author.id)]["tags"]
		if no_tags:
			await ctx.embed_reply("You don't have any tags :slight_frown:\nAdd one with `{}{} add <tag> <content>`".format(ctx.prefix, ctx.invoked_with))
			# TODO: Fix invoked_with for subcommands
		return no_tags
	
	async def check_no_tag(self, ctx, tag):
		tags = self.tags_data[str(ctx.author.id)]["tags"]
		if tag not in tags:
			close_matches = difflib.get_close_matches(tag, tags.keys())
			close_matches = "\nDid you mean:\n{}".format('\n'.join(close_matches)) if close_matches else ""
			await ctx.embed_reply("You don't have that tag{}".format(close_matches))
		return tag not in tags
	
	@commands.command()
	@checks.not_forbidden()
	async def timer(self, ctx, seconds : int):
		'''Timer'''
		# TODO: other units, persistence through restarts
		await ctx.embed_reply("I'll remind you in {} seconds".format(seconds))
		await asyncio.sleep(seconds)
		await ctx.send("{}: {} seconds have passed".format(ctx.author.mention, seconds))
	
	@commands.command(hidden = True)
	@checks.not_forbidden()
	async def webmtogif(self, ctx):
		'''
		This command has been deprecated
		See https://imgur.com/vidgif instead
		'''
		await ctx.embed_reply("See https://imgur.com/vidgif")

