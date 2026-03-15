"""Glitch Stinger renderer — black background, vertical red bars, scanline distortion, RGB split.

Production spec:
- Background: Solid black with digital noise
- Subject: Vertical red bar with scanline distortion, fragmented glitch patterns
- Treatment: Heavy VHS glitch, chromatic aberration, RGB split
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw

WIDTH, HEIGHT = 1920, 1080


def _draw_vertical_red_bars(draw: ImageDraw.Draw) -> None:
    """Vertical red bars at random positions."""
    rng = random.Random(77)
    for _ in range(3):
        x = rng.randint(200, WIDTH - 200)
        w = rng.randint(30, 120)
        alpha = rng.randint(180, 255)
        draw.rectangle(
            [(x - w // 2, 0), (x + w // 2, HEIGHT)],
            fill=(200, 0, 0, alpha),
        )


def _draw_scanline_distortion(img: Image.Image) -> None:
    """Horizontal scanline distortion bands — shift horizontal strips."""
    pixels = img.load()
    rng = random.Random(33)

    for _ in range(20):
        y = rng.randint(0, HEIGHT - 1)
        band_h = rng.randint(2, 8)
        shift = rng.randint(-50, 50)

        for dy in range(band_h):
            yy = min(y + dy, HEIGHT - 1)
            row = [pixels[x, yy] for x in range(WIDTH)]
            for x in range(WIDTH):
                src_x = (x - shift) % WIDTH
                pixels[x, yy] = row[src_x]


def _add_rgb_split(img: Image.Image) -> Image.Image:
    """RGB channel split effect — offset red and blue channels."""
    r, g, b, a = img.split()

    from PIL import ImageChops

    offset = 8
    # Shift red channel left
    r_shifted = ImageChops.offset(r, -offset, 0)
    # Shift blue channel right
    b_shifted = ImageChops.offset(b, offset, 0)

    return Image.merge("RGBA", (r_shifted, g, b_shifted, a))


def _add_scanlines(img: Image.Image) -> None:
    """Faint CRT scanlines."""
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(0, HEIGHT, 2):
        draw.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, 40))
    img.alpha_composite(overlay)


def render(shot: dict, output_dir: Path) -> Path:
    """Render a glitch stinger graphic."""
    shot_id = shot.get("id", "S000")
    slug = "glitch_stinger"

    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    _draw_vertical_red_bars(draw)
    _draw_scanline_distortion(img)
    img = _add_rgb_split(img)
    _add_scanlines(img)

    filename = f"{shot_id}_{slug}.png"
    out_path = output_dir / filename
    img.save(str(out_path), "PNG")
    return out_path
