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


from researcher.cli import cmd_survey, cmd_deepen  # noqa: E402 (after mock install)


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


# ---------------------------------------------------------------------------
# Phase 9 tests — cmd_deepen (Pass 2 deep dive)
# ---------------------------------------------------------------------------

import json as _json  # noqa: E402 (late import for test helpers)


def _write_manifest(output_dir: Path, sources: list[dict], topic: str = "Test Topic") -> Path:
    """Write a source_manifest.json to output_dir and return its path."""
    manifest = {
        "topic": topic,
        "run_timestamp": "2026-03-14T10:00:00Z",
        "sources": sources,
    }
    manifest_path = output_dir / "source_manifest.json"
    manifest_path.write_text(_json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


def _mock_fetch(content: str = "test content " * 50) -> dict:
    """Return a successful mock fetch result dict."""
    return {
        "success": True,
        "content": content,
        "error": "",
        "fetch_status": "ok",
        "attempts_used": 1,
    }


def test_cmd_deepen_reads_recommended_only(tmp_path: Path) -> None:
    """cmd_deepen only fetches URLs from sources with verdict='recommended'."""
    output_dir = tmp_path / "research"
    output_dir.mkdir()

    sources = [
        {
            "index": 1, "filename": "src_001.json", "url": "https://en.wikipedia.org/wiki/X",
            "domain": "en.wikipedia.org", "tier": 1, "word_count": 500, "fetch_status": "ok",
            "verdict": "recommended",
            "deep_dive_urls": ["https://vault.fbi.gov/jonestown"],
        },
        {
            "index": 2, "filename": "src_002.json", "url": "https://bbc.com/article",
            "domain": "bbc.com", "tier": 2, "word_count": 300, "fetch_status": "ok",
            "verdict": "skip",
            "deep_dive_urls": ["https://loc.gov/something"],
        },
    ]
    # Write src files so budget guard passes
    (output_dir / "src_001.json").write_text(_json.dumps({"url": "https://en.wikipedia.org/wiki/X"}), encoding="utf-8")
    (output_dir / "src_002.json").write_text(_json.dumps({"url": "https://bbc.com/article"}), encoding="utf-8")
    _write_manifest(output_dir, sources)

    with (
        patch("researcher.cli.resolve_output_dir", return_value=output_dir),
        patch("researcher.cli._get_project_root", return_value=tmp_path),
        patch("researcher.cli.fetch_with_retry", return_value=_mock_fetch()) as mock_fetch,
    ):
        cmd_deepen("Test Topic")

    # Only the recommended source's URL should have been fetched
    fetched_urls = [call.args[0] for call in mock_fetch.call_args_list]
    assert "https://vault.fbi.gov/jonestown" in fetched_urls
    assert "https://loc.gov/something" not in fetched_urls


def test_cmd_deepen_writes_pass2_json(tmp_path: Path) -> None:
    """cmd_deepen writes pass2_001.json with correct schema keys."""
    output_dir = tmp_path / "research"
    output_dir.mkdir()

    sources = [
        {
            "index": 1, "filename": "src_001.json", "url": "https://en.wikipedia.org/wiki/X",
            "domain": "en.wikipedia.org", "tier": 1, "word_count": 500, "fetch_status": "ok",
            "verdict": "recommended",
            "deep_dive_urls": ["https://vault.fbi.gov/jonestown"],
        },
    ]
    (output_dir / "src_001.json").write_text(_json.dumps({"url": "https://en.wikipedia.org/wiki/X"}), encoding="utf-8")
    _write_manifest(output_dir, sources)

    with (
        patch("researcher.cli.resolve_output_dir", return_value=output_dir),
        patch("researcher.cli._get_project_root", return_value=tmp_path),
        patch("researcher.cli.fetch_with_retry", return_value=_mock_fetch()),
    ):
        cmd_deepen("Test Topic")

    pass2_file = output_dir / "pass2_001.json"
    assert pass2_file.exists(), "pass2_001.json not written"
    data = _json.loads(pass2_file.read_text(encoding="utf-8"))
    required_keys = {"index", "url", "domain", "tier", "word_count", "fetch_status", "error", "content"}
    missing = required_keys - set(data.keys())
    assert not missing, f"pass2_001.json missing keys: {missing}"


def test_cmd_deepen_updates_manifest_pass2_sources(tmp_path: Path) -> None:
    """cmd_deepen adds 'pass2_sources' key to source_manifest.json."""
    output_dir = tmp_path / "research"
    output_dir.mkdir()

    sources = [
        {
            "index": 1, "filename": "src_001.json", "url": "https://en.wikipedia.org/wiki/X",
            "domain": "en.wikipedia.org", "tier": 1, "word_count": 500, "fetch_status": "ok",
            "verdict": "recommended",
            "deep_dive_urls": ["https://vault.fbi.gov/jonestown"],
        },
    ]
    (output_dir / "src_001.json").write_text(_json.dumps({"url": "https://en.wikipedia.org/wiki/X"}), encoding="utf-8")
    _write_manifest(output_dir, sources)

    with (
        patch("researcher.cli.resolve_output_dir", return_value=output_dir),
        patch("researcher.cli._get_project_root", return_value=tmp_path),
        patch("researcher.cli.fetch_with_retry", return_value=_mock_fetch()),
    ):
        cmd_deepen("Test Topic")

    manifest = _json.loads((output_dir / "source_manifest.json").read_text(encoding="utf-8"))
    assert "pass2_sources" in manifest, "pass2_sources key not added to manifest"


def test_cmd_deepen_budget_guard(tmp_path: Path, capsys) -> None:
    """cmd_deepen respects 15-file budget (14 existing + 3 deep_dive = fetch only 1)."""
    output_dir = tmp_path / "research"
    output_dir.mkdir()

    # Create 14 existing src_*.json files
    for i in range(1, 15):
        (output_dir / f"src_{i:03d}.json").write_text(
            _json.dumps({"url": f"https://example.com/page{i}"}), encoding="utf-8"
        )

    sources = [
        {
            "index": 1, "filename": "src_001.json", "url": "https://example.com/page1",
            "domain": "example.com", "tier": 2, "word_count": 100, "fetch_status": "ok",
            "verdict": "recommended",
            "deep_dive_urls": [
                "https://archive.org/url1",
                "https://archive.org/url2",
                "https://archive.org/url3",
            ],
        },
    ]
    _write_manifest(output_dir, sources)

    with (
        patch("researcher.cli.resolve_output_dir", return_value=output_dir),
        patch("researcher.cli._get_project_root", return_value=tmp_path),
        patch("researcher.cli.fetch_with_retry", return_value=_mock_fetch()) as mock_fetch,
    ):
        cmd_deepen("Test Topic")

    # Only 1 URL should be fetched (15 - 14 = 1 budget)
    assert mock_fetch.call_count == 1

    captured = capsys.readouterr().out
    assert "budget" in captured.lower() or "skip" in captured.lower()


def test_cmd_deepen_dedup_pass1_urls(tmp_path: Path) -> None:
    """cmd_deepen does not re-fetch a URL already in a src_*.json file."""
    output_dir = tmp_path / "research"
    output_dir.mkdir()

    already_fetched_url = "https://example.com/page"
    (output_dir / "src_001.json").write_text(
        _json.dumps({"url": already_fetched_url}), encoding="utf-8"
    )

    sources = [
        {
            "index": 1, "filename": "src_001.json", "url": already_fetched_url,
            "domain": "example.com", "tier": 2, "word_count": 100, "fetch_status": "ok",
            "verdict": "recommended",
            "deep_dive_urls": [already_fetched_url],
        },
    ]
    _write_manifest(output_dir, sources)

    with (
        patch("researcher.cli.resolve_output_dir", return_value=output_dir),
        patch("researcher.cli._get_project_root", return_value=tmp_path),
        patch("researcher.cli.fetch_with_retry", return_value=_mock_fetch()) as mock_fetch,
    ):
        cmd_deepen("Test Topic")

    assert mock_fetch.call_count == 0, "Should not re-fetch already-fetched URL"


def test_cmd_deepen_dedup_across_sources(tmp_path: Path) -> None:
    """Same deep_dive_url in two recommended sources is only fetched once."""
    output_dir = tmp_path / "research"
    output_dir.mkdir()

    shared_url = "https://vault.fbi.gov/jonestown"
    sources = [
        {
            "index": 1, "filename": "src_001.json", "url": "https://en.wikipedia.org/wiki/X",
            "domain": "en.wikipedia.org", "tier": 1, "word_count": 500, "fetch_status": "ok",
            "verdict": "recommended",
            "deep_dive_urls": [shared_url],
        },
        {
            "index": 2, "filename": "src_002.json", "url": "https://bbc.com/article",
            "domain": "bbc.com", "tier": 2, "word_count": 300, "fetch_status": "ok",
            "verdict": "recommended",
            "deep_dive_urls": [shared_url],
        },
    ]
    (output_dir / "src_001.json").write_text(_json.dumps({"url": "https://en.wikipedia.org/wiki/X"}), encoding="utf-8")
    (output_dir / "src_002.json").write_text(_json.dumps({"url": "https://bbc.com/article"}), encoding="utf-8")
    _write_manifest(output_dir, sources)

    with (
        patch("researcher.cli.resolve_output_dir", return_value=output_dir),
        patch("researcher.cli._get_project_root", return_value=tmp_path),
        patch("researcher.cli.fetch_with_retry", return_value=_mock_fetch()) as mock_fetch,
    ):
        cmd_deepen("Test Topic")

    fetched_urls = [call.args[0] for call in mock_fetch.call_args_list]
    assert fetched_urls.count(shared_url) == 1, f"URL fetched {fetched_urls.count(shared_url)} times, expected 1"


def test_cmd_deepen_clean_exit_no_urls(tmp_path: Path, capsys) -> None:
    """cmd_deepen exits cleanly when no fetchable URLs exist."""
    output_dir = tmp_path / "research"
    output_dir.mkdir()

    sources = [
        {
            "index": 1, "filename": "src_001.json", "url": "https://bbc.com/article",
            "domain": "bbc.com", "tier": 2, "word_count": 300, "fetch_status": "ok",
            "verdict": "skip",
            "deep_dive_urls": ["https://some.url.com/article"],
        },
    ]
    (output_dir / "src_001.json").write_text(_json.dumps({"url": "https://bbc.com/article"}), encoding="utf-8")
    _write_manifest(output_dir, sources)

    with (
        patch("researcher.cli.resolve_output_dir", return_value=output_dir),
        patch("researcher.cli._get_project_root", return_value=tmp_path),
        patch("researcher.cli.fetch_with_retry", return_value=_mock_fetch()) as mock_fetch,
    ):
        cmd_deepen("Test Topic")

    assert mock_fetch.call_count == 0
    captured = capsys.readouterr().out
    assert "No deep-dive URLs found" in captured


def test_cmd_deepen_tier3_filtered(tmp_path: Path) -> None:
    """cmd_deepen does not fetch Tier 3 URLs in deep_dive_urls."""
    output_dir = tmp_path / "research"
    output_dir.mkdir()

    sources = [
        {
            "index": 1, "filename": "src_001.json", "url": "https://en.wikipedia.org/wiki/X",
            "domain": "en.wikipedia.org", "tier": 1, "word_count": 500, "fetch_status": "ok",
            "verdict": "recommended",
            "deep_dive_urls": ["https://facebook.com/page/cult-info"],
        },
    ]
    (output_dir / "src_001.json").write_text(_json.dumps({"url": "https://en.wikipedia.org/wiki/X"}), encoding="utf-8")
    _write_manifest(output_dir, sources)

    with (
        patch("researcher.cli.resolve_output_dir", return_value=output_dir),
        patch("researcher.cli._get_project_root", return_value=tmp_path),
        patch("researcher.cli.fetch_with_retry", return_value=_mock_fetch()) as mock_fetch,
    ):
        cmd_deepen("Test Topic")

    assert mock_fetch.call_count == 0, "Tier 3 URL should not be fetched"


def test_cmd_deepen_cleans_old_pass2_files(tmp_path: Path) -> None:
    """cmd_deepen deletes existing pass2_*.json files before a new run."""
    output_dir = tmp_path / "research"
    output_dir.mkdir()

    # Create a stale pass2 file from a previous run
    stale_file = output_dir / "pass2_001.json"
    stale_file.write_text(_json.dumps({"url": "https://old.example.com/stale"}), encoding="utf-8")

    # Manifest with no fetchable URLs (so the stale file gets deleted but nothing new written)
    sources = [
        {
            "index": 1, "filename": "src_001.json", "url": "https://bbc.com/article",
            "domain": "bbc.com", "tier": 2, "word_count": 300, "fetch_status": "ok",
            "verdict": "skip",
        },
    ]
    (output_dir / "src_001.json").write_text(_json.dumps({"url": "https://bbc.com/article"}), encoding="utf-8")
    _write_manifest(output_dir, sources)

    with (
        patch("researcher.cli.resolve_output_dir", return_value=output_dir),
        patch("researcher.cli._get_project_root", return_value=tmp_path),
        patch("researcher.cli.fetch_with_retry", return_value=_mock_fetch()),
    ):
        cmd_deepen("Test Topic")

    assert not stale_file.exists(), "Stale pass2_001.json should have been deleted"


def test_cmd_deepen_missing_verdict_treated_as_skip(tmp_path: Path) -> None:
    """Sources without a 'verdict' key are treated as skip — URLs not fetched."""
    output_dir = tmp_path / "research"
    output_dir.mkdir()

    sources = [
        {
            "index": 1, "filename": "src_001.json", "url": "https://en.wikipedia.org/wiki/X",
            "domain": "en.wikipedia.org", "tier": 1, "word_count": 500, "fetch_status": "ok",
            # No "verdict" key
            "deep_dive_urls": ["https://vault.fbi.gov/jonestown"],
        },
    ]
    (output_dir / "src_001.json").write_text(_json.dumps({"url": "https://en.wikipedia.org/wiki/X"}), encoding="utf-8")
    _write_manifest(output_dir, sources)

    with (
        patch("researcher.cli.resolve_output_dir", return_value=output_dir),
        patch("researcher.cli._get_project_root", return_value=tmp_path),
        patch("researcher.cli.fetch_with_retry", return_value=_mock_fetch()) as mock_fetch,
    ):
        cmd_deepen("Test Topic")

    assert mock_fetch.call_count == 0, "Source without verdict should be treated as skip"


def test_cmd_deepen_summary_table_printed(tmp_path: Path, capsys) -> None:
    """cmd_deepen prints summary table with 'Domain' and 'Status' column headers."""
    output_dir = tmp_path / "research"
    output_dir.mkdir()

    sources = [
        {
            "index": 1, "filename": "src_001.json", "url": "https://en.wikipedia.org/wiki/X",
            "domain": "en.wikipedia.org", "tier": 1, "word_count": 500, "fetch_status": "ok",
            "verdict": "recommended",
            "deep_dive_urls": ["https://vault.fbi.gov/jonestown"],
        },
    ]
    (output_dir / "src_001.json").write_text(_json.dumps({"url": "https://en.wikipedia.org/wiki/X"}), encoding="utf-8")
    _write_manifest(output_dir, sources)

    with (
        patch("researcher.cli.resolve_output_dir", return_value=output_dir),
        patch("researcher.cli._get_project_root", return_value=tmp_path),
        patch("researcher.cli.fetch_with_retry", return_value=_mock_fetch()),
    ):
        cmd_deepen("Test Topic")

    captured = capsys.readouterr().out
    assert "Domain" in captured
    assert "Status" in captured
