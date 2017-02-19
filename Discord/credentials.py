
import os
import sys

if os.getenv("TRAVIS") and os.getenv("CI"):
	for credential in ("token", "owm_api_key", "twitter_consumer_key", "twitter_consumer_secret", "twitter_access_token", "twitter_access_token_secret", "wordnik_apikey", "imgur_client_id", "imgur_client_secret", "wolframalpha_appid", "discord_bots_api_token", "myid"):
		if credential in os.environ:
			setattr(sys.modules[__name__], credential, os.environ[credential])
else:
	import _credentials
	for variable in _credentials.__dir__():
		if not variable.startswith("__"):
			setattr(sys.modules[__name__], variable, getattr(_credentials, variable))

