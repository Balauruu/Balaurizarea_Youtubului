"""Font loading utilities for graphics renderers."""
from pathlib import Path

from PIL import ImageFont


def load_font(size: int = 48, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a font with Windows fallback chain.

    Tries arialbd.ttf/arial.ttf from Windows font dir, then Pillow default.
    """
    win_fonts = Path("C:/Windows/Fonts")
    candidates = (
        [win_fonts / "arialbd.ttf", win_fonts / "arial.ttf"] if bold
        else [win_fonts / "arial.ttf", win_fonts / "arialbd.ttf"]
    )

    for font_path in candidates:
        if font_path.exists():
            try:
                return ImageFont.truetype(str(font_path), size)
            except (OSError, IOError):
                continue

    return ImageFont.load_default()


def load_mono_font(size: int = 24) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a monospaced font for code screens.

    Tries consola.ttf (Consolas) from Windows font dir, then Pillow default.
    """
    win_fonts = Path("C:/Windows/Fonts")
    candidates = [
        win_fonts / "consola.ttf",
        win_fonts / "consolab.ttf",
        win_fonts / "cour.ttf",
    ]

    for font_path in candidates:
        if font_path.exists():
            try:
                return ImageFont.truetype(str(font_path), size)
            except (OSError, IOError):
                continue

    return ImageFont.load_default()
