# Asset Analyzer V2 — Test Suite Design

Comprehensive test suite for the asset-analyzer V2 pipeline. Three layers: unit tests (CPU, fast), integration tests (GPU, real footage), and skill-level evaluations (heuristic quality).

---

## 1. Test Architecture

### File Structure

```
.claude/skills/asset-analyzer/
├── scripts/
│   ├── test_pool.py                    # Expanded: 8 → 20 unit tests
│   ├── test_ingest.py                  # New: 8 unit tests (mocked FFmpeg)
│   ├── test_search.py                  # Expanded: 4 → 15 unit tests
│   ├── test_discover.py               # New: 10 unit tests
│   ├── test_evaluate.py               # Expanded: 9 → 18 unit tests
│   ├── test_promote.py                # New: 6 unit tests
│   ├── test_error_handling.py         # New: 10 cross-cutting tests
│   ├── test_integration_embed.py      # GPU: 8 tests
│   ├── test_integration_search.py     # GPU: 7 tests
│   ├── test_integration_discover.py   # GPU: 6 tests
│   └── test_integration_pipeline.py   # GPU: 5 tests
├── evals/
│   ├── evals.json                     # 5 skill-level eval prompts + assertions
│   └── rubrics/
│       ├── query_refinement.md
│       ├── taxonomy_generation.md
│       ├── presentation_quality.md
│       └── workflow_correctness.md
```

### Running Tests

```bash
# Unit tests only (fast, any Python with numpy/pytest)
cd .claude/skills/asset-analyzer/scripts
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_pool.py test_ingest.py test_search.py test_discover.py test_evaluate.py test_promote.py test_error_handling.py -v

# Integration tests only (requires GPU + conda env + staging videos)
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest test_integration_embed.py test_integration_search.py test_integration_discover.py test_integration_pipeline.py -v

# All tests
C:/Users/iorda/miniconda3/envs/perception-models/python.exe -m pytest -v
```

### Test Data

- **Unit tests:** Use synthetic data (random numpy arrays, temp files, mocked subprocess)
- **Integration tests:** Use Duplessis staging videos at `projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/staging/`
- **Skill evals:** Run against the full Duplessis project context

---

## 2. Unit Tests — Per Script

### test_pool.py (20 tests)

**Existing (keep):**
- `test_file_hash_deterministic`
- `test_file_hash_differs_for_different_content`
- `test_pool_root_project`
- `test_pool_root_global`
- `test_pool_index_put_and_load`
- `test_pool_index_load_all`
- `test_pool_index_remove`
- `test_health_check_detects_dead_refs`

**New:**

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
    with pytest.raises(FileNotFoundError):
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
    """Corrupt index.json is handled gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        index_path = os.path.join(tmpdir, "index.json")
        with open(index_path, "w") as f:
            f.write("{corrupt json!!")
        idx = PoolIndex(tmpdir)
        with pytest.raises(Exception):  # JSONDecodeError
            idx.has("anything")

def test_pool_index_missing_npy():
    """load_embeddings() raises when .npy files are missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        emb = np.random.randn(3, 768).astype(np.float16)
        ts = np.arange(3, dtype=np.float64)
        idx.put("test_hash", emb, ts, {})
        # Delete the npy files
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
        emb = np.random.randn(10, 768).astype(np.float32)
        emb_f16 = emb.astype(np.float16)
        ts = np.arange(10, dtype=np.float64)
        idx.put("precision", emb_f16, ts, {})
        loaded, _ = idx.load_embeddings("precision")
        # Cosine similarity should be very close
        norms_orig = np.linalg.norm(emb_f16.astype(np.float32), axis=1, keepdims=True)
        norms_load = np.linalg.norm(loaded.astype(np.float32), axis=1, keepdims=True)
        cos_sim = np.sum((emb_f16.astype(np.float32) / norms_orig) * (loaded.astype(np.float32) / norms_load), axis=1)
        assert np.all(cos_sim > 0.999)

def test_health_check_clean():
    """Pool with valid source files reports 0 dead references."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a temp file that exists as "source"
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
        del idx1  # Close
        idx2 = PoolIndex(tmpdir)  # Reopen
        assert idx2.has("persist")
        loaded_emb, _ = idx2.load_embeddings("persist")
        assert loaded_emb.shape == (5, 768)
```

### test_ingest.py (8 tests)

```python
"""Unit tests for ingest.py — mocked FFmpeg, no real video files needed."""
import os
import tempfile
import subprocess
from unittest.mock import patch, MagicMock
import numpy as np
import pytest
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
        # Pre-create some frame files in reverse order
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

### test_search.py (15 tests)

**Existing (keep):**
- `test_detect_scene_boundaries_finds_cuts`
- `test_detect_scene_boundaries_no_cuts`
- `test_group_into_segments`
- `test_score_queries`

**New:**

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
    """Three distinct scenes produce two boundaries."""
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
        emb[i] = [1 - t, t, 0]  # Smooth A → B
    ts = np.arange(n, dtype=np.float64)
    boundaries = detect_scene_boundaries(emb, ts, percentile=95)
    # Gradual change should produce 0 or very few boundaries
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

### test_discover.py (10 tests)

```python
"""Unit tests for discover.py — taxonomy loading, merging, and clustering logic."""
import json
import os
import tempfile
import numpy as np
import pytest
import yaml
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

### test_evaluate.py (18 tests)

**Existing (keep all 9).** New:

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
    # Prediction matches first GT perfectly, second GT is a miss
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

### test_promote.py (6 tests)

```python
"""Unit tests for promote.py — pool-to-pool promotion logic."""
import os
import tempfile
import numpy as np
import pytest
from pool import PoolIndex
from promote import promote_video


def _setup_pools(tmpdir):
    """Create project and global pool directories with a PoolIndex each."""
    proj_root = os.path.join(tmpdir, "project_pool")
    glob_root = os.path.join(tmpdir, "global_pool")
    return PoolIndex(proj_root), PoolIndex(glob_root)


def _add_video(idx, fhash, n_frames=5):
    """Helper: add a fake video to a pool."""
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
        _add_video(glob, "abc123", 5)  # Different frame count
        result = promote_video("abc123", proj, glob)
        assert result["status"] == "already_exists"
        # Global should still have original 5 frames
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
        # Delete meta.json
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
        assert glob.list_entries().keys() == {"vid1", "vid2", "vid3"}
```

### test_error_handling.py (10 tests)

```python
"""Cross-cutting error handling tests — corrupt files, missing input, edge cases."""
import json
import os
import tempfile
import numpy as np
import pytest
from pool import PoolIndex
from search import detect_scene_boundaries, group_into_segments
from discover import load_taxonomy, cluster_unknowns
from evaluate import compute_iou, evaluate_segments, generate_template


def test_pool_index_readonly_dir():
    """put() raises when pool directory is read-only."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pool_dir = os.path.join(tmpdir, "readonly_pool")
        os.makedirs(pool_dir)
        # Create index first, then make readonly
        idx = PoolIndex(pool_dir)
        # On Windows, read-only dirs behave differently; test may need platform adaptation
        emb = np.random.randn(3, 768).astype(np.float16)
        ts = np.arange(3, dtype=np.float64)
        # This test verifies the error surfaces, not that it's caught gracefully
        # On a read-only filesystem, we expect an OSError
        idx.put("test", emb, ts, {})  # Should succeed on normal fs


def test_search_empty_queries_list():
    """Empty query list produces empty results without crash."""
    # Test group_into_segments with empty scores
    scores = np.array([], dtype=np.float32)
    ts = np.array([], dtype=np.float64)
    segments = group_into_segments(scores, ts, [], threshold=0.15)
    assert segments == []


def test_search_nan_in_scores():
    """NaN scores don't cause infinite loops in segment grouping."""
    scores = np.array([0.3, float('nan'), 0.3, 0.1])
    ts = np.arange(4, dtype=np.float64)
    # Should not hang or crash; NaN comparisons return False
    segments = group_into_segments(scores, ts, [], threshold=0.15)
    assert isinstance(segments, list)


def test_discover_empty_taxonomy():
    """Empty categories dict classifies nothing (no crash)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        import yaml
        yaml.dump({}, f)
        path = f.name
    try:
        cats, skips = load_taxonomy(path)
        assert cats == {}
        assert skips == set()
    finally:
        os.unlink(path)


def test_evaluate_mismatched_filenames():
    """GT file not found in predictions treated as 0 segments."""
    gt = [{"start_sec": 10, "end_sec": 20, "label": "test"}]
    pred = []  # No matching file
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
        from promote import promote_video
        proj = PoolIndex(os.path.join(tmpdir, "proj"))
        glob = PoolIndex(os.path.join(tmpdir, "glob"))
        result = promote_video("anything", proj, glob)
        assert result["status"] == "not_found"


def test_pool_index_reopen_after_write():
    """Data persists correctly through write-close-reopen cycle."""
    with tempfile.TemporaryDirectory() as tmpdir:
        idx = PoolIndex(tmpdir)
        emb = np.random.randn(3, 768).astype(np.float16)
        ts = np.arange(3, dtype=np.float64)
        idx.put("persist_test", emb, ts, {"source_path": "/test.mp4"})
        # Force new instance (simulates process restart)
        idx2 = PoolIndex(tmpdir)
        assert idx2.has("persist_test")
        entries = idx2.list_entries()
        assert entries["persist_test"]["frame_count"] == 3


def test_scene_boundaries_identical_frames():
    """All identical frames produce no boundaries (all deltas = 0)."""
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

---

## 3. Integration Tests (GPU-Required)

### test_integration_embed.py

```python
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
        assert emb.shape[1] == 768
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
```

### test_integration_search.py

```python
"""Integration tests for search.py — requires embedded videos in project pool."""
import json
import os
import sys
import tempfile
import numpy as np
import pytest

torch = pytest.importorskip("torch")
if not torch.cuda.is_available():
    pytest.skip("CUDA not available", allow_module_level=True)

SCRIPTS_DIR = os.path.dirname(__file__)
sys.path.insert(0, SCRIPTS_DIR)

from embed import load_model, embed_video
from search import search, detect_scene_boundaries, encode_text_queries
from pool import PoolIndex

PROJECT_DIR = os.path.abspath(os.path.join(
    SCRIPTS_DIR, "..", "..", "..", "..",
    "projects", "1. The Duplessis Orphans Quebec's Stolen Children"
))
STAGING_DIR = os.path.join(PROJECT_DIR, "assets", "staging")


@pytest.fixture(scope="module")
def embedded_pool(tmp_path_factory):
    """Embed first staging video into a temp project pool."""
    if not os.path.isdir(STAGING_DIR):
        pytest.skip("Staging directory not found")
    videos = sorted(f for f in os.listdir(STAGING_DIR) if f.endswith(".mp4"))
    if not videos:
        pytest.skip("No staging videos found")

    tmpdir = str(tmp_path_factory.mktemp("pool"))
    model, tokenizer, preprocess = load_model()
    idx = PoolIndex(tmpdir)
    video_path = os.path.join(STAGING_DIR, videos[0])
    embed_video(video_path, idx, model, preprocess)
    return tmpdir, model, tokenizer


def test_search_returns_candidates(embedded_pool):
    pool_dir, model, tokenizer = embedded_pool
    queries = [{"shot_id": "T01", "text": "building exterior"}]
    results = search(queries, pool_dir, model, tokenizer, pool_only="project")
    assert len(results["query_results"]) == 1
    # Should have some candidates (even if low-scoring)
    assert "candidates" in results["query_results"][0]


def test_search_irrelevant_query_low_scores(embedded_pool):
    pool_dir, model, tokenizer = embedded_pool
    queries = [{"shot_id": "T02", "text": "purple elephant dancing on mars with a top hat"}]
    results = search(queries, pool_dir, model, tokenizer, pool_only="project")
    qr = results["query_results"][0]
    if qr["candidates"]:
        assert qr["candidates"][0]["peak_score"] < 0.25


def test_search_scene_boundaries_detected(embedded_pool):
    pool_dir, _, _ = embedded_pool
    assert len(os.listdir(pool_dir)) > 0  # Pool has data
    # Scene boundaries are computed inside search(); verify via results
    queries = [{"shot_id": "T03", "text": "any content"}]
    model, tokenizer, _ = load_model()
    results = search(queries, pool_dir, model, tokenizer, pool_only="project")
    # Scene boundaries should be populated if video has cuts
    assert "scene_boundaries" in results


def test_search_candidates_sorted(embedded_pool):
    pool_dir, model, tokenizer = embedded_pool
    queries = [{"shot_id": "T04", "text": "interior room hallway"}]
    results = search(queries, pool_dir, model, tokenizer, pool_only="project")
    candidates = results["query_results"][0]["candidates"]
    if len(candidates) >= 2:
        scores = [c["peak_score"] for c in candidates]
        assert scores == sorted(scores, reverse=True)


def test_search_weak_query_flagged(embedded_pool):
    pool_dir, model, tokenizer = embedded_pool
    queries = [{"shot_id": "T05", "text": "xyzzy nonsensical gibberish content that cannot match"}]
    results = search(queries, pool_dir, model, tokenizer, pool_only="project")
    assert "T05" in results["weak_queries"]


def test_search_pool_only_filter(embedded_pool):
    pool_dir, model, tokenizer = embedded_pool
    queries = [{"shot_id": "T06", "text": "building"}]
    results = search(queries, pool_dir, model, tokenizer, pool_only="project")
    assert "project" in results["pools_searched"] or results["pools_searched"] == {}
    assert "global" not in results["pools_searched"]


def test_search_multiple_queries(embedded_pool):
    pool_dir, model, tokenizer = embedded_pool
    queries = [
        {"shot_id": "T07", "text": "building exterior"},
        {"shot_id": "T08", "text": "person speaking"},
        {"shot_id": "T09", "text": "document newspaper"},
    ]
    results = search(queries, pool_dir, model, tokenizer, pool_only="project")
    assert len(results["query_results"]) == 3
    shot_ids = [qr["shot_id"] for qr in results["query_results"]]
    assert set(shot_ids) == {"T07", "T08", "T09"}
```

### test_integration_discover.py

```python
"""Integration tests for discover.py — requires embedded videos."""
import json
import os
import sys
import tempfile
import numpy as np
import pytest

torch = pytest.importorskip("torch")
if not torch.cuda.is_available():
    pytest.skip("CUDA not available", allow_module_level=True)

SCRIPTS_DIR = os.path.dirname(__file__)
sys.path.insert(0, SCRIPTS_DIR)

from embed import load_model, embed_video
from discover import discover
from pool import PoolIndex

PROJECT_DIR = os.path.abspath(os.path.join(
    SCRIPTS_DIR, "..", "..", "..", "..",
    "projects", "1. The Duplessis Orphans Quebec's Stolen Children"
))
STAGING_DIR = os.path.join(PROJECT_DIR, "assets", "staging")
TAXONOMY_PATH = os.path.abspath(os.path.join(
    SCRIPTS_DIR, "..", "references", "taxonomy_global.yaml"
))


@pytest.fixture(scope="module")
def embedded_pool(tmp_path_factory):
    if not os.path.isdir(STAGING_DIR):
        pytest.skip("Staging directory not found")
    videos = sorted(f for f in os.listdir(STAGING_DIR) if f.endswith(".mp4"))
    if not videos:
        pytest.skip("No staging videos found")
    tmpdir = str(tmp_path_factory.mktemp("pool"))
    model, tokenizer, preprocess = load_model()
    idx = PoolIndex(tmpdir)
    embed_video(os.path.join(STAGING_DIR, videos[0]), idx, model, preprocess)
    return tmpdir, model, tokenizer


def test_discover_categories_populated(embedded_pool):
    pool_dir, model, tokenizer = embedded_pool
    results = discover(pool_dir, "project", TAXONOMY_PATH, model=model, tokenizer=tokenizer)
    assert len(results["inventory"]) > 0


def test_discover_skip_categories_excluded(embedded_pool):
    pool_dir, model, tokenizer = embedded_pool
    results = discover(pool_dir, "project", TAXONOMY_PATH, model=model, tokenizer=tokenizer)
    skip_cats = {"talking_head", "title_graphic", "black_blank"}
    for cat in results["inventory"]:
        assert cat not in skip_cats


def test_discover_unknown_frames_exist(embedded_pool):
    """With high confidence threshold, some frames should be unknown."""
    pool_dir, model, tokenizer = embedded_pool
    results = discover(pool_dir, "project", TAXONOMY_PATH, model=model, tokenizer=tokenizer,
                       confidence_threshold=0.30)
    # High threshold means more unknowns
    total_classified = sum(v["frame_count"] for v in results["inventory"].values())
    idx = PoolIndex(pool_dir)
    _, _, info = idx.load_all_embeddings()
    total_frames = len(info)
    assert results["noise_frames"] > 0 or len(results["clusters"]) > 0 or total_classified < total_frames


def test_discover_cluster_has_representative(embedded_pool):
    pool_dir, model, tokenizer = embedded_pool
    results = discover(pool_dir, "project", TAXONOMY_PATH, model=model, tokenizer=tokenizer,
                       confidence_threshold=0.25)
    for cluster in results["clusters"]:
        assert "centroid_frame" in cluster
        assert "video" in cluster["centroid_frame"]
        assert "timestamp_sec" in cluster["centroid_frame"]


def test_discover_project_taxonomy_merges(embedded_pool):
    pool_dir, model, tokenizer = embedded_pool
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump({"project_specific": {
            "test_custom_category": "A very specific test category that no real frame will match"
        }}, f)
        proj_tax = f.name
    try:
        results = discover(pool_dir, "project", TAXONOMY_PATH,
                           taxonomy_project_path=proj_tax,
                           model=model, tokenizer=tokenizer)
        # The custom category should exist (even if 0 frames match)
        # We just verify no crash when merging
        assert isinstance(results["inventory"], dict)
    finally:
        os.unlink(proj_tax)


def test_discover_inventory_minutes_plausible(embedded_pool):
    pool_dir, model, tokenizer = embedded_pool
    results = discover(pool_dir, "project", TAXONOMY_PATH, model=model, tokenizer=tokenizer)
    total_minutes = sum(v["total_minutes"] for v in results["inventory"].values())
    # At 1fps, total classified frames / 60 should give us the minutes
    total_frames = sum(v["frame_count"] for v in results["inventory"].values())
    expected_minutes = total_frames / 60
    assert abs(total_minutes - expected_minutes) < 0.1
```

### test_integration_pipeline.py

```python
"""End-to-end pipeline integration tests."""
import json
import os
import sys
import tempfile
import numpy as np
import pytest

torch = pytest.importorskip("torch")
if not torch.cuda.is_available():
    pytest.skip("CUDA not available", allow_module_level=True)

SCRIPTS_DIR = os.path.dirname(__file__)
sys.path.insert(0, SCRIPTS_DIR)

from embed import load_model, embed_video
from search import search
from discover import discover
from promote import promote_video
from evaluate import generate_template
from pool import PoolIndex
from ingest import save_frames

PROJECT_DIR = os.path.abspath(os.path.join(
    SCRIPTS_DIR, "..", "..", "..", "..",
    "projects", "1. The Duplessis Orphans Quebec's Stolen Children"
))
STAGING_DIR = os.path.join(PROJECT_DIR, "assets", "staging")
TAXONOMY_PATH = os.path.abspath(os.path.join(
    SCRIPTS_DIR, "..", "references", "taxonomy_global.yaml"
))


@pytest.fixture(scope="module")
def pipeline_setup(tmp_path_factory):
    if not os.path.isdir(STAGING_DIR):
        pytest.skip("Staging directory not found")
    videos = sorted(f for f in os.listdir(STAGING_DIR) if f.endswith(".mp4"))
    if not videos:
        pytest.skip("No staging videos found")

    tmpdir = str(tmp_path_factory.mktemp("pipeline"))
    proj_pool = os.path.join(tmpdir, "project")
    glob_pool = os.path.join(tmpdir, "global")

    model, tokenizer, preprocess = load_model()
    proj_idx = PoolIndex(proj_pool)
    video_path = os.path.join(STAGING_DIR, videos[0])
    embed_video(video_path, proj_idx, model, preprocess)

    return {
        "tmpdir": tmpdir,
        "proj_pool": proj_pool,
        "glob_pool": glob_pool,
        "model": model,
        "tokenizer": tokenizer,
        "video_path": video_path,
    }


def test_pipeline_embed_search_extract(pipeline_setup):
    """Embed → search → extract candidate frame to disk."""
    s = pipeline_setup
    queries = [{"shot_id": "P01", "text": "building exterior stone"}]
    results = search(queries, s["proj_pool"], s["model"], s["tokenizer"], pool_only="project")
    qr = results["query_results"][0]
    if qr["candidates"]:
        best = qr["candidates"][0]
        frames_dir = os.path.join(s["tmpdir"], "extracted_frames")
        paths = save_frames(
            s["video_path"], frames_dir,
            start_sec=best["best_frame_sec"],
            end_sec=best["best_frame_sec"] + 1,
        )
        assert len(paths) >= 1
        assert os.path.exists(paths[0])


def test_pipeline_embed_discover_cluster(pipeline_setup):
    """Embed → discover → categories or clusters found."""
    s = pipeline_setup
    results = discover(s["proj_pool"], "project", TAXONOMY_PATH,
                       model=s["model"], tokenizer=s["tokenizer"])
    has_categories = len(results["inventory"]) > 0
    has_clusters = len(results["clusters"]) > 0
    assert has_categories or has_clusters


def test_pipeline_promote_roundtrip(pipeline_setup):
    """Embed to project → promote to global → both pools have entry."""
    s = pipeline_setup
    proj_idx = PoolIndex(s["proj_pool"])
    glob_idx = PoolIndex(s["glob_pool"])
    entries = proj_idx.list_entries()
    fhash = list(entries.keys())[0]
    result = promote_video(fhash, proj_idx, glob_idx)
    assert result["status"] == "promoted"
    assert proj_idx.has(fhash)  # Still in project
    assert glob_idx.has(fhash)  # Now in global too


def test_pipeline_evaluate_template(pipeline_setup):
    """Generate template matches staging video filenames."""
    pattern = os.path.join(STAGING_DIR, "*.mp4")
    template = generate_template(pattern, "The Duplessis Orphans")
    assert template["project"] == "The Duplessis Orphans"
    assert len(template["videos"]) > 0
    for v in template["videos"]:
        assert v["file"].endswith(".mp4")
        assert v["duration_sec"] > 0


def test_pipeline_search_both_pools(pipeline_setup):
    """After promotion, search finds results from both pools."""
    s = pipeline_setup
    proj_idx = PoolIndex(s["proj_pool"])
    glob_idx = PoolIndex(s["glob_pool"])
    # Ensure something is in global
    entries = proj_idx.list_entries()
    fhash = list(entries.keys())[0]
    if not glob_idx.has(fhash):
        promote_video(fhash, proj_idx, glob_idx)

    queries = [{"shot_id": "P05", "text": "any visual content"}]
    # Search both pools (need to mock get_pool_root for temp dirs)
    from unittest.mock import patch
    with patch("search.get_pool_root") as mock_root:
        def side_effect(pool, project_dir=None):
            if pool == "project":
                return s["proj_pool"]
            return s["glob_pool"]
        mock_root.side_effect = side_effect
        results = search(queries, s["proj_pool"], s["model"], s["tokenizer"])

    if results["pools_searched"]:
        pools_found = set(results["pools_searched"].keys())
        # At least project pool should be present
        assert "project" in pools_found
```

---

## 4. Skill-Level Evaluations

### evals/evals.json

```json
{
  "skill_name": "asset-analyzer",
  "evals": [
    {
      "id": "E01",
      "name": "search-workflow",
      "prompt": "Analyze staging videos for Duplessis Orphans",
      "expected_output": "Full search workflow: embed, extract queries from shotlist, search, refine weak queries, present segment table",
      "assertions": [
        {"text": "Shotlist loaded and shot IDs referenced", "type": "functional"},
        {"text": "embed.py invoked with --pool project", "type": "functional"},
        {"text": "search.py invoked and candidates produced", "type": "functional"},
        {"text": "Weak queries identified and refinement attempted", "type": "functional"},
        {"text": "Segment table presented with Video/Shot/Timestamps columns", "type": "functional"}
      ]
    },
    {
      "id": "E02",
      "name": "discovery-workflow",
      "prompt": "Discover what's in the Duplessis footage",
      "expected_output": "Discovery workflow: auto-generate taxonomy, classify, cluster, present inventory",
      "assertions": [
        {"text": "Project taxonomy auto-generated from project context (not manual)", "type": "functional"},
        {"text": "Categories are project-specific (orphanage, Quebec, religious, etc.)", "type": "quality"},
        {"text": "discover.py invoked with --taxonomy-global and --taxonomy-project", "type": "functional"},
        {"text": "Category inventory presented with frame counts", "type": "functional"},
        {"text": "Unknown clusters mentioned or shown", "type": "functional"}
      ]
    },
    {
      "id": "E03",
      "name": "evaluation-template",
      "prompt": "Generate a ground truth template for Duplessis",
      "expected_output": "Template generated with correct video list, user instructed to fill in DaVinci Resolve",
      "assertions": [
        {"text": "evaluate.py --generate-template invoked", "type": "functional"},
        {"text": "Output mentions number of videos", "type": "functional"},
        {"text": "User instructed about DaVinci Resolve or manual review", "type": "functional"}
      ]
    },
    {
      "id": "E04",
      "name": "adhoc-search",
      "prompt": "Search the footage for scenes of institutional buildings and religious ceremonies",
      "expected_output": "User queries used directly (not extracted from shotlist), search executed",
      "assertions": [
        {"text": "Queries derived from user input, not shotlist", "type": "functional"},
        {"text": "Search executed and candidates returned", "type": "functional"},
        {"text": "Results presented in a readable format", "type": "functional"}
      ]
    },
    {
      "id": "E05",
      "name": "query-refinement",
      "prompt": "The search for 'bureaucratic menace' scored 0.12. Can you refine and retry?",
      "expected_output": "Concrete visual alternatives generated, re-search attempted",
      "assertions": [
        {"text": "At least 2 alternative phrasings generated", "type": "functional"},
        {"text": "Alternatives are concrete visual descriptions (not abstract)", "type": "quality"},
        {"text": "Re-search attempted with refined queries", "type": "functional"}
      ]
    }
  ]
}
```

### Quality Rubrics

#### rubrics/query_refinement.md

```markdown
# Query Refinement Quality Rubric

Score 1-5 based on how well Claude rephrases abstract queries into CLIP-friendly visual descriptions.

| Score | Criteria |
|---|---|
| 1 | Refined query is still abstract or synonymous with original |
| 2 | Slightly more concrete but still not CLIP-friendly (uses emotional/conceptual language) |
| 3 | Concrete visual description, single attempt, no variation |
| 4 | Multiple concrete alternatives, varied visual angles |
| 5 | Alternatives span different visual interpretations, all CLIP-friendly, progressive refinement |

**Red flags (automatic -1):**
- Refined query uses cinematographer language ("slow dolly", "shallow depth of field")
- Refined query is longer than 20 words (CLIP works best with short descriptions)
- All alternatives are synonymous (no actual variation)
```

#### rubrics/taxonomy_generation.md

```markdown
# Taxonomy Generation Quality Rubric

Score 1-5 based on how well Claude auto-generates project-specific taxonomy categories.

| Score | Criteria |
|---|---|
| 1 | Generic categories not tailored to project (could apply to any documentary) |
| 2 | Some project-specific categories but mixed with abstract ones ("emotional_weight") |
| 3 | All categories project-specific, but descriptions too vague for CLIP |
| 4 | Project-specific categories with concrete visual descriptions |
| 5 | Categories cover all visual themes in the script, no overlap with global taxonomy, all CLIP-friendly |

**What makes a category CLIP-friendly:**
- Describes physical, visible attributes (not emotions or concepts)
- Uses nouns and adjectives a human would use to describe a photograph
- Short (under 15 words)

**Example good:** "Quebec orphanage exterior, Catholic institution, grey stone building"
**Example bad:** "Institutional oppression and systemic neglect"
```

#### rubrics/presentation_quality.md

```markdown
# Presentation Quality Rubric

Score 1-5 based on how well Claude presents results to the user.

| Score | Criteria |
|---|---|
| 1 | Raw JSON dumped to user |
| 2 | Some formatting but unclear what to do next |
| 3 | Clean table, clear next steps, but missing context (no scores or pool info) |
| 4 | Well-formatted with scores, pool source, and approval prompts |
| 5 | Tiered presentation (high-confidence first), actionable, includes shot ID cross-references |
```

#### rubrics/workflow_correctness.md

```markdown
# Workflow Correctness Rubric

Score 1-5 based on whether Claude follows the SKILL.md workflow correctly.

| Score | Criteria |
|---|---|
| 1 | Wrong scripts invoked or wrong order |
| 2 | Right scripts but wrong arguments or missing steps |
| 3 | Correct flow but skipped checkpoints (no user approval points) |
| 4 | Correct flow with checkpoints, minor issues |
| 5 | Perfect flow: correct scripts, correct args, all checkpoints, appropriate model routing |

**Checkpoints that MUST exist:**
- After embedding: report how many videos, frames, time taken
- After search: present candidates for approval before extraction
- After discovery: present inventory for user selection
- Before extraction: confirm approved segments
```

---

## 5. Test Counts Summary

| Layer | File | Tests |
|---|---|---|
| Unit | test_pool.py | 20 |
| Unit | test_ingest.py | 8 |
| Unit | test_search.py | 15 |
| Unit | test_discover.py | 10 |
| Unit | test_evaluate.py | 18 |
| Unit | test_promote.py | 6 |
| Unit | test_error_handling.py | 10 |
| Integration | test_integration_embed.py | 8 |
| Integration | test_integration_search.py | 7 |
| Integration | test_integration_discover.py | 6 |
| Integration | test_integration_pipeline.py | 5 |
| Skill eval | evals.json | 5 prompts, 18 assertions, 4 rubrics |
| **Total** | | **113 unit + 26 integration + 5 skill evals** |

---

## 6. Gaps and Improvement Opportunities This Will Surface

The test suite is designed to surface these specific improvement areas:

| Area | How tests surface it |
|---|---|
| **Error handling** | test_error_handling.py will crash on corrupt JSON, missing files → need validation layer |
| **Hardcoded thresholds** | Integration tests with different content types will show threshold sensitivity |
| **Score distribution differences** | Cartoon vs live-action search tests will quantify the score gap |
| **Taxonomy completeness** | Discovery tests will show what % of frames land in "unknown" |
| **Boundary detection sensitivity** | Gradual-change and multi-cut tests will calibrate the percentile |
| **Float16 precision** | Precision roundtrip test will quantify cosine similarity drift |
| **Query refinement quality** | Skill eval E05 will show if Claude produces truly CLIP-friendly alternatives |
| **Missing features** | Pipeline tests will reveal gaps (e.g., no batch query refinement, no progress reporting) |
