import os
import pytest
from PIL import Image, ImageDraw
from visual_style_extractor.dedup import deduplicate_frames
from visual_style_extractor.scene_detect import SceneInfo


def _make_scene(num, path, duration=3.0):
    return SceneInfo(
        scene_number=num,
        start_time=float(num * 3),
        end_time=float(num * 3 + duration),
        duration=duration,
        keyframe_path=path,
    )


def test_identical_frames_deduped(tmp_path):
    """Two identical images should be deduped to one."""
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()

    # Create two identical images
    img = Image.new("RGB", (200, 200), color=(100, 50, 50))
    path_a = str(frames_dir / "frame_0000.jpg")
    path_b = str(frames_dir / "frame_0001.jpg")
    img.save(path_a)
    img.save(path_b)

    scenes = [
        _make_scene(0, path_a),
        _make_scene(1, path_b),
    ]

    result = deduplicate_frames(scenes, str(frames_dir))
    assert len(result) == 1
    assert result[0]["represents_count"] >= 2


def test_different_frames_kept(tmp_path):
    """Two very different images should both be kept."""
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()

    # Create images with distinct patterns (not just solid colors)
    # so that perceptual hashing sees them as genuinely different
    img_a = Image.new("RGB", (200, 200), color=(255, 255, 255))
    draw_a = ImageDraw.Draw(img_a)
    draw_a.rectangle([0, 0, 100, 200], fill=(0, 0, 0))  # left half black

    img_b = Image.new("RGB", (200, 200), color=(0, 0, 0))
    draw_b = ImageDraw.Draw(img_b)
    draw_b.rectangle([0, 0, 200, 100], fill=(255, 255, 255))  # top half white

    path_a = str(frames_dir / "frame_0000.jpg")
    path_b = str(frames_dir / "frame_0001.jpg")
    img_a.save(path_a)
    img_b.save(path_b)

    scenes = [
        _make_scene(0, path_a),
        _make_scene(1, path_b),
    ]

    result = deduplicate_frames(scenes, str(frames_dir), max_distance_threshold=5)
    assert len(result) == 2


def test_output_has_required_keys(tmp_path):
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()

    img = Image.new("RGB", (200, 200), color=(50, 100, 150))
    path = str(frames_dir / "frame_0000.jpg")
    img.save(path)

    scenes = [_make_scene(0, path)]
    result = deduplicate_frames(scenes, str(frames_dir))

    required_keys = {"frame_id", "frame_path", "timestamp", "scene_duration", "represents_count"}
    assert required_keys.issubset(set(result[0].keys()))
