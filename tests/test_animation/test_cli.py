"""Tests for animation.cli — CLI context aggregator with load/render/status.

All tests use tmp_path and capsys fixtures. No filesystem side-effects outside tmp_path.
Subprocess calls are mocked — no real Remotion installation required.
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from animation.cli import (
    cmd_load,
    cmd_render,
    cmd_status,
    resolve_project_dir,
    _map_shot_to_props,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_project_dir(
    root: Path,
    name: str = "1. The Duplessis Orphans Quebec's Stolen Children",
    shots: list[dict] | None = None,
) -> Path:
    """Create a fake project directory with shotlist.json containing map shots."""
    project_dir = root / "projects" / name
    project_dir.mkdir(parents=True)

    if shots is None:
        shots = [
            {
                "id": "S003",
                "chapter": 1,
                "chapter_title": "The Geography",
                "narrative_context": "Locations across Quebec.",
                "visual_need": "Map showing orphanage locations",
                "building_block": "Illustrated Map",
                "shotlist_type": "map",
            },
            {
                "id": "S007",
                "chapter": 2,
                "chapter_title": "The Network",
                "narrative_context": "Connections between institutions.",
                "visual_need": "Network connections across province",
                "building_block": "Connection/Arc Map",
                "shotlist_type": "map",
            },
            {
                "id": "S001",
                "chapter": 1,
                "chapter_title": "The Scheme",
                "narrative_context": "Opening scene.",
                "visual_need": "Silhouette of a leader figure.",
                "building_block": "Silhouette Figure",
                "shotlist_type": "animation",
            },
        ]

    shotlist = {
        "project": "Duplessis Orphans",
        "guide_source": "Test Guide",
        "generated": "2026-03-15T00:00:00Z",
        "shots": shots,
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


def _make_remotion_dir(root: Path) -> Path:
    """Create a fake Remotion project directory with node_modules."""
    remotion_dir = root / ".claude" / "skills" / "animation" / "remotion"
    remotion_dir.mkdir(parents=True)
    (remotion_dir / "node_modules").mkdir()
    return remotion_dir


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
    assert "animation" in str(result)


def test_resolve_project_dir_ambiguous_raises(tmp_path: Path) -> None:
    """Multiple matching directories raises ValueError."""
    _make_project_dir(tmp_path, "1. Mystery of the Lake")
    _make_project_dir(tmp_path, "2. Mystery of the Forest")
    with pytest.raises(ValueError, match="Multiple project directories"):
        resolve_project_dir(tmp_path, "Mystery")


# ---------------------------------------------------------------------------
# cmd_load tests
# ---------------------------------------------------------------------------

def test_cmd_load_prints_map_shots_section(tmp_path: Path, capsys) -> None:
    """cmd_load prints MAP_SHOTS section label with map-type shots."""
    _setup_full_project(tmp_path)
    with patch("animation.cli._get_project_root", return_value=tmp_path):
        cmd_load("Duplessis Orphans")
    captured = capsys.readouterr().out
    assert "=== MAP_SHOTS ===" in captured
    assert "Illustrated Map" in captured
    assert "Connection/Arc Map" in captured


def test_cmd_load_excludes_non_map_shots(tmp_path: Path, capsys) -> None:
    """cmd_load does NOT include animation-type shots in MAP_SHOTS section."""
    _setup_full_project(tmp_path)
    with patch("animation.cli._get_project_root", return_value=tmp_path):
        cmd_load("Duplessis Orphans")
    captured = capsys.readouterr().out
    # The MAP_SHOTS section should have map shots but not the animation shot
    # S001 Silhouette Figure is shotlist_type "animation", not "map"
    map_section = captured.split("=== MAP_SHOTS ===")[1].split("===")[0]
    assert "Silhouette Figure" not in map_section


def test_cmd_load_prints_channel_dna(tmp_path: Path, capsys) -> None:
    """cmd_load prints CHANNEL_DNA section with content."""
    _setup_full_project(tmp_path)
    with patch("animation.cli._get_project_root", return_value=tmp_path):
        cmd_load("Duplessis Orphans")
    captured = capsys.readouterr().out
    assert "=== CHANNEL_DNA ===" in captured
    assert "Authoritative narrator" in captured


def test_cmd_load_prints_manifest_absent(tmp_path: Path, capsys) -> None:
    """cmd_load notes manifest absence when manifest.json doesn't exist."""
    _setup_full_project(tmp_path)
    with patch("animation.cli._get_project_root", return_value=tmp_path):
        cmd_load("Duplessis Orphans")
    captured = capsys.readouterr().out
    assert "=== MANIFEST ===" in captured
    assert "No manifest.json found" in captured


def test_cmd_load_missing_shotlist_exits_1(tmp_path: Path, capsys) -> None:
    """cmd_load exits 1 when shotlist.json is not found."""
    _make_channel_file(tmp_path)
    project_dir = tmp_path / "projects" / "1. Some Topic"
    project_dir.mkdir(parents=True)

    with patch("animation.cli._get_project_root", return_value=tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            cmd_load("Some Topic")

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert len(captured.err) > 0


def test_cmd_load_no_map_shots_message(tmp_path: Path, capsys) -> None:
    """cmd_load prints 'No map shots' when shotlist has no map-type entries."""
    # Create project with only animation shots, no map shots
    _make_project_dir(tmp_path, shots=[
        {
            "id": "S001",
            "chapter": 1,
            "chapter_title": "Ch1",
            "narrative_context": "Scene.",
            "visual_need": "A figure.",
            "building_block": "Silhouette Figure",
            "shotlist_type": "animation",
        }
    ])
    _make_channel_file(tmp_path)
    with patch("animation.cli._get_project_root", return_value=tmp_path):
        cmd_load("Duplessis Orphans")
    captured = capsys.readouterr().out
    assert "No map shots found" in captured


# ---------------------------------------------------------------------------
# cmd_render tests (subprocess mocked)
# ---------------------------------------------------------------------------

def test_cmd_render_calls_subprocess_with_correct_args(tmp_path: Path) -> None:
    """cmd_render invokes npx remotion render with correct cwd and composition."""
    _make_project_dir(tmp_path)
    remotion_dir = _make_remotion_dir(tmp_path)

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""
    mock_result.stdout = ""

    with patch("animation.cli._get_project_root", return_value=tmp_path), \
         patch("animation.cli.subprocess.run", return_value=mock_result) as mock_run:
        # Create a fake output file when subprocess "succeeds"
        def side_effect(*args, **kwargs):
            cmd = args[0]
            # cmd layout: [npx, remotion, render, entry, MapComposition, output_path, --props=...]
            output_path = Path(cmd[5])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"fake mp4 content")
            return mock_result

        mock_run.side_effect = side_effect
        cmd_render("Duplessis Orphans")

    # Should have been called twice (2 map shots in default fixture)
    assert mock_run.call_count == 2

    # Verify first call has correct structure
    first_call = mock_run.call_args_list[0]
    call_args = first_call[0][0]  # positional args[0] is the command list
    call_kwargs = first_call[1]

    assert call_args[0] == "npx"
    assert call_args[1] == "remotion"
    assert call_args[2] == "render"
    assert call_args[4] == "MapComposition"
    assert call_kwargs["cwd"] == str(remotion_dir)


def test_cmd_render_merges_manifest(tmp_path: Path) -> None:
    """cmd_render creates manifest.json with animation entries after rendering."""
    _make_project_dir(tmp_path)
    _make_remotion_dir(tmp_path)

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""
    mock_result.stdout = ""

    def side_effect(*args, **kwargs):
        cmd = args[0]
        output_path = Path(cmd[5])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake mp4")
        return mock_result

    with patch("animation.cli._get_project_root", return_value=tmp_path), \
         patch("animation.cli.subprocess.run", side_effect=side_effect):
        cmd_render("Duplessis Orphans")

    project_dir = tmp_path / "projects" / "1. The Duplessis Orphans Quebec's Stolen Children"
    manifest_path = project_dir / "assets" / "manifest.json"
    assert manifest_path.exists()

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(data["assets"]) == 2
    for asset in data["assets"]:
        assert asset["acquired_by"] == "agent_animation"
        assert asset["folder"] == "animations"
        assert asset["source"] == "remotion_render"


def test_cmd_render_subprocess_failure_exits_1(tmp_path: Path, capsys) -> None:
    """cmd_render exits 1 when subprocess fails."""
    _make_project_dir(tmp_path)
    _make_remotion_dir(tmp_path)

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "TypeScript compilation error"
    mock_result.stdout = ""

    with patch("animation.cli._get_project_root", return_value=tmp_path), \
         patch("animation.cli.subprocess.run", return_value=mock_result):
        with pytest.raises(SystemExit) as exc_info:
            cmd_render("Duplessis Orphans")

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "TypeScript compilation error" in captured.err


def test_cmd_render_missing_shotlist_exits_1(tmp_path: Path) -> None:
    """cmd_render exits 1 when shotlist.json doesn't exist."""
    project_dir = tmp_path / "projects" / "1. Some Topic"
    project_dir.mkdir(parents=True)

    with patch("animation.cli._get_project_root", return_value=tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            cmd_render("Some Topic")

    assert exc_info.value.code == 1


def test_cmd_render_no_map_shots_exits_0(tmp_path: Path) -> None:
    """cmd_render exits 0 with message when no map shots found."""
    _make_project_dir(tmp_path, shots=[
        {
            "id": "S001",
            "chapter": 1,
            "chapter_title": "Ch1",
            "narrative_context": "Scene.",
            "visual_need": "A figure.",
            "building_block": "Silhouette Figure",
            "shotlist_type": "animation",
        }
    ])
    _make_remotion_dir(tmp_path)

    with patch("animation.cli._get_project_root", return_value=tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            cmd_render("Duplessis Orphans")

    assert exc_info.value.code == 0
