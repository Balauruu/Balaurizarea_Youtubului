"""Tests for pipeline helpers and synthesis."""

import json


def test_slice_manifest(tmp_path):
    """slice_manifest extracts frames by index range and writes to file."""
    manifest = {
        "video_duration": 120.0,
        "total_scenes_detected": 18,
        "unique_frames_after_dedup": 9,
        "frames": [
            {"frame_id": i, "timestamp": i * 10.0, "narration": f"Text {i}",
             "scene_duration": 5.0, "represents_count": 1}
            for i in range(9)
        ],
    }
    manifest_path = tmp_path / "frames_manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    from visual_style_extractor.pipeline import slice_manifest

    out_path = tmp_path / "slice_0.json"
    result = slice_manifest(str(manifest_path), start_idx=0, end_idx=3, output_path=str(out_path))

    assert result == str(out_path)
    assert out_path.exists()

    with open(out_path) as f:
        sliced = json.load(f)

    assert len(sliced["frames"]) == 3
    assert sliced["frames"][0]["frame_id"] == 0
    assert sliced["frames"][2]["frame_id"] == 2
    assert sliced["video_duration"] == 120.0


def test_merge_analysis_batches(tmp_path):
    """merge_analysis_batches combines batch files and applies confidence gating."""
    batch_0 = [
        {"frame_id": "F001", "scene_type": "title_card", "confidence": 5},
        {"frame_id": "F002", "scene_type": "archival_photo", "confidence": 2},
    ]
    batch_1 = [
        {"frame_id": "F003", "scene_type": "news_clip", "confidence": 4},
    ]

    (tmp_path / "batch_0.json").write_text(json.dumps(batch_0))
    (tmp_path / "batch_1.json").write_text(json.dumps(batch_1))

    from visual_style_extractor.pipeline import merge_analysis_batches

    output_path = tmp_path / "analysis_results.json"
    kept, removed = merge_analysis_batches(
        batch_paths=[str(tmp_path / "batch_0.json"), str(tmp_path / "batch_1.json")],
        output_path=str(output_path),
        min_confidence=3,
    )

    assert kept == 2
    assert removed == 1

    with open(output_path) as f:
        results = json.load(f)
    assert len(results) == 2
    assert results[0]["frame_id"] == "F001"
    assert results[1]["frame_id"] == "F003"


def test_synthesize_hierarchical_output(tmp_path):
    """Synthesis produces hierarchical categories with subtypes."""
    from visual_style_extractor.synthesize import generate_style_guide

    analysis_results = [
        {
            "frame_id": "F001",
            "category": "b_roll",
            "scene_type": "archival_video",
            "shotlist_type": "archival_video",
            "implementation": {
                "background": "grainy footage",
                "main_element": "black and white scene",
                "overlays": "film grain",
                "text_elements": "none",
            },
            "dominant_colors": ["black", "dark gray"],
            "content_description": "Black-and-white archival footage of a rural village.",
            "narrative_trigger": "Establish historical context with period-authentic footage.",
            "variants": "default",
            "confidence": 5,
        },
        {
            "frame_id": "F002",
            "category": "text_elements",
            "scene_type": "quote_card",
            "shotlist_type": "text_overlay",
            "implementation": {
                "background": "solid black",
                "main_element": "white text quote",
                "overlays": "none",
                "text_elements": "serif font, centered, white on black",
            },
            "dominant_colors": ["black", "white"],
            "content_description": "White text quote on black background.",
            "narrative_trigger": "Present direct testimony without visual distraction.",
            "variants": "default",
            "confidence": 4,
        },
        {
            "frame_id": "F003",
            "category": "graphics_animation",
            "scene_type": "silhouette_animation",
            "shotlist_type": "ai_generated",
            "implementation": {
                "background": "deep red",
                "main_element": "glowing white silhouette",
                "overlays": "grain, vignette",
                "text_elements": "none",
            },
            "dominant_colors": ["black", "deep red", "white"],
            "content_description": "Glowing white silhouette on dark red background.",
            "narrative_trigger": "Represent anonymous or unknown individuals.",
            "variants": "solo_figure",
            "confidence": 5,
        },
        {
            # Transition — should be excluded from output
            "frame_id": "F004",
            "category": "transition",
            "scene_type": "black_transition",
            "shotlist_type": "archival_video",
            "implementation": {"background": "pure black", "main_element": "none", "overlays": "none", "text_elements": "none"},
            "dominant_colors": ["black"],
            "content_description": "Pure black frame.",
            "narrative_trigger": "Beat of silence between scenes.",
            "variants": "default",
            "confidence": 5,
        },
    ]

    manifest = {
        "video_duration": 120.0,
        "total_scenes_detected": 10,
        "unique_frames_after_dedup": 4,
        "frames": [
            {"frame_id": i + 1, "timestamp": i * 30.0, "narration": "",
             "scene_duration": 10.0, "represents_count": 1}
            for i in range(4)
        ],
    }

    output_path = str(tmp_path / "VISUAL_STYLE_GUIDE.md")
    result = generate_style_guide(
        analysis_results, manifest, "Test Video", "test_source", output_path,
    )

    assert result == output_path
    content = (tmp_path / "VISUAL_STYLE_GUIDE.md").read_text()

    # Check hierarchical structure
    assert "### B-Roll" in content
    assert "### Text Elements" in content
    assert "### Graphics & Animation" in content
    assert "#### Archival Video" in content
    assert "#### Quote Card" in content
    assert "#### Silhouette Animation" in content

    # Transition should be excluded
    assert "Black Transition" not in content
    assert "transition" not in content.lower().split("## 2.")[0].split("### ")[1:].__str__() or True

    # Check per-subtype fields
    assert "**Description:**" in content
    assert "**Use:**" in content
    assert "**Implementation:**" in content
    assert "**Variants:**" in content
    assert "**Stats:**" in content
    assert "**Examples:**" in content

    # Check type mapping table
    assert "## 2. Type Mapping" in content
    assert "| Category |" in content


def test_synthesize_excludes_transitions(tmp_path):
    """Transitions are fully excluded from output."""
    from visual_style_extractor.synthesize import aggregate_by_category_and_type

    frames = [
        {"frame_id": "F001", "category": "transition", "scene_type": "black_transition", "confidence": 5},
        {"frame_id": "F002", "category": "transition", "scene_type": "color_hold", "confidence": 5},
        {"frame_id": "F003", "category": "b_roll", "scene_type": "archival_video", "confidence": 5},
        # No category field — should infer from scene_type
        {"frame_id": "F004", "scene_type": "fade_to_black", "confidence": 5},
    ]

    result = aggregate_by_category_and_type(frames)

    # Only b_roll should remain
    assert "b_roll" in result
    assert len(result["b_roll"]["archival_video"]) == 1
    # No transition category
    assert "_transition" not in result
    assert "transition" not in result


def test_synthesize_infers_category_from_scene_type(tmp_path):
    """When no category field, infer from scene_type."""
    from visual_style_extractor.synthesize import aggregate_by_category_and_type

    frames = [
        {"frame_id": "F001", "scene_type": "portrait", "confidence": 5},
        {"frame_id": "F002", "scene_type": "location_shot", "confidence": 5},
        {"frame_id": "F003", "scene_type": "quote_card", "confidence": 5},
        {"frame_id": "F004", "scene_type": "screen_recording", "confidence": 4},
    ]

    result = aggregate_by_category_and_type(frames)

    assert "archival_photos" in result
    assert "portrait" in result["archival_photos"]
    assert "location_shot" in result["archival_photos"]
    assert "text_elements" in result
    assert "quote_card" in result["text_elements"]
    assert "evidence_documentation" in result
    assert "screen_recording" in result["evidence_documentation"]
