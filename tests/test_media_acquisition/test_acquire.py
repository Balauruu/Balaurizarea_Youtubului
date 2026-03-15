"""Tests for the acquire module — download orchestration, manifest, and gap analysis."""
import json
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from media_acquisition.acquire import (
    load_search_plan,
    load_shotlist,
    execute_plan,
    identify_gaps,
    merge_assets,
    build_manifest,
    write_manifest_atomic,
    run_acquire,
    ACQUISITION_RELEVANT_TYPES,
)
from media_acquisition.schema import validate_manifest
from media_acquisition.sources import SearchResult, DownloadResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal project directory with shotlist.json."""
    shotlist = {
        "project": "Test Project",
        "generated": "2026-03-15T00:00:00Z",
        "shots": [
            {"id": "S001", "chapter": 1, "chapter_title": "Ch1",
             "narrative_context": "Opening", "visual_need": "Old photo of building",
             "building_block": "Archival Photo", "shotlist_type": "archival_photo"},
            {"id": "S002", "chapter": 1, "chapter_title": "Ch1",
             "narrative_context": "Transition", "visual_need": "Historic footage",
             "building_block": "Archival Footage", "shotlist_type": "archival_video"},
            {"id": "S003", "chapter": 2, "chapter_title": "Ch2",
             "narrative_context": "Document reveal", "visual_need": "Scanned letter",
             "building_block": "Document Scan", "shotlist_type": "document_scan"},
            {"id": "S004", "chapter": 2, "chapter_title": "Ch2",
             "narrative_context": "Map animation", "visual_need": "Animated map",
             "building_block": "Animation", "shotlist_type": "animation"},
            {"id": "S005", "chapter": 3, "chapter_title": "Ch3",
             "narrative_context": "Timeline", "visual_need": "Timeline graphic",
             "building_block": "Motion Graphic", "shotlist_type": "motion_graphic"},
        ],
    }
    (tmp_path / "shotlist.json").write_text(json.dumps(shotlist), encoding="utf-8")
    (tmp_path / "assets").mkdir()
    return tmp_path


@pytest.fixture
def simple_plan(tmp_path):
    """Create a minimal search_plan.json."""
    plan = [
        {
            "source": "wikimedia_commons",
            "query": "old building photo",
            "media_type": "image",
            "shot_ids": ["S001"],
            "dest_folder": "archival_photos",
            "limit": 2,
        },
        {
            "source": "archive_org",
            "query": "historic footage 1940",
            "media_type": "video",
            "shot_ids": ["S002"],
            "dest_folder": "archival_footage",
            "limit": 1,
        },
    ]
    plan_path = tmp_path / "search_plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    return plan_path


def _make_fake_source(results=None, download_success=True):
    """Create a fake source module with search/download."""
    module = SimpleNamespace()

    def search(query, media_type="image", limit=10):
        if results is not None:
            return results[:limit]
        return [
            SearchResult(
                url=f"https://example.com/{query.replace(' ', '_')}.jpg",
                title=f"Result for {query}",
                description=f"Description of {query}",
                source="fake_source",
                license="CC0",
                media_type=media_type,
            )
        ]

    def download(url, dest_dir, filename=None):
        if download_success:
            fname = filename or url.split("/")[-1]
            # Create the file on disk
            dest = Path(dest_dir)
            dest.mkdir(parents=True, exist_ok=True)
            (dest / fname).write_bytes(b"fake content")
            return DownloadResult(
                success=True,
                filepath=str(dest / fname),
                filename=fname,
                size_bytes=12,
            )
        return DownloadResult(success=False, error="download failed")

    module.search = search
    module.download = download
    return module


# ---------------------------------------------------------------------------
# load_search_plan
# ---------------------------------------------------------------------------

class TestLoadSearchPlan:
    def test_valid_plan(self, simple_plan):
        plan = load_search_plan(simple_plan)
        assert len(plan) == 2
        assert plan[0]["source"] == "wikimedia_commons"

    def test_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_search_plan(tmp_path / "nonexistent.json")

    def test_invalid_json(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not json", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_search_plan(bad)

    def test_missing_fields(self, tmp_path):
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps([{"source": "x"}]), encoding="utf-8")
        with pytest.raises(ValueError, match="missing fields"):
            load_search_plan(plan_path)

    def test_not_array(self, tmp_path):
        plan_path = tmp_path / "plan.json"
        plan_path.write_text(json.dumps({"source": "x"}), encoding="utf-8")
        with pytest.raises(ValueError, match="must be a JSON array"):
            load_search_plan(plan_path)


# ---------------------------------------------------------------------------
# load_shotlist
# ---------------------------------------------------------------------------

class TestLoadShotlist:
    def test_load(self, tmp_project):
        shotlist = load_shotlist(tmp_project / "shotlist.json")
        assert "S001" in shotlist
        assert shotlist["S001"]["shotlist_type"] == "archival_photo"
        assert len(shotlist) == 5

    def test_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_shotlist(tmp_path / "nope.json")


# ---------------------------------------------------------------------------
# execute_plan
# ---------------------------------------------------------------------------

class TestExecutePlan:
    def test_basic_execution(self, tmp_project):
        """Execute a plan with fake sources, verify assets are built."""
        fake = _make_fake_source()
        plan = [
            {
                "source": "wikimedia_commons",
                "query": "test query",
                "media_type": "image",
                "shot_ids": ["S001"],
                "dest_folder": "archival_photos",
                "limit": 1,
            }
        ]

        with patch("media_acquisition.acquire.get_source", return_value=fake):
            assets, summary = execute_plan(plan, tmp_project / "assets")

        assert len(assets) == 1
        assert assets[0]["folder"] == "archival_photos"
        assert assets[0]["mapped_shots"] == ["S001"]
        assert assets[0]["acquired_by"] == "media_acquisition"
        assert summary["wikimedia_commons"]["searched"] == 1
        assert summary["wikimedia_commons"]["downloaded"] == 1

    def test_download_failure_skips(self, tmp_project):
        """Failed downloads don't produce assets."""
        fake = _make_fake_source(download_success=False)
        plan = [
            {
                "source": "pexels",
                "query": "failure test",
                "media_type": "image",
                "shot_ids": ["S001"],
                "dest_folder": "broll",
                "limit": 1,
            }
        ]

        with patch("media_acquisition.acquire.get_source", return_value=fake):
            assets, summary = execute_plan(plan, tmp_project / "assets")

        assert len(assets) == 0
        assert summary["pexels"]["searched"] == 1
        assert summary["pexels"]["downloaded"] == 0

    def test_source_summary_accumulates(self, tmp_project):
        """source_summary merges with existing when provided."""
        fake = _make_fake_source()
        existing = {"wikimedia_commons": {"searched": 5, "downloaded": 3}}
        plan = [
            {
                "source": "wikimedia_commons",
                "query": "more stuff",
                "media_type": "image",
                "shot_ids": ["S001"],
                "dest_folder": "archival_photos",
                "limit": 1,
            }
        ]

        with patch("media_acquisition.acquire.get_source", return_value=fake):
            _, summary = execute_plan(
                plan, tmp_project / "assets", source_summary=existing
            )

        assert summary["wikimedia_commons"]["searched"] == 6
        assert summary["wikimedia_commons"]["downloaded"] == 4


# ---------------------------------------------------------------------------
# identify_gaps
# ---------------------------------------------------------------------------

class TestIdentifyGaps:
    def test_all_gaps(self, tmp_project):
        """No assets → all acquisition-relevant shots are gaps."""
        shotlist = load_shotlist(tmp_project / "shotlist.json")
        gaps = identify_gaps(shotlist, [])
        # S001 (archival_photo), S002 (archival_video), S003 (document_scan)
        # S004 (animation) and S005 (motion_graphic) are NOT acquisition-relevant
        assert len(gaps) == 3
        gap_ids = {g["shot_id"] for g in gaps}
        assert gap_ids == {"S001", "S002", "S003"}
        assert all(g["status"] == "pending_generation" for g in gaps)

    def test_partial_coverage(self, tmp_project):
        """Some shots covered → only uncovered acquisition-relevant shots are gaps."""
        shotlist = load_shotlist(tmp_project / "shotlist.json")
        assets = [
            {"mapped_shots": ["S001"]},
        ]
        gaps = identify_gaps(shotlist, assets)
        gap_ids = {g["shot_id"] for g in gaps}
        assert "S001" not in gap_ids
        assert "S002" in gap_ids
        assert "S003" in gap_ids

    def test_full_coverage(self, tmp_project):
        """All acquisition-relevant shots covered → no gaps."""
        shotlist = load_shotlist(tmp_project / "shotlist.json")
        assets = [
            {"mapped_shots": ["S001", "S002", "S003"]},
        ]
        gaps = identify_gaps(shotlist, assets)
        assert len(gaps) == 0

    def test_animation_not_flagged(self, tmp_project):
        """Animation and motion_graphic types are never flagged as gaps."""
        shotlist = load_shotlist(tmp_project / "shotlist.json")
        gaps = identify_gaps(shotlist, [])
        gap_types = {g["shotlist_type"] for g in gaps}
        assert "animation" not in gap_types
        assert "motion_graphic" not in gap_types

    def test_gap_has_visual_need(self, tmp_project):
        """Gaps carry visual_need from shotlist for downstream use."""
        shotlist = load_shotlist(tmp_project / "shotlist.json")
        gaps = identify_gaps(shotlist, [])
        s001_gap = next(g for g in gaps if g["shot_id"] == "S001")
        assert s001_gap["visual_need"] == "Old photo of building"


# ---------------------------------------------------------------------------
# merge_assets
# ---------------------------------------------------------------------------

class TestMergeAssets:
    def test_dedup_by_source_url(self):
        existing = [{"source_url": "https://a.com/1.jpg", "filename": "1.jpg"}]
        new = [
            {"source_url": "https://a.com/1.jpg", "filename": "1_dup.jpg"},
            {"source_url": "https://b.com/2.jpg", "filename": "2.jpg"},
        ]
        merged = merge_assets(existing, new)
        assert len(merged) == 2
        filenames = {a["filename"] for a in merged}
        assert "1.jpg" in filenames  # existing kept
        assert "2.jpg" in filenames  # new added
        assert "1_dup.jpg" not in filenames  # duplicate skipped

    def test_empty_existing(self):
        new = [{"source_url": "https://a.com/1.jpg"}]
        merged = merge_assets([], new)
        assert len(merged) == 1

    def test_empty_new(self):
        existing = [{"source_url": "https://a.com/1.jpg"}]
        merged = merge_assets(existing, [])
        assert len(merged) == 1


# ---------------------------------------------------------------------------
# build_manifest + schema validation
# ---------------------------------------------------------------------------

class TestBuildManifest:
    def test_passes_schema_validation(self, tmp_project):
        """Built manifest passes validate_manifest()."""
        assets = [
            {
                "filename": "photo.jpg",
                "folder": "archival_photos",
                "source": "wikimedia_commons",
                "source_url": "https://example.com/photo.jpg",
                "description": "A historic photo",
                "license": "CC0",
                "mapped_shots": ["S001"],
                "acquired_by": "media_acquisition",
            }
        ]
        gaps = [
            {
                "shot_id": "S002",
                "visual_need": "Historic footage",
                "shotlist_type": "archival_video",
                "status": "pending_generation",
            }
        ]
        summary = {"wikimedia_commons": {"searched": 5, "downloaded": 1}}

        manifest = build_manifest("Test Project", assets, gaps, summary)
        errors = validate_manifest(manifest)
        assert errors == [], f"Validation errors: {errors}"

    def test_has_required_top_level_keys(self):
        manifest = build_manifest("P", [], [], {})
        assert set(manifest.keys()) == {
            "project", "generated", "updated", "assets", "gaps", "source_summary"
        }


# ---------------------------------------------------------------------------
# write_manifest_atomic
# ---------------------------------------------------------------------------

class TestWriteManifestAtomic:
    def test_atomic_write(self, tmp_path):
        manifest = {"project": "Test", "assets": [], "gaps": [],
                     "generated": "now", "updated": "now", "source_summary": {}}
        path = tmp_path / "assets" / "manifest.json"
        write_manifest_atomic(manifest, path)

        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["project"] == "Test"

    def test_overwrite_existing(self, tmp_path):
        path = tmp_path / "manifest.json"
        path.write_text('{"project": "old"}', encoding="utf-8")

        new = {"project": "new", "assets": [], "gaps": [],
               "generated": "now", "updated": "now", "source_summary": {}}
        write_manifest_atomic(new, path)

        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["project"] == "new"

    def test_no_temp_files_left(self, tmp_path):
        path = tmp_path / "manifest.json"
        manifest = {"project": "Test", "assets": [], "gaps": [],
                     "generated": "now", "updated": "now", "source_summary": {}}
        write_manifest_atomic(manifest, path)

        # No .tmp files should remain
        tmp_files = list(tmp_path.glob(".manifest_*.tmp"))
        assert len(tmp_files) == 0


# ---------------------------------------------------------------------------
# run_acquire (integration-level with mocked sources)
# ---------------------------------------------------------------------------

class TestRunAcquire:
    def test_full_pipeline(self, tmp_project, simple_plan):
        """Full pipeline: plan → search → download → manifest → gaps."""
        fake = _make_fake_source()

        with patch("media_acquisition.acquire.get_source", return_value=fake):
            manifest = run_acquire(tmp_project, simple_plan, "Test Project")

        # Validate manifest structure
        errors = validate_manifest(manifest)
        assert errors == [], f"Validation errors: {errors}"

        # Check assets were created
        assert len(manifest["assets"]) >= 1
        assert all(a["acquired_by"] == "media_acquisition" for a in manifest["assets"])

        # Check gaps — S003 (document_scan) should be a gap since we only
        # searched for S001 and S002
        gap_ids = {g["shot_id"] for g in manifest["gaps"]}
        assert "S003" in gap_ids

        # source_summary populated
        assert len(manifest["source_summary"]) > 0

        # Manifest file written to disk
        manifest_path = tmp_project / "assets" / "manifest.json"
        assert manifest_path.exists()

    def test_incremental_merge(self, tmp_project, simple_plan):
        """Running acquire twice merges assets without duplicates."""
        fake = _make_fake_source()

        with patch("media_acquisition.acquire.get_source", return_value=fake):
            manifest1 = run_acquire(tmp_project, simple_plan, "Test Project")
            count1 = len(manifest1["assets"])

            manifest2 = run_acquire(tmp_project, simple_plan, "Test Project")
            count2 = len(manifest2["assets"])

        # Same URLs → no new assets added
        assert count2 == count1

    def test_incremental_adds_new(self, tmp_project, tmp_path):
        """Second run with different URLs adds new assets."""
        fake1 = _make_fake_source(results=[
            SearchResult(url="https://a.com/1.jpg", title="First", description="First",
                         source="fake", license="CC0", media_type="image"),
        ])

        plan1 = [{"source": "wikimedia_commons", "query": "q1", "media_type": "image",
                   "shot_ids": ["S001"], "dest_folder": "archival_photos", "limit": 1}]
        plan1_path = tmp_path / "plan1.json"
        plan1_path.write_text(json.dumps(plan1), encoding="utf-8")

        with patch("media_acquisition.acquire.get_source", return_value=fake1):
            m1 = run_acquire(tmp_project, plan1_path, "Test")

        fake2 = _make_fake_source(results=[
            SearchResult(url="https://b.com/2.jpg", title="Second", description="Second",
                         source="fake", license="CC0", media_type="image"),
        ])

        plan2 = [{"source": "wikimedia_commons", "query": "q2", "media_type": "image",
                   "shot_ids": ["S002"], "dest_folder": "archival_footage", "limit": 1}]
        plan2_path = tmp_path / "plan2.json"
        plan2_path.write_text(json.dumps(plan2), encoding="utf-8")

        with patch("media_acquisition.acquire.get_source", return_value=fake2):
            m2 = run_acquire(tmp_project, plan2_path, "Test")

        assert len(m2["assets"]) == 2


# ---------------------------------------------------------------------------
# CLI subcommand wiring (smoke test)
# ---------------------------------------------------------------------------

class TestAcquireCLI:
    def test_acquire_help(self):
        """Acquire subcommand is registered in argparse."""
        from media_acquisition.cli import main
        import subprocess
        result = subprocess.run(
            ["python", "-m", "media_acquisition", "acquire", "--help"],
            capture_output=True, text=True,
            env={**os.environ, "PYTHONPATH": str(
                Path(__file__).resolve().parents[2] / ".claude" / "skills" /
                "media-acquisition" / "scripts"
            )},
            cwd=str(Path(__file__).resolve().parents[2]),
        )
        assert result.returncode == 0
        assert "search_plan" in result.stdout
