
# Suits from https://game-icons.net/tags/board.html

from PIL import Image, ImageDraw, ImageFont


PATH = "../assets/segmented_playing_cards"

COLOR = "whitesmoke"  # #F5F5F5
FONT = "calibrib.ttf"
FONT_SIZE = 500
IMAGE_SIZE = 512  # height and width
RADIUS = 100


circle = Image.new('1', (RADIUS * 2, RADIUS * 2), 0)
circle_draw = ImageDraw.Draw(circle)
circle_draw.ellipse((0, 0, RADIUS * 2 - 1, RADIUS * 2 - 1), fill = COLOR)

for color in ("black", "red"):
    for segment in ("top_left", "bottom_right"):
        for value in (
            'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', "K"
        ):
            image = Image.new("RGBA", (IMAGE_SIZE, IMAGE_SIZE), COLOR)
            draw = ImageDraw.Draw(image)

            draw.text(
                (256, 256), text = value, fill = color,
                font = ImageFont.truetype(FONT, FONT_SIZE), anchor = "mm"
            )

            alpha = Image.new('1', (IMAGE_SIZE, IMAGE_SIZE), COLOR)
            if segment == "top_left":
                alpha.paste(circle.crop((0, 0, RADIUS, RADIUS)), (0, 0))
            else:
                alpha.paste(
                    circle.crop((RADIUS, RADIUS, RADIUS * 2, RADIUS * 2)),
                    (IMAGE_SIZE - RADIUS, IMAGE_SIZE - RADIUS)
                )
            image.putalpha(alpha)

            image.save(f"{PATH}/{color}_{segment}_{value}_segment.png", "PNG")

image = Image.new("RGBA", (IMAGE_SIZE, IMAGE_SIZE), COLOR)
draw = ImageDraw.Draw(image)

alpha = Image.new('1', (IMAGE_SIZE, IMAGE_SIZE), COLOR)
alpha.paste(
    circle.crop((0, RADIUS, RADIUS, RADIUS * 2)), (0, IMAGE_SIZE - RADIUS)
)
image.putalpha(alpha)
image.save(f"{PATH}/blank_bottom_left_segment.png", "PNG")

alpha = Image.new('1', (IMAGE_SIZE, IMAGE_SIZE), COLOR)
alpha.paste(
    circle.crop((RADIUS, 0, RADIUS * 2, RADIUS)), (IMAGE_SIZE - RADIUS, 0)
)
image.putalpha(alpha)
image.save(f"{PATH}/blank_top_right_segment.png", "PNG")

