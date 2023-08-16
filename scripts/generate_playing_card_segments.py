
# Suits from https://game-icons.net/tags/board.html

from PIL import Image, ImageDraw, ImageFont


PATH = "../assets/segmented_playing_cards"

COLOR = "whitesmoke"  # background color: #F5F5F5
FONT = "calibrib.ttf"
FONT_SIZE = 500
IMAGE_SIZE = 512  # height and width
RADIUS = 100  # radius of rounded corners


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


BACK_SIZE = 500  # height and width
CELL_SIZE = 100  # height and width of diamonds and margins
DIAMOND_COLOR = "blue"


image = Image.new("RGBA", (BACK_SIZE * 2, BACK_SIZE * 3), COLOR)
draw = ImageDraw.Draw(image)

draw.line(
    (CELL_SIZE, CELL_SIZE, CELL_SIZE, BACK_SIZE * 3 - CELL_SIZE),
    fill = "black", width = 5
)
draw.line(
    (CELL_SIZE, CELL_SIZE, BACK_SIZE * 2 - CELL_SIZE, CELL_SIZE),
    fill = "black", width = 5
)
draw.line(
    (
        BACK_SIZE * 2 - CELL_SIZE, CELL_SIZE,
        BACK_SIZE * 2 - CELL_SIZE, BACK_SIZE * 3 - CELL_SIZE
    ),
    fill = "black", width = 5
)
draw.line(
    (
        CELL_SIZE, BACK_SIZE * 3 - CELL_SIZE,
        BACK_SIZE * 2 - CELL_SIZE, BACK_SIZE * 3 - CELL_SIZE
    ),
    fill = "black", width = 5
)

for x in range(CELL_SIZE // 2 * 3, BACK_SIZE * 2 - CELL_SIZE, CELL_SIZE):
    for y in range(CELL_SIZE // 2 * 3, BACK_SIZE * 3 - CELL_SIZE, CELL_SIZE):
        draw.regular_polygon((x, y, 50), 4, 45, fill = DIAMOND_COLOR)

alpha = Image.new('1', (BACK_SIZE * 2, BACK_SIZE * 3), COLOR)
alpha.paste(circle.crop((0, 0, RADIUS, RADIUS)), (0, 0))
alpha.paste(
    circle.crop((RADIUS, 0, RADIUS * 2, RADIUS)), (BACK_SIZE * 2 - RADIUS, 0)
)
alpha.paste(
    circle.crop((0, RADIUS, RADIUS, RADIUS * 2)), (0, BACK_SIZE * 3 - RADIUS)
)
alpha.paste(
    circle.crop((RADIUS, RADIUS, RADIUS * 2, RADIUS * 2)),
    (BACK_SIZE * 2 - RADIUS, BACK_SIZE * 3 - RADIUS)
)
image.putalpha(alpha)

top_left = image.crop((0, 0, BACK_SIZE, BACK_SIZE))
top_left.save(f"{PATH}/back_top_left_segment.png", "PNG")

top_right = image.crop((BACK_SIZE, 0, BACK_SIZE * 2, BACK_SIZE))
top_right.save(f"{PATH}/back_top_right_segment.png", "PNG")

middle_left = image.crop((0, BACK_SIZE, BACK_SIZE, BACK_SIZE * 2))
middle_left.save(f"{PATH}/back_middle_left_segment.png", "PNG")

middle_right = image.crop((BACK_SIZE, BACK_SIZE, BACK_SIZE * 2, BACK_SIZE * 2))
middle_right.save(f"{PATH}/back_middle_right_segment.png", "PNG")

bottom_left = image.crop((0, BACK_SIZE * 2, BACK_SIZE, BACK_SIZE * 3))
bottom_left.save(f"{PATH}/back_bottom_left_segment.png", "PNG")

bottom_right = image.crop(
    (BACK_SIZE, BACK_SIZE * 2, BACK_SIZE * 2, BACK_SIZE * 3)
)
bottom_right.save(f"{PATH}/back_bottom_right_segment.png", "PNG")

