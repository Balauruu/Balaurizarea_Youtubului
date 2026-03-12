"""Integration tests for the researcher skill.

These tests require:
- Network access
- crawl4ai installed and Playwright binaries present

Run separately from unit tests:
    pytest tests/test_researcher/test_integration.py -x --tb=short

Skip in fast unit test runs:
    pytest tests/test_researcher/ -x --tb=short -m "not integration"

IMPORTANT: Run these tests in isolation from unit tests because test_fetcher.py
installs a module-level crawl4ai mock that interferes with real crawl4ai access.
"""
import sys
import pytest


def _has_real_crawl4ai() -> bool:
    """Return True if the real crawl4ai (not a mock) is installed in sys.modules."""
    crawl4ai = sys.modules.get("crawl4ai")
    if crawl4ai is None:
        # Not yet imported — real install should be importable
        try:
            import importlib
            spec = importlib.util.find_spec("crawl4ai")
            return spec is not None
        except (ImportError, ValueError):
            return False
    # Detect mock: real crawl4ai has __version__ and AsyncWebCrawler is a real class
    return hasattr(crawl4ai, "__version__") or (
        hasattr(crawl4ai, "AsyncWebCrawler")
        and not isinstance(crawl4ai.AsyncWebCrawler, type)
        is False  # real class, not MagicMock
    )


def _clear_crawl4ai_mock() -> None:
    """Remove test_fetcher.py mock from sys.modules so real crawl4ai is imported."""
    crawl4ai = sys.modules.get("crawl4ai")
    if crawl4ai is not None and not hasattr(crawl4ai, "__version__"):
        # It's a mock module (no version attribute) — remove it so real one loads
        del sys.modules["crawl4ai"]


# ---------------------------------------------------------------------------
# Test: crawl4ai markdown field access (STATE.md blocker)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_crawl4ai_field_access() -> None:
    """Verify the correct field for accessing markdown content from crawl4ai.

    Validates:
    - result.success is True for a stable Tier 1 page
    - result.markdown is StringCompatibleMarkdown (str subclass) in crawl4ai 0.8.0
    - result.markdown.raw_markdown is a string with length > 1000
    """
    _clear_crawl4ai_mock()
    import asyncio
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

    async def _fetch():
        browser_conf = BrowserConfig(
            browser_type="chromium",
            headless=True,
            use_persistent_context=False,
            verbose=False,
        )
        run_conf = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        async with AsyncWebCrawler(config=browser_conf) as crawler:
            result = await crawler.arun(
                url="https://en.wikipedia.org/wiki/Web_scraping",
                config=run_conf,
            )
        return result

    result = asyncio.run(_fetch())

    assert result.success is True, f"Fetch failed: {result.error_message}"

    # In crawl4ai 0.8.0:
    # result is CrawlResultContainer (proxies success, markdown, etc.)
    # result.markdown is StringCompatibleMarkdown — a str subclass with a
    # .raw_markdown attribute.  isinstance(result.markdown, str) is True.
    # fetcher.py accesses result.markdown.raw_markdown which is the correct path.
    assert isinstance(result.markdown, str), (
        f"result.markdown should be StringCompatibleMarkdown (str subclass), got {type(result.markdown)}"
    )

    # Confirm .raw_markdown attribute exists and contains text
    assert hasattr(result.markdown, "raw_markdown"), (
        "result.markdown must have .raw_markdown attribute for fetcher.py to work"
    )
    content = result.markdown.raw_markdown
    assert isinstance(content, str), (
        f"result.markdown.raw_markdown must be str, got {type(content)}"
    )

    assert len(content) > 1000, (
        f"Expected > 1000 chars from result.markdown.raw_markdown, got {len(content)}"
    )
    print(f"\ncrawl4ai markdown field: 'result.markdown.raw_markdown' — {len(content)} chars")


# ---------------------------------------------------------------------------
# Test: DuckDuckGo HTML scraping (STATE.md blocker)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_ddg_html_scraping() -> None:
    """Validate DuckDuckGo HTML endpoint returns usable search results.

    If this test fails (anti-bot block), the fallback test below
    (test_ddg_library_fallback) must pass instead.
    """
    _clear_crawl4ai_mock()
    import asyncio
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

    async def _fetch():
        browser_conf = BrowserConfig(
            browser_type="chromium",
            headless=True,
            use_persistent_context=False,
            verbose=False,
        )
        run_conf = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        async with AsyncWebCrawler(config=browser_conf) as crawler:
            result = await crawler.arun(
                url="https://html.duckduckgo.com/html/?q=Jonestown+Massacre",
                config=run_conf,
            )
        return result

    result = asyncio.run(_fetch())

    if not result.success:
        pytest.skip(f"DDG HTML fetch failed (likely anti-bot): {result.error_message} — see test_ddg_library_fallback")

    # Get content from appropriate field
    if hasattr(result.markdown, "raw_markdown"):
        content = result.markdown.raw_markdown or ""
    else:
        content = str(result.markdown)

    if len(content) < 500:
        pytest.skip(
            f"DDG HTML returned too little content ({len(content)} chars) — likely anti-bot block"
        )

    assert "Jonestown" in content, (
        f"Expected 'Jonestown' in DDG results but content starts with: {content[:200]}"
    )
    print(f"\nDDG HTML scraping: {len(content)} chars, 'Jonestown' found in content")


@pytest.mark.integration
def test_ddg_library_fallback() -> None:
    """Validate ddgs library returns usable results.

    This is the fallback if HTML endpoint is blocked by anti-bot.
    Note: duckduckgo-search was renamed to ddgs — install with: pip install ddgs
    """
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS  # type: ignore[assignment]
        except ImportError:
            pytest.skip("ddgs not installed — run: pip install ddgs")

    results = list(DDGS().text("Jonestown Massacre", max_results=5))

    assert len(results) >= 3, (
        f"Expected >= 3 results from ddgs, got {len(results)}"
    )
    for r in results:
        assert "href" in r, f"Result missing 'href' key: {r}"
        assert "title" in r, f"Result missing 'title' key: {r}"

    print(f"\nDDGS library fallback: {len(results)} results")
    for r in results[:3]:
        print(f"  - {r['title']}: {r['href']}")
