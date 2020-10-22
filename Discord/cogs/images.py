
from discord.ext import commands

import inspect
import re
from typing import Optional

import clarifai.rest
import imgurpython

from utilities import checks

def setup(bot):
	bot.add_cog(Images(bot))

class Images(commands.Cog):

	'''
	All image subcommands are also commands
	'''
	
	def __init__(self, bot):
		self.bot = bot
		# Add commands as image subcommands
		for name, command in inspect.getmembers(self):
			if isinstance(command, commands.Command) and command.parent is None and name != "image":
				self.bot.add_command(command)
				self.image.add_command(command)
		# Add image google / google images subcommands
		self.image.add_command(commands.Command(self.google, aliases = ["search"], checks = [checks.not_forbidden().predicate]))
		if (cog := self.bot.get_cog("Search")) and (parent := getattr(cog, "google")):
			parent.add_command(commands.Command(self.google, name = "images", aliases = ["image"], checks = [checks.not_forbidden().predicate]))
		# Add imgur search / search imgur subcommands
		self.imgur.add_command(commands.Command(self.imgur_search, name = "search", checks = [checks.not_forbidden().predicate]))
		if cog and (parent := getattr(cog, "search")):
			parent.add_command(commands.Command(self.imgur_search, name = "imgur", checks = [checks.not_forbidden().predicate]))
	
	def cog_unload(self):
		if (cog := self.bot.get_cog("Search")) and (parent := getattr(cog, "google")):
			parent.remove_command("images")
		if cog and (parent := getattr(cog, "search")):
			parent.remove_command("imgur")
	
	async def cog_check(self, ctx):
		return await checks.not_forbidden().predicate(ctx)
	
	@commands.group(aliases = ["images", "photo", "photos"], invoke_without_command = True, case_insensitive = True)
	async def image(self, ctx, *, query):
		'''Images/Photos'''
		url = "https://api.unsplash.com/search/photos"
		headers = {"Accept-Version": "v1", "Authorization": f"Client-ID {ctx.bot.UNSPLASH_ACCESS_KEY}"}
		params = {"query": query, "per_page": 1}
		async with ctx.bot.aiohttp_session.get(url, headers = headers, params = params) as resp:
			data = await resp.json()
		if not data["results"]:
			return await ctx.embed_reply("No photo results found")
		photo = data["results"][0]
		await ctx.embed_reply(photo["description"] or "", 
								author_name = f"{photo['user']['name']} on Unsplash", 
								author_url = f"{photo['user']['links']['html']}?utm_source=Harmonbot&utm_medium=referral", 
								author_icon_url = photo["user"]["profile_image"]["small"], 
								image_url = photo["urls"]["full"])
	
	@image.command(name = "color", aliases = ["colour"])
	async def image_color(self, ctx, image_url: Optional[str]):
		'''
		Image color density values
		and the closest W3C color name for each identified color
		'''
		if not image_url:
			if not ctx.message.attachments:
				return await ctx.embed_reply(f"{ctx.bot.error_emoji} Please input an image and/or url")
			image_url = ctx.message.attachments[0].url
		try:
			response = self.bot.clarifai_app.public_models.color_model.predict_by_url(image_url)
		except clarifai.rest.ApiError as e:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: `{e.response.json()['outputs'][0]['status']['details']}`")
		if response["status"]["description"] != "Ok":
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error")
		fields = []
		for color in sorted(response["outputs"][0]["data"]["colors"], key = lambda c: c["value"], reverse = True):
			fields.append((color["raw_hex"].upper(), f"{color['value'] * 100:.2f}%\n"
														f"{re.sub(r'(?!^)(?=[A-Z])', ' ', color['w3c']['name'])}\n"
														f"({color['w3c']['hex'].upper()})"))
		await ctx.embed_reply(title = "Color Density", fields = fields, thumbnail_url = image_url)
	
	async def google(self, ctx, *, search: str):
		'''Google image search something'''
		url = "https://www.googleapis.com/customsearch/v1"
		params = {"key": ctx.bot.GOOGLE_API_KEY, "cx": ctx.bot.GOOGLE_CUSTOM_SEARCH_ENGINE_ID, 
					"searchType": "image", 'q': search, "num": 1, "safe": "active"}
		# TODO: Option to disable SafeSearch
		async with ctx.bot.aiohttp_session.get(url, params = params) as resp:
			if resp.status == 403:
				return await ctx.embed_reply(f"{ctx.bot.error_emoji} Daily limit exceeded")
			data = await resp.json()
		if "items" not in data:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} No images with that search found")
		await ctx.embed_reply(image_url = data["items"][0]["link"], 
								title = f"Image of {search}", 
								title_url = data["items"][0]["link"])
		# TODO: handle 403 daily limit exceeded error
	
	@image.command(name = "recognition")
	async def image_recognition(self, ctx, image_url: Optional[str]):
		'''Image recognition'''
		if not image_url:
			if not ctx.message.attachments:
				return await ctx.embed_reply(f"{ctx.bot.error_emoji} Please input an image and/or url")
			image_url = ctx.message.attachments[0].url
		try:
			response = self.bot.clarifai_app.public_models.general_model.predict_by_url(image_url)
		except clarifai.rest.ApiError as e:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: `{e.response.json()['outputs'][0]['status']['details']}`")
		if response["status"]["description"] != "Ok":
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error")
		names = {}
		for concept in response["outputs"][0]["data"]["concepts"]:
			names[concept["name"]] = concept["value"] * 100
		output = ""
		for name, value in sorted(names.items(), key = lambda i: i[1], reverse = True):
			output += f"**{name}**: {value:.2f}%, "
		output = output[:-2]
		await ctx.embed_reply(output, thumbnail_url = image_url)
	
	# TODO: add as search subcommand
	@commands.group(invoke_without_command = True, case_insensitive = True)
	async def giphy(self, ctx, *, search: str):
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
	
	@commands.group(invoke_without_command = True, case_insensitive = True)
	async def imgur(self, ctx):
		'''Imgur'''
		await ctx.send_help(ctx.command)
	
	@imgur.command(name = "upload")
	async def imgur_upload(self, ctx, url: str = ""):
		'''Upload images to Imgur'''
		if not (url or ctx.message.attachments):
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Please input an image and/or url")
		image = url or ctx.message.attachments[0].url
		try:
			await ctx.embed_reply(self.bot.imgur_client.upload_from_url(image)["link"])
		except imgurpython.helpers.error.ImgurClientError as e:
			await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: {e}")
	
	async def imgur_search(self, ctx, *, search: str):
		'''Search images on Imgur'''
		result = self.bot.imgur_client.gallery_search(search, sort = "top")
		if not result:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} No results found")
		result = result[0]
		if result.is_album:
			result = self.bot.imgur_client.get_album(result.id).images[0]
			await ctx.embed_reply(image_url = result["link"])
		else:
			await ctx.embed_reply(image_url = result.link)
	
	@commands.command()
	async def nsfw(self, ctx, image_url: Optional[str]):
		'''NSFW recognition'''
		if not image_url:
			if not ctx.message.attachments:
				return await ctx.embed_reply(f"{ctx.bot.error_emoji} Please input an image and/or url")
			image_url = ctx.message.attachments[0].url
		try:
			response = self.bot.clarifai_app.public_models.nsfw_model.predict_by_url(image_url)
		except clarifai.rest.ApiError as e:
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error: `{e.response.json()['outputs'][0]['status']['details']}`")
		if response["status"]["description"] != "Ok":
			return await ctx.embed_reply(f"{ctx.bot.error_emoji} Error")
		percentages = {}
		for concept in response["outputs"][0]["data"]["concepts"]:
			percentages[concept["name"]] = concept["value"] * 100
		await ctx.embed_reply(f"NSFW: {percentages['nsfw']:.2f}%", thumbnail_url = image_url)

