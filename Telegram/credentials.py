
import os
import sys

if os.getenv("TRAVIS") and os.getenv("CI"):
	for credential in ("telegram_harmonbot_token",):
		if credential in os.environ:
			setattr(sys.modules[__name__], credential, os.environ[credential])
else:
	import _credentials
	for variable in _credentials.__dir__():
		if not variable.startswith("__"):
			setattr(sys.modules[__name__], variable, getattr(_credentials, variable))

