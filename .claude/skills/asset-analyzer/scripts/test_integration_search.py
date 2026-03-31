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
from pool import PoolIndex, get_pool_root

PROJECT_DIR = os.path.abspath(os.path.join(
    SCRIPTS_DIR, "..", "..", "..", "..",
    "projects", "1. The Duplessis Orphans Quebec's Stolen Children"
))
STAGING_DIR = os.path.join(PROJECT_DIR, "assets", "staging")


@pytest.fixture(scope="module")
def embedded_pool(tmp_path_factory):
    """Embed first staging video into a temp project pool.

    The pool is created at <tmpdir>/.broll-index so that
    get_pool_root('project', project_dir=<tmpdir>) resolves correctly.
    """
    if not os.path.isdir(STAGING_DIR):
        pytest.skip("Staging directory not found")
    videos = sorted(f for f in os.listdir(STAGING_DIR) if f.endswith(".mp4"))
    if not videos:
        pytest.skip("No staging videos found")

    tmpdir = str(tmp_path_factory.mktemp("pool"))
    model, tokenizer, preprocess = load_model()
    # Pool root must be at .broll-index subdirectory for get_pool_root to find it
    pool_root = get_pool_root("project", project_dir=tmpdir)
    idx = PoolIndex(pool_root)
    video_path = os.path.join(STAGING_DIR, videos[0])
    embed_video(video_path, idx, model, preprocess)
    # Return project_dir (tmpdir), not the pool root
    return tmpdir, model, tokenizer


def test_search_returns_candidates(embedded_pool):
    project_dir, model, tokenizer = embedded_pool
    queries = [{"shot_id": "T01", "text": "building exterior"}]
    results = search(queries, project_dir, model, tokenizer, pool_only="project")
    assert len(results["query_results"]) == 1
    # Should have some candidates (even if low-scoring)
    assert "candidates" in results["query_results"][0]


def test_search_irrelevant_query_low_scores(embedded_pool):
    project_dir, model, tokenizer = embedded_pool
    queries = [{"shot_id": "T02", "text": "purple elephant dancing on mars with a top hat"}]
    results = search(queries, project_dir, model, tokenizer, pool_only="project")
    qr = results["query_results"][0]
    if qr["candidates"]:
        assert qr["candidates"][0]["peak_score"] < 0.25


def test_search_scene_boundaries_detected(embedded_pool):
    project_dir, _, _ = embedded_pool
    model, tokenizer, _ = load_model()
    queries = [{"shot_id": "T03", "text": "any content"}]
    results = search(queries, project_dir, model, tokenizer, pool_only="project")
    # Scene boundaries should be present in results (even if empty dict)
    assert "scene_boundaries" in results


def test_search_candidates_sorted(embedded_pool):
    project_dir, model, tokenizer = embedded_pool
    queries = [{"shot_id": "T04", "text": "interior room hallway"}]
    results = search(queries, project_dir, model, tokenizer, pool_only="project")
    candidates = results["query_results"][0]["candidates"]
    if len(candidates) >= 2:
        scores = [c["peak_score"] for c in candidates]
        assert scores == sorted(scores, reverse=True)


def test_search_weak_query_flagged(embedded_pool):
    project_dir, model, tokenizer = embedded_pool
    queries = [{"shot_id": "T05", "text": "xyzzy nonsensical gibberish content that cannot match"}]
    results = search(queries, project_dir, model, tokenizer, pool_only="project")
    assert "T05" in results["weak_queries"]


def test_search_pool_only_filter(embedded_pool):
    project_dir, model, tokenizer = embedded_pool
    queries = [{"shot_id": "T06", "text": "building"}]
    results = search(queries, project_dir, model, tokenizer, pool_only="project")
    assert "project" in results["pools_searched"] or results["pools_searched"] == {}
    assert "global" not in results["pools_searched"]


def test_search_multiple_queries(embedded_pool):
    project_dir, model, tokenizer = embedded_pool
    queries = [
        {"shot_id": "T07", "text": "building exterior"},
        {"shot_id": "T08", "text": "person speaking"},
        {"shot_id": "T09", "text": "document newspaper"},
    ]
    results = search(queries, project_dir, model, tokenizer, pool_only="project")
    assert len(results["query_results"]) == 3
    shot_ids = [qr["shot_id"] for qr in results["query_results"]]
    assert set(shot_ids) == {"T07", "T08", "T09"}
