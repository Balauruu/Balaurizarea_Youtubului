"""Tests for researcher.url_builder — project directory resolution
and DuckDuckGo URL construction.
"""
import pytest
from pathlib import Path

from researcher.url_builder import find_project_dir, resolve_output_dir, make_ddg_url


# ---------------------------------------------------------------------------
# Tests: find_project_dir
# ---------------------------------------------------------------------------

def test_find_project_dir(tmp_path: Path) -> None:
    """find_project_dir returns path when exact title matches."""
    projects = tmp_path / "projects"
    target = projects / "1. Jonestown Massacre"
    target.mkdir(parents=True)

    result = find_project_dir(tmp_path, "Jonestown")
    assert result == target


def test_find_project_dir_case_insensitive(tmp_path: Path) -> None:
    """find_project_dir matches regardless of query case."""
    projects = tmp_path / "projects"
    target = projects / "1. Jonestown Massacre"
    target.mkdir(parents=True)

    result = find_project_dir(tmp_path, "jonestown")
    assert result == target


def test_find_project_dir_multiple_matches(tmp_path: Path) -> None:
    """find_project_dir raises ValueError listing all matches when multiple dirs match."""
    projects = tmp_path / "projects"
    (projects / "1. Cult of XYZ").mkdir(parents=True)
    (projects / "2. Cult ABC").mkdir(parents=True)

    with pytest.raises(ValueError) as exc_info:
        find_project_dir(tmp_path, "cult")

    error_msg = str(exc_info.value)
    assert "Cult of XYZ" in error_msg
    assert "Cult ABC" in error_msg


def test_find_project_dir_no_match(tmp_path: Path) -> None:
    """find_project_dir returns None when no directory matches."""
    projects = tmp_path / "projects"
    (projects / "1. Jonestown Massacre").mkdir(parents=True)

    result = find_project_dir(tmp_path, "nonexistent")
    assert result is None


def test_find_project_dir_no_projects_dir(tmp_path: Path) -> None:
    """find_project_dir returns None when projects/ directory doesn't exist."""
    result = find_project_dir(tmp_path, "anything")
    assert result is None


# ---------------------------------------------------------------------------
# Tests: resolve_output_dir
# ---------------------------------------------------------------------------

def test_resolve_output_dir_project_exists(tmp_path: Path) -> None:
    """resolve_output_dir returns research/ subdir and creates it when project exists."""
    projects = tmp_path / "projects"
    target = projects / "1. Jonestown Massacre"
    target.mkdir(parents=True)

    result = resolve_output_dir(tmp_path, "Jonestown")
    expected = target / "research"
    assert result == expected
    assert result.is_dir(), "research/ directory should have been created"


def test_resolve_output_dir_standalone(tmp_path: Path) -> None:
    """resolve_output_dir returns .claude/scratch/researcher/ when no project matches."""
    result = resolve_output_dir(tmp_path, "nonexistent")
    expected = tmp_path / ".claude" / "scratch" / "researcher"
    assert result == expected
    assert result.is_dir(), "scratch/researcher/ directory should have been created"


# ---------------------------------------------------------------------------
# Tests: make_ddg_url
# ---------------------------------------------------------------------------

def test_make_ddg_url() -> None:
    """make_ddg_url returns correct URL-encoded DuckDuckGo HTML endpoint URL."""
    result = make_ddg_url("Jonestown Massacre")
    assert result == "https://html.duckduckgo.com/html/?q=Jonestown+Massacre"


def test_make_ddg_url_special_chars() -> None:
    """make_ddg_url properly encodes special characters."""
    result = make_ddg_url("cult & murder")
    assert result == "https://html.duckduckgo.com/html/?q=cult+%26+murder"


# ---------------------------------------------------------------------------
# Phase 8 tests — build_survey_urls refactor (Wikipedia-only return)
# ---------------------------------------------------------------------------

def test_build_survey_urls_wikipedia_only() -> None:
    """build_survey_urls returns a list of exactly one URL (Wikipedia only)."""
    from researcher.url_builder import build_survey_urls
    result = build_survey_urls("Jonestown")
    assert len(result) == 1


def test_build_survey_urls_no_ddg() -> None:
    """build_survey_urls result contains no DuckDuckGo URL."""
    from researcher.url_builder import build_survey_urls
    result = build_survey_urls("Jonestown")
    assert not any("duckduckgo.com" in url for url in result)


def test_build_survey_urls_wikipedia_url_format() -> None:
    """build_survey_urls result[0] is a valid Wikipedia URL."""
    from researcher.url_builder import build_survey_urls
    result = build_survey_urls("Jonestown")
    assert result[0].startswith("https://en.wikipedia.org/wiki/")
