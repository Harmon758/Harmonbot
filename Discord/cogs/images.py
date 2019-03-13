
from discord.ext import commands

import inspect
import re

import clarifai.rest
import imgurpython

from modules import utilities
from utilities import checks

def setup(bot):
	bot.add_cog(Images(bot))

class Images(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot
		# Add commands as image subcommands
		for name, command in inspect.getmembers(self):
			if isinstance(command, commands.Command) and command.parent is None and name != "image":
				self.bot.add_command(command)
				self.image.add_command(command)
		# Add image google subcommand as google images subcommand
		utilities.add_as_subcommand(self, self.image_google, "Search.google", "images", aliases = ["image"])
		# Add imgur search subcommand as search imgur subcommand
		utilities.add_as_subcommand(self, self.imgur_search, "Search.search", "imgur")
	
	def cog_unload(self):
		utilities.remove_as_subcommand(self, "Search.google", "images")
		utilities.remove_as_subcommand(self, "Search.search", "imgur")
	
	def cog_check(self, ctx):
		return checks.not_forbidden_predicate(ctx)
	
	@commands.group(aliases = ["images"], invoke_without_command = True)
	async def image(self, ctx):
		'''
		Images
		All image subcommands are also commands
		'''
		await ctx.invoke(ctx.bot.get_command("help"), ctx.invoked_with)
	
	@image.command(name = "color", aliases = ["colour"])
	async def image_color(self, ctx, image_url : str):
		'''
		Image color density values
		and the closest W3C color name for each identified color
		'''
		try:
			response = self.bot.clarifai_app.public_models.color_model.predict_by_url(image_url)
		except clarifai.rest.ApiError as e:
			return await ctx.embed_reply(f":no_entry: Error: `{e.response.json()['outputs'][0]['status']['details']}`")
		if response["status"]["description"] != "Ok":
			return await ctx.embed_reply(":no_entry: Error")
		fields = []
		for color in sorted(response["outputs"][0]["data"]["colors"], key = lambda c: c["value"], reverse = True):
			fields.append((color["raw_hex"].upper(), f"{color['value'] * 100:.2f}%\n"
														f"{re.sub(r'(?!^)(?=[A-Z])', ' ', color['w3c']['name'])}\n"
														f"({color['w3c']['hex'].upper()})"))
		await ctx.embed_reply(title = "Color Density", fields = fields, thumbnail_url = image_url)
	
	@image.command(name = "google", aliases = ["search"])
	async def image_google(self, ctx, *, search : str):
		'''Google image search something'''
		url = "https://www.googleapis.com/customsearch/v1"
		params = {"key": ctx.bot.GOOGLE_API_KEY, "cx": ctx.bot.GOOGLE_CUSTOM_SEARCH_ENGINE_ID, 
					"searchType": "image", 'q': search, "num": 1, "safe": "active"}
		# TODO: Option to disable SafeSearch
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			if resp.status == 403:
				return await ctx.embed_reply(":no_entry: Daily limit exceeded")
			data = await resp.json()
		if "items" not in data:
			return await ctx.embed_reply(":no_entry: No images with that search found")
		await ctx.embed_reply(image_url = data["items"][0]["link"], 
								title = f"Image of {search}", 
								title_url = data["items"][0]["link"])
		# TODO: handle 403 daily limit exceeded error
	
	@image.command(name = "recognition")
	async def image_recognition(self, ctx, image_url : str):
		'''Image recognition'''
		try:
			response = self.bot.clarifai_app.public_models.general_model.predict_by_url(image_url)
		except clarifai.rest.ApiError as e:
			return await ctx.embed_reply(f":no_entry: Error: `{e.response.json()['outputs'][0]['status']['details']}`")
		if response["status"]["description"] != "Ok":
			return await ctx.embed_reply(":no_entry: Error")
		names = {}
		for concept in response["outputs"][0]["data"]["concepts"]:
			names[concept["name"]] = concept["value"] * 100
		output = ""
		for name, value in sorted(names.items(), key = lambda i: i[1], reverse = True):
			output += f"**{name}**: {value:.2f}%, "
		output = output[:-2]
		await ctx.embed_reply(output, thumbnail_url = image_url)
	
	# TODO: add as search subcommand
	@commands.group(invoke_without_command = True)
	async def giphy(self, ctx, *, search : str):
		'''Find an image on giphy'''
		url = "http://api.giphy.com/v1/gifs/search"
		params = {"api_key": ctx.bot.GIPHY_API_KEY, 'q': search, "limit": 1}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		await ctx.embed_reply(image_url = data["data"][0]["images"]["original"]["url"])
	
	@giphy.command(name = "trending")
	async def giphy_trending(self, ctx):
		'''Trending gif'''
		url = "http://api.giphy.com/v1/gifs/trending"
		params = {"api_key": ctx.bot.GIPHY_API_KEY}
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			data = await resp.json()
		await ctx.embed_reply(image_url = data["data"][0]["images"]["original"]["url"])
	
	@commands.group(invoke_without_command = True)
	async def imgur(self, ctx):
		'''Imgur'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	@imgur.command(name = "upload")
	async def imgur_upload(self, ctx, url : str = ""):
		'''Upload images to Imgur'''
		if not (url or ctx.message.attachments):
			return await ctx.embed_reply(":no_entry: Please input an image and/or url")
		image = url or ctx.message.attachments[0].url
		try:
			await ctx.embed_reply(self.bot.imgur_client.upload_from_url(image)["link"])
		except imgurpython.helpers.error.ImgurClientError as e:
			await ctx.embed_reply(f":no_entry: Error: {e}")
	
	@imgur.command(name = "search")
	async def imgur_search(self, ctx, *, search : str):
		'''Search images on Imgur'''
		result = self.bot.imgur_client.gallery_search(search, sort = "top")
		if not result:
			await ctx.embed_reply(":no_entry: No results found")
			return
		result = result[0]
		if result.is_album:
			result = self.bot.imgur_client.get_album(result.id).images[0]
			await ctx.embed_reply(image_url = result["link"])
		else:
			await ctx.embed_reply(image_url = result.link)
	
	@commands.command()
	async def nsfw(self, ctx, image_url : str):
		'''NSFW recognition'''
		try:
			response = self.bot.clarifai_app.public_models.nsfw_model.predict_by_url(image_url)
		except clarifai.rest.ApiError as e:
			await ctx.embed_reply(":no_entry: Error: `{}`".format(e.response.json()["outputs"][0]["status"]["details"]))
			return
		if response["status"]["description"] != "Ok":
			await ctx.embed_reply(":no_entry: Error")
			return
		percentages = {}
		for concept in response["outputs"][0]["data"]["concepts"]:
			percentages[concept["name"]] = concept["value"] * 100
		await ctx.embed_reply("NSFW: {:.2f}%".format(percentages["nsfw"]), thumbnail_url = image_url)

