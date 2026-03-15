"""Abstract Texture renderer — crimson background with dark vertical streaks/drips, heavy scanlines.

Production spec:
- Background: Deep crimson/dark red solid
- Subject: Dark vertical streaks, drip shapes, abstract marks
- Treatment: Heavy scanlines, noise, textured overlay
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

WIDTH, HEIGHT = 1920, 1080


def _draw_crimson_bg(draw: ImageDraw.Draw) -> None:
    """Deep crimson background."""
    draw.rectangle([(0, 0), (WIDTH, HEIGHT)], fill=(120, 10, 10, 255))


def _draw_streaks(img: Image.Image, count: int = 12) -> None:
    """Random dark vertical streaks/drips."""
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    rng = random.Random(99)

    for _ in range(count):
        x = rng.randint(50, WIDTH - 50)
        y_start = rng.randint(0, HEIGHT // 3)
        y_end = rng.randint(HEIGHT // 2, HEIGHT)
        w = rng.randint(3, 15)
        alpha = rng.randint(120, 220)

        # Irregular drip shape
        points = []
        for y in range(y_start, y_end, 10):
            wobble = rng.randint(-w, w)
            points.append((x + wobble, y))

        if len(points) >= 2:
            for i in range(len(points) - 1):
                draw.line(
                    [points[i], points[i + 1]],
                    fill=(20, 0, 0, alpha),
                    width=w,
                )

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=2))
    img.alpha_composite(overlay)


def _add_heavy_scanlines(img: Image.Image) -> None:
    """Heavy scanline overlay."""
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(0, HEIGHT, 3):
        draw.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, 60))
    img.alpha_composite(overlay)


def render(shot: dict, output_dir: Path) -> Path:
    """Render an abstract texture graphic."""
    shot_id = shot.get("id", "S000")
    slug = "abstract_texture"

    img = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    _draw_crimson_bg(draw)
    _draw_streaks(img)
    _add_heavy_scanlines(img)

    filename = f"{shot_id}_{slug}.png"
    out_path = output_dir / filename
    img.save(str(out_path), "PNG")
    return out_path
