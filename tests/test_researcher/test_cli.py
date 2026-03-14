"""Tests for researcher.cli — CLI entry point with survey subcommand.

All tests mock external dependencies (fetcher, filesystem) so no crawl4ai
install or network access is required.
"""
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Module-level crawl4ai mock — installed before any researcher import
# ---------------------------------------------------------------------------

def _install_crawl4ai_mock() -> None:
    """Install a minimal crawl4ai mock into sys.modules."""
    if "crawl4ai" in sys.modules:
        return

    cache_mode_mock = MagicMock()
    cache_mode_mock.BYPASS = "BYPASS_SENTINEL"

    crawl4ai_mod = types.ModuleType("crawl4ai")
    crawl4ai_mod.CacheMode = cache_mode_mock
    crawl4ai_mod.BrowserConfig = MagicMock
    crawl4ai_mod.CrawlerRunConfig = MagicMock
    crawl4ai_mod.AsyncWebCrawler = MagicMock
    sys.modules["crawl4ai"] = crawl4ai_mod


_install_crawl4ai_mock()


from researcher.cli import cmd_survey  # noqa: E402 (after mock install)


# ---------------------------------------------------------------------------
# Test: cmd_survey smoke test
# ---------------------------------------------------------------------------

def test_cmd_survey_smoke(tmp_path: Path, capsys) -> None:
    """cmd_survey with a topic string does not crash (wiring smoke test)."""
    # Mock resolve_output_dir to return a tmp path so no filesystem side-effects
    output_dir = tmp_path / "research"
    output_dir.mkdir()

    # Mock fetch_with_retry to return a successful result
    mock_fetch_result = {
        "success": True,
        "content": "x" * 500,
        "error": "",
        "fetch_status": "ok",
        "attempts_used": 1,
    }

    with (
        patch("researcher.cli.resolve_output_dir", return_value=output_dir),
        patch("researcher.cli._get_project_root", return_value=tmp_path),
        patch("researcher.cli.fetch_with_retry", return_value=mock_fetch_result),
    ):
        # Should not raise
        cmd_survey("Jonestown Massacre")

    captured = capsys.readouterr()
    # Should print some output (path, status lines, summary)
    assert len(captured.out) > 0


# ---------------------------------------------------------------------------
# Phase 8 tests — summary table, domain field, manifest schema
# ---------------------------------------------------------------------------

def test_summary_table_columns(tmp_path: Path, capsys) -> None:
    """cmd_survey stdout contains summary table with required column headers."""
    output_dir = tmp_path / "research"
    output_dir.mkdir()

    mock_fetch_result = {
        "success": True,
        "content": "x" * 500,
        "error": "",
        "fetch_status": "ok",
        "attempts_used": 1,
    }

    with (
        patch("researcher.cli.resolve_output_dir", return_value=output_dir),
        patch("researcher.cli._get_project_root", return_value=tmp_path),
        patch("researcher.cli.fetch_with_retry", return_value=mock_fetch_result),
    ):
        cmd_survey("Jonestown Massacre")

    captured = capsys.readouterr().out
    assert "#" in captured
    assert "Domain" in captured
    assert "Tier" in captured
    assert "Words" in captured
    assert "Status" in captured


def test_domain_field_in_src_json(tmp_path: Path) -> None:
    """src_001.json written by cmd_survey has a 'domain' key."""
    output_dir = tmp_path / "research"
    output_dir.mkdir()

    mock_fetch_result = {
        "success": True,
        "content": "x" * 500,
        "error": "",
        "fetch_status": "ok",
        "attempts_used": 1,
    }

    with (
        patch("researcher.cli.resolve_output_dir", return_value=output_dir),
        patch("researcher.cli._get_project_root", return_value=tmp_path),
        patch(
            "researcher.cli.build_survey_urls",
            return_value=["https://en.wikipedia.org/wiki/Jonestown_Massacre"],
        ),
        patch("researcher.cli.fetch_with_retry", return_value=mock_fetch_result),
    ):
        cmd_survey("Jonestown Massacre")

    import json
    src_file = output_dir / "src_001.json"
    assert src_file.exists(), "src_001.json not created"
    data = json.loads(src_file.read_text(encoding="utf-8"))
    assert "domain" in data, f"'domain' key missing from src_001.json keys: {list(data.keys())}"


def test_manifest_schema_fields(tmp_path: Path) -> None:
    """source_manifest.json sources[0] has all required schema fields."""
    output_dir = tmp_path / "research"
    output_dir.mkdir()

    mock_fetch_result = {
        "success": True,
        "content": "x" * 500,
        "error": "",
        "fetch_status": "ok",
        "attempts_used": 1,
    }

    with (
        patch("researcher.cli.resolve_output_dir", return_value=output_dir),
        patch("researcher.cli._get_project_root", return_value=tmp_path),
        patch(
            "researcher.cli.build_survey_urls",
            return_value=["https://en.wikipedia.org/wiki/Jonestown_Massacre"],
        ),
        patch("researcher.cli.fetch_with_retry", return_value=mock_fetch_result),
    ):
        cmd_survey("Jonestown Massacre")

    import json
    manifest_file = output_dir / "source_manifest.json"
    assert manifest_file.exists(), "source_manifest.json not created"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    sources = manifest.get("sources", [])
    assert len(sources) > 0, "source_manifest.json has no sources"
    source = sources[0]
    required_keys = {"index", "filename", "url", "domain", "tier", "word_count", "fetch_status"}
    missing = required_keys - set(source.keys())
    assert not missing, f"source_manifest.json sources[0] missing keys: {missing}"


def test_scratch_dir_content_not_in_stdout(tmp_path: Path, capsys) -> None:
    """cmd_survey stdout does not contain fetched content body."""
    output_dir = tmp_path / "research"
    output_dir.mkdir()

    content_body = "UNIQUE_CONTENT_MARKER_XYZ_" + "z" * 300

    mock_fetch_result = {
        "success": True,
        "content": content_body,
        "error": "",
        "fetch_status": "ok",
        "attempts_used": 1,
    }

    with (
        patch("researcher.cli.resolve_output_dir", return_value=output_dir),
        patch("researcher.cli._get_project_root", return_value=tmp_path),
        patch("researcher.cli.fetch_with_retry", return_value=mock_fetch_result),
    ):
        cmd_survey("Jonestown Massacre")

    captured = capsys.readouterr().out
    assert "UNIQUE_CONTENT_MARKER_XYZ_" not in captured


def test_tier3_url_skipped_in_table(tmp_path: Path, capsys) -> None:
    """Summary table shows 'skipped' for a Tier 3 URL."""
    output_dir = tmp_path / "research"
    output_dir.mkdir()

    mock_fetch_result_skipped = {
        "success": False,
        "content": "",
        "error": "Tier 3 domain skipped",
        "fetch_status": "skipped_tier3",
        "attempts_used": 0,
    }

    with (
        patch("researcher.cli.resolve_output_dir", return_value=output_dir),
        patch("researcher.cli._get_project_root", return_value=tmp_path),
        patch(
            "researcher.cli.build_survey_urls",
            return_value=["https://reddit.com/r/history/wiki_post"],
        ),
        patch("researcher.cli.fetch_with_retry", return_value=mock_fetch_result_skipped),
    ):
        cmd_survey("history")

    captured = capsys.readouterr().out
    assert "skipped" in captured.lower()


def test_ddg_page_not_saved_as_src(tmp_path: Path) -> None:
    """After DDG URL expansion, no src file has url containing 'duckduckgo.com'."""
    output_dir = tmp_path / "research"
    output_dir.mkdir()

    mock_fetch_result = {
        "success": True,
        "content": "x" * 500,
        "error": "",
        "fetch_status": "ok",
        "attempts_used": 1,
    }

    with (
        patch("researcher.cli.resolve_output_dir", return_value=output_dir),
        patch("researcher.cli._get_project_root", return_value=tmp_path),
        patch(
            "researcher.cli.build_survey_urls",
            return_value=["https://en.wikipedia.org/wiki/Jonestown_Massacre"],
        ),
        patch("researcher.cli.fetch_with_retry", return_value=mock_fetch_result),
    ):
        cmd_survey("Jonestown Massacre")

    import json
    for f in output_dir.glob("src_*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        url = data.get("url", "")
        assert "duckduckgo.com" not in url, (
            f"{f.name} contains a DDG URL: {url}"
        )
