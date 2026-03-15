"""Static Noise / Corruption renderer — full-frame noise with faint dark silhouette.

Production spec:
- Background: Full-frame TV static/noise
- Subject: Barely visible dark silhouette of a structure or shape
- Treatment: Extreme static overlay, near-total obscuration, monochrome
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

WIDTH, HEIGHT = 1920, 1080


def _generate_noise(img: Image.Image) -> None:
    """Fill image with random static noise."""
    pixels = img.load()
    rng = random.Random(55)

    for y in range(HEIGHT):
        for x in range(WIDTH):
            v = rng.randint(0, 255)
            pixels[x, y] = (v, v, v, 255)


def _draw_faint_silhouette(img: Image.Image) -> None:
    """Draw a barely visible building silhouette blended into the noise."""
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    cx = WIDTH // 2

    # Simple building shape
    draw.rectangle(
        [(cx - 120, HEIGHT // 3), (cx + 120, HEIGHT - 100)],
        fill=(0, 0, 0, 40),
    )
    # Roof triangle
    draw.polygon(
        [
            (cx - 150, HEIGHT // 3),
            (cx, HEIGHT // 3 - 80),
            (cx + 150, HEIGHT // 3),
        ],
        fill=(0, 0, 0, 35),
    )

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=5))
    img.alpha_composite(overlay)


def render(shot: dict, output_dir: Path) -> Path:
    """Render a static noise / corruption graphic."""
    shot_id = shot.get("id", "S000")
    slug = "static_noise"

    img = Image.new("RGBA", (WIDTH, HEIGHT))

    _generate_noise(img)
    _draw_faint_silhouette(img)

    filename = f"{shot_id}_{slug}.png"
    out_path = output_dir / filename
    img.save(str(out_path), "PNG")
    return out_path
