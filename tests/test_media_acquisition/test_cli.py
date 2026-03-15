"""Tests for media_acquisition.cli — load/status subcommands and media_urls parser."""
import json
import textwrap

import pytest

from media_acquisition.cli import cmd_load, cmd_status, parse_media_urls, resolve_project_dir


# ---------------------------------------------------------------------------
# Helpers — create fake project structures
# ---------------------------------------------------------------------------

def _create_project(tmp_path, topic_dir_name="1. Test Topic", with_manifest=False):
    """Create a minimal project structure for testing."""
    root = tmp_path
    (root / "CLAUDE.md").write_text("# marker", encoding="utf-8")

    project_dir = root / "projects" / topic_dir_name
    project_dir.mkdir(parents=True)

    # shotlist.json
    shotlist = {
        "project": "Test Topic",
        "guide_source": "Test Guide",
        "generated": "2026-03-15T00:00:00Z",
        "shots": [
            {
                "id": "S001",
                "chapter": 1,
                "chapter_title": "Chapter One",
                "narrative_context": "Test context.",
                "visual_need": "Test visual need.",
                "building_block": "Archival Footage",
                "shotlist_type": "archival_video",
            }
        ],
    }
    (project_dir / "shotlist.json").write_text(
        json.dumps(shotlist, indent=2), encoding="utf-8"
    )

    # media_urls.md
    research_dir = project_dir / "research"
    research_dir.mkdir()
    (research_dir / "media_urls.md").write_text(textwrap.dedent("""\
        # Media URLs — Test Topic

        ## Archival Photos

        - **URL:** https://example.com/photo1.jpg
          **Description:** A test photo.
          **Source:** example.com

        ## Documents

        - **URL:** https://example.com/doc1.pdf
          **Description:** A test document.
          **Source:** example.com
    """), encoding="utf-8")

    # channel.md
    channel_dir = root / "context" / "channel"
    channel_dir.mkdir(parents=True)
    (channel_dir / "channel.md").write_text("# Channel DNA\nTest channel.", encoding="utf-8")

    if with_manifest:
        assets_dir = project_dir / "assets"
        assets_dir.mkdir()
        manifest = {
            "project": "Test Topic",
            "generated": "2026-03-15T01:00:00Z",
            "updated": "2026-03-15T01:30:00Z",
            "assets": [
                {
                    "filename": "photo1.jpg",
                    "folder": "archival_photos",
                    "source": "wikimedia_commons",
                    "source_url": "https://example.com/photo1.jpg",
                    "description": "A test photo",
                    "license": "Public domain",
                    "mapped_shots": ["S001"],
                    "acquired_by": "agent_acquisition",
                }
            ],
            "gaps": [
                {
                    "shot_id": "S002",
                    "visual_need": "A missing visual",
                    "shotlist_type": "archival_photo",
                    "status": "pending_generation",
                },
                {
                    "shot_id": "S003",
                    "visual_need": "Another missing visual",
                    "shotlist_type": "animation",
                    "status": "unfilled",
                },
            ],
            "source_summary": {
                "wikimedia_commons": {"searched": 10, "downloaded": 5},
                "pexels": {"searched": 3, "downloaded": 1},
            },
        }
        (assets_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

    return root, project_dir


# ---------------------------------------------------------------------------
# resolve_project_dir tests
# ---------------------------------------------------------------------------

class TestResolveProjectDir:

    def test_resolve_by_substring(self, tmp_path):
        root, project_dir = _create_project(tmp_path, "1. The Duplessis Orphans")
        result = resolve_project_dir(root, "Duplessis")
        assert result == project_dir

    def test_resolve_case_insensitive(self, tmp_path):
        root, project_dir = _create_project(tmp_path, "1. The Duplessis Orphans")
        result = resolve_project_dir(root, "duplessis")
        assert result == project_dir

    def test_resolve_fallback_to_scratch(self, tmp_path):
        root = tmp_path
        (root / "CLAUDE.md").write_text("# marker", encoding="utf-8")
        result = resolve_project_dir(root, "nonexistent")
        assert "scratch" in str(result)


# ---------------------------------------------------------------------------
# cmd_load tests
# ---------------------------------------------------------------------------

class TestCmdLoad:

    def test_load_prints_all_sections(self, tmp_path, capsys, monkeypatch):
        root, _ = _create_project(tmp_path)
        monkeypatch.setattr(
            "media_acquisition.cli._get_project_root", lambda: root
        )
        cmd_load("Test Topic")
        out = capsys.readouterr().out
        assert "=== Shotlist ===" in out
        assert "=== Media URLs ===" in out
        assert "=== Channel DNA ===" in out
        assert "Assets directory:" in out

    def test_load_missing_file_exits_1(self, tmp_path, monkeypatch):
        root = tmp_path
        (root / "CLAUDE.md").write_text("# marker", encoding="utf-8")
        project_dir = root / "projects" / "1. Test Topic"
        project_dir.mkdir(parents=True)
        # No shotlist.json, no media_urls.md
        monkeypatch.setattr(
            "media_acquisition.cli._get_project_root", lambda: root
        )
        with pytest.raises(SystemExit) as exc_info:
            cmd_load("Test Topic")
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# cmd_status tests
# ---------------------------------------------------------------------------

class TestCmdStatus:

    def test_status_prints_summary(self, tmp_path, capsys, monkeypatch):
        root, _ = _create_project(tmp_path, with_manifest=True)
        monkeypatch.setattr(
            "media_acquisition.cli._get_project_root", lambda: root
        )
        cmd_status("Test Topic")
        out = capsys.readouterr().out
        assert "Assets: 1" in out
        assert "Gaps: 2" in out
        assert "pending_generation: 1" in out
        assert "unfilled: 1" in out
        assert "Coverage:" in out
        assert "wikimedia_commons:" in out

    def test_status_no_manifest_exits_1(self, tmp_path, capsys, monkeypatch):
        root, _ = _create_project(tmp_path)
        monkeypatch.setattr(
            "media_acquisition.cli._get_project_root", lambda: root
        )
        with pytest.raises(SystemExit) as exc_info:
            cmd_status("Test Topic")
        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "No manifest found" in err


# ---------------------------------------------------------------------------
# parse_media_urls tests
# ---------------------------------------------------------------------------

class TestParseMediaUrls:

    def test_parses_entries_with_categories(self):
        text = textwrap.dedent("""\
            # Media URLs — Test

            ## Archival Photos

            - **URL:** https://example.com/photo.jpg
              **Description:** A photo.
              **Source:** example.com

            ## Documents

            - **URL:** https://example.com/doc.pdf
              **Description:** A document.
              **Source:** example.com
        """)
        results = parse_media_urls(text)
        assert len(results) == 2
        assert results[0]["url"] == "https://example.com/photo.jpg"
        assert results[0]["category"] == "Archival Photos"
        assert results[0]["description"] == "A photo."
        assert results[0]["source"] == "example.com"
        assert results[1]["category"] == "Documents"

    def test_empty_section_returns_nothing(self):
        text = textwrap.dedent("""\
            ## Archival Footage

            *(none found)*

            ## Archival Photos

            - **URL:** https://example.com/photo.jpg
              **Description:** A photo.
              **Source:** example.com
        """)
        results = parse_media_urls(text)
        assert len(results) == 1
        assert results[0]["category"] == "Archival Photos"

    def test_empty_text_returns_empty_list(self):
        assert parse_media_urls("") == []
