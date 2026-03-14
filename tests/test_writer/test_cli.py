"""Tests for writer.cli — CLI context aggregator with load subcommand.

All tests use tmp_path and capsys fixtures. No filesystem side-effects outside tmp_path.
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_project_dir(root: Path, name: str = "1. The Duplessis Orphans Quebec's Stolen Children") -> Path:
    """Create a fake project directory with Research.md."""
    project_dir = root / "projects" / name
    research_dir = project_dir / "research"
    research_dir.mkdir(parents=True)
    (research_dir / "Research.md").write_text(
        "# Research Dossier\n\nResearch content here.",
        encoding="utf-8",
    )
    return project_dir


def _make_channel_files(root: Path) -> None:
    """Create fake STYLE_PROFILE.md and channel.md."""
    channel_dir = root / "context" / "channel"
    channel_dir.mkdir(parents=True)
    (channel_dir / "STYLE_PROFILE.md").write_text(
        "# Channel Style Profile\n\nRule 1: Declarative Factual Claims.",
        encoding="utf-8",
    )
    (channel_dir / "channel.md").write_text(
        "# Channel DNA\n\nVoice: Authoritative narrator.",
        encoding="utf-8",
    )


def _make_prompt_file(root: Path) -> Path:
    """Create fake generation.md prompt file."""
    prompt_dir = root / ".claude" / "skills" / "writer" / "prompts"
    prompt_dir.mkdir(parents=True)
    prompt_path = prompt_dir / "generation.md"
    prompt_path.write_text("# Generation Prompt\n\nWriter instructions here.", encoding="utf-8")
    return prompt_path


# ---------------------------------------------------------------------------
# Imports (after helpers defined)
# ---------------------------------------------------------------------------

from writer.cli import cmd_load, resolve_project_dir  # noqa: E402


# ---------------------------------------------------------------------------
# Task 1 tests: resolve_project_dir
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
    """Unmatched topic falls back to .claude/scratch/writer/{topic}."""
    result = resolve_project_dir(tmp_path, "Totally Unknown Topic XYZ")
    assert result is not None
    assert ".claude" in str(result)
    assert "scratch" in str(result)
    assert "writer" in str(result)


# ---------------------------------------------------------------------------
# Task 1 tests: cmd_load stdout content
# ---------------------------------------------------------------------------

def test_cmd_load_prints_research(tmp_path: Path, capsys) -> None:
    """cmd_load prints 'Research Dossier' label and Research.md content to stdout."""
    _make_project_dir(tmp_path)
    _make_channel_files(tmp_path)
    _make_prompt_file(tmp_path)

    with patch("writer.cli._get_project_root", return_value=tmp_path):
        cmd_load("Duplessis Orphans")

    captured = capsys.readouterr().out
    assert "Research Dossier" in captured
    assert "Research content here." in captured


def test_cmd_load_prints_style_profile(tmp_path: Path, capsys) -> None:
    """cmd_load prints 'Style Profile' label and STYLE_PROFILE.md content to stdout."""
    _make_project_dir(tmp_path)
    _make_channel_files(tmp_path)
    _make_prompt_file(tmp_path)

    with patch("writer.cli._get_project_root", return_value=tmp_path):
        cmd_load("Duplessis Orphans")

    captured = capsys.readouterr().out
    assert "Style Profile" in captured
    assert "Rule 1: Declarative Factual Claims." in captured


def test_cmd_load_prints_channel_dna(tmp_path: Path, capsys) -> None:
    """cmd_load prints 'Channel DNA' label and channel.md content to stdout."""
    _make_project_dir(tmp_path)
    _make_channel_files(tmp_path)
    _make_prompt_file(tmp_path)

    with patch("writer.cli._get_project_root", return_value=tmp_path):
        cmd_load("Duplessis Orphans")

    captured = capsys.readouterr().out
    assert "Channel DNA" in captured
    assert "Voice: Authoritative narrator." in captured


def test_cmd_load_prints_output_path(tmp_path: Path, capsys) -> None:
    """cmd_load prints resolved Script.md output path to stdout."""
    _make_project_dir(tmp_path)
    _make_channel_files(tmp_path)
    _make_prompt_file(tmp_path)

    with patch("writer.cli._get_project_root", return_value=tmp_path):
        cmd_load("Duplessis Orphans")

    captured = capsys.readouterr().out
    assert "Script.md" in captured


def test_cmd_load_prints_generation_prompt_path(tmp_path: Path, capsys) -> None:
    """cmd_load prints generation.md prompt path to stdout."""
    _make_project_dir(tmp_path)
    _make_channel_files(tmp_path)
    _make_prompt_file(tmp_path)

    with patch("writer.cli._get_project_root", return_value=tmp_path):
        cmd_load("Duplessis Orphans")

    captured = capsys.readouterr().out
    assert "generation.md" in captured


def test_cmd_load_missing_research(tmp_path: Path, capsys) -> None:
    """cmd_load exits with error when Research.md is not found."""
    # Project dir exists but no Research.md
    project_dir = tmp_path / "projects" / "1. Some Topic"
    project_dir.mkdir(parents=True)
    _make_channel_files(tmp_path)
    _make_prompt_file(tmp_path)

    with patch("writer.cli._get_project_root", return_value=tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            cmd_load("Some Topic")

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert len(captured.err) > 0
