import numpy as np
import pytest
from search import detect_scene_boundaries, group_into_segments, score_queries

def test_detect_scene_boundaries_finds_cuts():
    """Sharp embedding changes should produce boundaries."""
    emb = np.vstack([
        np.tile([1, 0, 0], (5, 1)),
        np.tile([0, 1, 0], (5, 1)),
    ]).astype(np.float32)
    ts = np.arange(10, dtype=np.float64)

    boundaries = detect_scene_boundaries(emb, ts, percentile=90)
    assert len(boundaries) >= 1
    assert any(abs(b - 4.5) < 1.5 for b in boundaries)

def test_detect_scene_boundaries_no_cuts():
    """Uniform embeddings should produce no boundaries."""
    emb = np.tile([1, 0, 0], (10, 1)).astype(np.float32)
    ts = np.arange(10, dtype=np.float64)
    boundaries = detect_scene_boundaries(emb, ts, percentile=90)
    assert len(boundaries) == 0

def test_group_into_segments():
    """Consecutive high-scoring frames within a scene should group into one segment."""
    scores = np.array([0.1, 0.3, 0.35, 0.28, 0.1, 0.1, 0.05, 0.32, 0.30, 0.1])
    ts = np.arange(10, dtype=np.float64)
    boundaries = [4.5]
    threshold = 0.20

    segments = group_into_segments(scores, ts, boundaries, threshold)
    assert len(segments) == 2
    assert segments[0]["start_sec"] == 1.0
    assert segments[0]["end_sec"] == 3.0
    assert segments[1]["start_sec"] == 7.0

def test_score_queries():
    """Text query embeddings scored against frame embeddings via dot product."""
    frame_emb = np.array([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ], dtype=np.float32)
    query_emb = np.array([
        [1, 0, 0],
        [0, 0, 1],
    ], dtype=np.float32)

    scores = score_queries(frame_emb, query_emb)
    assert scores.shape == (3, 2)
    assert scores[0, 0] > scores[1, 0]
    assert scores[2, 1] > scores[0, 1]


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
    boundaries = detect_scene_boundaries(emb, ts, percentile=90)
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
