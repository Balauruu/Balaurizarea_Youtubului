"""Character Profile Card renderer — dark background, vertical magenta accent bars, placeholder photos.

Production spec:
- Background: Dark black with vertical magenta/red accent bands on sides
- Subject: Portrait photos as placeholder black rectangles with teal text labels
- Treatment: Desaturated, CRT scanlines, VHS color bleed
"""
from pathlib import Path

from PIL import Image, ImageDraw

from graphics_generator.fonts import load_font

WIDTH, HEIGHT = 1920, 1080


def _draw_background(draw: ImageDraw.Draw) -> None:
    """Dark background with vertical magenta accent bars."""
    draw.rectangle([(0, 0), (WIDTH, HEIGHT)], fill=(15, 15, 15, 255))

    # Left magenta accent bar
    draw.rectangle([(0, 0), (40, HEIGHT)], fill=(180, 20, 80, 255))
    draw.rectangle([(50, 0), (55, HEIGHT)], fill=(180, 20, 80, 120))

    # Right magenta accent bar
    draw.rectangle([(WIDTH - 40, 0), (WIDTH, HEIGHT)], fill=(180, 20, 80, 255))
    draw.rectangle([(WIDTH - 55, 0), (WIDTH - 50, HEIGHT)], fill=(180, 20, 80, 120))


def _draw_profile_cards(draw: ImageDraw.Draw, names: list[str]) -> None:
    """Draw placeholder profile card regions with teal labels."""
    font = load_font(size=28, bold=True)
    card_count = min(len(names), 4) if names else 3

    if card_count == 0:
        card_count = 3
        names = ["SUBJECT 1", "SUBJECT 2", "SUBJECT 3"]

    card_w = 280
    card_h = 350
    photo_h = 250
    spacing = 60
    total_w = card_count * card_w + (card_count - 1) * spacing
    start_x = (WIDTH - total_w) // 2
    start_y = (HEIGHT - card_h) // 2

    for i in range(card_count):
        x = start_x + i * (card_w + spacing)
        y = start_y

        # Photo placeholder — black rectangle
        draw.rectangle(
            [(x, y), (x + card_w, y + photo_h)],
            fill=(0, 0, 0, 255),
            outline=(40, 40, 40, 255),
            width=2,
        )

        # Redaction bar across face area
        bar_y = y + photo_h // 3
        draw.rectangle(
            [(x, bar_y), (x + card_w, bar_y + 40)],
            fill=(0, 0, 0, 255),
        )

        # Teal name label
        name = names[i] if i < len(names) else f"SUBJECT {i + 1}"
        name_upper = name.upper()
        bbox = draw.textbbox((0, 0), name_upper, font=font)
        tw = bbox[2] - bbox[0]
        tx = x + (card_w - tw) // 2
        ty = y + photo_h + 20
        # Teal/cyan color
        draw.text((tx, ty), name_upper, fill=(0, 210, 200, 255), font=font)


def _add_scanlines(img: Image.Image) -> None:
    """CRT scanline overlay."""
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(0, HEIGHT, 3):
        draw.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, 35))
    img.alpha_composite(overlay)


def render(shot: dict, output_dir: Path) -> Path:
    """Render a character profile card graphic."""
    shot_id = shot.get("id", "S000")
    slug = "profile_card"

    # Extract names from shot data if available
    names = shot.get("names", [])
    if not names:
        visual_need = shot.get("visual_need", "")
        if visual_need:
            names = [visual_need[:25]]
        else:
            names = ["SUBJECT 1", "SUBJECT 2", "SUBJECT 3"]

    img = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    _draw_background(draw)
    _draw_profile_cards(draw, names)
    _add_scanlines(img)

    filename = f"{shot_id}_{slug}.png"
    out_path = output_dir / filename
    img.save(str(out_path), "PNG")
    return out_path
