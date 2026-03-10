"""Stage 4: Contact Sheet generation for LLM analysis."""

import os
import math
from PIL import Image

SHEET_SIZE = 1568
COLS = 3
ROWS = 3
FRAMES_PER_SHEET = COLS * ROWS
PADDING = 4
JPEG_QUALITY = 90


def generate_contact_sheets(frames: list[dict], output_dir: str) -> list[str]:
    """Generate 3x3 contact sheets from frame data.

    Each cell contains only the frame image — no labels or metadata.
    Narration context is passed to subagents via the manifest JSON separately.

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

    cell_width = (SHEET_SIZE - PADDING * (COLS + 1)) // COLS
    cell_height = (SHEET_SIZE - PADDING * (ROWS + 1)) // ROWS

    output_paths = []
    num_sheets = math.ceil(len(frames) / FRAMES_PER_SHEET)

    for sheet_idx in range(num_sheets):
        batch = frames[
            sheet_idx * FRAMES_PER_SHEET : (sheet_idx + 1) * FRAMES_PER_SHEET
        ]
        sheet = Image.new("RGB", (SHEET_SIZE, SHEET_SIZE), (255, 255, 255))

        for i, frame in enumerate(batch):
            col = i % COLS
            row = i // COLS

            x = PADDING + col * (cell_width + PADDING)
            y = PADDING + row * (cell_height + PADDING)

            try:
                img = Image.open(frame["frame_path"])
                img = img.resize((cell_width, cell_height), Image.LANCZOS)
                sheet.paste(img, (x, y))
            except (FileNotFoundError, OSError):
                pass  # Leave cell white as placeholder

        sheet_path = os.path.join(output_dir, f"contact_sheet_{sheet_idx:03d}.jpg")
        sheet.save(sheet_path, quality=JPEG_QUALITY)
        output_paths.append(sheet_path)
        print(f"Saved contact sheet: {sheet_path} ({len(batch)} frames)")

    return output_paths
