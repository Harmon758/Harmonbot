
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import requests


# Most recent commit at https://github.com/lichess-org/lila
COMMIT = "cbd628f7e3739ee4c62253814b67b52182fb646c"

FONT_URL = f"https://raw.githubusercontent.com/lichess-org/lila/{COMMIT}/public/font/lichess.woff2"
SCRIPT_URL = f"https://raw.githubusercontent.com/lichess-org/lila/{COMMIT}/bin/gen/licon.py"
SFD_URL = f"https://raw.githubusercontent.com/lichess-org/lila/{COMMIT}/public/font/lichess.sfd"

SIZE = 128


(Path(__file__).parent / "licon.py").write_bytes(requests.get(SCRIPT_URL).content)

from licon import parse_codes

(Path(__file__).parent / "licon.py").unlink()


Path("lichess.sfd").write_bytes(requests.get(SFD_URL).content)

codes = parse_codes()

Path("lichess.sfd").unlink()


font = ImageFont.truetype(BytesIO(requests.get(FONT_URL).content), size = SIZE)

(Path(__file__).parent.parent / "assets" / "lichess_icons").mkdir(exist_ok = True)

for name, code in codes.items():
    image = Image.new("RGBA", (SIZE, SIZE))
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), chr(code), font = font, fill = "black")
    image.save(Path(__file__).parent.parent / "assets" / "lichess_icons" / f"{name}.png")

