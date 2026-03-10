import os
import pytest
from PIL import Image
from visual_style_extractor.contact_sheets import generate_contact_sheets


def _make_frame(frame_id, tmp_path, color=(100, 50, 50)):
    """Create a test frame image and return a frame dict."""
    img = Image.new("RGB", (640, 360), color=color)
    path = str(tmp_path / f"frame_{frame_id:04d}.jpg")
    img.save(path)
    return {
        "frame_id": frame_id,
        "frame_path": path,
        "timestamp": f"00:{frame_id * 10:02d}",
        "scene_duration": 3.0,
        "represents_count": 1,
        "narration": f"This is narration text for frame {frame_id} which may be quite long.",
    }


def test_single_sheet_created(tmp_path):
    """5 frames should produce exactly 1 contact sheet (9 per sheet)."""
    frames = [_make_frame(i, tmp_path) for i in range(1, 6)]
    output_dir = str(tmp_path / "contact_sheets")

    sheets = generate_contact_sheets(frames, output_dir)
    assert len(sheets) == 1
    assert os.path.exists(sheets[0])


def test_multiple_sheets(tmp_path):
    """12 frames should produce 2 contact sheets."""
    frames = [_make_frame(i, tmp_path, color=(i * 20, i * 10, 50)) for i in range(1, 13)]
    output_dir = str(tmp_path / "contact_sheets")

    sheets = generate_contact_sheets(frames, output_dir)
    assert len(sheets) == 2


def test_sheet_dimensions(tmp_path):
    """Sheet should be 1568x1568px."""
    frames = [_make_frame(i, tmp_path) for i in range(1, 4)]
    output_dir = str(tmp_path / "contact_sheets")

    sheets = generate_contact_sheets(frames, output_dir)
    img = Image.open(sheets[0])
    assert img.width == 1568
    assert img.height == 1568


def test_empty_frames(tmp_path):
    """Empty frame list should return empty list."""
    output_dir = str(tmp_path / "contact_sheets")
    sheets = generate_contact_sheets([], output_dir)
    assert sheets == []
