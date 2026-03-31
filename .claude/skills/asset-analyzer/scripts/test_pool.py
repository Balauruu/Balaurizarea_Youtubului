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


def test_file_hash_small_file():
    """Files smaller than 64KB hash the entire file content."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
        f.write(b"tiny")
        path = f.name
    try:
        h = file_hash(path)
        assert len(h) == 64
    finally:
        os.unlink(path)


def test_file_hash_nonexistent():
    """Missing file raises FileNotFoundError."""
    with pytest.raises((FileNotFoundError, OSError)):
        file_hash("/nonexistent/video.mp4")


def test_pool_root_invalid_pool():
    """Invalid pool name raises ValueError."""
    with pytest.raises(ValueError):
        get_pool_root("invalid")


def test_pool_root_project_no_dir():
    """Project pool without project_dir raises ValueError."""
    with pytest.raises(ValueError):
        get_pool_root("project")


def test_pool_index_empty_load_all():
    """Empty pool returns (0, 0) shaped array and empty lists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        emb, ts, info = idx.load_all_embeddings()
        assert emb.shape == (0, 0)
        assert len(ts) == 0
        assert len(info) == 0


def test_pool_index_put_overwrites():
    """Second put() with same hash overwrites without error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        emb1 = np.random.randn(5, 768).astype(np.float16)
        emb2 = np.random.randn(8, 768).astype(np.float16)
        ts1 = np.arange(5, dtype=np.float64)
        ts2 = np.arange(8, dtype=np.float64)
        idx.put("same_hash", emb1, ts1, {"source_path": "/v1.mp4"})
        idx.put("same_hash", emb2, ts2, {"source_path": "/v2.mp4"})
        loaded_emb, loaded_ts = idx.load_embeddings("same_hash")
        assert loaded_emb.shape == (8, 768)
        assert idx.get("same_hash")["frame_count"] == 8


def test_pool_index_corrupt_json():
    """Corrupt index.json raises ValueError on access."""
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = os.path.join(tmpdir, "index.json")
        with open(index_path, "w") as f:
            f.write("{corrupt json!!")
        idx = PoolIndex(tmpdir)
        with pytest.raises(ValueError):
            idx.has("anything")


def test_pool_index_missing_npy():
    """load_embeddings() raises when .npy files are deleted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        emb = np.random.randn(3, 768).astype(np.float16)
        ts = np.arange(3, dtype=np.float64)
        idx.put("test_hash", emb, ts, {})
        os.unlink(os.path.join(tmpdir, "test_hash", "embeddings.npy"))
        with pytest.raises(FileNotFoundError):
            idx.load_embeddings("test_hash")


def test_pool_index_unicode_paths():
    """Pool handles non-ASCII characters in source paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        emb = np.random.randn(3, 768).astype(np.float16)
        ts = np.arange(3, dtype=np.float64)
        meta = {"source_path": "/vidéos/montréal_été.mp4"}
        idx.put("unicode_test", emb, ts, meta)
        entry = idx.get("unicode_test")
        assert "montréal" in entry["source_path"]


def test_pool_index_float16_precision():
    """Float16 roundtrip preserves enough precision for cosine similarity."""
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        emb = np.random.randn(10, 768).astype(np.float16)
        ts = np.arange(10, dtype=np.float64)
        idx.put("precision", emb, ts, {})
        loaded, _ = idx.load_embeddings("precision")
        norms_orig = np.linalg.norm(emb.astype(np.float32), axis=1, keepdims=True)
        norms_load = np.linalg.norm(loaded.astype(np.float32), axis=1, keepdims=True)
        cos_sim = np.sum(
            (emb.astype(np.float32) / np.maximum(norms_orig, 1e-8))
            * (loaded.astype(np.float32) / np.maximum(norms_load, 1e-8)),
            axis=1,
        )
        assert np.all(cos_sim > 0.999)


def test_health_check_clean():
    """Pool with valid source files reports 0 dead references."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src_file = os.path.join(tmpdir, "real_video.mp4")
        with open(src_file, "wb") as f:
            f.write(b"fake video")
        idx = PoolIndex(os.path.join(tmpdir, "pool"))
        emb = np.random.randn(3, 768).astype(np.float16)
        ts = np.arange(3, dtype=np.float64)
        idx.put("clean", emb, ts, {"source_path": src_file})
        report = idx.health_check()
        assert len(report["dead_references"]) == 0


def test_pool_index_reopen_consistency():
    """Data persists when PoolIndex is closed and reopened."""
    with tempfile.TemporaryDirectory() as tmpdir:
        idx1 = PoolIndex(tmpdir)
        emb = np.random.randn(5, 768).astype(np.float16)
        ts = np.arange(5, dtype=np.float64)
        idx1.put("persist", emb, ts, {"source_path": "/test.mp4"})
        del idx1
        idx2 = PoolIndex(tmpdir)
        assert idx2.has("persist")
        loaded_emb, _ = idx2.load_embeddings("persist")
        assert loaded_emb.shape == (5, 768)
