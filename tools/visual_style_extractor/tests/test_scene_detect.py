import os
import json
import pytest
from unittest.mock import patch, MagicMock
from visual_style_extractor.scene_detect import detect_scenes, SceneInfo


def test_scene_info_structure():
    s = SceneInfo(scene_number=1, start_time=0.0, end_time=4.5, duration=4.5, keyframe_path="frame.jpg")
    assert s.scene_number == 1
    assert s.duration == 4.5


def test_detect_scenes_low_count_warning(tmp_path, capsys):
    """When fewer than 10 scenes detected, print a warning."""
    fake_scenes = [(MagicMock(get_seconds=MagicMock(return_value=0.0)),
                     MagicMock(get_seconds=MagicMock(return_value=5.0)))]

    with patch("visual_style_extractor.scene_detect._run_detection", return_value=fake_scenes):
        with patch("visual_style_extractor.scene_detect._extract_keyframes", return_value=["frame.jpg"]):
            results = detect_scenes("fake.mp4", str(tmp_path))

    captured = capsys.readouterr()
    assert "WARNING" in captured.out


def test_detect_scenes_returns_list(tmp_path):
    """Result is always a list of SceneInfo."""
    fake_scenes = []
    for i in range(15):
        start = MagicMock()
        start.get_seconds.return_value = float(i * 3)
        end = MagicMock()
        end.get_seconds.return_value = float(i * 3 + 3)
        fake_scenes.append((start, end))

    with patch("visual_style_extractor.scene_detect._run_detection", return_value=fake_scenes):
        with patch("visual_style_extractor.scene_detect._extract_keyframes",
                   return_value=[f"frame_{i:04d}.jpg" for i in range(15)]):
            results = detect_scenes("fake.mp4", str(tmp_path))

    assert isinstance(results, list)
    assert len(results) == 15
    assert all(isinstance(r, SceneInfo) for r in results)
