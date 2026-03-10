"""Stage 4: Annotated Contact Sheet generation for LLM analysis."""

import os
import math
from PIL import Image, ImageDraw, ImageFont


SHEET_WIDTH = 1568
COLS = 3
ROWS = 3
FRAMES_PER_SHEET = COLS * ROWS
PADDING = 4
LABEL_HEIGHT = 30
LABEL_BG = (51, 51, 51)  # #333
LABEL_FG = (255, 255, 255)
NARRATION_MAX_CHARS = 40
JPEG_QUALITY = 90


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def _get_font(size: int = 14):
    """Try to load a monospace font, fall back to default."""
    try:
        return ImageFont.truetype("consola.ttf", size)
    except OSError:
        try:
            return ImageFont.truetype("DejaVuSansMono.ttf", size)
        except OSError:
            return ImageFont.load_default()


def generate_contact_sheets(frames: list[dict], output_dir: str) -> list[str]:
    """Generate annotated 3x3 contact sheets from frame data.

    Each cell contains the frame image + a label bar with frame ID, timestamp,
    and narration snippet.

    Args:
        frames: List of frame dicts (must have frame_path, frame_id, timestamp,
                narration).
        output_dir: Directory to write contact sheet JPEGs.

    Returns:
        List of output file paths.
    """
    if not frames:
        return []

    os.makedirs(output_dir, exist_ok=True)

    SHEET_HEIGHT = 1568
    cell_width = (SHEET_WIDTH - PADDING * (COLS + 1)) // COLS
    cell_height = (SHEET_HEIGHT - PADDING * (ROWS + 1)) // ROWS
    cell_img_height = cell_height - LABEL_HEIGHT
    sheet_height = SHEET_HEIGHT

    font = _get_font()
    output_paths = []

    num_sheets = math.ceil(len(frames) / FRAMES_PER_SHEET)

    for sheet_idx in range(num_sheets):
        batch = frames[
            sheet_idx * FRAMES_PER_SHEET : (sheet_idx + 1) * FRAMES_PER_SHEET
        ]
        sheet = Image.new("RGB", (SHEET_WIDTH, sheet_height), (255, 255, 255))
        draw = ImageDraw.Draw(sheet)

        for i, frame in enumerate(batch):
            col = i % COLS
            row = i // COLS

            x = PADDING + col * (cell_width + PADDING)
            y = PADDING + row * (cell_height + PADDING)

            # Load and resize frame image
            try:
                img = Image.open(frame["frame_path"])
                img = img.resize((cell_width, cell_img_height), Image.LANCZOS)
                sheet.paste(img, (x, y))
            except (FileNotFoundError, OSError):
                # Draw placeholder
                draw.rectangle(
                    [x, y, x + cell_width, y + cell_img_height], fill=(80, 80, 80)
                )
                draw.text(
                    (x + 10, y + cell_img_height // 2),
                    "Missing",
                    fill=LABEL_FG,
                    font=font,
                )

            # Draw label bar
            label_y = y + cell_img_height
            draw.rectangle(
                [x, label_y, x + cell_width, label_y + LABEL_HEIGHT], fill=LABEL_BG
            )

            snippet = _truncate(frame.get("narration", ""), NARRATION_MAX_CHARS)
            label_text = (
                f"F{frame['frame_id']:03d} | {frame['timestamp']} | \"{snippet}\""
            )
            draw.text((x + 4, label_y + 6), label_text, fill=LABEL_FG, font=font)

        sheet_path = os.path.join(output_dir, f"contact_sheet_{sheet_idx:03d}.jpg")
        sheet.save(sheet_path, quality=JPEG_QUALITY)
        output_paths.append(sheet_path)
        print(f"Saved contact sheet: {sheet_path} ({len(batch)} frames)")

    return output_paths
