"""Retro Code Screen renderer — black CRT screen, monospaced code, phosphor glow, scanlines.

Production spec:
- Background: Black CRT screen
- Subject: Lines of monospaced code text
- Treatment: CRT scanlines, phosphor glow, slight flicker
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from graphics_generator.fonts import load_mono_font

WIDTH, HEIGHT = 1920, 1080

# Fake retro BASIC-ish code lines for atmospheric effect
_CODE_LINES = [
    "10 REM === SYSTEM DIAGNOSTICS ===",
    "20 PRINT \"INITIALIZING SEQUENCE...\"",
    "30 FOR I = 1 TO 1024",
    "40   READ A(I)",
    "50   IF A(I) = 0 THEN GOTO 90",
    "60   POKE 49152 + I, A(I)",
    "70   PRINT CHR$(A(I));",
    "80 NEXT I",
    "90 PRINT",
    "100 PRINT \"DATA LOADED:\" ; I ; \"BYTES\"",
    "110 REM --- SCANNING RECORDS ---",
    "120 OPEN \"RECORDS.DAT\" FOR INPUT AS #1",
    "130 INPUT #1, N$, D$, L$",
    "140 IF N$ = \"\" THEN CLOSE #1: GOTO 170",
    "150 PRINT N$; TAB(20); D$; TAB(40); L$",
    "160 GOTO 130",
    "170 PRINT \"--- END OF RECORDS ---\"",
    "180 PRINT \"ENTRIES PROCESSED:\" ; CNT",
    "190 SYS 64738",
    "200 END",
    "RUN",
    "INITIALIZING SEQUENCE...",
    ">_ READY",
]


def _draw_code_text(img: Image.Image) -> Image.Image:
    """Draw code lines on black background, return glow layer for compositing."""
    draw = ImageDraw.Draw(img)
    font = load_mono_font(size=22)

    rng = random.Random(42)
    y = 40
    line_height = 36

    for line in _CODE_LINES:
        if y > HEIGHT - 60:
            break
        # Slight brightness variation per line
        brightness = rng.randint(200, 255)
        draw.text(
            (60, y),
            line,
            fill=(brightness, brightness, brightness, 255),
            font=font,
        )
        y += line_height

    return img


def _add_phosphor_glow(img: Image.Image) -> None:
    """Green-white phosphor glow effect via blur + composite."""
    glow = img.copy()
    # Tint slightly green for CRT phosphor
    glow_data = glow.load()
    for y in range(HEIGHT):
        for x in range(0, WIDTH, 3):  # Sample every 3rd pixel for speed
            r, g, b, a = glow_data[x, y]
            if r > 30:
                glow_data[x, y] = (r // 2, min(255, g + 20), b // 2, a // 3)

    glow = glow.filter(ImageFilter.GaussianBlur(radius=6))
    img.alpha_composite(glow)


def _add_scanlines(img: Image.Image) -> None:
    """CRT scanlines."""
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(0, HEIGHT, 3):
        draw.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, 50))
    img.alpha_composite(overlay)


def render(shot: dict, output_dir: Path) -> Path:
    """Render a retro code screen graphic."""
    shot_id = shot.get("id", "S000")
    slug = "code_screen"

    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))

    _draw_code_text(img)
    _add_phosphor_glow(img)
    _add_scanlines(img)

    filename = f"{shot_id}_{slug}.png"
    out_path = output_dir / filename
    img.save(str(out_path), "PNG")
    return out_path
