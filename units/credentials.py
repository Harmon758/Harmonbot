
import os
import sys

if not os.getenv("TRAVIS") or not os.getenv("CI"):
	from . import _credentials
	for variable in _credentials.__dir__():
		if not variable.startswith("__"):
			setattr(sys.modules[__name__], variable, getattr(_credentials, variable))

