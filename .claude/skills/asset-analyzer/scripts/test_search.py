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
