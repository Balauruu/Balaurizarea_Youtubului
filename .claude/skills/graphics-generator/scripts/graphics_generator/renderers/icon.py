"""Symbolic Icon renderer — crimson background with scanline texture, centered icon silhouette.

Production spec:
- Background: Deep crimson solid with scanline texture
- Subject: Recognizable silhouette icon
- Treatment: Flat graphic, horizontal scanlines, bold contrast
"""
from pathlib import Path

from PIL import Image, ImageDraw

from graphics_generator.fonts import load_font

WIDTH, HEIGHT = 1920, 1080


def _draw_crimson_bg(draw: ImageDraw.Draw) -> None:
    """Deep crimson background."""
    draw.rectangle([(0, 0), (WIDTH, HEIGHT)], fill=(140, 15, 15, 255))


def _draw_scanlines(img: Image.Image, spacing: int = 3, alpha: int = 50) -> None:
    """Horizontal scanline texture."""
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for y in range(0, HEIGHT, spacing):
        d.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, alpha))
    img.alpha_composite(overlay)


def _draw_icon_silhouette(draw: ImageDraw.Draw) -> None:
    """Centered geometric icon — a diamond/rhombus shape as a generic symbolic icon."""
    cx, cy = WIDTH // 2, HEIGHT // 2
    size = 200

    # Diamond shape
    draw.polygon(
        [
            (cx, cy - size),
            (cx + size, cy),
            (cx, cy + size),
            (cx - size, cy),
        ],
        fill=(0, 0, 0, 255),
    )

    # Inner smaller diamond for visual interest
    inner = size // 2
    draw.polygon(
        [
            (cx, cy - inner),
            (cx + inner, cy),
            (cx, cy + inner),
            (cx - inner, cy),
        ],
        fill=(80, 5, 5, 255),
    )


def render(shot: dict, output_dir: Path) -> Path:
    """Render a symbolic icon graphic."""
    shot_id = shot.get("id", "S000")
    label = shot.get("visual_need", "")
    slug = "symbolic_icon"

    img = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    _draw_crimson_bg(draw)
    _draw_icon_silhouette(draw)
    _draw_scanlines(img)

    # Bold label below icon
    if label:
        font = load_font(size=40, bold=True)
        short_label = label[:40].upper()
        bbox = draw.textbbox((0, 0), short_label, font=font)
        tw = bbox[2] - bbox[0]
        tx = (WIDTH - tw) // 2
        ty = HEIGHT - 100
        draw.text((tx, ty), short_label, fill=(255, 255, 255, 230), font=font)

    filename = f"{shot_id}_{slug}.png"
    out_path = output_dir / filename
    img.save(str(out_path), "PNG")
    return out_path
