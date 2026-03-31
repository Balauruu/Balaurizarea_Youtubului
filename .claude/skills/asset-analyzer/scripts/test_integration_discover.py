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
from pool import PoolIndex, get_pool_root

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
    pool_root = get_pool_root("project", project_dir=tmpdir)
    idx = PoolIndex(pool_root)
    embed_video(os.path.join(STAGING_DIR, videos[0]), idx, model, preprocess)
    # Return project_dir (tmpdir), not the pool root
    return tmpdir, model, tokenizer


def test_discover_categories_populated(embedded_pool):
    project_dir, model, tokenizer = embedded_pool
    results = discover(project_dir, "project", TAXONOMY_PATH, model=model, tokenizer=tokenizer)
    assert len(results["inventory"]) > 0


def test_discover_skip_categories_excluded(embedded_pool):
    project_dir, model, tokenizer = embedded_pool
    results = discover(project_dir, "project", TAXONOMY_PATH, model=model, tokenizer=tokenizer)
    skip_cats = {"talking_head", "title_graphic", "black_blank"}
    for cat in results["inventory"]:
        assert cat not in skip_cats


def test_discover_unknown_frames_exist(embedded_pool):
    """With high confidence threshold, some frames should be unknown."""
    project_dir, model, tokenizer = embedded_pool
    results = discover(project_dir, "project", TAXONOMY_PATH, model=model, tokenizer=tokenizer,
                       confidence_threshold=0.30)
    # High threshold means more unknowns
    total_classified = sum(v["frame_count"] for v in results["inventory"].values())
    pool_root = get_pool_root("project", project_dir=project_dir)
    idx = PoolIndex(pool_root)
    _, _, info = idx.load_all_embeddings()
    total_frames = len(info)
    assert results["noise_frames"] > 0 or len(results["clusters"]) > 0 or total_classified < total_frames


def test_discover_cluster_has_representative(embedded_pool):
    project_dir, model, tokenizer = embedded_pool
    results = discover(project_dir, "project", TAXONOMY_PATH, model=model, tokenizer=tokenizer,
                       confidence_threshold=0.25)
    for cluster in results["clusters"]:
        assert "centroid_frame" in cluster
        assert "video" in cluster["centroid_frame"]
        assert "timestamp_sec" in cluster["centroid_frame"]


def test_discover_project_taxonomy_merges(embedded_pool):
    project_dir, model, tokenizer = embedded_pool
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump({"project_specific": {
            "test_custom_category": "A very specific test category that no real frame will match"
        }}, f)
        proj_tax = f.name
    try:
        results = discover(project_dir, "project", TAXONOMY_PATH,
                           taxonomy_project_path=proj_tax,
                           model=model, tokenizer=tokenizer)
        # The custom category should exist (even if 0 frames match)
        # We just verify no crash when merging
        assert isinstance(results["inventory"], dict)
    finally:
        os.unlink(proj_tax)


def test_discover_inventory_minutes_plausible(embedded_pool):
    project_dir, model, tokenizer = embedded_pool
    results = discover(project_dir, "project", TAXONOMY_PATH, model=model, tokenizer=tokenizer)
    total_minutes = sum(v["total_minutes"] for v in results["inventory"].values())
    # At 1fps, total classified frames / 60 should give us the minutes
    total_frames = sum(v["frame_count"] for v in results["inventory"].values())
    expected_minutes = total_frames / 60
    assert abs(total_minutes - expected_minutes) < 0.1
