from copy import copy
from importlib.resources import path
from io import BytesIO
from typing import Any

from PIL import Image, ImageDraw, ImageFont


height_correction = 14
dnd_roll_text_margin = 25
with path(f'{__package__}.static.images', 'scroll_bg.jpg') as p:
    dnd_roll_image: Image = Image.open(str(p)).resize((1080, 1080))
with path(f'{__package__}.static.fonts', 'Blackcastlemf-BG5n.ttf') as p:
    dnd_roll_font = ImageFont.truetype(str(p), 100)


def get_roll_text(value: Any) -> BytesIO:
    w, h = dnd_roll_font.getsize(str(value))

    img = copy(dnd_roll_image)

    img = img.resize((w + dnd_roll_text_margin * 2, h - height_correction + dnd_roll_text_margin * 2))

    draw = ImageDraw.Draw(img)
    draw.text((dnd_roll_text_margin, dnd_roll_text_margin-height_correction), str(value), font=dnd_roll_font, fill='black')

    res = BytesIO()
    img.save(res, 'PNG')

    return res
