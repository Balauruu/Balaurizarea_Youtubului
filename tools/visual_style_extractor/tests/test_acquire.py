import os
import tempfile
import pytest
from visual_style_extractor.acquire import validate_local_input, find_video_file, find_transcript_file


def test_find_video_file_mp4(tmp_path):
    video = tmp_path / "test.mp4"
    video.write_bytes(b"fake video")
    assert find_video_file(str(tmp_path)) == str(video)


def test_find_video_file_none(tmp_path):
    assert find_video_file(str(tmp_path)) is None


def test_find_transcript_vtt(tmp_path):
    sub = tmp_path / "subs.vtt"
    sub.write_text("WEBVTT\n\n00:00.000 --> 00:01.000\nHello")
    assert find_transcript_file(str(tmp_path)) == str(sub)


def test_find_transcript_srt(tmp_path):
    sub = tmp_path / "subs.srt"
    sub.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello")
    assert find_transcript_file(str(tmp_path)) == str(sub)


def test_find_transcript_none(tmp_path):
    assert find_transcript_file(str(tmp_path)) is None


def test_validate_local_input_success(tmp_path):
    (tmp_path / "video.mp4").write_bytes(b"fake")
    (tmp_path / "subs.vtt").write_text("WEBVTT\n\n00:00.000 --> 00:01.000\nHi")
    result = validate_local_input(str(tmp_path))
    assert result["video_path"].endswith(".mp4")
    assert result["transcript_path"].endswith(".vtt")


def test_validate_local_input_no_video(tmp_path):
    (tmp_path / "subs.vtt").write_text("WEBVTT")
    with pytest.raises(FileNotFoundError, match="No video file found"):
        validate_local_input(str(tmp_path))


def test_validate_local_input_no_transcript(tmp_path):
    (tmp_path / "video.mp4").write_bytes(b"fake")
    with pytest.raises(FileNotFoundError, match="No transcript found"):
        validate_local_input(str(tmp_path))
