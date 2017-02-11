
import os
if os.getenv("TRAVIS") and os.getenv("CI"):
	for credential in ("telegram_harmonbot_token"):
		if credential in os.environ:
			exec("{0} = os.environ['{0}']".format(credential))
else:
	import _credentials
	for variable in _credentials.__dir__():
		if not variable.startswith("__"):
			exec("{0} = _credentials.{0}".format(variable))

