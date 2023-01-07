
from enum import IntEnum


class TextColor(IntEnum):
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37


class BackgroundColor(IntEnum):
    BLACK = 40
    RED = 41
    GREEN = 42
    YELLOW = 43
    BLUE = 44
    MAGENTA = 45
    CYAN = 46
    WHITE = 47


def affix_ansi(
    string: str,
    bold: bool = False, underline: bool = False,
    text_color: TextColor = None, background_color: BackgroundColor = None
):
    prefix = "\N{ESCAPE}["

    if bold and underline:
        prefix += "1;4"
    elif bold:
        prefix += '1'
    elif underline:
        prefix += '4'
    else:
        prefix += '0'

    if text_color is not None:
        prefix += f";{text_color}"

    if background_color is not None:
        prefix += f";{background_color}"

    prefix += 'm'

    return f"{prefix}{string}\N{ESCAPE}[0m"

