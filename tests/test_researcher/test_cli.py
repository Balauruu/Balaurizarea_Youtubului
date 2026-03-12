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
