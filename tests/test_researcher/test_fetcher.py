"""Tests for researcher.fetcher module — crawl4ai wrapper with domain isolation,
retry logic, and content validation.

All tests mock crawl4ai entirely — no browser or crawl4ai install required.
"""
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import types

import pytest


# ---------------------------------------------------------------------------
# Module-level crawl4ai mock — installed before any fetcher import
# ---------------------------------------------------------------------------
# Create a fake crawl4ai module so fetcher.py's deferred imports work.

def _install_crawl4ai_mock():
    """Install a minimal crawl4ai mock into sys.modules."""
    if "crawl4ai" in sys.modules:
        return  # already installed (real or mock)

    # Sentinel for CacheMode.BYPASS that tests can compare against
    cache_mode_mock = MagicMock()
    cache_mode_mock.BYPASS = "BYPASS_SENTINEL"

    crawl4ai_mod = types.ModuleType("crawl4ai")
    crawl4ai_mod.CacheMode = cache_mode_mock
    crawl4ai_mod.BrowserConfig = MagicMock
    crawl4ai_mod.CrawlerRunConfig = MagicMock
    crawl4ai_mod.AsyncWebCrawler = MagicMock
    sys.modules["crawl4ai"] = crawl4ai_mod


_install_crawl4ai_mock()

from researcher.fetcher import fetch_with_retry  # noqa: E402 (after mock install)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_crawl_result(success: bool, content: str = "", error: str = "") -> MagicMock:
    """Build a mock CrawlResult object matching crawl4ai 0.8 API."""
    result = MagicMock()
    result.success = success
    result.markdown = MagicMock()
    result.markdown.raw_markdown = content
    result.error_message = error
    return result


def _make_crawler_context(crawl_result: MagicMock) -> MagicMock:
    """Build a mock AsyncWebCrawler context manager that returns crawl_result."""
    crawler = MagicMock()
    crawler.arun = AsyncMock(return_value=crawl_result)
    async_ctx = MagicMock()
    async_ctx.__aenter__ = AsyncMock(return_value=crawler)
    async_ctx.__aexit__ = AsyncMock(return_value=None)
    return async_ctx


# ---------------------------------------------------------------------------
# Test: Domain isolation (SCRP-01)
# ---------------------------------------------------------------------------

def test_domain_isolation():
    """Each fetch_with_retry call must create AsyncWebCrawler with
    BrowserConfig(use_persistent_context=False) and CrawlerRunConfig with BYPASS cache.
    """
    import crawl4ai  # the mock module

    crawl_result = _make_crawl_result(success=True, content="x" * 500)
    async_ctx = _make_crawler_context(crawl_result)

    browser_cfg_mock = MagicMock(return_value=MagicMock())
    run_cfg_mock = MagicMock(return_value=MagicMock())

    with (
        patch.object(crawl4ai, "AsyncWebCrawler", return_value=async_ctx),
        patch.object(crawl4ai, "BrowserConfig", browser_cfg_mock),
        patch.object(crawl4ai, "CrawlerRunConfig", run_cfg_mock),
    ):
        result = fetch_with_retry("https://en.wikipedia.org/wiki/Test", max_attempts=1)

    # BrowserConfig created with use_persistent_context=False
    browser_cfg_mock.assert_called_once()
    kwargs = browser_cfg_mock.call_args.kwargs
    assert kwargs.get("use_persistent_context") is False, (
        "BrowserConfig must set use_persistent_context=False"
    )

    # CrawlerRunConfig created with cache_mode=CacheMode.BYPASS
    run_cfg_mock.assert_called_once()
    run_kwargs = run_cfg_mock.call_args.kwargs
    assert run_kwargs.get("cache_mode") == crawl4ai.CacheMode.BYPASS, (
        "CrawlerRunConfig must use CacheMode.BYPASS"
    )

    assert result["success"] is True


# ---------------------------------------------------------------------------
# Test: Content length validation (SCRP-02)
# ---------------------------------------------------------------------------

def test_content_length_validation():
    """A successful fetch returning < MIN_CONTENT_CHARS should fail with
    error containing 'content too short'.
    """
    import crawl4ai

    short_content = "x" * 50  # below 200 char threshold
    crawl_result = _make_crawl_result(success=True, content=short_content)
    async_ctx = _make_crawler_context(crawl_result)

    with patch.object(crawl4ai, "AsyncWebCrawler", return_value=async_ctx):
        result = fetch_with_retry(
            "https://en.wikipedia.org/wiki/Test",
            max_attempts=1,
            delay_seconds=0,
        )

    assert result["success"] is False
    assert "content too short" in result["error"]
    assert "50" in result["error"]


def test_retry_on_short_content():
    """Short content causes retry up to max_attempts (tier-controlled)."""
    import crawl4ai

    short_content = "x" * 50
    crawl_result = _make_crawl_result(success=True, content=short_content)
    async_ctx = _make_crawler_context(crawl_result)

    with patch.object(crawl4ai, "AsyncWebCrawler", return_value=async_ctx):
        # Tier 1 URL → TIER_RETRY_MAP[1] == 3 attempts
        result = fetch_with_retry(
            "https://en.wikipedia.org/wiki/Test",
            max_attempts=3,
            delay_seconds=0,
        )

    assert result["success"] is False
    assert result["attempts_used"] == 3


# ---------------------------------------------------------------------------
# Test: Retry exhaustion on fetch failure (SCRP-02)
# ---------------------------------------------------------------------------

def test_retry_exhaustion():
    """When result.success is False for all attempts, should return
    success=False and attempts_used == effective_attempts (tier-controlled).
    """
    import crawl4ai

    crawl_result = _make_crawl_result(success=False, error="network error")
    async_ctx = _make_crawler_context(crawl_result)

    with patch.object(crawl4ai, "AsyncWebCrawler", return_value=async_ctx):
        # Tier 1 URL → 3 attempts
        result = fetch_with_retry(
            "https://en.wikipedia.org/wiki/Test",
            max_attempts=3,
            delay_seconds=0,
        )

    assert result["success"] is False
    assert result["attempts_used"] == 3


# ---------------------------------------------------------------------------
# Test: Successful fetch
# ---------------------------------------------------------------------------

def test_successful_fetch():
    """A successful fetch with sufficient content returns success=True."""
    import crawl4ai

    content = "x" * 500
    crawl_result = _make_crawl_result(success=True, content=content)
    async_ctx = _make_crawler_context(crawl_result)

    with patch.object(crawl4ai, "AsyncWebCrawler", return_value=async_ctx):
        result = fetch_with_retry(
            "https://en.wikipedia.org/wiki/Test",
            max_attempts=3,
            delay_seconds=0,
        )

    assert result["success"] is True
    assert result["content"] == content
    assert result["attempts_used"] == 1
    assert result["fetch_status"] == "ok"


# ---------------------------------------------------------------------------
# Test: Tier 3 skipped (SCRP-03)
# ---------------------------------------------------------------------------

def test_tier3_skipped():
    """A Tier 3 URL returns immediately with fetch_status='skipped_tier3'
    without calling crawl4ai.
    """
    import crawl4ai

    original = crawl4ai.AsyncWebCrawler
    call_count = [0]

    class CountingMock:
        def __init__(self, *args, **kwargs):
            call_count[0] += 1

    crawl4ai.AsyncWebCrawler = CountingMock
    try:
        result = fetch_with_retry("https://www.facebook.com/page", max_attempts=3)
    finally:
        crawl4ai.AsyncWebCrawler = original

    assert call_count[0] == 0, "AsyncWebCrawler should not be instantiated for Tier 3"
    assert result["success"] is False
    assert result["fetch_status"] == "skipped_tier3"
    assert result["attempts_used"] == 0


def test_tier3_x_com_skipped():
    """x.com (Twitter) should also be skipped as Tier 3."""
    import crawl4ai

    original = crawl4ai.AsyncWebCrawler
    call_count = [0]

    class CountingMock:
        def __init__(self, *args, **kwargs):
            call_count[0] += 1

    crawl4ai.AsyncWebCrawler = CountingMock
    try:
        result = fetch_with_retry("https://x.com/user/status/123")
    finally:
        crawl4ai.AsyncWebCrawler = original

    assert call_count[0] == 0
    assert result["fetch_status"] == "skipped_tier3"


# ---------------------------------------------------------------------------
# Test: fetch_status field present
# ---------------------------------------------------------------------------

def test_failed_fetch_status_is_failed():
    """A failed fetch should set fetch_status='failed'."""
    import crawl4ai

    crawl_result = _make_crawl_result(success=False, error="timeout")
    async_ctx = _make_crawler_context(crawl_result)

    with patch.object(crawl4ai, "AsyncWebCrawler", return_value=async_ctx):
        result = fetch_with_retry(
            "https://en.wikipedia.org/wiki/Test",
            max_attempts=1,
            delay_seconds=0,
        )

    assert result["fetch_status"] == "failed"
