
import os
import sys

if not (os.getenv("CIRCLECI") or os.getenv("TRAVIS") or os.getenv("CI")):
	import _credentials
	for variable in _credentials.__dir__():
		if not variable.startswith("__"):
			setattr(sys.modules[__name__], variable, getattr(_credentials, variable))

