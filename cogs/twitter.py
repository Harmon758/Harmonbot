
from discord.ext import commands
import tweepy

import credentials
from utilities import checks

auth = tweepy.OAuthHandler(credentials.twitter_consumer_key, credentials.twitter_consumer_secret)
auth.set_access_token(credentials.twitter_access_token, credentials.twitter_access_token_secret)
twitter_api = tweepy.API(auth)

def setup(bot):
	bot.add_cog(Twitter(bot))

class TwitterStreamListener(tweepy.StreamListener):
	
	def on_status(self, status):
		print(status.text)
	
	def on_error(self, status_code):
		if status_code == 420:
			#returning False in on_data disconnects the stream
			return False

class Twitter:
	
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command()
	async def status(self, handle : str):
		'''Get twitter status'''
		tweet = twitter_api.user_timeline(handle, count = 1)[0]
		await self.bot.reply(tweet.text)

	@commands.command()
	@checks.is_owner()
	async def start_stream(self):
		'''WIP'''
		_TwitterStreamListener = TwitterStreamListener()
		TwitterStream = tweepy.Stream(auth = twitter_api.auth, listener = _TwitterStreamListener)
		TwitterStream.filter(follow = ["7744592"], **{"async" : "True"})
