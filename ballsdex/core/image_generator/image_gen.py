import os
from pathlib import Path
import textwrap
from PIL import Image, ImageFont, ImageDraw, ImageOps
from typing import TYPE_CHECKING
from ballsdex.core.models import Economy, Regime

if TYPE_CHECKING:
    from ballsdex.core.models import BallInstance


SOURCES_PATH = Path(os.path.dirname(os.path.abspath(__file__)), "./src")
WIDTH = 1500
HEIGHT = 2000

RECTANGLE_WIDTH = WIDTH - 40
RECTANGLE_HEIGHT = (HEIGHT // 5) * 2

CORNERS = ((34, 261), (1393, 992))
artwork_size = [b - a for a, b in zip(*CORNERS)]


title_font = ImageFont.truetype(str(SOURCES_PATH / "ArsenicaTrial-Extrabold.ttf"), 170)
capacity_name_font = ImageFont.truetype(str(SOURCES_PATH / "Bobby Jones Soft.otf"), 110)
capacity_description_font = ImageFont.truetype(str(SOURCES_PATH / "OpenSans-Semibold.ttf"), 75)
stats_font = ImageFont.truetype(str(SOURCES_PATH / "Bobby Jones Soft.otf"), 130)

democracy = Image.open(str(SOURCES_PATH / "democracy.png"))
dictatorship = Image.open(str(SOURCES_PATH / "dictatorship.png"))
union = Image.open(str(SOURCES_PATH / "union.png"))

capitalist = Image.open(str(SOURCES_PATH / "capitalist.png"))
communist = Image.open(str(SOURCES_PATH / "communist.png"))

test = Image.open(str(SOURCES_PATH / "fr_test.png"))


def draw_card(ball_instance: "BallInstance"):
    ball = ball_instance.ball
    if ball.regime == Regime.DEMOCRACY:
        image = democracy.copy()
    elif ball.regime == Regime.DICTATORSHIP:
        image = dictatorship.copy()
    elif ball.regime == Regime.UNION:
        image = union.copy()
    else:
        raise RuntimeError(f"Regime unknown: {ball.regime}")

    if ball.economy == Economy.CAPITALIST:
        icon = capitalist.copy()
    elif ball.economy == Economy.COMMUNIST:
        icon = communist.copy
    elif ball.economy == Economy.ANARCHY:
        icon = communist.copy()
    else:
        raise RuntimeError(f"Economy unknown: {ball.economy}")

    draw = ImageDraw.Draw(image)
    draw.text((50, 20), ball.country, font=title_font)
    for i, line in enumerate(textwrap.wrap(f"Ability: {ball.capacity_name}", width=28)):
        draw.text(
            (100, 1050 + 100 * i),
            line,
            font=capacity_name_font,
            fill=(230, 230, 230, 255),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 255),
        )
    for i, line in enumerate(textwrap.wrap(ball.capacity_description, width=33)):
        draw.text(
            (60, 1300 + 60 * i),
            line,
            font=capacity_description_font,
            stroke_width=1,
            stroke_fill=(0, 0, 0, 255),
        )
    draw.text(
        (320, 1670),
        str(ball.health + ball_instance.health_bonus),
        font=stats_font,
        fill=(237, 115, 101, 255),
        stroke_width=1,
        stroke_fill=(0, 0, 0, 255),
    )
    draw.text(
        (960, 1670),
        str(ball.attack + ball_instance.attack_bonus),
        font=stats_font,
        fill=(252, 194, 76, 255),
        stroke_width=1,
        stroke_fill=(0, 0, 0, 255),
    )

    artwork = Image.open("." + ball.collection_card)
    image.paste(ImageOps.fit(artwork, artwork_size), CORNERS[0])

    icon = ImageOps.fit(icon, (192, 192))
    image.paste(icon, (1200, 30), mask=icon)

    return image