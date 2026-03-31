"""Unit tests for promote.py — pool-to-pool promotion logic."""
import os
import sys
import tempfile
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from pool import PoolIndex
from promote import promote_video


def _setup_pools(tmpdir):
    proj_root = os.path.join(tmpdir, "project_pool")
    glob_root = os.path.join(tmpdir, "global_pool")
    return PoolIndex(proj_root), PoolIndex(glob_root)


def _add_video(idx, fhash, n_frames=5):
    emb = np.random.randn(n_frames, 768).astype(np.float16)
    ts = np.arange(n_frames, dtype=np.float64)
    idx.put(fhash, emb, ts, {"source_path": f"/fake/{fhash}.mp4"})


def test_promote_video_success():
    """Promotes embeddings + metadata from project to global."""
    with tempfile.TemporaryDirectory() as tmpdir:
        proj, glob = _setup_pools(tmpdir)
        _add_video(proj, "abc123", 10)
        result = promote_video("abc123", proj, glob)
        assert result["status"] == "promoted"
        assert glob.has("abc123")


def test_promote_video_already_exists():
    """Returns already_exists if hash already in global, no overwrite."""
    with tempfile.TemporaryDirectory() as tmpdir:
        proj, glob = _setup_pools(tmpdir)
        _add_video(proj, "abc123", 10)
        _add_video(glob, "abc123", 5)
        result = promote_video("abc123", proj, glob)
        assert result["status"] == "already_exists"
        emb, _ = glob.load_embeddings("abc123")
        assert emb.shape[0] == 5


def test_promote_video_not_found():
    """Returns not_found for hash not in project pool."""
    with tempfile.TemporaryDirectory() as tmpdir:
        proj, glob = _setup_pools(tmpdir)
        result = promote_video("nonexistent", proj, glob)
        assert result["status"] == "not_found"


def test_promote_preserves_embeddings():
    """Promoted embeddings are numerically identical to source."""
    with tempfile.TemporaryDirectory() as tmpdir:
        proj, glob = _setup_pools(tmpdir)
        _add_video(proj, "abc123", 10)
        orig_emb, orig_ts = proj.load_embeddings("abc123")
        promote_video("abc123", proj, glob)
        prom_emb, prom_ts = glob.load_embeddings("abc123")
        np.testing.assert_array_equal(orig_emb, prom_emb)
        np.testing.assert_array_equal(orig_ts, prom_ts)


def test_promote_missing_meta_json():
    """Works even if meta.json is missing (uses index entry)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        proj, glob = _setup_pools(tmpdir)
        _add_video(proj, "abc123")
        meta_path = proj.root / "abc123" / "meta.json"
        if meta_path.exists():
            os.unlink(meta_path)
        result = promote_video("abc123", proj, glob)
        assert result["status"] == "promoted"


def test_promote_multiple_videos():
    """Batch promotion of 3 videos all succeed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        proj, glob = _setup_pools(tmpdir)
        for h in ["vid1", "vid2", "vid3"]:
            _add_video(proj, h)
        results = [promote_video(h, proj, glob) for h in ["vid1", "vid2", "vid3"]]
        assert all(r["status"] == "promoted" for r in results)
        assert set(glob.list_entries().keys()) == {"vid1", "vid2", "vid3"}
