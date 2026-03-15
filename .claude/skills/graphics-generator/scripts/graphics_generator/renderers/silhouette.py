"""Silhouette Figure renderer — deep red gradient, black humanoid silhouette, optional label.

Production spec from VISUAL_STYLE_GUIDE:
- Background: Deep red smoky gradient
- Subject: Black geometric humanoid silhouette (head circle + body trapezoid)
- Treatment: Atmospheric fog, film grain
- Text: Optional white sans-serif role label
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from graphics_generator.fonts import load_font

WIDTH, HEIGHT = 1920, 1080


def _draw_gradient_bg(img: Image.Image) -> None:
    """Deep red smoky gradient background."""
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(80 + 60 * t)
        g = int(5 + 10 * t)
        b = int(5 + 15 * t)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))


def _draw_silhouette(draw: ImageDraw.Draw, cx: int, cy: int, scale: float = 1.0) -> None:
    """Draw a geometric humanoid silhouette at center (cx, cy)."""
    head_r = int(40 * scale)
    body_top_w = int(60 * scale)
    body_bot_w = int(90 * scale)
    body_h = int(180 * scale)

    # Head circle
    draw.ellipse(
        [cx - head_r, cy - head_r - body_h // 2 - head_r,
         cx + head_r, cy + head_r - body_h // 2 - head_r],
        fill=(0, 0, 0, 255),
    )

    # Body trapezoid
    body_top_y = cy - body_h // 2 + head_r
    body_bot_y = cy + body_h // 2 + head_r
    draw.polygon(
        [
            (cx - body_top_w, body_top_y),
            (cx + body_top_w, body_top_y),
            (cx + body_bot_w, body_bot_y),
            (cx - body_bot_w, body_bot_y),
        ],
        fill=(0, 0, 0, 255),
    )


def _add_fog_overlay(img: Image.Image) -> None:
    """Subtle fog overlay for atmospheric depth."""
    fog = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    fog_draw = ImageDraw.Draw(fog)

    rng = random.Random(42)
    for _ in range(15):
        x = rng.randint(0, WIDTH)
        y = rng.randint(HEIGHT // 2, HEIGHT)
        r = rng.randint(100, 300)
        fog_draw.ellipse(
            [x - r, y - r, x + r, y + r],
            fill=(60, 20, 20, 25),
        )

    fog = fog.filter(ImageFilter.GaussianBlur(radius=40))
    img.alpha_composite(fog)


def _add_scanlines(img: Image.Image, spacing: int = 4, alpha: int = 30) -> None:
    """CRT scanline overlay."""
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(0, HEIGHT, spacing):
        draw.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, alpha))
    img.alpha_composite(overlay)


def render(shot: dict, output_dir: Path) -> Path:
    """Render a silhouette figure graphic."""
    shot_id = shot.get("id", "S000")
    label = shot.get("text_content") or shot.get("building_block_variant", "")
    slug = "silhouette_figure"

    img = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    _draw_gradient_bg(img)
    _draw_silhouette(draw, WIDTH // 2, HEIGHT // 2, scale=1.5)
    _add_fog_overlay(img)
    _add_scanlines(img)

    # Optional label text
    if label:
        font = load_font(size=36, bold=True)
        label_upper = label.upper()
        bbox = draw.textbbox((0, 0), label_upper, font=font)
        tw = bbox[2] - bbox[0]
        tx = (WIDTH - tw) // 2
        ty = HEIGHT - 120
        draw.text((tx, ty), label_upper, fill=(255, 255, 255, 220), font=font)

    filename = f"{shot_id}_{slug}.png"
    out_path = output_dir / filename
    img.save(str(out_path), "PNG")
    return out_path
