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
