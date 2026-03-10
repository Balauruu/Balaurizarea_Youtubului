"""Tests for pipeline helpers — slice_manifest and merge_analysis_batches."""

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
    # Metadata preserved
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

    assert kept == 2  # F001 (5) and F003 (4)
    assert removed == 1  # F002 (2)

    with open(output_path) as f:
        results = json.load(f)
    assert len(results) == 2
    assert results[0]["frame_id"] == "F001"
    assert results[1]["frame_id"] == "F003"
