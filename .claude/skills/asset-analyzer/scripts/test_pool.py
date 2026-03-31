import tempfile, os, json
import numpy as np
import pytest
from pool import file_hash, PoolIndex, get_pool_root

def test_file_hash_deterministic():
    """Same file content produces same hash."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
        f.write(b"x" * 100_000)
        path = f.name
    try:
        h1 = file_hash(path)
        h2 = file_hash(path)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex
    finally:
        os.unlink(path)

def test_file_hash_differs_for_different_content():
    paths = []
    for content in [b"a" * 100_000, b"b" * 100_000]:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
            f.write(content)
            paths.append(f.name)
    try:
        assert file_hash(paths[0]) != file_hash(paths[1])
    finally:
        for p in paths:
            os.unlink(p)

def test_pool_root_project():
    root = get_pool_root("project", project_dir="/some/project")
    assert root.endswith(".broll-index")
    assert "some/project" in root.replace("\\", "/") or "some\\project" in root

def test_pool_root_global():
    root = get_pool_root("global")
    assert ".broll-index" in root
    assert "global" in root

def test_pool_index_put_and_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        emb = np.random.randn(10, 768).astype(np.float16)
        ts = np.arange(10, dtype=np.float64)
        meta = {"source_path": "/fake/video.mp4", "duration_sec": 10.0, "embed_date": "2026-03-31"}

        idx.put("abc123", emb, ts, meta)

        assert idx.has("abc123")
        assert not idx.has("xyz999")

        loaded_emb, loaded_ts = idx.load_embeddings("abc123")
        assert loaded_emb.shape == (10, 768)
        assert loaded_ts.shape == (10,)
        np.testing.assert_array_almost_equal(loaded_emb, emb, decimal=2)

def test_pool_index_load_all():
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        for name, n in [("aaa", 5), ("bbb", 3)]:
            emb = np.random.randn(n, 768).astype(np.float16)
            ts = np.arange(n, dtype=np.float64)
            idx.put(name, emb, ts, {"source_path": f"/fake/{name}.mp4"})

        all_emb, all_ts, info = idx.load_all_embeddings()
        assert all_emb.shape == (8, 768)
        assert len(all_ts) == 8
        assert len(info) == 8

def test_pool_index_remove():
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        emb = np.random.randn(3, 768).astype(np.float16)
        ts = np.arange(3, dtype=np.float64)
        idx.put("todelete", emb, ts, {})
        assert idx.has("todelete")
        idx.remove("todelete")
        assert not idx.has("todelete")

def test_health_check_detects_dead_refs():
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        emb = np.random.randn(3, 768).astype(np.float16)
        ts = np.arange(3, dtype=np.float64)
        idx.put("dead", emb, ts, {"source_path": "/nonexistent/video.mp4"})
        report = idx.health_check()
        assert report["total_files"] == 1
        assert len(report["dead_references"]) == 1
