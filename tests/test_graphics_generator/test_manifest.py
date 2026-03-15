"""Tests for manifest merge logic in graphics_generator.cli.

Tests cover: append without overwrite, gap status update, atomic write produces valid JSON.
"""
import json
from pathlib import Path
from unittest.mock import patch

from graphics_generator.cli import _merge_manifest, _empty_manifest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_shotlist_data() -> dict:
    return {
        "project": "Test Project",
        "guide_source": "Test Guide",
        "generated": "2026-03-15T00:00:00Z",
        "shots": [
            {
                "id": "S001",
                "chapter": 1,
                "chapter_title": "Chapter 1",
                "narrative_context": "Context.",
                "visual_need": "Need.",
                "building_block": "Silhouette Figure",
                "shotlist_type": "animation",
            },
        ],
    }


def _make_generated_entry(shot_id: str = "S001", filename: str = "S001_silhouette_figure.png") -> dict:
    return {
        "shot": {
            "id": shot_id,
            "building_block": "Silhouette Figure",
            "visual_need": "A dark figure.",
        },
        "path": Path(f"/tmp/vectors/{filename}"),
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestManifestMerge:
    def test_creates_manifest_when_absent(self, tmp_path: Path) -> None:
        """Merge creates manifest.json when none exists."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        generated = [_make_generated_entry()]
        _merge_manifest(project_dir, _make_shotlist_data(), generated)

        manifest_path = project_dir / "assets" / "manifest.json"
        assert manifest_path.exists()

        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert len(data["assets"]) == 1
        assert data["assets"][0]["filename"] == "S001_silhouette_figure.png"

    def test_appends_without_overwriting(self, tmp_path: Path) -> None:
        """Merge appends new assets without removing existing ones."""
        project_dir = tmp_path / "project"
        assets_dir = project_dir / "assets"
        assets_dir.mkdir(parents=True)

        # Pre-existing manifest with one asset
        existing = {
            "project": "Test",
            "generated": "2026-03-14T00:00:00Z",
            "updated": "2026-03-14T00:00:00Z",
            "assets": [
                {
                    "filename": "existing_photo.jpg",
                    "folder": "archival_photos",
                    "source": "wikimedia",
                    "source_url": "https://example.com/photo.jpg",
                    "description": "An old photo.",
                    "license": "CC0",
                    "mapped_shots": ["S002"],
                    "acquired_by": "agent_media",
                },
            ],
            "gaps": [],
            "source_summary": {},
        }
        (assets_dir / "manifest.json").write_text(
            json.dumps(existing, indent=2), encoding="utf-8"
        )

        generated = [_make_generated_entry()]
        _merge_manifest(project_dir, _make_shotlist_data(), generated)

        data = json.loads((assets_dir / "manifest.json").read_text(encoding="utf-8"))
        assert len(data["assets"]) == 2
        filenames = {a["filename"] for a in data["assets"]}
        assert "existing_photo.jpg" in filenames
        assert "S001_silhouette_figure.png" in filenames

    def test_skips_duplicate_filenames(self, tmp_path: Path) -> None:
        """Merge doesn't add assets that already exist by filename."""
        project_dir = tmp_path / "project"
        assets_dir = project_dir / "assets"
        assets_dir.mkdir(parents=True)

        existing = {
            "project": "Test",
            "generated": "2026-03-14T00:00:00Z",
            "updated": "2026-03-14T00:00:00Z",
            "assets": [
                {
                    "filename": "S001_silhouette_figure.png",
                    "folder": "vectors",
                    "source": "code_gen",
                    "source_url": "local://graphics_generator/silhouette_figure",
                    "description": "Previous run.",
                    "license": "generated",
                    "mapped_shots": ["S001"],
                    "acquired_by": "agent_graphics",
                },
            ],
            "gaps": [],
            "source_summary": {},
        }
        (assets_dir / "manifest.json").write_text(
            json.dumps(existing, indent=2), encoding="utf-8"
        )

        generated = [_make_generated_entry()]
        _merge_manifest(project_dir, _make_shotlist_data(), generated)

        data = json.loads((assets_dir / "manifest.json").read_text(encoding="utf-8"))
        assert len(data["assets"]) == 1  # No duplicate added

    def test_gap_status_update(self, tmp_path: Path) -> None:
        """Merge updates gaps from pending_generation to filled for generated shots."""
        project_dir = tmp_path / "project"
        assets_dir = project_dir / "assets"
        assets_dir.mkdir(parents=True)

        existing = {
            "project": "Test",
            "generated": "2026-03-14T00:00:00Z",
            "updated": "2026-03-14T00:00:00Z",
            "assets": [],
            "gaps": [
                {
                    "shot_id": "S001",
                    "visual_need": "A silhouette.",
                    "shotlist_type": "animation",
                    "status": "pending_generation",
                },
                {
                    "shot_id": "S002",
                    "visual_need": "A map.",
                    "shotlist_type": "map",
                    "status": "pending_generation",
                },
            ],
            "source_summary": {},
        }
        (assets_dir / "manifest.json").write_text(
            json.dumps(existing, indent=2), encoding="utf-8"
        )

        generated = [_make_generated_entry("S001")]
        _merge_manifest(project_dir, _make_shotlist_data(), generated)

        data = json.loads((assets_dir / "manifest.json").read_text(encoding="utf-8"))
        gaps = {g["shot_id"]: g for g in data["gaps"]}
        assert gaps["S001"]["status"] == "filled"
        assert gaps["S002"]["status"] == "pending_generation"  # Unchanged

    def test_atomic_write_produces_valid_json(self, tmp_path: Path) -> None:
        """Manifest is written atomically and contains valid JSON."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        generated = [_make_generated_entry()]
        _merge_manifest(project_dir, _make_shotlist_data(), generated)

        manifest_path = project_dir / "assets" / "manifest.json"
        content = manifest_path.read_text(encoding="utf-8")
        data = json.loads(content)  # Should not raise

        # Verify required top-level keys
        assert "project" in data
        assert "assets" in data
        assert "gaps" in data
        assert "source_summary" in data

    def test_asset_entry_has_required_fields(self, tmp_path: Path) -> None:
        """Generated asset entries include all S02-schema required fields."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        generated = [_make_generated_entry()]
        _merge_manifest(project_dir, _make_shotlist_data(), generated)

        data = json.loads(
            (project_dir / "assets" / "manifest.json").read_text(encoding="utf-8")
        )
        asset = data["assets"][0]

        required_fields = {
            "filename", "folder", "source", "source_url",
            "description", "license", "mapped_shots", "acquired_by",
        }
        for field in required_fields:
            assert field in asset, f"Missing required field: {field}"

        assert asset["folder"] == "vectors"
        assert asset["source"] == "code_gen"
        assert asset["source_url"].startswith("local://graphics_generator/")
        assert asset["license"] == "generated"
        assert asset["acquired_by"] == "agent_graphics"
        assert isinstance(asset["mapped_shots"], list)
