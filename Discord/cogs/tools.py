
import discord
from discord.ext import commands

import asyncio
import concurrent.futures
import difflib
import json
import math
import matplotlib
import moviepy.editor
import multiprocessing
import numexpr
import numpy
import pandas
import random
import re
import seaborn
# import subprocess
import sympy
import time
import unicodedata
import urllib

import clients
from clients import py_code_block
from modules import utilities
from utilities import checks
from utilities import errors
from utilities import paginator

def setup(bot):
	bot.add_cog(Tools(bot))

class Tools:
	
	def __init__(self, bot):
		self.bot = bot
		clients.create_file("tags", content = {"global": {}})
		with open(clients.data_path + "/tags.json", 'r') as tags_file:
			self.tags_data = json.load(tags_file)
	
	@commands.command()
	@checks.not_forbidden()
	async def add(self, ctx, *numbers : float):
		'''Add numbers together'''
		if not numbers:
			await ctx.embed_reply("Add what?")
			return
		await ctx.embed_reply("{} = {:g}".format(" + ".join("{:g}".format(number) for number in numbers), sum(numbers)))
	
	@commands.command(aliases = ["calc", "calculator"])
	@checks.not_forbidden()
	async def calculate(self, ctx, *, equation : str):
		'''Calculator'''
		#_equation = re.sub("[^[0-9]+-/*^%\.]", "", equation).replace('^', "**") #words
		replacements = {"pi" : "math.pi", 'e' : "math.e", "sin" : "math.sin", "cos" : "math.cos", "tan" : "math.tan", '^' : "**"}
		allowed = set("0123456789.+-*/^%()")
		for key, value in replacements.items():
			equation = equation.replace(key, value)
		equation = "".join(character for character in equation if character in allowed)
		print("Calculated " + equation)
		with multiprocessing.Pool(1) as pool:
			async_result = pool.apply_async(eval, (equation,))
			future = self.bot.loop.run_in_executor(None, async_result.get, 10.0)
			try:
				result = await asyncio.wait_for(future, 10.0, loop = self.bot.loop)
				await ctx.embed_reply("{} = {}".format(equation, result))
			except discord.errors.HTTPException:
				await ctx.embed_reply(":no_entry: Output too long")
			except SyntaxError:
				await ctx.embed_reply(":no_entry: Syntax error")
			except ZeroDivisionError:
				await ctx.embed_reply(":no_entry: Error: Division by zero")
			except (concurrent.futures.TimeoutError, multiprocessing.context.TimeoutError):
				await ctx.embed_reply(":no_entry: Execution exceeded time limit")
	
	@commands.command(aliases = ["differ", "derivative", "differentiation"])
	@checks.not_forbidden()
	async def differentiate(self, ctx, *, equation : str):
		'''
		Differentiate an equation
		with respect to x (dx)
		'''
		x = sympy.symbols('x')
		try:
			await ctx.embed_reply("`{}`".format(sympy.diff(equation.strip('`'), x)), title = "Derivative of {}".format(equation))
		except Exception as e:
			await ctx.embed_reply(py_code_block.format("{}: {}".format(type(e).__name__, e)), title = "Error")
	
	@commands.group(aliases = ["integral", "integration"], invoke_without_command = True)
	@checks.not_forbidden()
	async def integrate(self, ctx, *, equation : str):
		'''
		Integrate an equation
		with respect to x (dx)
		'''
		x = sympy.symbols('x')
		try:
			await ctx.embed_reply("`{}`".format(sympy.integrate(equation.strip('`'), x)), title = "Integral of {}".format(equation))
		except Exception as e:
			await ctx.embed_reply(py_code_block.format("{}: {}".format(type(e).__name__, e)), title = "Error")
	
	@integrate.command(name = "definite")
	@checks.not_forbidden()
	async def integrate_definite(self, ctx, lower_limit : str, upper_limit : str, *, equation : str):
		'''
		Definite integral of an equation
		with respect to x (dx)
		'''
		x = sympy.symbols('x')
		try:
			await ctx.embed_reply("`{}`".format(sympy.integrate(equation.strip('`'), (x, lower_limit, upper_limit))), title = "Definite Integral of {} from {} to {}".format(equation, lower_limit, upper_limit))
		except Exception as e:
			await ctx.embed_reply(py_code_block.format("{}: {}".format(type(e).__name__, e)), title = "Error")
	
	@commands.command(aliases = ["charinfo", "char_info", "character_info"])
	@checks.not_forbidden()
	async def characterinfo(self, ctx, character : str):
		'''Information about a unicode character'''
		character = character[0]
		# TODO: return info on each character in the input string; use paste tool api?
		try:
			name = unicodedata.name(character)
		except ValueError:
			name = "UNKNOWN"
		hex_char = hex(ord(character))
		url = "http://www.fileformat.info/info/unicode/char/{}/index.htm".format(hex_char[2:])
		await ctx.embed_reply("`{} ({})`".format(character, hex_char), title = name, title_url = url)
	
	@commands.command(aliases = ["choice", "pick"])
	@checks.not_forbidden()
	async def choose(self, ctx, *choices : str):
		'''
		Randomly chooses between multiple options
		choose <option1> <option2> <...>
		'''
		if not choices:
			await ctx.embed_reply("Choose between what?")
			return
		await ctx.embed_reply(random.choice(choices))
	
	@commands.command(aliases = ["flip"])
	@checks.not_forbidden()
	async def coin(self, ctx):
		'''Flip a coin'''
		await ctx.embed_reply(random.choice(["Heads!", "Tails!"]))
	
	@commands.group(aliases = ["plot"], invoke_without_command = True)
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
			await self.bot.reply(py_code_block.format("{}: {}".format(type(e).__name__, e)))
			return
		try:
			matplotlib.pyplot.plot(x, y)
		except ValueError as e:
			await ctx.embed_reply(":no_entry: Error: {}".format(e))
			return
		matplotlib.pyplot.savefig(filename)
		matplotlib.pyplot.clf()
		await self.bot.send_file(destination = ctx.channel, fp = filename, content = ctx.author.display_name + ':')
		# TODO: Send as embed?
	
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
	@checks.is_owner()
	async def graph_alternative(self, ctx, *, data : str):
		'''WIP'''
		filename = clients.data_path + "/temp/graph_alternative.png"
		seaborn.jointplot(**eval(data)).savefig(name)
		await self.bot.send_file(destination = ctx.channel, fp = filename, content = ctx.author.display_name + ':')
	
	@commands.group(aliases = ["trigger", "note", "tags", "triggers", "notes"], invoke_without_command = True)
	@checks.not_forbidden()
	async def tag(self, ctx, tag : str = ""):
		'''Tags/notes that you can trigger later'''
		if not tag:
			await ctx.embed_reply("Add a tag with `{0}tag add [tag] [content]`\nUse `{0}tag [tag]` to trigger the tag you added\n`{0}tag edit [tag] [content]` to edit it and `{0}tag delete [tag]` to delete it".format(ctx.prefix))
			return
		if tag in self.tags_data.get(ctx.author.id, {}).get("tags", []):
			await self.bot.reply(self.tags_data[ctx.author.id]["tags"][tag])
		elif tag in self.tags_data["global"]:
			await self.bot.reply(self.tags_data["global"][tag]["response"])
			self.tags_data["global"][tag]["usage_counter"] += 1
			with open(clients.data_path + "/tags.json", 'w') as tags_file:
				json.dump(self.tags_data, tags_file, indent = 4)
		else:
			close_matches = difflib.get_close_matches(tag, list(self.tags_data.get(ctx.author.id, {}).get("tags", {}).keys()) + list(self.tags_data["global"].keys()))
			close_matches = "\nDid you mean:\n{}".format('\n'.join(close_matches)) if close_matches else ""
			await ctx.embed_reply("Tag not found{}".format(close_matches))
	
	@tag.command(name = "list", aliases = ["all", "mine"])
	async def tag_list(self, ctx):
		'''List your tags'''
		if (await self.check_no_tags(ctx)): return
		tags_paginator = paginator.CustomPaginator(seperator = ", ")
		for tag in sorted(self.tags_data[ctx.author.id]["tags"].keys()):
			tags_paginator.add_section(tag)
		# DM
		for page in tags_paginator.pages:
			await ctx.embed_reply(page, title = "Your tags:")
	
	@tag.command(name = "add", aliases = ["make", "new", "create"])
	async def tag_add(self, ctx, tag : str, *, content : str):
		'''Add a tag'''
		if not ctx.author.id in self.tags_data:
			self.tags_data[ctx.author.id] = {"name" : ctx.author.name, "tags" : {}}
		tags = self.tags_data[ctx.author.id]["tags"]
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
		self.tags_data[ctx.author.id]["tags"][tag] = utilities.clean_content(content)
		with open(clients.data_path + "/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await ctx.embed_reply(":ok_hand::skin-tone-2: Your tag has been edited")
	
	@tag.command(name = "delete", aliases = ["remove", "destroy"])
	async def tag_delete(self, ctx, tag : str):
		'''Delete one of your tags'''
		if (await self.check_no_tags(ctx)): return
		if (await self.check_no_tag(ctx, tag)): return
		try:
			del self.tags_data[ctx.author.id]["tags"][tag]
		except KeyError:
			await ctx.embed_reply(":no_entry: Tag not found")
			return
		with open(clients.data_path + "/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await ctx.embed_reply(":ok_hand::skin-tone-2: Your tag has been deleted")
	
	@tag.command(name = "expunge", pass_context = True)
	@checks.is_owner()
	async def tag_expunge(self, ctx, owner : discord.Member, tag : str):
		'''Delete someone else's tags'''
		try:
			del self.tags_data[owner.id]["tags"][tag]
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
		tags = self.tags_data[ctx.author.id]["tags"]
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
		self.tags_data["global"][tag] = {"response": self.tags_data[ctx.author.id]["tags"][tag], "owner": ctx.author.id, "created_at": time.time(), "usage_counter": 0}
		del self.tags_data[ctx.author.id]["tags"][tag]
		with open(clients.data_path + "/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await ctx.embed_reply(":thumbsup::skin-tone-2: Your tag has been {}d".format(ctx.invoked_with))
	
	# TODO: rename, aliases
	
	@tag.group(name = "global", invoke_without_command = True)
	async def tag_global(self, ctx):
		'''Global tags'''
		await ctx.invoke(self.bot.get_command("help"), "tag", ctx.invoked_with)
	
	@tag_global.command(name = "add", aliases = ["make", "new", "create"])
	async def tag_global_add(self, ctx, tag : str, *, content : str):
		'''Add a global tag'''
		tags = self.tags_data["global"]
		if tag in tags:
			await ctx.embed_reply("That global tag already exists\nIf you own it, use `{}tag global edit <tag> <content>` to edit it".format(ctx.prefix))
			return
		tags[tag] = {"response": utilities.clean_content(content), "owner": ctx.author.id, "created_at": time.time(), "usage_counter": 0}
		with open(clients.data_path + "/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await ctx.embed_reply(":thumbsup::skin-tone-2: Your tag has been added")
	
	@tag_global.command(name = "edit", aliases = ["update"])
	async def tag_global_edit(self, ctx, tag : str, *, content : str):
		'''Edit one of your global tags'''
		if tag not in self.tags_data["global"]:
			await ctx.embed_reply(":no_entry: That global tag doesn't exist")
			return
		elif self.tags_data["global"][tag]["owner"] != ctx.author.id:
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
		elif self.tags_data["global"][tag]["owner"] != ctx.author.id:
			await ctx.embed_reply(":no_entry: You don't own that global tag")
			return
		del self.tags_data["global"][tag]
		with open(clients.data_path + "/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await ctx.embed_reply(":ok_hand::skin-tone-2: Your tag has been deleted")
	
	# TODO: global search, list?
	
	async def check_no_tags(self, ctx):
		if not ctx.author.id in self.tags_data:
			await ctx.embed_reply("You don't have any tags :slight_frown:\nAdd one with `{}{} add <tag> <content>`".format(ctx.prefix, ctx.invoked_with))
		return not ctx.author.id in self.tags_data
	
	async def check_no_tag(self, ctx, tag):
		tags = self.tags_data[ctx.author.id]["tags"]
		if not tag in tags:
			close_matches = difflib.get_close_matches(tag, tags.keys())
			close_matches = "\nDid you mean:\n{}".format('\n'.join(close_matches)) if close_matches else ""
			await ctx.embed_reply("You don't have that tag{}".format(close_matches))
		return not tag in tags
	
	@commands.command()
	@checks.not_forbidden()
	async def timer(self, ctx, seconds : int):
		'''Timer'''
		# TODO: other units, persistence through restarts
		await ctx.embed_reply("I'll remind you in {} seconds".format(seconds))
		await asyncio.sleep(seconds)
		await self.bot.say("{}: {} seconds have passed".format(ctx.author.mention, seconds))
	
	@commands.command(hidden = True)
	@checks.not_forbidden()
	async def webmtogif(self, ctx, url : str):
		'''
		Convert webm to gif files
		Only converts at 1 fps
		See http://imgur.com/vidgif instead
		'''
		webmfile = urllib.request.urlretrieve(url, clients.data_path + "/temp/webmtogif.webm")
		# subprocess.call(["ffmpeg", "-i", clients.data_path + "/temp/webmtogif.webm", "-pix_fmt", "rgb8", clients.data_path + "/temp/webmtogif.gif"], shell=True)
		clip = moviepy.editor.VideoFileClip(clients.data_path + "/temp/webmtogif.webm")
		clip.write_gif(clients.data_path + "/temp/webmtogif.gif", fps = 1, program = "ffmpeg")
		# clip.write_gif(clients.data_path + "/temp/webmtogif.gif", fps=15, program="ImageMagick", opt="optimizeplus")
		await self.bot.send_file(ctx.channel, clients.data_path + "/temp/webmtogif.gif")

