
import inspect

from discord.ext import commands

import clients
import credentials
from modules import utilities
from utilities import checks

def setup(bot):
	bot.add_cog(Images(bot))

class Images:
	
	def __init__(self, bot):
		self.bot = bot
		# Add commands as image subcommands
		for name, command in inspect.getmembers(self):
			if isinstance(command, commands.Command) and command.parent is None and name != "image":
				self.bot.add_command(command)
				self.image.add_command(command)
		# Add image google subcommand as google images subcommand
		utilities.add_as_subcommand(self, self.image_google, "Search.google", "images", aliases = ["image"])
	
	def __unload(self):
		utilities.remove_as_subcommand(self, "Search.google", "images")
	
	def __local_check(self, ctx):
		return checks.not_forbidden_predicate(ctx)
	
	@commands.group(aliases = ["images"], invoke_without_command = True)
	async def image(self, ctx):
		'''
		Images
		All image subcommands are also commands
		'''
		await ctx.invoke(ctx.bot.get_command("help"), ctx.invoked_with)
	
	@image.command(name = "google", aliases = ["search"])
	async def image_google(self, ctx, *, search : str):
		'''Google image search something'''
		url = "https://www.googleapis.com/customsearch/v1?key={}&cx={}&searchType=image&q={}".format(credentials.google_apikey, credentials.google_cse_cx, search.replace(' ', '+'))
		async with clients.aiohttp_session.get(url) as resp:
			if resp.status == 403:
				await ctx.embed_reply(":no_entry: Daily limit exceeded")
				return
			data = await resp.json()
		if "items" not in data:
			await ctx.embed_reply(":no_entry: No images with that search found")
			return
		await ctx.embed_reply(image_url = data["items"][0]["link"], title = "Image of {}".format(search), title_url = data["items"][0]["link"])
		# handle 403 daily limit exceeded error
	
	@image.command(name = "recognition")
	async def image_recognition(self, ctx, image_url : str):
		'''Image recognition'''
		try:
			response = self.bot.clarifai_app.public_models.general_model.predict_by_url(image_url)
		except clarifai.rest.ApiError as e:
			await ctx.embed_reply(":no_entry: Error: `{}`".format(e.response.json()["outputs"][0]["status"]["details"]))
			return
		if response["status"]["description"] != "Ok":
			await ctx.embed_reply(":no_entry: Error")
			return
		names = {}
		for concept in response["outputs"][0]["data"]["concepts"]:
			names[concept["name"]] = concept["value"] * 100
		output = ""
		for name, value in sorted(names.items(), key = lambda i: i[1], reverse = True):
			output += "**{}**: {:.2f}%, ".format(name, value)
		output = output[:-2]
		await ctx.embed_reply(output)
	
	# TODO: add as search subcommand
	@commands.group(invoke_without_command = True)
	async def giphy(self, ctx, *, search : str):
		'''Find an image on giphy'''
		url = "http://api.giphy.com/v1/gifs/search?api_key={}&q={}&limit=1".format(credentials.giphy_public_beta_api_key, search)
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json()
		await ctx.embed_reply(image_url = data["data"][0]["images"]["original"]["url"])
	
	@giphy.command(name = "trending")
	async def giphy_trending(self, ctx):
		'''Trending gif'''
		url = "http://api.giphy.com/v1/gifs/trending?api_key={}".format(credentials.giphy_public_beta_api_key)
		async with clients.aiohttp_session.get(url) as resp:
			data = await resp.json()
		await ctx.embed_reply(image_url = data["data"][0]["images"]["original"]["url"])
	
	@commands.group(invoke_without_command = True)
	async def imgur(self, ctx):
		'''Imgur'''
		await ctx.invoke(self.bot.get_command("help"), ctx.invoked_with)
	
	@imgur.command(name = "upload")
	async def imgur_upload(self, ctx, url : str = ""):
		'''Upload images to Imgur'''
		if url:
			await self._imgur_upload(ctx, url)
		if ctx.message.attachments:
			await self._imgur_upload(ctx, ctx.message.attachments[0]["url"])
		if not (url or ctx.message.attachments):
			await ctx.embed_reply(":no_entry: Please input an image and/or url")
	
	async def _imgur_upload(self, ctx, url):
		try:
			await ctx.embed_reply(self.bot.imgur_client.upload_from_url(url)["link"])
		except imgurpython.helpers.error.ImgurClientError as e:
			await ctx.embed_reply(":no_entry: Error: {}".format(e))
	
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
		await ctx.embed_reply("NSFW: {:.2f}%".format(percentages["nsfw"]))

