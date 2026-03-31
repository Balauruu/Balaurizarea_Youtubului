# Asset Analyzer V2 Test Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 113-unit + 26-integration + 5-eval test suite that covers every component of the asset-analyzer V2 pipeline, surfaces bugs, and identifies improvement opportunities.

**Architecture:** Unit tests use synthetic data and mocked subprocess calls (no GPU). Integration tests use real Duplessis staging videos with PE-Core on GPU. Skill evals test Claude's orchestration quality via prompts + rubrics. All tests live in `.claude/skills/asset-analyzer/scripts/` alongside the code they test.

**Tech Stack:** pytest, numpy, unittest.mock, PyYAML, PE-Core (integration only)

**Spec:** `docs/superpowers/specs/2026-03-31-asset-analyzer-test-suite-design.md`

**Conda env Python:** `C:/Users/iorda/miniconda3/envs/perception-models/python.exe`

**All test files go in:** `.claude/skills/asset-analyzer/scripts/`

---

## File Map

| File | Action | Tests |
|------|--------|-------|
| `.claude/skills/asset-analyzer/scripts/test_pool.py` | Modify | 8 existing + 12 new = 20 |
| `.claude/skills/asset-analyzer/scripts/test_ingest.py` | Create | 8 |
| `.claude/skills/asset-analyzer/scripts/test_search.py` | Modify | 4 existing + 11 new = 15 |
| `.claude/skills/asset-analyzer/scripts/test_discover.py` | Create | 10 |
| `.claude/skills/asset-analyzer/scripts/test_evaluate.py` | Modify | 9 existing + 9 new = 18 |
| `.claude/skills/asset-analyzer/scripts/test_promote.py` | Create | 6 |
| `.claude/skills/asset-analyzer/scripts/test_error_handling.py` | Create | 10 |
| `.claude/skills/asset-analyzer/scripts/test_integration_embed.py` | Create | 8 |
| `.claude/skills/asset-analyzer/scripts/test_integration_search.py` | Create | 7 |
| `.claude/skills/asset-analyzer/scripts/test_integration_discover.py` | Create | 6 |
| `.claude/skills/asset-analyzer/scripts/test_integration_pipeline.py` | Create | 5 |
| `.claude/skills/asset-analyzer/evals/evals.json` | Create | 5 prompts |
| `.claude/skills/asset-analyzer/evals/rubrics/query_refinement.md` | Create | Rubric |
| `.claude/skills/asset-analyzer/evals/rubrics/taxonomy_generation.md` | Create | Rubric |
| `.claude/skills/asset-analyzer/evals/rubrics/presentation_quality.md` | Create | Rubric |
| `.claude/skills/asset-analyzer/evals/rubrics/workflow_correctness.md` | Create | Rubric |

---

## Task 1: Expand test_pool.py (12 new tests)

**Files:**
- Modify: `.claude/skills/asset-analyzer/scripts/test_pool.py`

- [ ] **Step 1: Add new tests to test_pool.py**

Append these 12 tests after the existing 8. Do NOT modify existing tests.

```python
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
    """Empty pool returns (0, 768) shaped array and empty lists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        emb, ts, info = idx.load_all_embeddings()
        assert emb.shape == (0, 768)
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
    """Corrupt index.json raises an exception on access."""
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = os.path.join(tmpdir, "index.json")
        with open(index_path, "w") as f:
            f.write("{corrupt json!!")
        idx = PoolIndex(tmpdir)
        with pytest.raises(Exception):
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
```

- [ ] **Step 2: Run all pool tests**

```bash
cd ".claude/skills/asset-analyzer/scripts"
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_pool.py -v
```

Expected: 20 tests PASS

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/asset-analyzer/scripts/test_pool.py
git commit -m "test: expand pool.py test coverage — 12 new edge case tests"
```

---

## Task 2: Create test_ingest.py (8 tests)

**Files:**
- Create: `.claude/skills/asset-analyzer/scripts/test_ingest.py`

- [ ] **Step 1: Write test_ingest.py**

```python
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
```

- [ ] **Step 2: Run tests**

```bash
cd ".claude/skills/asset-analyzer/scripts"
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_ingest.py -v
```

Expected: 8 tests PASS

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/asset-analyzer/scripts/test_ingest.py
git commit -m "test: add ingest.py unit tests — 8 tests with mocked FFmpeg"
```

---

## Task 3: Expand test_search.py (11 new tests)

**Files:**
- Modify: `.claude/skills/asset-analyzer/scripts/test_search.py`

- [ ] **Step 1: Append new tests**

Add after existing 4 tests. Do NOT modify existing tests.

```python
def test_scene_boundaries_single_frame():
    """Single frame input returns empty boundaries."""
    emb = np.array([[1, 0, 0]], dtype=np.float32)
    ts = np.array([0.0])
    assert detect_scene_boundaries(emb, ts) == []


def test_scene_boundaries_two_frames():
    """Two very different frames produce one boundary."""
    emb = np.array([[1, 0, 0], [0, 1, 0]], dtype=np.float32)
    ts = np.array([0.0, 1.0])
    boundaries = detect_scene_boundaries(emb, ts, percentile=50)
    assert len(boundaries) == 1
    assert abs(boundaries[0] - 0.5) < 0.01


def test_scene_boundaries_multiple_cuts():
    """Three distinct scenes produce at least two boundaries."""
    emb = np.vstack([
        np.tile([1, 0, 0], (4, 1)),
        np.tile([0, 1, 0], (4, 1)),
        np.tile([0, 0, 1], (4, 1)),
    ]).astype(np.float32)
    ts = np.arange(12, dtype=np.float64)
    boundaries = detect_scene_boundaries(emb, ts, percentile=80)
    assert len(boundaries) >= 2


def test_scene_boundaries_gradual_change():
    """Smooth linear interpolation produces no sharp boundaries."""
    n = 20
    emb = np.zeros((n, 3), dtype=np.float32)
    for i in range(n):
        t = i / (n - 1)
        emb[i] = [1 - t, t, 0]
    ts = np.arange(n, dtype=np.float64)
    boundaries = detect_scene_boundaries(emb, ts, percentile=95)
    assert len(boundaries) <= 1


def test_group_segments_all_below_threshold():
    """No frames above threshold returns empty segments."""
    scores = np.array([0.05, 0.08, 0.02, 0.10])
    ts = np.arange(4, dtype=np.float64)
    segments = group_into_segments(scores, ts, [], threshold=0.15)
    assert segments == []


def test_group_segments_all_above_threshold():
    """All frames above threshold produces one segment."""
    scores = np.array([0.3, 0.4, 0.35, 0.25])
    ts = np.arange(4, dtype=np.float64)
    segments = group_into_segments(scores, ts, [], threshold=0.15)
    assert len(segments) == 1
    assert segments[0]["start_sec"] == 0.0
    assert segments[0]["end_sec"] == 3.0


def test_group_segments_single_frame_segment():
    """A lone high-scoring frame becomes a segment."""
    scores = np.array([0.05, 0.05, 0.40, 0.05, 0.05])
    ts = np.arange(5, dtype=np.float64)
    segments = group_into_segments(scores, ts, [], threshold=0.15)
    assert len(segments) == 1
    assert segments[0]["start_sec"] == 2.0
    assert segments[0]["end_sec"] == 2.0


def test_group_segments_boundary_splits():
    """Scene boundary in the middle of a high-scoring run splits into two segments."""
    scores = np.array([0.3, 0.3, 0.3, 0.3])
    ts = np.array([0.0, 1.0, 2.0, 3.0])
    boundaries = [1.5]
    segments = group_into_segments(scores, ts, boundaries, threshold=0.15)
    assert len(segments) == 2
    assert segments[0]["end_sec"] == 1.0
    assert segments[1]["start_sec"] == 2.0


def test_score_queries_normalized():
    """L2-normalized inputs produce scores in [-1, 1]."""
    frame_emb = np.random.randn(50, 768).astype(np.float32)
    frame_emb /= np.linalg.norm(frame_emb, axis=1, keepdims=True)
    query_emb = np.random.randn(5, 768).astype(np.float32)
    query_emb /= np.linalg.norm(query_emb, axis=1, keepdims=True)
    scores = score_queries(frame_emb, query_emb)
    assert scores.shape == (50, 5)
    assert np.all(scores >= -1.01)
    assert np.all(scores <= 1.01)


def test_score_queries_empty_frames():
    """Empty frame array returns correct shape."""
    frame_emb = np.empty((0, 768), dtype=np.float32)
    query_emb = np.random.randn(3, 768).astype(np.float32)
    scores = score_queries(frame_emb, query_emb)
    assert scores.shape == (0, 3)


def test_score_queries_single_query():
    """Single query returns (N, 1) shape."""
    frame_emb = np.random.randn(10, 3).astype(np.float32)
    query_emb = np.random.randn(1, 3).astype(np.float32)
    scores = score_queries(frame_emb, query_emb)
    assert scores.shape == (10, 1)
```

- [ ] **Step 2: Run tests**

```bash
cd ".claude/skills/asset-analyzer/scripts"
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_search.py -v
```

Expected: 15 tests PASS

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/asset-analyzer/scripts/test_search.py
git commit -m "test: expand search.py test coverage — 11 new boundary and scoring tests"
```

---

## Task 4: Create test_discover.py (10 tests)

**Files:**
- Create: `.claude/skills/asset-analyzer/scripts/test_discover.py`

- [ ] **Step 1: Write test_discover.py**

```python
"""Unit tests for discover.py — taxonomy loading, merging, and clustering logic."""
import json
import os
import sys
import tempfile
import numpy as np
import pytest
import yaml

sys.path.insert(0, os.path.dirname(__file__))
from discover import load_taxonomy, merge_taxonomies, cluster_unknowns


def _write_taxonomy(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)


def test_load_taxonomy_valid_yaml():
    """Parses taxonomy YAML and returns categories dict + skip keys."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        yaml.dump({
            "atmospheric": {"atmospheric_urban": "City texture"},
            "skip": {"talking_head": "Person speaking to camera"},
        }, f)
        path = f.name
    try:
        cats, skips = load_taxonomy(path)
        assert "atmospheric_urban" in cats
        assert "talking_head" in cats
        assert "talking_head" in skips
        assert "atmospheric_urban" not in skips
    finally:
        os.unlink(path)


def test_load_taxonomy_skip_keys():
    """All entries under 'skip' group are in skip_keys set."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        yaml.dump({
            "good": {"a": "desc a", "b": "desc b"},
            "skip": {"x": "desc x", "y": "desc y", "z": "desc z"},
        }, f)
        path = f.name
    try:
        _, skips = load_taxonomy(path)
        assert skips == {"x", "y", "z"}
    finally:
        os.unlink(path)


def test_load_taxonomy_missing_file():
    """Missing taxonomy file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_taxonomy("/nonexistent/taxonomy.yaml")


def test_load_taxonomy_malformed_yaml():
    """Malformed YAML raises an exception."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("{{invalid yaml!!")
        path = f.name
    try:
        with pytest.raises(Exception):
            load_taxonomy(path)
    finally:
        os.unlink(path)


def test_merge_taxonomies_global_only():
    """No project taxonomy returns global categories only."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        yaml.dump({"cat": {"a": "desc a"}}, f)
        path = f.name
    try:
        cats, _ = merge_taxonomies(path, project_path=None)
        assert "a" in cats
    finally:
        os.unlink(path)


def test_merge_taxonomies_project_overrides():
    """Project taxonomy category with same key overrides global."""
    with tempfile.TemporaryDirectory() as tmpdir:
        glob_path = os.path.join(tmpdir, "global.yaml")
        proj_path = os.path.join(tmpdir, "project.json")
        _write_taxonomy(glob_path, {"cat": {"shared_key": "global desc"}})
        with open(proj_path, "w") as f:
            json.dump({"shared_key": "project desc"}, f)
        cats, _ = merge_taxonomies(glob_path, proj_path)
        assert cats["shared_key"] == "project desc"


def test_merge_taxonomies_project_wrapper():
    """Handles {"project_specific": {...}} wrapper format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        glob_path = os.path.join(tmpdir, "global.yaml")
        proj_path = os.path.join(tmpdir, "project.json")
        _write_taxonomy(glob_path, {"cat": {"a": "desc a"}})
        with open(proj_path, "w") as f:
            json.dump({"project_specific": {"b": "desc b"}}, f)
        cats, _ = merge_taxonomies(glob_path, proj_path)
        assert "a" in cats
        assert "b" in cats


def test_cluster_unknowns_few_samples():
    """Fewer embeddings than min_samples returns all noise."""
    emb = np.random.randn(2, 768).astype(np.float32)
    labels = cluster_unknowns(emb, eps=0.3, min_samples=3)
    assert np.all(labels == -1)


def test_cluster_unknowns_clear_clusters():
    """Two tight groups produce 2 distinct clusters."""
    group_a = np.random.randn(10, 768).astype(np.float32) * 0.01 + np.array([1.0] + [0.0] * 767)
    group_b = np.random.randn(10, 768).astype(np.float32) * 0.01 + np.array([0.0, 1.0] + [0.0] * 766)
    emb = np.vstack([group_a, group_b])
    labels = cluster_unknowns(emb, eps=0.3, min_samples=3)
    unique = set(labels)
    unique.discard(-1)
    assert len(unique) == 2


def test_cluster_unknowns_all_noise():
    """Scattered points with tight eps returns all noise."""
    emb = np.random.randn(20, 768).astype(np.float32)
    labels = cluster_unknowns(emb, eps=0.001, min_samples=3)
    assert np.all(labels == -1)
```

- [ ] **Step 2: Run tests**

```bash
cd ".claude/skills/asset-analyzer/scripts"
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_discover.py -v
```

Expected: 10 tests PASS

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/asset-analyzer/scripts/test_discover.py
git commit -m "test: add discover.py unit tests — taxonomy loading, merging, clustering"
```

---

## Task 5: Expand test_evaluate.py (9 new tests)

**Files:**
- Modify: `.claude/skills/asset-analyzer/scripts/test_evaluate.py`

- [ ] **Step 1: Append new tests**

Add after existing 9 tests. Do NOT modify existing tests.

```python
def test_iou_zero_length_segment():
    """Segment with start == end has zero area, IoU = 0."""
    assert compute_iou(5, 5, 0, 10) == 0.0


def test_iou_negative_segment():
    """Segment with start > end returns 0."""
    assert compute_iou(10, 5, 0, 15) == 0.0


def test_iou_touching_segments():
    """Adjacent segments [0,5] and [5,10] have IoU = 0 (no overlap)."""
    assert compute_iou(0, 5, 5, 10) == 0.0


def test_evaluate_multiple_gt_one_pred():
    """One prediction can only match one GT segment (greedy)."""
    gt = [
        {"start_sec": 10, "end_sec": 20, "label": "a"},
        {"start_sec": 12, "end_sec": 18, "label": "b"},
    ]
    pred = [{"start_sec": 10, "end_sec": 20}]
    result = evaluate_segments(gt, pred, iou_threshold=0.5)
    assert result["hits"] == 1
    assert result["misses"] == 1


def test_evaluate_one_gt_multiple_pred():
    """Multiple predictions, only one matches GT, rest are FP."""
    gt = [{"start_sec": 10, "end_sec": 20, "label": "a"}]
    pred = [
        {"start_sec": 10, "end_sec": 20},
        {"start_sec": 50, "end_sec": 60},
        {"start_sec": 70, "end_sec": 80},
    ]
    result = evaluate_segments(gt, pred, iou_threshold=0.5)
    assert result["hits"] == 1
    assert result["false_positives"] == 2


def test_evaluate_empty_both():
    """No GT + no predictions returns zeroed metrics."""
    result = evaluate_segments([], [], iou_threshold=0.5)
    assert result["hits"] == 0
    assert result["misses"] == 0
    assert result["false_positives"] == 0
    assert result["precision"] == 0.0
    assert result["recall"] == 0.0


def test_suggest_calibration_low_precision():
    """Precision < 0.75 suggests raising high_threshold."""
    metrics = {"recall": 0.90, "precision": 0.60, "hits": 6, "misses": 0, "false_positives": 4}
    suggestions = suggest_calibration(metrics, [], current_params={
        "boundary_percentile": 90, "high_threshold": 0.25, "low_threshold": 0.15,
    })
    assert any(s["param"] == "high_threshold" for s in suggestions)


def test_suggest_calibration_both_low():
    """Both low recall and low precision produce multiple suggestions."""
    metrics = {"recall": 0.50, "precision": 0.50, "hits": 2, "misses": 2, "false_positives": 2}
    missed = [
        {"label": "test", "nearest_pred_score": 0.13},
        {"label": "test2", "nearest_pred_score": 0.14},
    ]
    suggestions = suggest_calibration(metrics, missed, current_params={
        "boundary_percentile": 90, "high_threshold": 0.25, "low_threshold": 0.15,
    })
    assert len(suggestions) >= 2


def test_generate_template_no_videos():
    """Empty glob pattern returns template with empty videos list."""
    template = generate_template("/nonexistent/path/*.mp4", "Test Project")
    assert template["project"] == "Test Project"
    assert template["videos"] == []
```

- [ ] **Step 2: Run tests**

```bash
cd ".claude/skills/asset-analyzer/scripts"
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_evaluate.py -v
```

Expected: 18 tests PASS

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/asset-analyzer/scripts/test_evaluate.py
git commit -m "test: expand evaluate.py test coverage — 9 new edge case tests"
```

---

## Task 6: Create test_promote.py (6 tests)

**Files:**
- Create: `.claude/skills/asset-analyzer/scripts/test_promote.py`

- [ ] **Step 1: Write test_promote.py**

```python
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
```

- [ ] **Step 2: Run tests**

```bash
cd ".claude/skills/asset-analyzer/scripts"
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_promote.py -v
```

Expected: 6 tests PASS

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/asset-analyzer/scripts/test_promote.py
git commit -m "test: add promote.py unit tests — 6 tests for pool promotion logic"
```

---

## Task 7: Create test_error_handling.py (10 tests)

**Files:**
- Create: `.claude/skills/asset-analyzer/scripts/test_error_handling.py`

- [ ] **Step 1: Write test_error_handling.py**

```python
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


def test_pool_index_readonly_dir():
    """put() on a directory that doesn't exist yet creates it."""
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
```

- [ ] **Step 2: Run tests**

```bash
cd ".claude/skills/asset-analyzer/scripts"
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_error_handling.py -v
```

Expected: 10 tests PASS

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/asset-analyzer/scripts/test_error_handling.py
git commit -m "test: add cross-cutting error handling tests — 10 edge case tests"
```

---

## Task 8: Create test_integration_embed.py (8 tests)

**Files:**
- Create: `.claude/skills/asset-analyzer/scripts/test_integration_embed.py`

- [ ] **Step 1: Write test_integration_embed.py**

Read the full test code from spec section 3, "test_integration_embed.py". Write the file with all 8 tests exactly as specified in the spec: `test_embed_single_video`, `test_embed_cache_skip`, `test_embed_force_reembed`, `test_embed_frame_count_matches_duration`, `test_embed_embeddings_normalized`, `test_embed_health_check_after_embed`, `test_embed_timestamps_sequential`, `test_embed_directory`.

Key structure:
- Module-level CUDA skip: `if not torch.cuda.is_available(): pytest.skip(...)`
- `_get_first_staging_video()` helper that skips if no staging videos
- `pe_model` module-scoped fixture that loads PE-Core once
- PROJECT_DIR and STAGING_DIR constants pointing to Duplessis project
- Each test uses temp directories for pool isolation

The full code is in `docs/superpowers/specs/2026-03-31-asset-analyzer-test-suite-design.md`, Section 3, "test_integration_embed.py".

- [ ] **Step 2: Run tests**

```bash
cd ".claude/skills/asset-analyzer/scripts"
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_integration_embed.py -v
```

Expected: 8 tests PASS (or SKIP if no staging videos)

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/asset-analyzer/scripts/test_integration_embed.py
git commit -m "test: add embed.py integration tests — 8 GPU tests with real footage"
```

---

## Task 9: Create test_integration_search.py (7 tests)

**Files:**
- Create: `.claude/skills/asset-analyzer/scripts/test_integration_search.py`

- [ ] **Step 1: Write test_integration_search.py**

Read the full test code from spec section 3, "test_integration_search.py". Write the file with all 7 tests: `test_search_returns_candidates`, `test_search_irrelevant_query_low_scores`, `test_search_scene_boundaries_detected`, `test_search_candidates_sorted`, `test_search_weak_query_flagged`, `test_search_pool_only_filter`, `test_search_multiple_queries`.

Key structure:
- Module-level CUDA skip
- `embedded_pool` module-scoped fixture that embeds first staging video
- Each test uses the pre-embedded pool and model

The full code is in the spec, Section 3, "test_integration_search.py".

- [ ] **Step 2: Run tests**

```bash
cd ".claude/skills/asset-analyzer/scripts"
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_integration_search.py -v
```

Expected: 7 tests PASS (or SKIP if no staging videos)

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/asset-analyzer/scripts/test_integration_search.py
git commit -m "test: add search.py integration tests — 7 GPU tests with real queries"
```

---

## Task 10: Create test_integration_discover.py (6 tests)

**Files:**
- Create: `.claude/skills/asset-analyzer/scripts/test_integration_discover.py`

- [ ] **Step 1: Write test_integration_discover.py**

Read the full test code from spec section 3, "test_integration_discover.py". Write the file with all 6 tests: `test_discover_categories_populated`, `test_discover_skip_categories_excluded`, `test_discover_unknown_frames_exist`, `test_discover_cluster_has_representative`, `test_discover_project_taxonomy_merges`, `test_discover_inventory_minutes_plausible`.

Key structure:
- Module-level CUDA skip
- `embedded_pool` module-scoped fixture
- TAXONOMY_PATH points to `references/taxonomy_global.yaml`

The full code is in the spec, Section 3, "test_integration_discover.py".

- [ ] **Step 2: Run tests**

```bash
cd ".claude/skills/asset-analyzer/scripts"
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_integration_discover.py -v
```

Expected: 6 tests PASS (or SKIP if no staging videos)

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/asset-analyzer/scripts/test_integration_discover.py
git commit -m "test: add discover.py integration tests — 6 GPU taxonomy + clustering tests"
```

---

## Task 11: Create test_integration_pipeline.py (5 tests)

**Files:**
- Create: `.claude/skills/asset-analyzer/scripts/test_integration_pipeline.py`

- [ ] **Step 1: Write test_integration_pipeline.py**

Read the full test code from spec section 3, "test_integration_pipeline.py". Write the file with all 5 tests: `test_pipeline_embed_search_extract`, `test_pipeline_embed_discover_cluster`, `test_pipeline_promote_roundtrip`, `test_pipeline_evaluate_template`, `test_pipeline_search_both_pools`.

Key structure:
- Module-level CUDA skip
- `pipeline_setup` module-scoped fixture that embeds video and creates both pool dirs
- Tests the full flow across multiple scripts

The full code is in the spec, Section 3, "test_integration_pipeline.py".

- [ ] **Step 2: Run tests**

```bash
cd ".claude/skills/asset-analyzer/scripts"
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_integration_pipeline.py -v
```

Expected: 5 tests PASS (or SKIP if no staging videos)

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/asset-analyzer/scripts/test_integration_pipeline.py
git commit -m "test: add end-to-end pipeline integration tests — 5 full-flow tests"
```

---

## Task 12: Create skill evaluation files

**Files:**
- Create: `.claude/skills/asset-analyzer/evals/evals.json`
- Create: `.claude/skills/asset-analyzer/evals/rubrics/query_refinement.md`
- Create: `.claude/skills/asset-analyzer/evals/rubrics/taxonomy_generation.md`
- Create: `.claude/skills/asset-analyzer/evals/rubrics/presentation_quality.md`
- Create: `.claude/skills/asset-analyzer/evals/rubrics/workflow_correctness.md`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p ".claude/skills/asset-analyzer/evals/rubrics"
```

- [ ] **Step 2: Write evals.json**

Write the evals.json file exactly as specified in spec Section 4, "evals/evals.json". Contains 5 eval prompts (E01-E05) with functional assertions.

- [ ] **Step 3: Write all 4 rubric files**

Write each rubric exactly as specified in spec Section 4, "Quality Rubrics":
- `query_refinement.md` — 1-5 scoring for query rephrasing quality
- `taxonomy_generation.md` — 1-5 scoring for auto-generated category quality
- `presentation_quality.md` — 1-5 scoring for results presentation
- `workflow_correctness.md` — 1-5 scoring for SKILL.md workflow adherence

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/asset-analyzer/evals/
git commit -m "test: add skill-level evaluation prompts and quality rubrics"
```

---

## Task 13: Run full unit test suite and fix failures

**Files:**
- Potentially modify any test file if tests fail due to implementation differences

- [ ] **Step 1: Run all unit tests**

```bash
cd ".claude/skills/asset-analyzer/scripts"
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_pool.py test_ingest.py test_search.py test_discover.py test_evaluate.py test_promote.py test_error_handling.py -v 2>&1 | tee unit_test_results.txt
```

Expected: 87 tests. Note any failures.

- [ ] **Step 2: Fix any failing tests**

If tests fail, diagnose whether the issue is in the test or the implementation:
- **Test expects wrong behavior:** Fix the test assertion
- **Implementation has a bug:** Fix the implementation, document the bug found
- **Import error:** Fix sys.path or module reference

- [ ] **Step 3: Run all integration tests**

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_integration_embed.py test_integration_search.py test_integration_discover.py test_integration_pipeline.py -v 2>&1 | tee integration_test_results.txt
```

Expected: 26 tests. Note any failures.

- [ ] **Step 4: Fix any failing integration tests**

Same diagnosis approach. Integration tests may reveal real bugs in the pipeline.

- [ ] **Step 5: Commit fixes**

```bash
git add .claude/skills/asset-analyzer/scripts/
git commit -m "test: fix test failures found during full suite run"
```

- [ ] **Step 6: Final full run**

```bash
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest -v 2>&1 | tee full_test_results.txt
```

Expected: All 113 tests PASS (some integration tests may SKIP if no staging videos).

- [ ] **Step 7: Report findings**

Create a summary of:
- Total tests: passed / failed / skipped
- Bugs found in implementation (if any)
- Edge cases that revealed issues
- Improvement opportunities identified

```bash
rm -f unit_test_results.txt integration_test_results.txt
git add .claude/skills/asset-analyzer/scripts/
git commit -m "test: complete asset-analyzer V2 test suite — all tests passing"
```
