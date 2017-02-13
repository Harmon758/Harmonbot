
import discord
from discord.ext import commands

import asyncio
import concurrent.futures
import difflib
import hashlib
import json
import math
import moviepy.editor
import multiprocessing
import pandas
import pygost.gost28147
import pygost.gost28147_mac
import pygost.gost34112012
import pygost.gost341194
import pygost.gost3412
import random
import seaborn
# import re
# import subprocess
import sympy
import time
import unicodedata
import urllib
import zlib

from modules import ciphers
from modules import utilities
from utilities import checks
from utilities import errors
from utilities import paginator
import clients
from clients import py_code_block

def setup(bot):
	bot.add_cog(Tools(bot))

class Tools:
	
	def __init__(self, bot):
		self.bot = bot
		utilities.create_file("tags", content = {"global": {}})
		with open("data/tags.json", 'r') as tags_file:
			self.tags_data = json.load(tags_file)
	
	@commands.command()
	@checks.not_forbidden()
	async def add(self, *numbers : float):
		'''Add numbers together'''
		if not numbers:
			await self.bot.embed_reply("Add what?")
			return
		await self.bot.embed_reply("{} = {:g}".format(" + ".join("{:g}".format(number) for number in numbers), sum(numbers)))
	
	@commands.command(aliases = ["calc", "calculator"])
	@checks.not_forbidden()
	async def calculate(self, *, equation : str):
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
				await self.bot.embed_reply("{} = {}".format(equation, result))
			except discord.errors.HTTPException:
				await self.bot.embed_reply(":no_entry: Output too long")
			except SyntaxError:
				await self.bot.embed_reply(":no_entry: Syntax error")
			except concurrent.futures.TimeoutError:
				await self.bot.embed_reply(":no_entry: Execution exceeded time limit")
	
	@commands.command(aliases = ["charinfo", "char_info", "character_info"])
	@checks.not_forbidden()
	async def characterinfo(self, character : str):
		'''Information about a unicode character'''
		character = character[0]
		# TODO: return info on each character in the input string; use paste tool api?
		try:
			name = unicodedata.name(character)
		except ValueError:
			name = "UNKNOWN"
		hex_char = hex(ord(character))
		url = "http://www.fileformat.info/info/unicode/char/{}/index.htm".format(hex_char[2:])
		await self.bot.embed_reply("`{} ({})`".format(character, hex_char), title = name, title_url = url)
	
	@commands.command(aliases = ["differ", "derivative", "differentiation"])
	@checks.not_forbidden()
	async def differentiate(self, *, equation : str):
		'''
		Differentiate an equation
		with respect to x (dx)
		'''
		x = sympy.symbols('x')
		try:
			await self.bot.embed_reply("`{}`".format(sympy.diff(equation.strip('`'), x)), title = "Derivative of {}".format(equation))
		except Exception as e:
			await self.bot.embed_reply(py_code_block.format("{}: {}".format(type(e).__name__, e)), title = "Error")
	
	@commands.group(aliases = ["integral", "integration"], invoke_without_command = True)
	@checks.not_forbidden()
	async def integrate(self, *, equation : str):
		'''
		Integrate an equation
		with respect to x (dx)
		'''
		x = sympy.symbols('x')
		try:
			await self.bot.embed_reply("`{}`".format(sympy.integrate(equation.strip('`'), x)), title = "Integral of {}".format(equation))
		except Exception as e:
			await self.bot.embed_reply(py_code_block.format("{}: {}".format(type(e).__name__, e)), title = "Error")
	
	@integrate.command(name = "definite")
	@checks.not_forbidden()
	async def integrate_definite(self, lower_limit : str, upper_limit : str, *, equation : str):
		'''
		Definite integral of an equation
		with respect to x (dx)
		'''
		x = sympy.symbols('x')
		try:
			await self.bot.embed_reply("`{}`".format(sympy.integrate(equation.strip('`'), (x, lower_limit, upper_limit))), title = "Definite Integral of {} from {} to {}".format(equation, lower_limit, upper_limit))
		except Exception as e:
			await self.bot.embed_reply(py_code_block.format("{}: {}".format(type(e).__name__, e)), title = "Error")
	
	@commands.command(aliases = ["choice"])
	@checks.not_forbidden()
	async def choose(self, *choices : str):
		'''
		Randomly chooses between multiple options
		choose <option1> <option2> <...>
		'''
		if not choices:
			await self.bot.embed_reply("Choose between what?")
			return
		await self.bot.embed_reply(random.choice(choices))
	
	@commands.command(aliases = ["flip"])
	@checks.not_forbidden()
	async def coin(self):
		'''Flip a coin'''
		await self.bot.embed_reply(random.choice(["Heads!", "Tails!"]))
	
	@commands.group(aliases = ["decrpyt"])
	@checks.not_forbidden()
	async def decode(self):
		'''Decodes coded messages'''
		return
	
	@decode.group(name = "caesar", aliases = ["rot"], invoke_without_command = True)
	async def decode_caesar(self, key : int, *, message : str):
		'''
		Decodes caesar codes
		key: 0 - 26
		'''
		if not 0 <= key <= 26:
			await self.bot.embed_reply(":no_entry: Key must be in range 0 - 26")
			return
		await self.bot.embed_reply(ciphers.decode_caesar(message, key))
	
	@decode_caesar.command(name = "brute")
	async def decode_caesar_brute(self, message : str):
		'''Brute force decode caesar code'''
		await self.bot.embed_reply(ciphers.brute_force_caesar(message))
	
	@decode.group(name = "gost", aliases = ["гост"])
	async def decode_gost(self):
		'''
		Russian Federation/Soviet Union GOST
		Межгосударственный стандарт
		From GOsudarstvennyy STandart
		(ГОсударственный СТандарт)
		'''
		...
	
	@decode_gost.group(name = "28147-89", aliases = ["магма", "magma"])
	async def decode_gost_28147_89(self):
		'''
		GOST 28147-89 block cipher
		Also known as Магма or Magma
		key length must be 32 (256-bit)
		'''
		# TODO: Add decode magma alias
		...
	
	@decode_gost_28147_89.command(name = "cbc")
	async def ddecode_gost_28147_89_cbc(self, key : str, *, data : str):
		'''Magma with CBC mode of operation'''
		try:
			await self.bot.embed_reply(pygost.gost28147.cbc_decrypt(key.encode("utf-8"), bytearray.fromhex(data)).decode("utf-8"))
		except ValueError as e:
			await self.bot.embed_reply(":no_entry: Error: {}".format(e))
	
	@decode_gost_28147_89.command(name = "cfb")
	async def decode_gost_28147_89_cfb(self, key : str, *, data : str):
		'''Magma with CFB mode of operation'''
		try:
			await self.bot.embed_reply(pygost.gost28147.cfb_decrypt(key.encode("utf-8"), bytearray.fromhex(data)).decode("utf-8"))
		except ValueError as e:
			await self.bot.embed_reply(":no_entry: Error: {}".format(e))
	
	@decode_gost_28147_89.command(name = "cnt")
	async def decode_gost_28147_89_cnt(self, key : str, *, data : str):
		'''Magma with CNT mode of operation'''
		try:
			await self.bot.embed_reply(pygost.gost28147.cnt(key.encode("utf-8"), bytearray.fromhex(data)).decode("utf-8"))
		except ValueError as e:
			await self.bot.embed_reply(":no_entry: Error: {}".format(e))
	
	@decode_gost_28147_89.command(name = "ecb")
	async def decode_gost_28147_89_ecb(self, key : str, *, data : str):
		'''
		Magma with ECB mode of operation
		data block size must be 8 (64-bit)
		This means the data length must be a multiple of 8
		'''
		try:
			await self.bot.embed_reply(pygost.gost28147.ecb_decrypt(key.encode("utf-8"), bytearray.fromhex(data)).decode("utf-8"))
		except ValueError as e:
			await self.bot.embed_reply(":no_entry: Error: {}".format(e))
	
	@decode_gost.command(name = "34.12-2015", aliases = ["кузнечик", "kuznyechik"])
	async def decode_gost_34_12_2015(self, key : str, *, data : str):
		'''
		GOST 34.12-2015 128-bit block cipher
		Also known as Кузнечик or Kuznyechik
		key length >= 32, data length >= 16
		'''
		# TODO: Add decode kuznyechik alias
		if len(key) < 32:
			await self.bot.embed_reply(":no_entry: Error: key length must be at least 32")
			return
		if len(data) < 16:
			await self.bot.embed_reply(":no_entry: Error: data length must be at least 16")
			return
		await self.bot.embed_reply(pygost.gost3412.GOST3412Kuz(key.encode("utf-8")).decrypt(bytearray.fromhex(data)).decode("utf-8"))
	
	@decode.command(name = "morse")
	async def decode_morse(self, *, message : str):
		'''Decodes morse code'''
		await self.bot.embed_reply(ciphers.decode_morse(message))
	
	@decode.command(name = "qr", pass_context = True)
	async def decode_qr(self, ctx, file_url : str = ""):
		'''
		Decodes QR codes
		Input a file url or attach an image
		'''
		if file_url:
			await self._decode_qr(file_url)
		if ctx.message.attachments and "filename" in ctx.message.attachments[0]:
			await self._decode_qr(ctx.message.attachments[0]["url"])
		if not file_url and not (ctx.message.attachments and "filename" in ctx.message.attachments[0]):
			await self.bot.embed_reply(":no_entry: Please input a file url or attach an image")
	
	async def _decode_qr(self, file_url):
		url = "https://api.qrserver.com/v1/read-qr-code/?fileurl={}".format(file_url)
		async with clients.aiohttp_session.get(url) as resp:
			if resp.status == 400:
				await self.bot.embed_reply(":no_entry: Error")
				return
			data = await resp.json()
		if data[0]["symbol"][0]["error"]:
			await self.bot.embed_reply(":no_entry: Error: {}".format(data[0]["symbol"][0]["error"]))
			return
		decoded = data[0]["symbol"][0]["data"].replace("QR-Code:", "")
		if len(decoded) > 1024:
			await self.bot.embed_reply(decoded[:1021] + "...", footer_text = "Decoded message exceeded character limit")
			return
		await self.bot.embed_reply(decoded)
	
	@decode.command(name = "reverse")
	async def decode_reverse(self, *, message : str):
		'''Reverses text'''
		await self.bot.embed_reply(message[::-1])
	
	@commands.group(aliases = ["encrypt"])
	@checks.not_forbidden()
	async def encode(self):
		'''Encode messages'''
		return
	
	@encode.command(name = "adler32", aliases = ["adler-32"])
	async def encode_adler32(self, *, message : str):
		'''Computer Adler-32 checksum'''
		await self.bot.embed_reply(zlib.adler32(message.encode("utf-8")))
	
	@encode.command(name = "caesar", aliases = ["rot"])
	async def encode_caesar(self, key : int, *, message : str):
		'''
		Encode a message using caesar code
		key: 0 - 26
		'''
		if not 0 <= key <= 26:
			await self.bot.embed_reply(":no_entry: Key must be in range 0 - 26")
			return
		await self.bot.embed_reply(ciphers.encode_caesar(message, key))
	
	@encode.command(name = "crc32", aliases = ["crc-32"])
	async def encode_crc32(self, *, message : str):
		'''Computer CRC32 checksum'''
		await self.bot.embed_reply(zlib.crc32(message.encode("utf-8")))
	
	@encode.group(name = "gost", aliases = ["гост"])
	async def encode_gost(self):
		'''
		Russian Federation/Soviet Union GOST
		Межгосударственный стандарт
		From GOsudarstvennyy STandart
		(ГОсударственный СТандарт)
		'''
		...
	
	@encode_gost.group(name = "28147-89", aliases = ["магма", "magma"])
	async def encode_gost_28147_89(self):
		'''
		GOST 28147-89 block cipher
		Also known as Магма or Magma
		key length must be 32 (256-bit)
		'''
		# TODO: Add encode magma alias
		...
	
	@encode_gost_28147_89.command(name = "cbc")
	async def encode_gost_28147_89_cbc(self, key : str, *, data : str):
		'''Magma with CBC mode of operation'''
		try:
			await self.bot.embed_reply(pygost.gost28147.cbc_encrypt(key.encode("utf-8"), data.encode("utf-8")).hex())
		except ValueError as e:
			await self.bot.embed_reply(":no_entry: Error: {}".format(e))
	
	@encode_gost_28147_89.command(name = "cfb")
	async def encode_gost_28147_89_cfb(self, key : str, *, data : str):
		'''Magma with CFB mode of operation'''
		try:
			await self.bot.embed_reply(pygost.gost28147.cfb_encrypt(key.encode("utf-8"), data.encode("utf-8")).hex())
		except ValueError as e:
			await self.bot.embed_reply(":no_entry: Error: {}".format(e))
	
	@encode_gost_28147_89.command(name = "cnt")
	async def encode_gost_28147_89_cnt(self, key : str, *, data : str):
		'''Magma with CNT mode of operation'''
		try:
			await self.bot.embed_reply(pygost.gost28147.cnt(key.encode("utf-8"), data.encode("utf-8")).hex())
		except ValueError as e:
			await self.bot.embed_reply(":no_entry: Error: {}".format(e))
	
	@encode_gost_28147_89.command(name = "ecb")
	async def encode_gost_28147_89_ecb(self, key : str, *, data : str):
		'''
		Magma with ECB mode of operation
		data block size must be 8 (64-bit)
		This means the data length must be a multiple of 8
		'''
		try:
			await self.bot.embed_reply(pygost.gost28147.ecb_encrypt(key.encode("utf-8"), data.encode("utf-8")).hex())
		except ValueError as e:
			await self.bot.embed_reply(":no_entry: Error: {}".format(e))
	
	@encode_gost_28147_89.command(name = "mac")
	async def encode_gost_28147_89_mac(self, key : str, *, data : str):
		'''Magma with MAC mode of operation'''
		try:
			mac = pygost.gost28147_mac.MAC(key = key.encode("utf-8"))
			mac.update(data.encode("utf-8"))
			await self.bot.embed_reply(mac.hexdigest())
		except ValueError as e:
			await self.bot.embed_reply(":no_entry: Error: {}".format(e))
	
	@encode_gost.group(name = "34.11-2012", aliases = ["стрибог", "streebog"])
	async def encode_gost_34_11_2012(self):
		'''
		GOST 34.11-2012 hash function
		Also known as Стрибог or Streebog
		'''
		# TODO: Add encode streebog-256 and encode streebog-512 aliases
		...
	
	@encode_gost_34_11_2012.command(name = "256")
	async def encode_gost_34_11_2012_256(self, *, data : str):
		'''
		GOST 34.11-2012 256-bit hash function
		Also known as Streebog-256
		'''
		await self.bot.embed_reply(pygost.gost34112012.GOST34112012(data.encode("utf-8"), digest_size = 32).hexdigest())
	
	@encode_gost_34_11_2012.command(name = "512")
	async def encode_gost_34_11_2012_512(self, *, data : str):
		'''
		GOST 34.11-2012 512-bit hash function
		Also known as Streebog-512
		'''
		await self.bot.embed_reply(pygost.gost34112012.GOST34112012(data.encode("utf-8"), digest_size = 64).hexdigest())
	
	@encode_gost.command(name = "34.11-94")
	async def encode_gost_34_11_94(self, *, data : str):
		'''GOST 34.11-94 hash function'''
		await self.bot.embed_reply(pygost.gost341194.GOST341194(data.encode("utf-8")).hexdigest())
	
	@encode_gost.command(name = "34.12-2015", aliases = ["кузнечик", "kuznyechik"])
	async def encode_gost_34_12_2015(self, key : str, *, data : str):
		'''
		GOST 34.12-2015 128-bit block cipher
		Also known as Кузнечик or Kuznyechik
		key length >= 32, data length >= 16
		'''
		# TODO: Add encode kuznyechik alias
		if len(key) < 32:
			await self.bot.embed_reply(":no_entry: Error: key length must be at least 32")
			return
		if len(data) < 16:
			await self.bot.embed_reply(":no_entry: Error: data length must be at least 16")
			return
		await self.bot.embed_reply(pygost.gost3412.GOST3412Kuz(key.encode("utf-8")).encrypt(data.encode("utf-8")).hex())
	
	@encode.command(name = "md4")
	async def encode_md4(self, *, message : str):
		'''Generate MD4 hash'''
		h = hashlib.new("md4")
		h.update(message.encode("utf-8"))
		await self.bot.embed_reply(h.hexdigest())
	
	@encode.command(name = "md5")
	async def encode_md5(self, *, message : str):
		'''Generate MD5 hash'''
		await self.bot.embed_reply(hashlib.md5(message.encode("utf-8")).hexdigest())
	
	@encode.command(name = "morse")
	async def encode_morse(self, *, message : str):
		'''Encode a message in morse code'''
		await self.bot.embed_reply(ciphers.encode_morse(message))
	
	@encode.command(name = "qr")
	async def encode_qr(self, *, message : str):
		'''Encode a message in a QR code'''
		url = "https://api.qrserver.com/v1/create-qr-code/?data={}".format(message).replace(' ', '+')
		await self.bot.embed_reply(None, image_url = url)
	
	@encode.command(name = "reverse")
	async def encode_reverse(self, *, message : str):
		'''Reverses text'''
		await self.bot.embed_reply(message[::-1])
	
	@encode.command(name = "ripemd160", aliases = ["ripemd-160"])
	async def encode_ripemd160(self, *, message : str):
		'''Generate RIPEMD-160 hash'''
		h = hashlib.new("ripemd160")
		h.update(message.encode("utf-8"))
		await self.bot.embed_reply(h.hexdigest())
	
	@encode.command(name = "sha1", aliases = ["sha-1"])
	async def encode_sha1(self, *, message : str):
		'''Generate SHA-1 hash'''
		await self.bot.embed_reply(hashlib.sha1(message.encode("utf-8")).hexdigest())
	
	@encode.command(name = "sha224", aliases = ["sha-224"])
	async def encode_sha224(self, *, message : str):
		'''Generate SHA-224 hash'''
		await self.bot.embed_reply(hashlib.sha224(message.encode("utf-8")).hexdigest())
	
	@encode.command(name = "sha256", aliases = ["sha-256"])
	async def encode_sha256(self, *, message : str):
		'''Generate SHA-256 hash'''
		await self.bot.embed_reply(hashlib.sha256(message.encode("utf-8")).hexdigest())
	
	@encode.command(name = "sha384", aliases = ["sha-384"])
	async def encode_sha384(self, *, message : str):
		'''Generate SHA-384 hash'''
		await self.bot.embed_reply(hashlib.sha384(message.encode("utf-8")).hexdigest())
	
	@encode.command(name = "sha512", aliases = ["sha-512"])
	async def encode_sha512(self, *, message : str):
		'''Generate SHA-512 hash'''
		await self.bot.embed_reply(hashlib.sha512(message.encode("utf-8")).hexdigest())
	
	@encode.command(name = "whirlpool")
	async def encode_whirlpool(self, *, message : str):
		'''Generate Whirlpool hash'''
		h = hashlib.new("whirlpool")
		h.update(message.encode("utf-8"))
		await self.bot.embed_reply(h.hexdigest())
	
	@commands.command(pass_context = True)
	@checks.not_forbidden()
	async def graph(self, ctx, *, data : str):
		'''WIP'''
		name = "data/graph_testing.png"
		seaborn.jointplot(**eval(data)).savefig(name)
		await self.bot.send_file(destination = ctx.message.channel, fp = name, content = "Testing Graph")
	
	@commands.group(pass_context = True, aliases = ["trigger", "note", "tags", "triggers", "notes"], invoke_without_command = True)
	@checks.not_forbidden()
	async def tag(self, ctx, tag : str = ""):
		'''Tags/notes that you can trigger later'''
		if not tag:
			await self.bot.embed_reply("Add a tag with `{0}tag add [tag] [content]`\nUse `{0}tag [tag]` to trigger the tag you added\n`{0}tag edit [tag] [content]` to edit it and `{0}tag delete [tag]` to delete it".format(ctx.prefix))
			return
		if tag in self.tags_data.get(ctx.message.author.id, {}).get("tags", []):
			await self.bot.reply(self.tags_data[ctx.message.author.id]["tags"][tag])
		elif tag in self.tags_data["global"]:
			await self.bot.reply(self.tags_data["global"][tag]["response"])
			self.tags_data["global"][tag]["usage_counter"] += 1
			with open("data/tags.json", 'w') as tags_file:
				json.dump(self.tags_data, tags_file, indent = 4)
		else:
			close_matches = difflib.get_close_matches(tag, list(self.tags_data[ctx.message.author.id]["tags"].keys()) + list(self.tags_data["global"].keys()))
			close_matches = "\nDid you mean:\n{}".format('\n'.join(close_matches)) if close_matches else ""
			await self.bot.embed_reply("Tag not found{}".format(close_matches))
	
	@tag.command(name = "list", aliases = ["all", "mine"], pass_context = True)
	async def tag_list(self, ctx):
		'''List your tags'''
		if (await self.check_no_tags(ctx)): return
		tags_paginator = paginator.CustomPaginator(seperator = ", ")
		for tag in sorted(self.tags_data[ctx.message.author.id]["tags"].keys()):
			tags_paginator.add_section(tag)
		# DM
		for page in tags_paginator.pages:
			await self.bot.embed_reply(page, title = "Your tags:")
	
	@tag.command(name = "add", aliases = ["make", "new", "create"], pass_context = True)
	async def tag_add(self, ctx, tag : str, *, content : str):
		'''Add a tag'''
		if not ctx.message.author.id in self.tags_data:
			self.tags_data[ctx.message.author.id] = {"name" : ctx.message.author.name, "tags" : {}}
		tags = self.tags_data[ctx.message.author.id]["tags"]
		if tag in tags:
			await self.bot.embed_reply("You already have that tag\nUse `{}tag edit <tag> <content>` to edit it".format(ctx.prefix))
			return
		tags[tag] = self.clean_tag_content(content)
		with open("data/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await self.bot.embed_reply(":thumbsup::skin-tone-2: Your tag has been added")
	
	@tag.command(name = "edit", aliases = ["update"], pass_context = True)
	async def tag_edit(self, ctx, tag : str, *, content : str):
		'''Edit one of your tags'''
		if (await self.check_no_tags(ctx)): return
		if (await self.check_no_tag(ctx, tag)): return
		self.tags_data[ctx.message.author.id]["tags"][tag] = self.clean_tag_content(content)
		with open("data/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await self.bot.embed_reply(":ok_hand::skin-tone-2: Your tag has been edited")
	
	@tag.command(name = "delete", aliases = ["remove", "destroy"], pass_context = True)
	async def tag_delete(self, ctx, tag : str):
		'''Delete one of your tags'''
		if (await self.check_no_tags(ctx)): return
		if (await self.check_no_tag(ctx, tag)): return
		del self.tags_data[ctx.message.author.id]["tags"][tag]
		with open("data/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await self.bot.embed_reply(":ok_hand::skin-tone-2: Your tag has been deleted")
	
	@tag.command(name = "search", aliases = ["contains", "find"], pass_context = True)
	async def tag_search(self, ctx, *, search : str):
		'''Search your tags'''
		if (await self.check_no_tags(ctx)): return
		tags = self.tags_data[ctx.message.author.id]["tags"]
		results = [t for t in tags.keys() if search in t]
		if results:
			await self.bot.embed_reply("{} tags found: {}".format(len(results), ", ".join(results)))
			return
		close_matches = difflib.get_close_matches(search, tags.keys())
		close_matches = "\nDid you mean:\n{}".format('\n'.join(close_matches)) if close_matches else ""
		await self.bot.embed_reply("No tags found{}".format(close_matches))
	
	@tag.command(name = "globalize", aliases = ["globalise"], pass_context = True)
	async def tag_globalize(self, ctx, tag : str):
		'''Globalize a tag'''
		if (await self.check_no_tags(ctx)): return
		if (await self.check_no_tag(ctx, tag)): return
		if tag in self.tags_data["global"]:
			await self.bot.embed_reply("That global tag already exists\nIf you own it, use `{}tag global edit <tag> <content>` to edit it".format(ctx.prefix))
			return
		self.tags_data["global"][tag] = {"response": self.tags_data[ctx.message.author.id]["tags"][tag], "owner": ctx.message.author.id, "created_at": time.time(), "usage_counter": 0}
		del self.tags_data[ctx.message.author.id]["tags"][tag]
		with open("data/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await self.bot.embed_reply(":thumbsup::skin-tone-2: Your tag has been {}d".format(ctx.invoked_with))
	
	# TODO: rename, aliases
	
	@tag.group(name = "global", invoke_without_command = True)
	async def tag_global(self):
		'''Global tags'''
		...
	
	@tag_global.command(name = "add", aliases = ["make", "new", "create"], pass_context = True)
	async def tag_global_add(self, ctx, tag : str, *, content : str):
		'''Add a global tag'''
		tags = self.tags_data["global"]
		if tag in tags:
			await self.bot.embed_reply("That global tag already exists\nIf you own it, use `{}tag global edit <tag> <content>` to edit it".format(ctx.prefix))
			return
		tags[tag] = {"response": self.clean_tag_content(content), "owner": ctx.message.author.id, "created_at": time.time(), "usage_counter": 0}
		with open("data/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await self.bot.embed_reply(":thumbsup::skin-tone-2: Your tag has been added")
	
	@tag_global.command(name = "edit", aliases = ["update"], pass_context = True)
	async def tag_global_edit(self, ctx, tag : str, *, content : str):
		'''Edit one of your global tags'''
		if tag not in self.tags_data["global"]:
			await self.bot.embed_reply(":no_entry: That global tag doesn't exist")
			return
		elif self.tags_data["global"][tag]["owner"] != ctx.message.author.id:
			await self.bot.embed_reply(":no_entry: You don't own that global tag")
			return
		self.tags_data["global"][tag]["response"] = self.clean_tag_content(content)
		with open("data/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await self.bot.embed_reply(":ok_hand::skin-tone-2: Your tag has been edited")
	
	@tag_global.command(name = "delete", aliases = ["remove", "destroy"], pass_context = True)
	async def tag_global_delete(self, ctx, tag : str):
		'''Delete one of your global tags'''
		if tag not in self.tags_data["global"]:
			await self.bot.embed_reply(":no_entry: That global tag doesn't exist")
			return
		elif self.tags_data["global"][tag]["owner"] != ctx.message.author.id:
			await self.bot.embed_reply(":no_entry: You don't own that global tag")
			return
		del self.tags_data["global"][tag]
		with open("data/tags.json", 'w') as tags_file:
			json.dump(self.tags_data, tags_file, indent = 4)
		await self.bot.embed_reply(":ok_hand::skin-tone-2: Your tag has been deleted")
	
	# TODO: global search, list?
	
	async def check_no_tags(self, ctx):
		if not ctx.message.author.id in self.tags_data:
			await self.bot.embed_reply("You don't have any tags :slight_frown:\nAdd one with `{}{} add <tag> <content>`".format(ctx.prefix, ctx.invoked_with))
		return not ctx.message.author.id in self.tags_data
	
	async def check_no_tag(self, ctx, tag):
		tags = self.tags_data[ctx.message.author.id]["tags"]
		if not tag in tags:
			close_matches = difflib.get_close_matches(tag, tags.keys())
			close_matches = "\nDid you mean:\n{}".format('\n'.join(close_matches)) if close_matches else ""
			await self.bot.embed_reply("You don't have that tag{}".format(close_matches))
		return not tag in tags
	
	def clean_tag_content(self, content):
		return content.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")
	
	@commands.command(pass_context = True)
	@checks.not_forbidden()
	async def timer(self, ctx, seconds : int):
		'''Timer'''
		# TODO: other units, persistence through restarts
		await self.bot.embed_reply("I'll remind you in {} seconds".format(seconds))
		await asyncio.sleep(seconds)
		await self.bot.say("{}: {} seconds have passed".format(ctx.message.author.mention, seconds))
	
	@commands.command(pass_context = True, hidden = True)
	@checks.not_forbidden()
	async def webmtogif(self, ctx, url : str):
		'''
		Convert webm to gif files
		Only converts at 1 fps
		See http://imgur.com/vidgif instead
		'''
		webmfile = urllib.request.urlretrieve(url, "data/temp/webmtogif.webm")
		# subprocess.call(["ffmpeg", "-i", "data/temp/webmtogif.webm", "-pix_fmt", "rgb8", "data/temp/webmtogif.gif"], shell=True)
		clip = moviepy.editor.VideoFileClip("data/temp/webmtogif.webm")
		clip.write_gif("data/temp/webmtogif.gif", fps = 1, program = "ffmpeg")
		# clip.write_gif("data/temp/webmtogif.gif", fps=15, program="ImageMagick", opt="optimizeplus")
		await self.bot.send_file(ctx.message.channel, "data/temp/webmtogif.gif")

