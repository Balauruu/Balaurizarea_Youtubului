"""Tests for asset_manager CLI routing and project resolution."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from asset_manager.cli import (
    cmd_load,
    cmd_status,
    main,
    resolve_project_dir,
)


# ---------------------------------------------------------------------------
# resolve_project_dir
# ---------------------------------------------------------------------------

class TestResolveProjectDir:
    def test_exact_match(self, tmp_path):
        projects = tmp_path / "projects"
        projects.mkdir()
        (projects / "1. Test Topic").mkdir()

        result = resolve_project_dir(tmp_path, "Test Topic")
        assert result.name == "1. Test Topic"

    def test_case_insensitive(self, tmp_path):
        projects = tmp_path / "projects"
        projects.mkdir()
        (projects / "1. The Big Topic").mkdir()

        result = resolve_project_dir(tmp_path, "big topic")
        assert result.name == "1. The Big Topic"

    def test_multiple_matches_raises(self, tmp_path):
        projects = tmp_path / "projects"
        projects.mkdir()
        (projects / "1. Topic A").mkdir()
        (projects / "2. Topic B").mkdir()

        with pytest.raises(ValueError, match="Multiple"):
            resolve_project_dir(tmp_path, "Topic")

    def test_no_match_falls_back(self, tmp_path):
        projects = tmp_path / "projects"
        projects.mkdir()

        result = resolve_project_dir(tmp_path, "Nonexistent")
        assert "scratch" in str(result)
        assert result.exists()


# ---------------------------------------------------------------------------
# CLI subcommand routing
# ---------------------------------------------------------------------------

class TestMainRouting:
    def test_load_routes(self, monkeypatch):
        called_with = {}
        def fake_load(topic):
            called_with["topic"] = topic

        monkeypatch.setattr("asset_manager.cli.cmd_load", fake_load)
        with patch("sys.argv", ["asset_manager", "load", "Test Topic"]):
            main()
        assert called_with["topic"] == "Test Topic"

    def test_organize_routes(self, monkeypatch):
        called_with = {}
        def fake_organize(topic):
            called_with["topic"] = topic

        monkeypatch.setattr("asset_manager.cli.cmd_organize", fake_organize)
        with patch("sys.argv", ["asset_manager", "organize", "Test Topic"]):
            main()
        assert called_with["topic"] == "Test Topic"

    def test_status_routes(self, monkeypatch):
        called_with = {}
        def fake_status(topic):
            called_with["topic"] = topic

        monkeypatch.setattr("asset_manager.cli.cmd_status", fake_status)
        with patch("sys.argv", ["asset_manager", "status", "Test Topic"]):
            main()
        assert called_with["topic"] == "Test Topic"


# ---------------------------------------------------------------------------
# cmd_load output format
# ---------------------------------------------------------------------------

class TestCmdLoad:
    def test_prints_labeled_sections(self, tmp_path, monkeypatch, capsys):
        """cmd_load prints SHOTLIST, MANIFEST, CHANNEL_DNA sections."""
        project_dir = tmp_path / "projects" / "1. Test Project"
        project_dir.mkdir(parents=True)

        shotlist = {"project": "Test", "shots": [{"id": "S001"}]}
        (project_dir / "shotlist.json").write_text(
            json.dumps(shotlist), encoding="utf-8"
        )

        manifest = {
            "project": "Test",
            "generated": "2026-01-01T00:00:00+00:00",
            "updated": "2026-01-01T00:00:00+00:00",
            "assets": [],
            "gaps": [],
            "source_summary": {},
        }
        assets_dir = project_dir / "assets"
        assets_dir.mkdir()
        (assets_dir / "manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

        channel_dir = tmp_path / "context" / "channel"
        channel_dir.mkdir(parents=True)
        (channel_dir / "channel.md").write_text("# Channel DNA", encoding="utf-8")

        (tmp_path / "CLAUDE.md").write_text("", encoding="utf-8")
        monkeypatch.setattr("asset_manager.cli._get_project_root", lambda: tmp_path)

        cmd_load("Test Project")

        output = capsys.readouterr().out
        assert "=== SHOTLIST ===" in output
        assert "=== MANIFEST ===" in output
        assert "=== CHANNEL_DNA ===" in output


# ---------------------------------------------------------------------------
# cmd_status output format
# ---------------------------------------------------------------------------

class TestCmdStatus:
    def test_status_output(self, tmp_path, monkeypatch, capsys):
        """cmd_status prints numbered/unnumbered/pool/gap counts."""
        project_dir = tmp_path / "projects" / "1. Test Project"
        project_dir.mkdir(parents=True)

        manifest = {
            "project": "Test",
            "generated": "2026-01-01T00:00:00+00:00",
            "updated": "2026-01-01T00:00:00+00:00",
            "assets": [
                {
                    "filename": "001_photo.jpg",
                    "folder": "archival_photos",
                    "source": "test",
                    "source_url": "http://example.com",
                    "description": "test",
                    "license": "public_domain",
                    "mapped_shots": ["S001"],
                    "acquired_by": "agent_media",
                },
                {
                    "filename": "raw.jpg",
                    "folder": "archival_photos",
                    "source": "test",
                    "source_url": "http://example.com",
                    "description": "test",
                    "license": "public_domain",
                    "mapped_shots": ["S002"],
                    "acquired_by": "agent_media",
                },
            ],
            "gaps": [
                {"shot_id": "S003", "visual_need": "x", "shotlist_type": "photo", "status": "unfilled"},
                {"shot_id": "S004", "visual_need": "y", "shotlist_type": "photo", "status": "pending_generation"},
            ],
            "source_summary": {},
        }

        assets_dir = project_dir / "assets"
        assets_dir.mkdir()
        (assets_dir / "manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

        (tmp_path / "CLAUDE.md").write_text("", encoding="utf-8")
        monkeypatch.setattr("asset_manager.cli._get_project_root", lambda: tmp_path)

        cmd_status("Test Project")

        output = capsys.readouterr().out
        assert "Numbered (NNN_): 1" in output
        assert "Unnumbered:      1" in output
        assert "unfilled:           1" in output
        assert "pending_generation: 1" in output
