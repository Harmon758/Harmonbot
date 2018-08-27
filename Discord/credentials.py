
import os
import sys

if (os.getenv("CIRCLECI") or os.getenv("TRAVIS")) and os.getenv("CI"):
	for credential in ("token", "wordnik_apikey", "imgur_client_id", "imgur_client_secret", "wolframalpha_appid", "discord_bots_api_token", "twitch_client_id"):
		if credential in os.environ:
			setattr(sys.modules[__name__], credential, os.environ[credential])
else:
	import _credentials
	for variable in _credentials.__dir__():
		if not variable.startswith("__"):
			setattr(sys.modules[__name__], variable, getattr(_credentials, variable))

