"""Integration tests that validate pipeline outputs on the Duplessis project.

These are post-hoc validators — they read files produced by the pipeline
and check schema validity, file existence, and cross-skill contract compliance.
Every test skips gracefully when the required artifact doesn't exist yet.

Run: pytest tests/test_integration/ -v -m integration
"""

import json
import re
from pathlib import Path

import pytest

from visual_orchestrator.schema import validate_shotlist
from media_acquisition.schema import validate_manifest

# ── Project paths ──────────────────────────────────────────────────────

PROJECTS_DIR = Path(__file__).resolve().parents[2] / "projects"
DUPLESSIS_DIR = next(
    (p for p in PROJECTS_DIR.iterdir() if "Duplessis" in p.name),
    None,
) if PROJECTS_DIR.exists() else None

SHOTLIST_PATH = DUPLESSIS_DIR / "shotlist.json" if DUPLESSIS_DIR else None
ASSETS_DIR = DUPLESSIS_DIR / "assets" if DUPLESSIS_DIR else None
MANIFEST_PATH = ASSETS_DIR / "manifest.json" if ASSETS_DIR else None

# Asset type subfolders expected under assets/
ASSET_TYPE_FOLDERS = [
    "archival_photos", "archival_footage", "documents",
    "broll", "vectors", "animations",
]

NUMBERED_PREFIX = re.compile(r"^\d{3}_")


def _load_json_or_skip(path: Path | None, label: str) -> dict:
    """Load a JSON file or skip the test with a clear message."""
    if path is None or not path.exists():
        pytest.skip(f"{label} not found — pipeline has not run yet")
    return json.loads(path.read_text(encoding="utf-8"))


# ── Tests ──────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_shotlist_exists_and_valid():
    """shotlist.json exists, passes schema validation, has ≥20 shots."""
    data = _load_json_or_skip(SHOTLIST_PATH, "shotlist.json")
    errors = validate_shotlist(data)
    assert errors == [], f"Shotlist validation errors:\n" + "\n".join(errors)
    assert len(data.get("shots", [])) >= 20, (
        f"Expected ≥20 shots, got {len(data.get('shots', []))}"
    )


@pytest.mark.integration
def test_manifest_exists_and_valid():
    """manifest.json exists and passes schema validation."""
    data = _load_json_or_skip(MANIFEST_PATH, "manifest.json")
    errors = validate_manifest(data)
    assert errors == [], f"Manifest validation errors:\n" + "\n".join(errors)


@pytest.mark.integration
def test_numbered_assets_exist():
    """At least one file in assets/ type folders matches \\d{3}_ prefix."""
    if ASSETS_DIR is None or not ASSETS_DIR.exists():
        pytest.skip("assets/ directory not found — pipeline has not run yet")

    numbered_files = []
    for folder_name in ASSET_TYPE_FOLDERS:
        folder = ASSETS_DIR / folder_name
        if folder.is_dir():
            numbered_files.extend(
                f for f in folder.iterdir()
                if f.is_file() and NUMBERED_PREFIX.match(f.name)
            )

    assert len(numbered_files) >= 1, (
        "No numbered asset files (###_*) found in any type folder under assets/"
    )


@pytest.mark.integration
def test_gaps_are_terminal():
    """All gaps in manifest have terminal status (filled or unfilled)."""
    data = _load_json_or_skip(MANIFEST_PATH, "manifest.json")
    gaps = data.get("gaps", [])
    if not gaps:
        pytest.skip("No gaps in manifest — nothing to validate")

    non_terminal = [
        g for g in gaps
        if g.get("status") not in ("filled", "unfilled")
    ]
    assert non_terminal == [], (
        f"{len(non_terminal)} gap(s) with non-terminal status:\n"
        + "\n".join(
            f"  {g.get('shot_id', '?')}: status={g.get('status', '?')}"
            for g in non_terminal
        )
    )


@pytest.mark.integration
def test_asset_folders_match_manifest():
    """Every asset in manifest has a corresponding file on disk."""
    data = _load_json_or_skip(MANIFEST_PATH, "manifest.json")
    assets = data.get("assets", [])
    if not assets:
        pytest.skip("No assets in manifest — nothing to validate")

    missing = []
    for asset in assets:
        local = asset.get("local_path")
        if local:
            full_path = DUPLESSIS_DIR / local
            if not full_path.exists():
                missing.append(f"  {asset.get('shot_id', '?')}: {local}")

    assert missing == [], (
        f"{len(missing)} asset(s) referenced in manifest but missing on disk:\n"
        + "\n".join(missing)
    )


@pytest.mark.integration
def test_shotlist_drives_manifest():
    """Every shot_id referenced in manifest assets exists in shotlist.json."""
    shotlist_data = _load_json_or_skip(SHOTLIST_PATH, "shotlist.json")
    manifest_data = _load_json_or_skip(MANIFEST_PATH, "manifest.json")

    shotlist_ids = {s["id"] for s in shotlist_data.get("shots", []) if "id" in s}
    manifest_assets = manifest_data.get("assets", [])
    if not manifest_assets:
        pytest.skip("No assets in manifest — nothing to cross-reference")

    orphan_ids = sorted({
        a.get("shot_id")
        for a in manifest_assets
        if a.get("shot_id") and a["shot_id"] not in shotlist_ids
    })
    assert orphan_ids == [], (
        f"{len(orphan_ids)} manifest asset(s) reference shot_ids not in shotlist:\n"
        + "\n".join(f"  {sid}" for sid in orphan_ids)
    )
