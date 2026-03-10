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
        {"frame_id": "F001", "pattern_name": "title_card", "confidence": 5},
        {"frame_id": "F002", "pattern_name": "archival_photo", "confidence": 2},
    ]
    batch_1 = [
        {"frame_id": "F003", "pattern_name": "news_clip", "confidence": 4},
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


def test_prepare_synthesis_input():
    """prepare_synthesis_input produces structured text with pattern data."""
    from visual_style_extractor.synthesize import prepare_synthesis_input

    analysis_results = [
        {
            "frame_id": "F001",
            "category": "b_roll",
            "pattern_name": "archival_bw_footage",
            "shotlist_type": "archival_video",
            "visual_recipe": {
                "background": "grainy footage",
                "subject": "black and white scene",
                "treatment": "film grain",
                "color_palette": "black, dark gray",
                "text_style": "none",
            },
            "narrative_function": "Establish historical context with period-authentic footage.",
            "variant_name": "default",
            "confidence": 5,
        },
        {
            "frame_id": "F002",
            "category": "text_elements",
            "pattern_name": "quote_card",
            "shotlist_type": "text_overlay",
            "visual_recipe": {
                "background": "solid black",
                "subject": "text block",
                "treatment": "none",
                "color_palette": "black, white",
                "text_style": "serif font, centered, white on black",
            },
            "narrative_function": "Present direct testimony without visual distraction.",
            "variant_name": "default",
            "confidence": 4,
        },
        {
            "frame_id": "F003",
            "category": "graphics_animation",
            "pattern_name": "silhouette_figure",
            "shotlist_type": "ai_generated",
            "visual_recipe": {
                "background": "deep red",
                "subject": "human silhouette",
                "treatment": "grain, vignette, chromatic aberration glow",
                "color_palette": "black, deep red, white",
                "text_style": "none",
            },
            "narrative_function": "Represent anonymous or unknown individuals.",
            "variant_name": "solo",
            "confidence": 5,
        },
        {
            # Transition — should be excluded
            "frame_id": "F004",
            "category": "transition",
            "pattern_name": "black_transition",
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

    result = prepare_synthesis_input(
        analysis_results, manifest, "Test Video", "test_source",
    )

    # Should be a string
    assert isinstance(result, str)

    # Should contain video metadata
    assert "VIDEO_TITLE: Test Video" in result
    assert "DURATION:" in result

    # Should contain category headers
    assert "=== CATEGORY: B-Roll" in result
    assert "=== CATEGORY: Text Elements" in result
    assert "=== CATEGORY: Graphics & Animation" in result

    # Should contain pattern data
    assert "--- PATTERN: archival_bw_footage ---" in result
    assert "--- PATTERN: quote_card ---" in result
    assert "--- PATTERN: silhouette_figure ---" in result

    # Should include visual recipe data
    assert "subject: human silhouette" in result
    assert "treatment: grain, vignette, chromatic aberration glow" in result

    # Should include narrative functions
    assert "Represent anonymous or unknown individuals." in result

    # Should include variants
    assert "Variants: solo" in result

    # Transition should be excluded
    assert "black_transition" not in result
    assert "CATEGORY: Transition" not in result


def test_aggregate_excludes_transitions():
    """Transitions are fully excluded from aggregation."""
    from visual_style_extractor.synthesize import aggregate_by_category_and_type

    frames = [
        {"frame_id": "F001", "category": "transition", "pattern_name": "black_transition", "confidence": 5},
        {"frame_id": "F002", "category": "transition", "pattern_name": "color_hold", "confidence": 5},
        {"frame_id": "F003", "category": "b_roll", "pattern_name": "archival_video", "confidence": 5},
        # No category field — should infer from pattern_name
        {"frame_id": "F004", "pattern_name": "fade_to_black", "confidence": 5},
    ]

    result = aggregate_by_category_and_type(frames)

    # Only b_roll should remain
    assert "b_roll" in result
    assert len(result["b_roll"]["archival_video"]) == 1
    # No transition category
    assert "_transition" not in result
    assert "transition" not in result


def test_aggregate_infers_category_from_pattern_name():
    """When no category field, infer from pattern_name."""
    from visual_style_extractor.synthesize import aggregate_by_category_and_type

    frames = [
        {"frame_id": "F001", "pattern_name": "portrait", "confidence": 5},
        {"frame_id": "F002", "pattern_name": "location_shot", "confidence": 5},
        {"frame_id": "F003", "pattern_name": "quote_card", "confidence": 5},
        {"frame_id": "F004", "pattern_name": "screen_recording", "confidence": 4},
    ]

    result = aggregate_by_category_and_type(frames)

    assert "archival_photos" in result
    assert "portrait" in result["archival_photos"]
    assert "location_shot" in result["archival_photos"]
    assert "text_elements" in result
    assert "quote_card" in result["text_elements"]
    assert "evidence_documentation" in result
    assert "screen_recording" in result["evidence_documentation"]


def test_aggregate_supports_v3_scene_type_field():
    """Backward compatibility: aggregate works with v3 scene_type field."""
    from visual_style_extractor.synthesize import aggregate_by_category_and_type

    frames = [
        {"frame_id": "F001", "category": "b_roll", "scene_type": "archival_video", "confidence": 5},
        {"frame_id": "F002", "category": "text_elements", "scene_type": "quote_card", "confidence": 4},
    ]

    result = aggregate_by_category_and_type(frames)

    assert "b_roll" in result
    assert "archival_video" in result["b_roll"]
    assert "text_elements" in result
    assert "quote_card" in result["text_elements"]


def test_run_stage_6_writes_synthesis_input(tmp_path):
    """run_stage_6 writes synthesis input to scratch directory."""
    import os
    from visual_style_extractor.pipeline import run_stage_6

    analysis_results = [
        {
            "frame_id": "F001",
            "category": "b_roll",
            "pattern_name": "archival_bw_footage",
            "shotlist_type": "archival_video",
            "visual_recipe": {
                "background": "grainy footage",
                "subject": "scene",
                "treatment": "film grain",
                "color_palette": "black, gray",
                "text_style": "none",
            },
            "narrative_function": "Historical context.",
            "variant_name": "default",
            "confidence": 5,
        },
    ]

    manifest = {
        "video_duration": 60.0,
        "total_scenes_detected": 5,
        "unique_frames_after_dedup": 1,
        "frames": [
            {"frame_id": 1, "timestamp": 0.0, "narration": "",
             "scene_duration": 10.0, "represents_count": 1},
        ],
    }

    # Write test data to tmp files
    analysis_path = str(tmp_path / "analysis.json")
    manifest_path = str(tmp_path / "manifest.json")
    with open(analysis_path, "w") as f:
        json.dump(analysis_results, f)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)

    # Change to tmp_path so .claude/scratch is created there
    original_dir = os.getcwd()
    os.chdir(str(tmp_path))
    try:
        result = run_stage_6(
            manifest_path=manifest_path,
            video_title="Test Video",
            video_source="test_url",
            output_dir=str(tmp_path),
            analysis_results_path=analysis_path,
        )

        assert os.path.exists(result)
        content = open(result).read()
        assert "VIDEO_TITLE: Test Video" in content
        assert "archival_bw_footage" in content
    finally:
        os.chdir(original_dir)
