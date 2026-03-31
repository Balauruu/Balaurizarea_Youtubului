"""Integration tests for embed.py — requires GPU + PE-Core + staging videos."""
import json
import os
import tempfile
import numpy as np
import pytest

# Skip entire module if CUDA unavailable
torch = pytest.importorskip("torch")
if not torch.cuda.is_available():
    pytest.skip("CUDA not available", allow_module_level=True)

import sys
SCRIPTS_DIR = os.path.dirname(__file__)
sys.path.insert(0, SCRIPTS_DIR)

from embed import load_model, embed_frames, embed_video
from pool import PoolIndex, file_hash
from ingest import extract_frames

PROJECT_DIR = os.path.abspath(os.path.join(
    SCRIPTS_DIR, "..", "..", "..", "..",
    "projects", "1. The Duplessis Orphans Quebec's Stolen Children"
))
STAGING_DIR = os.path.join(PROJECT_DIR, "assets", "staging")


def _get_first_staging_video():
    """Return path to first .mp4 in staging, or skip test."""
    if not os.path.isdir(STAGING_DIR):
        pytest.skip("Staging directory not found")
    videos = sorted(f for f in os.listdir(STAGING_DIR) if f.endswith(".mp4"))
    if not videos:
        pytest.skip("No staging videos found")
    return os.path.join(STAGING_DIR, videos[0])


@pytest.fixture(scope="module")
def pe_model():
    """Load PE-Core model once for all tests in this module."""
    model, tokenizer, preprocess = load_model()
    return model, tokenizer, preprocess


def test_embed_single_video(pe_model):
    video = _get_first_staging_video()
    model, _, preprocess = pe_model
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        result = embed_video(video, idx, model, preprocess)
        assert result["status"] == "embedded"
        assert result["frames"] > 0
        emb, ts = idx.load_embeddings(result["hash"])
        assert emb.shape[1] == 1024  # PE-Core-L14-336 produces 1024-dim embeddings
        assert emb.dtype == np.float16
        assert len(ts) == result["frames"]


def test_embed_cache_skip(pe_model):
    video = _get_first_staging_video()
    model, _, preprocess = pe_model
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        r1 = embed_video(video, idx, model, preprocess)
        r2 = embed_video(video, idx, model, preprocess)
        assert r1["status"] == "embedded"
        assert r2["status"] == "cached"
        assert r2["frames"] == r1["frames"]


def test_embed_force_reembed(pe_model):
    video = _get_first_staging_video()
    model, _, preprocess = pe_model
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        r1 = embed_video(video, idx, model, preprocess)
        r2 = embed_video(video, idx, model, preprocess, force=True)
        assert r1["status"] == "embedded"
        assert r2["status"] == "embedded"


def test_embed_frame_count_matches_duration(pe_model):
    video = _get_first_staging_video()
    model, _, preprocess = pe_model
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        result = embed_video(video, idx, model, preprocess, fps=1)
        # At 1fps, frame count should be roughly equal to duration in seconds
        import subprocess
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", video],
            capture_output=True, text=True
        )
        duration = float(json.loads(probe.stdout)["format"]["duration"])
        assert abs(result["frames"] - duration) < 3  # Within 3 seconds


def test_embed_embeddings_normalized(pe_model):
    video = _get_first_staging_video()
    model, _, preprocess = pe_model
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        result = embed_video(video, idx, model, preprocess)
        emb, _ = idx.load_embeddings(result["hash"])
        norms = np.linalg.norm(emb.astype(np.float32), axis=1)
        np.testing.assert_allclose(norms, 1.0, atol=0.02)


def test_embed_health_check_after_embed(pe_model):
    video = _get_first_staging_video()
    model, _, preprocess = pe_model
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        result = embed_video(video, idx, model, preprocess)
        report = idx.health_check()
        assert report["total_files"] == 1
        assert report["total_frames"] == result["frames"]


def test_embed_timestamps_sequential(pe_model):
    video = _get_first_staging_video()
    model, _, preprocess = pe_model
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        result = embed_video(video, idx, model, preprocess)
        _, ts = idx.load_embeddings(result["hash"])
        assert np.all(np.diff(ts) >= 0)  # Monotonically non-decreasing


def test_embed_directory(pe_model):
    """Embedding a directory processes all video files."""
    model, _, preprocess = pe_model
    if not os.path.isdir(STAGING_DIR):
        pytest.skip("Staging directory not found")
    videos = [f for f in os.listdir(STAGING_DIR) if f.endswith(".mp4")]
    if len(videos) < 2:
        pytest.skip("Need at least 2 staging videos")
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        count = 0
        for v in videos[:2]:  # Only test first 2 for speed
            r = embed_video(os.path.join(STAGING_DIR, v), idx, model, preprocess)
            if r["status"] == "embedded":
                count += 1
        assert count >= 1
        assert len(idx.list_entries()) >= 1
