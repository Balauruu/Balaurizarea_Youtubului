"""Cross-cutting error handling tests — corrupt files, missing input, edge cases."""
import json
import os
import sys
import tempfile
import numpy as np
import pytest
import yaml

sys.path.insert(0, os.path.dirname(__file__))
from pool import PoolIndex
from search import detect_scene_boundaries, group_into_segments
from discover import load_taxonomy, cluster_unknowns
from evaluate import compute_iou, evaluate_segments, generate_template
from promote import promote_video


def test_pool_index_deep_nested_dir():
    """put() on a deeply nested path creates all directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        deep_path = os.path.join(tmpdir, "a", "b", "c", "pool")
        idx = PoolIndex(deep_path)
        emb = np.random.randn(3, 768).astype(np.float16)
        ts = np.arange(3, dtype=np.float64)
        idx.put("test", emb, ts, {})
        assert idx.has("test")


def test_search_empty_queries_list():
    """Empty score/timestamp arrays produce empty segments."""
    scores = np.array([], dtype=np.float32)
    ts = np.array([], dtype=np.float64)
    segments = group_into_segments(scores, ts, [], threshold=0.15)
    assert segments == []


def test_search_nan_in_scores():
    """NaN scores don't cause infinite loops in segment grouping."""
    scores = np.array([0.3, float('nan'), 0.3, 0.1])
    ts = np.arange(4, dtype=np.float64)
    segments = group_into_segments(scores, ts, [], threshold=0.15)
    assert isinstance(segments, list)


def test_discover_empty_taxonomy():
    """Empty YAML file produces empty categories."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        yaml.dump({}, f)
        path = f.name
    try:
        cats, skips = load_taxonomy(path)
        assert cats == {}
        assert skips == set()
    finally:
        os.unlink(path)


def test_evaluate_mismatched_filenames():
    """GT segments with no matching predictions count as misses."""
    gt = [{"start_sec": 10, "end_sec": 20, "label": "test"}]
    pred = []
    result = evaluate_segments(gt, pred, iou_threshold=0.5)
    assert result["misses"] == 1
    assert result["false_positives"] == 0


def test_evaluate_negative_timestamps():
    """Negative timestamps don't crash IoU calculation."""
    iou = compute_iou(-5, 5, 0, 10)
    assert 0 <= iou <= 1


def test_promote_source_pool_empty():
    """Promoting from empty pool returns not_found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        proj = PoolIndex(os.path.join(tmpdir, "proj"))
        glob = PoolIndex(os.path.join(tmpdir, "glob"))
        result = promote_video("anything", proj, glob)
        assert result["status"] == "not_found"


def test_pool_index_reopen_after_write():
    """Data persists through write-close-reopen cycle."""
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        emb = np.random.randn(3, 768).astype(np.float16)
        ts = np.arange(3, dtype=np.float64)
        idx.put("persist_test", emb, ts, {"source_path": "/test.mp4"})
        idx2 = PoolIndex(tmpdir)
        assert idx2.has("persist_test")
        entries = idx2.list_entries()
        assert entries["persist_test"]["frame_count"] == 3


def test_scene_boundaries_identical_frames():
    """All identical frames produce no boundaries."""
    emb = np.tile([0.5, 0.5, 0.5], (20, 1)).astype(np.float32)
    ts = np.arange(20, dtype=np.float64)
    boundaries = detect_scene_boundaries(emb, ts, percentile=90)
    assert boundaries == []


def test_cluster_unknowns_single_embedding():
    """Single embedding returns noise label."""
    emb = np.random.randn(1, 768).astype(np.float32)
    labels = cluster_unknowns(emb, eps=0.3, min_samples=3)
    assert labels[0] == -1
