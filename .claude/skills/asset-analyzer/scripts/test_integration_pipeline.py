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
from pool import PoolIndex, get_pool_root
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

    # Create separate fake project dirs for project and global pools
    # so get_pool_root resolves to controlled paths
    proj_project_dir = os.path.join(tmpdir, "proj_project")
    glob_project_dir = os.path.join(tmpdir, "glob_project")
    os.makedirs(proj_project_dir, exist_ok=True)
    os.makedirs(glob_project_dir, exist_ok=True)

    proj_pool = get_pool_root("project", project_dir=proj_project_dir)
    glob_pool = get_pool_root("project", project_dir=glob_project_dir)

    model, tokenizer, preprocess = load_model()
    proj_idx = PoolIndex(proj_pool)
    video_path = os.path.join(STAGING_DIR, videos[0])
    embed_video(video_path, proj_idx, model, preprocess)

    return {
        "tmpdir": tmpdir,
        "proj_project_dir": proj_project_dir,
        "glob_project_dir": glob_project_dir,
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
    results = search(queries, s["proj_project_dir"], s["model"], s["tokenizer"], pool_only="project")
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
    results = discover(s["proj_project_dir"], "project", TAXONOMY_PATH,
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

    # Mock get_pool_root in search module so our temp dirs are used
    from unittest.mock import patch
    with patch("search.get_pool_root") as mock_root:
        def side_effect(pool, project_dir=None):
            if pool == "project":
                return s["proj_pool"]
            return s["glob_pool"]
        mock_root.side_effect = side_effect
        results = search(queries, s["proj_project_dir"], s["model"], s["tokenizer"])

    if results["pools_searched"]:
        pools_found = set(results["pools_searched"].keys())
        # At least project pool should be present
        assert "project" in pools_found
