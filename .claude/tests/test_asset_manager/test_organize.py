"""Tests for asset_manager organize logic."""
import json
import os
from pathlib import Path

import pytest

from asset_manager.cli import (
    _add_prefix,
    _build_shot_order,
    _compute_numbering,
    _strip_existing_prefix,
    cmd_organize,
)
from media_acquisition.schema import validate_manifest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_shotlist(shots: list[dict]) -> dict:
    """Create a minimal shotlist dict."""
    return {"project": "Test Project", "shots": shots}


def _make_manifest(assets: list[dict], gaps: list[dict] | None = None) -> dict:
    """Create a minimal valid manifest dict."""
    return {
        "project": "Test Project",
        "generated": "2026-01-01T00:00:00+00:00",
        "updated": "2026-01-01T00:00:00+00:00",
        "assets": assets,
        "gaps": gaps or [],
        "source_summary": {},
    }


def _make_asset(
    filename: str,
    folder: str = "archival_photos",
    mapped_shots: list[str] | None = None,
) -> dict:
    return {
        "filename": filename,
        "folder": folder,
        "source": "test",
        "source_url": "http://example.com/test.jpg",
        "description": "Test asset",
        "license": "public_domain",
        "mapped_shots": mapped_shots or [],
        "acquired_by": "agent_media",
    }


def _make_gap(shot_id: str, status: str = "pending_generation") -> dict:
    return {
        "shot_id": shot_id,
        "visual_need": "test visual",
        "shotlist_type": "archival_photo",
        "status": status,
    }


def _setup_project(tmp_path: Path, shotlist: dict, manifest: dict) -> Path:
    """Create a project directory with shotlist and manifest, return project_dir."""
    project_dir = tmp_path / "projects" / "1. Test Project"
    project_dir.mkdir(parents=True)

    (project_dir / "shotlist.json").write_text(
        json.dumps(shotlist, indent=2), encoding="utf-8"
    )

    assets_dir = project_dir / "assets"
    assets_dir.mkdir()
    (assets_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    return project_dir


def _create_asset_file(project_dir: Path, folder: str, filename: str) -> Path:
    """Create a dummy asset file in the appropriate folder."""
    folder_path = project_dir / "assets" / folder
    folder_path.mkdir(parents=True, exist_ok=True)
    file_path = folder_path / filename
    file_path.write_text("dummy content", encoding="utf-8")
    return file_path


# ---------------------------------------------------------------------------
# Unit tests: _build_shot_order
# ---------------------------------------------------------------------------

class TestBuildShotOrder:
    def test_basic_ordering(self):
        shotlist = _make_shotlist([
            {"id": "S001"}, {"id": "S002"}, {"id": "S003"},
        ])
        order = _build_shot_order(shotlist)
        assert order == {"S001": 1, "S002": 2, "S003": 3}

    def test_empty_shotlist(self):
        assert _build_shot_order(_make_shotlist([])) == {}

    def test_deduplicates_shot_ids(self):
        """If a shot ID appears twice (shouldn't but defensive), first wins."""
        shotlist = _make_shotlist([{"id": "S001"}, {"id": "S001"}])
        order = _build_shot_order(shotlist)
        assert order == {"S001": 1}

    def test_missing_id_field_skipped(self):
        shotlist = _make_shotlist([{"id": "S001"}, {}, {"id": "S003"}])
        order = _build_shot_order(shotlist)
        assert order == {"S001": 1, "S003": 3}


# ---------------------------------------------------------------------------
# Unit tests: _compute_numbering
# ---------------------------------------------------------------------------

class TestComputeNumbering:
    def test_basic_numbering(self):
        """Asset mapped to S002 gets seq 2."""
        assets = [_make_asset("photo.jpg", mapped_shots=["S002"])]
        shot_order = {"S001": 1, "S002": 2, "S003": 3}
        numbered, unmapped = _compute_numbering(assets, shot_order)
        assert len(numbered) == 1
        assert numbered[0][1] == 2
        assert unmapped == []

    def test_multi_shot_gets_earliest(self):
        """Asset mapped to [S003, S001] gets seq 1 (earliest)."""
        assets = [_make_asset("photo.jpg", mapped_shots=["S003", "S001"])]
        shot_order = {"S001": 1, "S002": 2, "S003": 3}
        numbered, unmapped = _compute_numbering(assets, shot_order)
        assert numbered[0][1] == 1

    def test_same_shot_assets_share_prefix(self):
        """Two assets on S002 both get seq 2."""
        assets = [
            _make_asset("a.jpg", mapped_shots=["S002"]),
            _make_asset("b.jpg", mapped_shots=["S002"]),
        ]
        shot_order = {"S001": 1, "S002": 2}
        numbered, _ = _compute_numbering(assets, shot_order)
        assert all(seq == 2 for _, seq in numbered)

    def test_unmapped_empty_shots(self):
        """Asset with no mapped_shots is unmapped."""
        assets = [_make_asset("orphan.jpg", mapped_shots=[])]
        shot_order = {"S001": 1}
        numbered, unmapped = _compute_numbering(assets, shot_order)
        assert len(numbered) == 0
        assert len(unmapped) == 1

    def test_unmapped_shots_not_in_shotlist(self):
        """Asset mapped to shots not in the shotlist is unmapped."""
        assets = [_make_asset("lost.jpg", mapped_shots=["S999"])]
        shot_order = {"S001": 1, "S002": 2}
        numbered, unmapped = _compute_numbering(assets, shot_order)
        assert len(numbered) == 0
        assert len(unmapped) == 1


# ---------------------------------------------------------------------------
# Unit tests: prefix helpers
# ---------------------------------------------------------------------------

class TestPrefixHelpers:
    def test_strip_existing_prefix(self):
        assert _strip_existing_prefix("001_photo.jpg") == "photo.jpg"
        assert _strip_existing_prefix("photo.jpg") == "photo.jpg"
        assert _strip_existing_prefix("123_video.mp4") == "video.mp4"

    def test_strip_only_leading_prefix(self):
        """Only strips a leading NNN_ — not embedded ones."""
        assert _strip_existing_prefix("001_file_002_name.jpg") == "file_002_name.jpg"

    def test_add_prefix(self):
        assert _add_prefix(1, "photo.jpg") == "001_photo.jpg"
        assert _add_prefix(42, "video.mp4") == "042_video.mp4"
        assert _add_prefix(100, "doc.pdf") == "100_doc.pdf"

    def test_add_prefix_strips_existing(self):
        """Adding prefix to already-numbered file strips first."""
        assert _add_prefix(5, "001_photo.jpg") == "005_photo.jpg"


# ---------------------------------------------------------------------------
# Integration tests: cmd_organize
# ---------------------------------------------------------------------------

class TestCmdOrganize:
    def test_basic_organize(self, tmp_path, monkeypatch):
        """Full organize: 2 assets mapped, 1 unmapped, 1 gap."""
        shots = [
            {"id": "S001", "shotlist_type": "archival_photo"},
            {"id": "S002", "shotlist_type": "archival_photo"},
        ]
        assets = [
            _make_asset("photo_a.jpg", "archival_photos", ["S001"]),
            _make_asset("photo_b.jpg", "archival_photos", ["S002"]),
            _make_asset("orphan.jpg", "archival_photos", []),
        ]
        gaps = [_make_gap("S003", "pending_generation")]
        manifest = _make_manifest(assets, gaps)
        shotlist = _make_shotlist(shots)

        project_dir = _setup_project(tmp_path, shotlist, manifest)
        _create_asset_file(project_dir, "archival_photos", "photo_a.jpg")
        _create_asset_file(project_dir, "archival_photos", "photo_b.jpg")
        _create_asset_file(project_dir, "archival_photos", "orphan.jpg")

        # Patch CLAUDE.md location
        (tmp_path / "CLAUDE.md").write_text("", encoding="utf-8")
        monkeypatch.setattr("asset_manager.cli._get_project_root", lambda: tmp_path)

        cmd_organize("Test Project")

        # Verify renames
        photos_dir = project_dir / "assets" / "archival_photos"
        assert (photos_dir / "001_photo_a.jpg").exists()
        assert (photos_dir / "002_photo_b.jpg").exists()
        assert not (photos_dir / "photo_a.jpg").exists()
        assert not (photos_dir / "photo_b.jpg").exists()

        # Verify pool
        pool_dir = project_dir / "assets" / "_pool"
        assert (pool_dir / "orphan.jpg").exists()
        assert not (photos_dir / "orphan.jpg").exists()

        # Verify manifest
        result = json.loads(
            (project_dir / "assets" / "manifest.json").read_text(encoding="utf-8")
        )
        assert len(result["assets"]) == 2  # orphan removed
        filenames = {a["filename"] for a in result["assets"]}
        assert "001_photo_a.jpg" in filenames
        assert "002_photo_b.jpg" in filenames

        # Gap finalized
        assert result["gaps"][0]["status"] == "unfilled"

        # Schema valid
        assert validate_manifest(result) == []

    def test_idempotent_rerun(self, tmp_path, monkeypatch):
        """Running organize twice produces the same result."""
        shots = [{"id": "S001", "shotlist_type": "archival_photo"}]
        assets = [_make_asset("photo.jpg", "archival_photos", ["S001"])]
        manifest = _make_manifest(assets)
        shotlist = _make_shotlist(shots)

        project_dir = _setup_project(tmp_path, shotlist, manifest)
        _create_asset_file(project_dir, "archival_photos", "photo.jpg")
        (tmp_path / "CLAUDE.md").write_text("", encoding="utf-8")
        monkeypatch.setattr("asset_manager.cli._get_project_root", lambda: tmp_path)

        # First run
        cmd_organize("Test Project")

        # Read manifest after first run
        manifest_after_1 = json.loads(
            (project_dir / "assets" / "manifest.json").read_text(encoding="utf-8")
        )

        # Second run — should not error
        cmd_organize("Test Project")

        manifest_after_2 = json.loads(
            (project_dir / "assets" / "manifest.json").read_text(encoding="utf-8")
        )

        # Filenames unchanged (ignore timestamps)
        names_1 = sorted(a["filename"] for a in manifest_after_1["assets"])
        names_2 = sorted(a["filename"] for a in manifest_after_2["assets"])
        assert names_1 == names_2
        assert names_1 == ["001_photo.jpg"]

        # File exists
        assert (project_dir / "assets" / "archival_photos" / "001_photo.jpg").exists()

    def test_cross_folder_numbering(self, tmp_path, monkeypatch):
        """Assets in different folders sharing a shot get same prefix."""
        shots = [
            {"id": "S001", "shotlist_type": "archival_photo"},
            {"id": "S002", "shotlist_type": "broll"},
        ]
        assets = [
            _make_asset("photo.jpg", "archival_photos", ["S001"]),
            _make_asset("clip.mp4", "broll", ["S001"]),
            _make_asset("vector.svg", "vectors", ["S002"]),
        ]
        manifest = _make_manifest(assets)
        shotlist = _make_shotlist(shots)

        project_dir = _setup_project(tmp_path, shotlist, manifest)
        _create_asset_file(project_dir, "archival_photos", "photo.jpg")
        _create_asset_file(project_dir, "broll", "clip.mp4")
        _create_asset_file(project_dir, "vectors", "vector.svg")
        (tmp_path / "CLAUDE.md").write_text("", encoding="utf-8")
        monkeypatch.setattr("asset_manager.cli._get_project_root", lambda: tmp_path)

        cmd_organize("Test Project")

        # Both S001 assets get prefix 001
        assert (project_dir / "assets" / "archival_photos" / "001_photo.jpg").exists()
        assert (project_dir / "assets" / "broll" / "001_clip.mp4").exists()
        # S002 asset gets prefix 002
        assert (project_dir / "assets" / "vectors" / "002_vector.svg").exists()

    def test_gap_finalization(self, tmp_path, monkeypatch):
        """pending_generation → unfilled, filled stays filled."""
        shots = [{"id": "S001", "shotlist_type": "archival_photo"}]
        gaps = [
            _make_gap("S001", "pending_generation"),
            _make_gap("S002", "filled"),
            _make_gap("S003", "pending_generation"),
        ]
        manifest = _make_manifest([], gaps)
        shotlist = _make_shotlist(shots)

        project_dir = _setup_project(tmp_path, shotlist, manifest)
        (tmp_path / "CLAUDE.md").write_text("", encoding="utf-8")
        monkeypatch.setattr("asset_manager.cli._get_project_root", lambda: tmp_path)

        cmd_organize("Test Project")

        result = json.loads(
            (project_dir / "assets" / "manifest.json").read_text(encoding="utf-8")
        )
        statuses = {g["shot_id"]: g["status"] for g in result["gaps"]}
        assert statuses["S001"] == "unfilled"
        assert statuses["S002"] == "filled"
        assert statuses["S003"] == "unfilled"

    def test_manifest_valid_after_organize(self, tmp_path, monkeypatch):
        """Post-organize manifest passes validate_manifest."""
        shots = [
            {"id": "S001", "shotlist_type": "archival_photo"},
            {"id": "S002", "shotlist_type": "broll"},
        ]
        assets = [
            _make_asset("a.jpg", "archival_photos", ["S001"]),
            _make_asset("b.mp4", "broll", ["S002"]),
            _make_asset("c.jpg", "archival_photos", []),
        ]
        gaps = [_make_gap("S003", "pending_generation")]
        manifest = _make_manifest(assets, gaps)
        shotlist = _make_shotlist(shots)

        project_dir = _setup_project(tmp_path, shotlist, manifest)
        _create_asset_file(project_dir, "archival_photos", "a.jpg")
        _create_asset_file(project_dir, "broll", "b.mp4")
        _create_asset_file(project_dir, "archival_photos", "c.jpg")
        (tmp_path / "CLAUDE.md").write_text("", encoding="utf-8")
        monkeypatch.setattr("asset_manager.cli._get_project_root", lambda: tmp_path)

        cmd_organize("Test Project")

        result = json.loads(
            (project_dir / "assets" / "manifest.json").read_text(encoding="utf-8")
        )
        errors = validate_manifest(result)
        assert errors == [], f"Manifest invalid: {errors}"

    def test_empty_manifest_and_shotlist(self, tmp_path, monkeypatch):
        """No assets, no shots — organize exits cleanly."""
        manifest = _make_manifest([], [])
        shotlist = _make_shotlist([])

        project_dir = _setup_project(tmp_path, shotlist, manifest)
        (tmp_path / "CLAUDE.md").write_text("", encoding="utf-8")
        monkeypatch.setattr("asset_manager.cli._get_project_root", lambda: tmp_path)

        cmd_organize("Test Project")

        result = json.loads(
            (project_dir / "assets" / "manifest.json").read_text(encoding="utf-8")
        )
        assert result["assets"] == []
        assert validate_manifest(result) == []
