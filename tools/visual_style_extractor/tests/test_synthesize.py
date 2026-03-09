import json
import pytest
from visual_style_extractor.synthesize import (
    aggregate_by_scene_type,
    compute_proportions,
    generate_style_guide,
)


SAMPLE_ANALYSIS = [
    {
        "frame_id": "F001",
        "timestamp": "00:10",
        "scene_type": "archival_photo",
        "background": "solid black",
        "main_element": "sepia photograph of a building",
        "overlays": ["film grain", "vignette"],
        "text_elements": None,
        "content_description": None,
        "narrative_function": "establishing historical context",
        "confidence": 4,
    },
    {
        "frame_id": "F002",
        "timestamp": "01:20",
        "scene_type": "archival_photo",
        "background": "solid black",
        "main_element": "black-and-white portrait of a man",
        "overlays": ["film grain"],
        "text_elements": None,
        "content_description": None,
        "narrative_function": "introducing key figure",
        "confidence": 5,
    },
    {
        "frame_id": "F003",
        "timestamp": "02:30",
        "scene_type": "map_animation",
        "background": "solid black",
        "main_element": "particle map of Europe",
        "overlays": ["vignette"],
        "text_elements": "location label top-right in teal, ALL CAPS sans-serif",
        "content_description": None,
        "narrative_function": "geographic context",
        "confidence": 4,
    },
]

SAMPLE_MANIFEST = {
    "frames": [
        {"frame_id": 1, "timestamp": "00:10", "scene_duration": 5.0, "represents_count": 2, "narration": "In 1920..."},
        {"frame_id": 2, "timestamp": "01:20", "scene_duration": 4.0, "represents_count": 1, "narration": "The man..."},
        {"frame_id": 3, "timestamp": "02:30", "scene_duration": 6.0, "represents_count": 3, "narration": "Located in..."},
    ],
    "video_duration": 600.0,
    "total_scenes_detected": 80,
    "unique_frames_after_dedup": 3,
}


def test_aggregate_by_scene_type():
    grouped = aggregate_by_scene_type(SAMPLE_ANALYSIS)
    assert "archival_photo" in grouped
    assert len(grouped["archival_photo"]) == 2
    assert "map_animation" in grouped
    assert len(grouped["map_animation"]) == 1


def test_compute_proportions():
    grouped = aggregate_by_scene_type(SAMPLE_ANALYSIS)
    proportions = compute_proportions(grouped, SAMPLE_MANIFEST)
    assert "archival_photo" in proportions
    # archival_photo: (5*2 + 4*1) / 600 = 14/600 ≈ 2.33%
    assert proportions["archival_photo"]["proportion"] == pytest.approx(14.0 / 600.0, rel=0.01)


def test_low_confidence_filtered():
    analysis = SAMPLE_ANALYSIS + [{
        "frame_id": "F004",
        "timestamp": "03:00",
        "scene_type": "b_roll_footage",
        "background": "unclear",
        "main_element": "unclear",
        "overlays": [],
        "text_elements": None,
        "content_description": "unclear",
        "narrative_function": "unclear",
        "confidence": 2,
    }]
    grouped = aggregate_by_scene_type(analysis, min_confidence=3)
    # The low-confidence frame should be excluded
    assert "b_roll_footage" not in grouped


def test_generate_style_guide(tmp_path):
    output_path = str(tmp_path / "VISUAL_STYLE_GUIDE.md")
    generate_style_guide(
        analysis_results=SAMPLE_ANALYSIS,
        manifest=SAMPLE_MANIFEST,
        video_title="Test Documentary",
        video_source="https://youtube.com/test",
        output_path=output_path,
    )
    with open(output_path) as f:
        content = f.read()

    assert "# Visual Style Guide" in content
    assert "archival_photo" in content.lower() or "Archival Photo" in content
    assert "map_animation" in content.lower() or "Map Animation" in content
    assert "Test Documentary" in content
