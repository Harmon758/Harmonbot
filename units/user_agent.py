
from platform import python_version

import aiohttp


SIMPLE_USER_AGENT = "Harmonbot"
AIOHTTP_USER_AGENT = (
    f"Harmonbot Python/{python_version()} aiohttp/{aiohttp.__version__}"
)
