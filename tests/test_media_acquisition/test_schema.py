"""Tests for media_acquisition.schema — manifest.json schema validator.

Each test modifies the valid fixture minimally to trigger exactly one error class.
"""
import copy

import pytest

from media_acquisition.schema import validate_manifest


# ---------------------------------------------------------------------------
# Minimal valid manifest fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def valid_manifest() -> dict:
    """Return a minimal valid manifest with 1 asset and 1 gap."""
    return {
        "project": "The Duplessis Orphans",
        "generated": "2026-03-15T01:00:00Z",
        "updated": "2026-03-15T01:30:00Z",
        "assets": [
            {
                "filename": "maurice_duplessis_1938.png",
                "folder": "archival_photos",
                "source": "wikimedia_commons",
                "source_url": "https://upload.wikimedia.org/example.png",
                "description": "Portrait of Maurice Duplessis, 1938",
                "license": "Public domain",
                "mapped_shots": ["S003", "S005"],
                "acquired_by": "agent_acquisition",
            }
        ],
        "gaps": [
            {
                "shot_id": "S012",
                "visual_need": "Interior of Mont-Providence institution, 1950s",
                "shotlist_type": "archival_photo",
                "status": "pending_generation",
            }
        ],
        "source_summary": {
            "wikimedia_commons": {"searched": 15, "downloaded": 8},
        },
    }


# ---------------------------------------------------------------------------
# Valid manifest tests
# ---------------------------------------------------------------------------

class TestValidManifest:
    """Tests that valid manifests pass validation."""

    def test_valid_manifest_passes(self, valid_manifest):
        errors = validate_manifest(valid_manifest)
        assert errors == []

    def test_empty_assets_and_gaps_valid(self, valid_manifest):
        valid_manifest["assets"] = []
        valid_manifest["gaps"] = []
        errors = validate_manifest(valid_manifest)
        assert errors == []

    def test_all_valid_folders(self, valid_manifest):
        """Each valid folder name is accepted."""
        valid_folders = [
            "archival_photos", "archival_footage", "documents",
            "broll", "vectors", "animations",
        ]
        for folder in valid_folders:
            manifest = copy.deepcopy(valid_manifest)
            manifest["assets"][0]["folder"] = folder
            errors = validate_manifest(manifest)
            assert errors == [], f"Folder '{folder}' should be valid"

    def test_all_valid_gap_statuses(self, valid_manifest):
        """Each valid gap status is accepted."""
        for status in ("pending_generation", "filled", "unfilled"):
            manifest = copy.deepcopy(valid_manifest)
            manifest["gaps"][0]["status"] = status
            errors = validate_manifest(manifest)
            assert errors == [], f"Status '{status}' should be valid"


# ---------------------------------------------------------------------------
# Missing top-level keys
# ---------------------------------------------------------------------------

class TestTopLevelKeys:
    """Tests for missing or invalid top-level keys."""

    @pytest.mark.parametrize("key", [
        "project", "generated", "updated", "assets", "gaps", "source_summary",
    ])
    def test_missing_top_level_key(self, valid_manifest, key):
        del valid_manifest[key]
        errors = validate_manifest(valid_manifest)
        assert any(key in e for e in errors)

    def test_empty_project_name(self, valid_manifest):
        valid_manifest["project"] = ""
        errors = validate_manifest(valid_manifest)
        assert any("non-empty" in e for e in errors)

    def test_source_summary_not_dict(self, valid_manifest):
        valid_manifest["source_summary"] = "not a dict"
        errors = validate_manifest(valid_manifest)
        assert any("object" in e for e in errors)


# ---------------------------------------------------------------------------
# Asset validation
# ---------------------------------------------------------------------------

class TestAssetValidation:
    """Tests for per-asset field validation."""

    @pytest.mark.parametrize("field", [
        "filename", "folder", "source", "source_url",
        "description", "license", "mapped_shots", "acquired_by",
    ])
    def test_missing_asset_field(self, valid_manifest, field):
        del valid_manifest["assets"][0][field]
        errors = validate_manifest(valid_manifest)
        assert any(field in e for e in errors)

    def test_invalid_folder_name(self, valid_manifest):
        valid_manifest["assets"][0]["folder"] = "random_folder"
        errors = validate_manifest(valid_manifest)
        assert any("invalid folder" in e for e in errors)

    def test_invalid_shot_id_in_mapped_shots(self, valid_manifest):
        valid_manifest["assets"][0]["mapped_shots"] = ["S003", "INVALID"]
        errors = validate_manifest(valid_manifest)
        assert any("INVALID" in e for e in errors)

    def test_mapped_shots_not_array(self, valid_manifest):
        valid_manifest["assets"][0]["mapped_shots"] = "S003"
        errors = validate_manifest(valid_manifest)
        assert any("array" in e for e in errors)

    def test_empty_source_url(self, valid_manifest):
        valid_manifest["assets"][0]["source_url"] = ""
        errors = validate_manifest(valid_manifest)
        assert any("non-empty" in e for e in errors)

    def test_assets_not_array(self, valid_manifest):
        valid_manifest["assets"] = "not an array"
        errors = validate_manifest(valid_manifest)
        assert any("array" in e for e in errors)


# ---------------------------------------------------------------------------
# Gap validation
# ---------------------------------------------------------------------------

class TestGapValidation:
    """Tests for per-gap field validation."""

    @pytest.mark.parametrize("field", [
        "shot_id", "visual_need", "shotlist_type", "status",
    ])
    def test_missing_gap_field(self, valid_manifest, field):
        del valid_manifest["gaps"][0][field]
        errors = validate_manifest(valid_manifest)
        assert any(field in e for e in errors)

    def test_invalid_gap_status(self, valid_manifest):
        valid_manifest["gaps"][0]["status"] = "completed"
        errors = validate_manifest(valid_manifest)
        assert any("invalid status" in e for e in errors)

    def test_invalid_gap_shot_id_format(self, valid_manifest):
        valid_manifest["gaps"][0]["shot_id"] = "SHOT12"
        errors = validate_manifest(valid_manifest)
        assert any("invalid shot_id" in e for e in errors)

    def test_gaps_not_array(self, valid_manifest):
        valid_manifest["gaps"] = {"not": "an array"}
        errors = validate_manifest(valid_manifest)
        assert any("array" in e for e in errors)

    def test_gap_lifecycle_all_statuses(self, valid_manifest):
        """All three gap lifecycle states are valid individually."""
        for status in ("pending_generation", "filled", "unfilled"):
            manifest = copy.deepcopy(valid_manifest)
            manifest["gaps"][0]["status"] = status
            errors = validate_manifest(manifest)
            assert errors == [], f"Gap status '{status}' should be valid"
