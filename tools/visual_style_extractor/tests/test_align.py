import os
import json
import pytest
from visual_style_extractor.align import parse_transcript, align_frames, build_manifest


def test_parse_vtt(tmp_path):
    vtt_content = """WEBVTT

00:00:01.000 --> 00:00:05.000
The story begins in a small town.

00:00:05.000 --> 00:00:10.000
Nobody knew what was coming next.
"""
    vtt_path = str(tmp_path / "subs.vtt")
    with open(vtt_path, "w") as f:
        f.write(vtt_content)

    segments = parse_transcript(vtt_path)
    assert len(segments) == 2
    assert segments[0]["start"] == pytest.approx(1.0)
    assert segments[0]["end"] == pytest.approx(5.0)
    assert "small town" in segments[0]["text"]


def test_parse_srt(tmp_path):
    srt_content = """1
00:00:01,000 --> 00:00:05,000
The story begins in a small town.

2
00:00:05,000 --> 00:00:10,000
Nobody knew what was coming next.
"""
    srt_path = str(tmp_path / "subs.srt")
    with open(srt_path, "w") as f:
        f.write(srt_content)

    segments = parse_transcript(srt_path)
    assert len(segments) == 2
    assert segments[1]["end"] == pytest.approx(10.0)


def test_align_frames():
    segments = [
        {"start": 0.0, "end": 5.0, "text": "Opening line."},
        {"start": 5.0, "end": 10.0, "text": "Second line."},
    ]
    frames = [
        {"frame_id": 1, "frame_path": "f1.jpg", "timestamp": "00:03", "scene_duration": 3.0, "represents_count": 1},
        {"frame_id": 2, "frame_path": "f2.jpg", "timestamp": "00:07", "scene_duration": 4.0, "represents_count": 2},
    ]

    aligned = align_frames(frames, segments)
    assert aligned[0]["narration"] == "Opening line."
    assert aligned[1]["narration"] == "Second line."


def test_align_frames_no_match():
    """Frame outside all segment ranges gets empty narration."""
    segments = [{"start": 10.0, "end": 15.0, "text": "Late text."}]
    frames = [
        {"frame_id": 1, "frame_path": "f1.jpg", "timestamp": "00:03", "scene_duration": 2.0, "represents_count": 1},
    ]

    aligned = align_frames(frames, segments)
    assert aligned[0]["narration"] == ""


def test_build_manifest(tmp_path):
    frames = [
        {"frame_id": 1, "frame_path": "f1.jpg", "timestamp": "00:03",
         "scene_duration": 3.0, "represents_count": 1, "narration": "Hello"},
    ]
    out_path = str(tmp_path / "frames_manifest.json")
    build_manifest(frames, video_duration=120.0, total_scenes=50, output_path=out_path)

    with open(out_path) as f:
        data = json.load(f)

    assert data["video_duration"] == 120.0
    assert data["total_scenes_detected"] == 50
    assert len(data["frames"]) == 1
