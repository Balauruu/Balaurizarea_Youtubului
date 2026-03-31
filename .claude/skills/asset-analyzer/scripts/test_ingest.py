"""Unit tests for ingest.py — mocked FFmpeg, no real video files needed."""
import os
import tempfile
from unittest.mock import patch, MagicMock
import numpy as np
import pytest

import sys
sys.path.insert(0, os.path.dirname(__file__))
from ingest import extract_frames, save_frames, _check_nvdec


def test_extract_frames_parses_raw_bytes():
    """Given known raw bytes, produces correct numpy arrays."""
    size = 336
    frame_bytes = np.zeros((size, size, 3), dtype=np.uint8).tobytes()
    two_frames = frame_bytes + frame_bytes

    mock_proc = MagicMock()
    mock_proc.stdout.read.return_value = two_frames
    mock_proc.wait.return_value = None
    mock_proc.returncode = 0
    mock_proc.stderr.read.return_value = b""

    with patch("ingest.subprocess.Popen", return_value=mock_proc):
        frames = extract_frames("fake.mp4", fps=1, size=size, use_hwaccel=False)

    assert len(frames) == 2
    assert frames[0].shape == (336, 336, 3)
    assert frames[0].dtype == np.uint8


def test_extract_frames_empty_video():
    """Zero bytes from FFmpeg returns empty list."""
    mock_proc = MagicMock()
    mock_proc.stdout.read.return_value = b""
    mock_proc.wait.return_value = None
    mock_proc.returncode = 0
    mock_proc.stderr.read.return_value = b""

    with patch("ingest.subprocess.Popen", return_value=mock_proc):
        frames = extract_frames("empty.mp4", fps=1, size=336, use_hwaccel=False)

    assert frames == []


def test_extract_frames_ffmpeg_failure():
    """FFmpeg non-zero exit raises RuntimeError."""
    mock_proc = MagicMock()
    mock_proc.stdout.read.return_value = b""
    mock_proc.wait.return_value = None
    mock_proc.returncode = 1
    mock_proc.stderr.read.return_value = b"Error: codec not found"

    with patch("ingest.subprocess.Popen", return_value=mock_proc):
        with pytest.raises(RuntimeError, match="FFmpeg failed"):
            extract_frames("bad.mp4", fps=1, size=336, use_hwaccel=False)


def test_save_frames_creates_directory():
    """Output directory is created if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = os.path.join(tmpdir, "nested", "frames")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        with patch("ingest.subprocess.run", return_value=mock_result):
            save_frames("fake.mp4", out_dir, fps=1, size=336)

        assert os.path.isdir(out_dir)


def test_save_frames_with_time_range():
    """Start/end arguments produce correct FFmpeg -ss and -t flags."""
    captured_cmd = []

    def capture_run(cmd, **kwargs):
        captured_cmd.extend(cmd)
        mock = MagicMock()
        mock.returncode = 0
        mock.stderr = ""
        return mock

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("ingest.subprocess.run", side_effect=capture_run):
            save_frames("video.mp4", tmpdir, start_sec=10.0, end_sec=20.0)

    assert "-ss" in captured_cmd
    ss_idx = captured_cmd.index("-ss")
    assert captured_cmd[ss_idx + 1] == "10.0"
    assert "-t" in captured_cmd
    t_idx = captured_cmd.index("-t")
    assert captured_cmd[t_idx + 1] == "10.0"


def test_check_nvdec_returns_bool():
    """_check_nvdec always returns a boolean."""
    result = _check_nvdec()
    assert isinstance(result, bool)


def test_extract_frames_size_parameter():
    """Frames match requested size."""
    size = 224
    frame_bytes = np.zeros((size, size, 3), dtype=np.uint8).tobytes()

    mock_proc = MagicMock()
    mock_proc.stdout.read.return_value = frame_bytes
    mock_proc.wait.return_value = None
    mock_proc.returncode = 0
    mock_proc.stderr.read.return_value = b""

    with patch("ingest.subprocess.Popen", return_value=mock_proc):
        frames = extract_frames("test.mp4", fps=1, size=size, use_hwaccel=False)

    assert len(frames) == 1
    assert frames[0].shape == (224, 224, 3)


def test_save_frames_returns_sorted_paths():
    """Returned paths are sorted and use frame_XXXXXX.jpg pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in [3, 1, 2]:
            with open(os.path.join(tmpdir, f"frame_{i:06d}.jpg"), "wb") as f:
                f.write(b"fake")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        with patch("ingest.subprocess.run", return_value=mock_result):
            paths = save_frames("fake.mp4", tmpdir)

        assert len(paths) == 3
        basenames = [os.path.basename(p) for p in paths]
        assert basenames == sorted(basenames)
