
import os
if os.getenv("TRAVIS") and os.getenv("CI"):
	for credential in ("token", "owm_api_key", "twitter_consumer_key", "twitter_consumer_secret", "twitter_access_token", "twitter_access_token_secret", "wordnik_apikey", "imgur_client_id", "imgur_client_secret", "wolframalpha_appid", "discord_bots_api_token", "myid"):
		if credential in os.environ:
			exec("{0} = os.environ['{0}']".format(credential))
else:
	import _credentials
	for variable in _credentials.__dir__():
		if not variable.startswith("__"):
			exec("{0} = _credentials.{0}".format(variable))

