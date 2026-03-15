"""Tests for graphics_generator.cli — CLI context aggregator with load/generate/status.

All tests use tmp_path and capsys fixtures. No filesystem side-effects outside tmp_path.
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from graphics_generator.cli import cmd_load, cmd_status, resolve_project_dir


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_project_dir(
    root: Path,
    name: str = "1. The Duplessis Orphans Quebec's Stolen Children",
) -> Path:
    """Create a fake project directory with shotlist.json."""
    project_dir = root / "projects" / name
    project_dir.mkdir(parents=True)
    shotlist = {
        "project": "Duplessis Orphans",
        "guide_source": "Test Guide",
        "generated": "2026-03-15T00:00:00Z",
        "shots": [
            {
                "id": "S001",
                "chapter": 1,
                "chapter_title": "The Scheme",
                "narrative_context": "Opening scene.",
                "visual_need": "Silhouette of a leader figure.",
                "building_block": "Silhouette Figure",
                "shotlist_type": "animation",
            }
        ],
    }
    (project_dir / "shotlist.json").write_text(
        json.dumps(shotlist, indent=2), encoding="utf-8"
    )
    return project_dir


def _make_channel_file(root: Path) -> None:
    """Create fake channel.md."""
    channel_dir = root / "context" / "channel"
    channel_dir.mkdir(parents=True, exist_ok=True)
    (channel_dir / "channel.md").write_text(
        "# Channel DNA\n\nVoice: Authoritative narrator.",
        encoding="utf-8",
    )


def _setup_full_project(root: Path) -> Path:
    """Create all files needed for a successful cmd_load call."""
    project_dir = _make_project_dir(root)
    _make_channel_file(root)
    return project_dir


# ---------------------------------------------------------------------------
# resolve_project_dir tests
# ---------------------------------------------------------------------------

def test_resolve_project_dir_substring_match(tmp_path: Path) -> None:
    """'Duplessis Orphans' matches the project directory."""
    _make_project_dir(tmp_path)
    result = resolve_project_dir(tmp_path, "Duplessis Orphans")
    assert result is not None
    assert "Duplessis" in result.name


def test_resolve_project_dir_case_insensitive(tmp_path: Path) -> None:
    """'duplessis orphans' (lowercase) matches same directory."""
    _make_project_dir(tmp_path)
    result = resolve_project_dir(tmp_path, "duplessis orphans")
    assert result is not None
    assert "Duplessis" in result.name


def test_resolve_project_dir_fallback_scratch(tmp_path: Path) -> None:
    """Unmatched topic falls back to scratch directory."""
    result = resolve_project_dir(tmp_path, "Totally Unknown Topic XYZ")
    assert result is not None
    assert "scratch" in str(result)
    assert "graphics-generator" in str(result)


def test_resolve_project_dir_ambiguous_raises(tmp_path: Path) -> None:
    """Multiple matching directories raises ValueError."""
    _make_project_dir(tmp_path, "1. Mystery of the Lake")
    _make_project_dir(tmp_path, "2. Mystery of the Forest")
    with pytest.raises(ValueError, match="Multiple project directories"):
        resolve_project_dir(tmp_path, "Mystery")


# ---------------------------------------------------------------------------
# cmd_load stdout content tests
# ---------------------------------------------------------------------------

def test_cmd_load_prints_shotlist(tmp_path: Path, capsys) -> None:
    """cmd_load prints shotlist label and content to stdout."""
    _setup_full_project(tmp_path)
    with patch("graphics_generator.cli._get_project_root", return_value=tmp_path):
        cmd_load("Duplessis Orphans")
    captured = capsys.readouterr().out
    assert "=== Shotlist ===" in captured
    assert "Silhouette Figure" in captured


def test_cmd_load_prints_channel_dna(tmp_path: Path, capsys) -> None:
    """cmd_load prints Channel DNA label and content."""
    _setup_full_project(tmp_path)
    with patch("graphics_generator.cli._get_project_root", return_value=tmp_path):
        cmd_load("Duplessis Orphans")
    captured = capsys.readouterr().out
    assert "=== Channel DNA ===" in captured
    assert "Authoritative narrator" in captured


def test_cmd_load_prints_manifest_absent(tmp_path: Path, capsys) -> None:
    """cmd_load notes manifest absence when manifest.json doesn't exist."""
    _setup_full_project(tmp_path)
    with patch("graphics_generator.cli._get_project_root", return_value=tmp_path):
        cmd_load("Duplessis Orphans")
    captured = capsys.readouterr().out
    assert "=== Manifest ===" in captured
    assert "No manifest.json found" in captured


def test_cmd_load_prints_prompt_path(tmp_path: Path, capsys) -> None:
    """cmd_load prints generation prompt path."""
    _setup_full_project(tmp_path)
    with patch("graphics_generator.cli._get_project_root", return_value=tmp_path):
        cmd_load("Duplessis Orphans")
    captured = capsys.readouterr().out
    assert "generation.md" in captured
    assert "Generation prompt:" in captured


def test_cmd_load_missing_shotlist_exits_1(tmp_path: Path, capsys) -> None:
    """cmd_load exits 1 when shotlist.json is not found."""
    _make_channel_file(tmp_path)
    project_dir = tmp_path / "projects" / "1. Some Topic"
    project_dir.mkdir(parents=True)

    with patch("graphics_generator.cli._get_project_root", return_value=tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            cmd_load("Some Topic")

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert len(captured.err) > 0
