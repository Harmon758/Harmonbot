
# https://genshin.dev/
# https://github.com/genshindev/api
API_BASE_URL = "https://api.genshin.dev"

from .characters import get_all_characters as get_all_characters  # noqa: E402 (module-import-not-at-top-of-file)
from .characters import get_character as get_character  # noqa: E402 (module-import-not-at-top-of-file)
from .characters import get_character_images as get_character_images  # noqa: E402 (module-import-not-at-top-of-file)
from .characters import get_characters as get_characters  # noqa: E402 (module-import-not-at-top-of-file)

