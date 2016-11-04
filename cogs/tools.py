
# import discord
from discord.ext import commands

import asyncio
import hashlib
import json
import math
# import mhashlib
import moviepy.editor
import pandas
import random
import seaborn
# import re
import sympy
import urllib
import zlib

from modules import utilities
from utilities import checks
from utilities import errors
from modules import ciphers
from clients import py_code_block

def setup(bot):
	bot.add_cog(Tools(bot))

class Tools:
	
	def __init__(self, bot):
		self.bot = bot
		self.tags_data, self.tags = None, None
		utilities.create_file("tags")
	
	@commands.command()
	@checks.not_forbidden()
	async def add(self, *numbers : float):
		'''Adds numbers together.'''
		if not numbers:
			await self.bot.reply("Add what?")
			return
		result = sum(numbers)
		if result.is_integer():
			result = int(result)
		addends = []
		for number in numbers:
			if number.is_integer():
				addends.append(str(int(number)))
			else:
				addends.append(str(number))
		await self.bot.reply(" + ".join(addends) + " = " + str(result))
	
	@commands.command(aliases = ["calc", "calculator"])
	@checks.not_forbidden()
	async def calculate(self, *, equation : str):
		'''Calculator'''
		'''
		Simple calculator
		calculate <number> <operation> <number>
		'''
		#_equation = re.sub("[^[0-9]+-/*^%\.]", "", equation).replace('^', "**") #words
		_replace = {"pi" : "math.pi", 'e' : "math.e", "sin" : "math.sin", "cos" : "math.cos", "tan" : "math.tan", '^' : "**"}
		_allowed = set("0123456789.+-*/^%()")
		_equation = equation
		for key, value in _replace.items():
			_equation = _equation.replace(key, value)
		_equation = ''.join(character for character in _equation if character in _allowed)
		print("Calculated " + _equation)
		try:
			await self.bot.reply(_equation + '=' + str(eval(_equation)))
		except:
			pass
		'''
		if len(equation) >= 3 and equation[0].isnumeric and equation[2].isnumeric and equation[1] in ['+', '-', '*', '/']:
			await self.bot.reply(' '.join(equation[:3]) + " = " + str(eval(''.join(equation[:3]))))
		else:
			await self.bot.reply("That's not a valid input.")
		'''
	
	@commands.command(aliases = ["differ", "derivative", "differentiation"])
	@checks.not_forbidden()
	async def differentiate(self, *, equation : str):
		'''
		Differentiate an equation
		with respect to x (dx)
		'''
		x = sympy.symbols('x')
		try:
			await self.bot.reply("`{}`".format(sympy.diff(equation.strip('`'), x)))
		except Exception as e:
			await self.bot.reply(py_code_block.format("{}: {}".format(type(e).__name__, e)))
	
	@commands.group(aliases = ["integral", "integration"], invoke_without_command = True)
	@checks.not_forbidden()
	async def integrate(self, *, equation : str):
		'''
		Integrate an equation
		with respect to x (dx)
		'''
		x = sympy.symbols('x')
		try:
			await self.bot.reply("`{}`".format(sympy.integrate(equation.strip('`'), x)))
		except Exception as e:
			await self.bot.reply(py_code_block.format("{}: {}".format(type(e).__name__, e)))
	
	@integrate.command(name = "definite")
	@checks.not_forbidden()
	async def integrate_definite(self, lower_limit : str, upper_limit : str, *, equation : str):
		'''
		Definite integral of an equation
		with respect to x (dx)
		'''
		x = sympy.symbols('x')
		try:
			await self.bot.reply("`{}`".format(sympy.integrate(equation.strip('`'), (x, lower_limit, upper_limit))))
		except Exception as e:
			await self.bot.reply(py_code_block.format("{}: {}".format(type(e).__name__, e)))
	
	@commands.command()
	@checks.not_forbidden()
	async def choose(self, *choices : str):
		'''
		Randomly chooses between multiple options
		choose <option1> <option2> <...>
		'''
		if not choices:
			await self.bot.reply("Choose between what?")
		else:
			await self.bot.reply(random.choice(choices))
	
	@commands.command(aliases = ["flip"])
	@checks.not_forbidden()
	async def coin(self):
		'''Flip a coin'''
		await self.bot.reply(random.choice(["Heads!", "Tails!"]))
	
	@commands.group(aliases = ["decrpyt"])
	@checks.not_forbidden()
	async def decode(self):
		'''
		Decodes coded messages
		options: morse <message>, reverse <message>, caesar (rot) <key (0 - 26) or brute> <message>
		'''
		return
	
	@decode.command(name = "morse")
	async def decode_morse(self, *, message : str):
		'''Decodes morse code'''
		await self.bot.reply('`' + ciphers.decode_morse(message) + '`')
	
	@decode.command(name = "reverse")
	async def decode_reverse(self, *, message : str):
		'''Reverses text'''
		await self.bot.reply('`' + message[::-1] + '`')
	
	@decode.command(name = "caesar", aliases = ["rot"])
	async def decode_caesar(self, option : str, *, message : str):
		'''
		Decodes caesar codes
		Options: key (0 - 26), brute
		'''
		if len(message) == 0 or not ((option.isdigit() and 0 <= int(option) <= 26) or option == "brute"):
			await self.bot.reply("Invalid Format. !decode caesar <key (0 - 26) or brute> <content>")
		elif option == "brute":
			await self.bot.reply('`' + ciphers.brute_force_caesar(message) + '`')
		else:
			await self.bot.reply('`' + ciphers.decode_caesar(message, option) + '`')
	
	@commands.group(aliases = ["encrypt"])
	@checks.not_forbidden()
	async def encode(self):
		'''
		Encode messages
		options: morse <message>, reverse <message>, caesar (rot) <key (0 - 26)> <message>
		'''
		return
	
	@encode.command(name = "morse")
	async def encode_morse(self, *, message : str):
		'''Encode a message in morse code'''
		await self.bot.reply('`' + ciphers.encode_morse(message) + '`')
	
	@encode.command(name = "reverse")
	async def encode_reverse(self, *, message : str):
		'''Reverses text'''
		await self.bot.reply('`' + message[::-1] + '`')
	
	@encode.command(name = "caesar", aliases = ["rot"])
	async def encode_caesar(self, key : int, *, message : str):
		'''
		Encode a message using caesar code
		key : 0 - 26
		'''
		if len(message) == 0 or not 0 <= key <= 26:
			await self.bot.reply("Invalid Format. !encode caesar <key (0 - 26)> <content>")
		else:
			await self.bot.reply('`' + ciphers.encode_caesar(message, key) + '`')
	
	@encode.command(name = "sha1", aliases = ["sha-1"])
	async def encode_sha1(self, *, message : str):
		'''Generate SHA-1 hash'''
		await self.bot.reply(hashlib.sha1(message.encode("utf-8")).hexdigest())
	
	@encode.command(name = "sha224", aliases = ["sha-224"])
	async def encode_sha224(self, *, message : str):
		'''Generate SHA-224 hash'''
		await self.bot.reply(hashlib.sha224(message.encode("utf-8")).hexdigest())
	
	@encode.command(name = "sha256", aliases = ["sha-256"])
	async def encode_sha256(self, *, message : str):
		'''Generate SHA-256 hash'''
		await self.bot.reply(hashlib.sha256(message.encode("utf-8")).hexdigest())
	
	@encode.command(name = "sha384", aliases = ["sha-384"])
	async def encode_sha384(self, *, message : str):
		'''Generate SHA-384 hash'''
		await self.bot.reply(hashlib.sha384(message.encode("utf-8")).hexdigest())
	
	@encode.command(name = "sha512", aliases = ["sha-512"])
	async def encode_sha512(self, *, message : str):
		'''Generate SHA-512 hash'''
		await self.bot.reply(hashlib.sha512(message.encode("utf-8")).hexdigest())
	
	@encode.command(name = "md4")
	async def encode_md4(self, *, message : str):
		'''Generate MD4 hash'''
		h = hashlib.new("md4")
		h.update(message.encode("utf-8"))
		await self.bot.reply(h.hexdigest())
	
	@encode.command(name = "md5")
	async def encode_md5(self, *, message : str):
		'''Generate MD5 hash'''
		await self.bot.reply(hashlib.md5(message.encode("utf-8")).hexdigest())
	
	@encode.command(name = "ripemd160", aliases = ["ripemd-160"])
	async def encode_ripemd160(self, *, message : str):
		'''Generate RIPEMD-160 hash'''
		h = hashlib.new("ripemd160")
		h.update(message.encode("utf-8"))
		await self.bot.reply(h.hexdigest())
	
	@encode.command(name = "whirlpool")
	async def encode_whirlpool(self, *, message : str):
		'''Generate Whirlpool hash'''
		h = hashlib.new("whirlpool")
		h.update(message.encode("utf-8"))
		await self.bot.reply(h.hexdigest())
	
	@encode.command(name = "adler32", aliases = ["adler-32"])
	async def encode_adler32(self, *, message : str):
		'''Computer Adler-32 checksum'''
		await self.bot.reply(zlib.adler32(message.encode("utf-8")))
	
	@encode.command(name = "crc32", aliases = ["crc-32"])
	async def encode_crc32(self, *, message : str):
		'''Computer CRC32 checksum'''
		await self.bot.reply(zlib.crc32(message.encode("utf-8")))
	
	@commands.command()
	@checks.not_forbidden()
	async def fancify(self, *, text : str):
		'''Fancify text'''
		output = ""
		for letter in text:
			if 65 <= ord(letter) <= 90:
				output += chr(ord(letter) + 119951)
			elif 97 <= ord(letter) <= 122:
				output += chr(ord(letter) + 119919)
			elif letter == ' ':
				output += ' '
		await self.bot.reply(output)
	
	@commands.command(pass_context = True)
	@checks.not_forbidden()
	async def graph(self, ctx, *, data : str):
		'''WIP'''
		name = "data/graph_testing.png"
		seaborn.jointplot(**eval(data)).savefig(name)
		await self.bot.send_file(destination = ctx.message.channel, fp = name, content = "Testing Graph")
	
	@commands.command()
	@checks.not_forbidden()
	async def randomlocation(self):
		'''Generate random location'''
		await self.bot.reply("{0}, {1}".format(str(random.uniform(-90, 90)), str(random.uniform(-180, 180))))
	
	@commands.command(aliases = ["randomnumber"])
	@checks.not_forbidden()
	async def rng(self, *number : int):
		'''
		Generate random number
		Default range is 1 to 10
		'''
		if len(number) and number[0] > 0:
			await self.bot.reply(str(random.randint(1, number[0])))
		else:
			await self.bot.reply(str(random.randint(1, 10)))
	
	@commands.group(pass_context = True, aliases = ["trigger", "note"])
	@checks.not_forbidden()
	async def tag(self, ctx):
		'''
		Tags/notes that you can trigger later
		options: list, add <tag> [content...], edit <tag> [content...], delete <tag>
		'''
		with open("data/tags.json", 'r') as tags_file:
			self.tags_data = json.load(tags_file)
		if len(ctx.message.content.split()) == 1:
			await self.bot.reply("Add a tag with `!tag add <tag> <content>`. " \
				"Use `!tag <tag>` to trigger the tag you added. `!tag edit` to edit, `!tag remove` to delete")
			return
		if not ctx.invoked_subcommand is self.tag_add:
			if not ctx.message.author.id in self.tags_data:
				raise errors.NoTags
			self.tags = self.tags_data[ctx.message.author.id]["tags"]
		if ctx.invoked_subcommand in (self.tag_edit, self.tag_delete) and not ctx.message.content.split()[2] in self.tags:
			raise errors.NoTag
		if not ctx.invoked_subcommand:
			if len(ctx.message.content.split()) >= 3:
				await self.bot.reply("Syntax error.")
			else:
				if not ctx.message.content.split()[1] in self.tags:
					raise errors.NoTag
				else:
					await self.bot.reply(self.tags[ctx.message.content.split()[1]])
	
	@tag.command(name = "list", aliases = ["all", "mine"])
	async def tag_list(self):
		'''List your tags'''
		_tag_list = ", ".join(sorted(self.tags.keys()))
		await self.bot.reply("Your tags: " + _tag_list)
	
	@tag.command(name = "add", aliases = ["make", "new", "create"], pass_context = True)
	async def tag_add(self, ctx, tag : str, *, content : str):
		'''Add a tag'''
		if not ctx.message.author.id in self.tags_data:
			self.tags_data[ctx.message.author.id] = {"name" : ctx.message.author.name, "tags" : {}}
		self.tags = self.tags_data[ctx.message.author.id]["tags"]
		if tag in self.tags:
			await self.bot.reply("You already have that tag. Use `!tag edit <tag> <content>` to edit it.")
			return
		self.tags[tag] = self.clean_tag_content(content)
		with open("data/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await self.bot.reply(":thumbsup::skin-tone-2: Your tag has been added.")
	
	@tag.command(name = "edit", aliases = ["update"], pass_context = True)
	async def tag_edit(self, ctx, tag : str, *, content : str):
		'''Edit one of your tags'''
		self.tags[tag] = self.clean_tag_content(content)
		with open("data/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await self.bot.reply(":ok_hand::skin-tone-2: Your tag has been edited.")
	
	@tag.command(name = "delete", aliases = ["remove", "destroy"])
	async def tag_delete(self, tag : str):
		'''Delete one of your tags'''
		del self.tags[tag]
		with open("data/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await self.bot.reply(":ok_hand::skin-tone-2: Your tag has been deleted.")
	
	@tag.command(name = "search", aliases = ["contains", "find"])
	async def tag_search(self, *, search : str):
		'''Search your tags'''
		results = [t for t in self.tags.keys() if search in t]
		await self.bot.reply("{} tags found: {}".format(len(results), ", ".join(results)))
	
	@tag.error
	async def tag_error(self, error, ctx):
		if isinstance(error.original, errors.NoTags):
			await self.bot.reply("You don't have any tags :slight_frown: "
			"Add one with `!tag add <tag> <content>`")
		elif isinstance(error.original, errors.NoTag):
			await self.bot.reply("You don't have that tag.")
	
	def clean_tag_content(self, content):
		return content.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")
	
	@commands.command(pass_context = True)
	@checks.not_forbidden()
	async def timer(self, ctx, seconds : int):
		'''WIP'''
		await self.bot.reply("I'll remind you in {} seconds.".format(seconds))
		await asyncio.sleep(seconds)
		await self.bot.say("{}: {} seconds have passed.".format(ctx.message.author.mention, seconds))
	
	@commands.command(hidden = True, pass_context = True)
	@checks.not_forbidden()
	async def webmtogif(self, ctx, url : str): #WIP
		'''WIP'''
		webmfile = urllib.request.urlretrieve(url, "data/webtogif.webm")
		# subprocess.call(["ffmpeg", "-i", "data/webtogif.webm", "-pix_fmt", "rgb8", "data/webtogif.gif"], shell=True)
		clip = moviepy.editor.VideoFileClip("data/webtogif.webm")
		clip.write_gif("data/webtogif.gif", fps = 1, program = "ffmpeg")
		# clip.write_gif("data/webtogif.gif", fps=15, program="ImageMagick", opt="optimizeplus")
		await self.bot.send_file(ctx.message.channel, "data/webtogif.gif")
		#subprocess.call(["ffmpeg", "-i", "data/webtogif.webm", "-pix_fmt", "rgb8", "data/webtogif.gif"], shell=True)
		#await self.bot.send_file(message.channel, "data/webtogif.gif")

