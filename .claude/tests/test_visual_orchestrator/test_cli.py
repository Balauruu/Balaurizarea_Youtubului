"""Tests for visual_orchestrator.cli — CLI context aggregator with load/validate subcommands.

All tests use tmp_path and capsys fixtures. No filesystem side-effects outside tmp_path.
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from visual_orchestrator.cli import cmd_load, resolve_project_dir


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_project_dir(
    root: Path,
    name: str = "1. The Duplessis Orphans Quebec's Stolen Children",
) -> Path:
    """Create a fake project directory with Script.md."""
    project_dir = root / "projects" / name
    project_dir.mkdir(parents=True)
    (project_dir / "Script.md").write_text(
        "# Chapter 1 — The Beginning\n\nScript content here.",
        encoding="utf-8",
    )
    return project_dir


def _make_visual_guide(root: Path, guide_name: str = "Test Guide") -> None:
    """Create a fake VISUAL_STYLE_GUIDE.md under context/visual-references/."""
    guide_dir = root / "context" / "visual-references" / guide_name
    guide_dir.mkdir(parents=True)
    (guide_dir / "VISUAL_STYLE_GUIDE.md").write_text(
        "# Visual Style Guide\n\nBuilding block: Silhouette Figure.",
        encoding="utf-8",
    )


def _make_channel_file(root: Path) -> None:
    """Create fake channel.md."""
    channel_dir = root / "context" / "channel"
    channel_dir.mkdir(parents=True, exist_ok=True)
    (channel_dir / "channel.md").write_text(
        "# Channel DNA\n\nVoice: Authoritative narrator.",
        encoding="utf-8",
    )


def _make_prompt_file(root: Path) -> Path:
    """Create fake generation.md prompt file."""
    prompt_dir = root / ".claude" / "skills" / "visual-orchestrator" / "prompts"
    prompt_dir.mkdir(parents=True)
    prompt_path = prompt_dir / "generation.md"
    prompt_path.write_text(
        "# Generation Prompt\n\nVisual orchestrator instructions here.",
        encoding="utf-8",
    )
    return prompt_path


def _setup_full_project(root: Path) -> Path:
    """Create all files needed for a successful cmd_load call. Returns project_dir."""
    project_dir = _make_project_dir(root)
    _make_visual_guide(root)
    _make_channel_file(root)
    _make_prompt_file(root)
    return project_dir


# ---------------------------------------------------------------------------
# resolve_project_dir tests
# ---------------------------------------------------------------------------

def test_resolve_project_dir_substring_match(tmp_path: Path) -> None:
    """'Duplessis Orphans' matches '1. The Duplessis Orphans Quebec's Stolen Children'."""
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
    """Unmatched topic falls back to .claude/scratch/visual-orchestrator/{topic}."""
    result = resolve_project_dir(tmp_path, "Totally Unknown Topic XYZ")
    assert result is not None
    assert ".claude" in str(result)
    assert "scratch" in str(result)
    assert "visual-orchestrator" in str(result)


def test_resolve_project_dir_ambiguous_raises(tmp_path: Path) -> None:
    """Multiple matching directories raises ValueError."""
    _make_project_dir(tmp_path, "1. Mystery of the Lake")
    _make_project_dir(tmp_path, "2. Mystery of the Forest")
    with pytest.raises(ValueError, match="Multiple project directories"):
        resolve_project_dir(tmp_path, "Mystery")


# ---------------------------------------------------------------------------
# cmd_load stdout content tests
# ---------------------------------------------------------------------------

def test_cmd_load_prints_script(tmp_path: Path, capsys) -> None:
    """cmd_load prints Script label and Script.md content to stdout."""
    _setup_full_project(tmp_path)
    with patch("visual_orchestrator.cli._get_project_root", return_value=tmp_path):
        cmd_load("Duplessis Orphans")
    captured = capsys.readouterr().out
    assert "=== Script ===" in captured
    assert "Script content here." in captured


def test_cmd_load_prints_visual_guide(tmp_path: Path, capsys) -> None:
    """cmd_load prints Visual Style Guide label and guide content to stdout."""
    _setup_full_project(tmp_path)
    with patch("visual_orchestrator.cli._get_project_root", return_value=tmp_path):
        cmd_load("Duplessis Orphans")
    captured = capsys.readouterr().out
    assert "Visual Style Guide" in captured
    assert "Building block: Silhouette Figure." in captured


def test_cmd_load_prints_channel_dna(tmp_path: Path, capsys) -> None:
    """cmd_load prints Channel DNA label and channel.md content to stdout."""
    _setup_full_project(tmp_path)
    with patch("visual_orchestrator.cli._get_project_root", return_value=tmp_path):
        cmd_load("Duplessis Orphans")
    captured = capsys.readouterr().out
    assert "Channel DNA" in captured
    assert "Voice: Authoritative narrator." in captured


def test_cmd_load_prints_output_path(tmp_path: Path, capsys) -> None:
    """cmd_load prints resolved shotlist.json output path to stdout."""
    _setup_full_project(tmp_path)
    with patch("visual_orchestrator.cli._get_project_root", return_value=tmp_path):
        cmd_load("Duplessis Orphans")
    captured = capsys.readouterr().out
    assert "shotlist.json" in captured
    assert "Output path:" in captured


def test_cmd_load_prints_generation_prompt_path(tmp_path: Path, capsys) -> None:
    """cmd_load prints generation.md prompt path to stdout."""
    _setup_full_project(tmp_path)
    with patch("visual_orchestrator.cli._get_project_root", return_value=tmp_path):
        cmd_load("Duplessis Orphans")
    captured = capsys.readouterr().out
    assert "generation.md" in captured
    assert "Generation prompt:" in captured


def test_cmd_load_missing_script_exits_1(tmp_path: Path, capsys) -> None:
    """cmd_load exits 1 when Script.md is not found."""
    # Project dir exists but no Script.md
    project_dir = tmp_path / "projects" / "1. Some Topic"
    project_dir.mkdir(parents=True)
    _make_visual_guide(tmp_path)
    _make_channel_file(tmp_path)
    _make_prompt_file(tmp_path)

    with patch("visual_orchestrator.cli._get_project_root", return_value=tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            cmd_load("Some Topic")

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert len(captured.err) > 0
