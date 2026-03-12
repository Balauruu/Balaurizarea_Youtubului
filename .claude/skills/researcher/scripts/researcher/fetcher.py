"""crawl4ai wrapper with domain-isolated browser contexts, retry logic,
and minimum content length validation.

Design decisions:
- Fresh AsyncWebCrawler context per fetch call — no session_id reuse across domains
- BrowserConfig(use_persistent_context=False) prevents cookie/session leakage
- CrawlerRunConfig(cache_mode=CacheMode.BYPASS) prevents stale cache contamination
- A fetch returning < MIN_CONTENT_CHARS triggers retry (anti-bot soft-block detection)
- Tier 3 URLs are skipped before any fetch attempt and logged as skipped_tier3

crawl4ai imports are deferred to function level so this module can be imported
and tested without crawl4ai installed (tests mock at the module level).
"""
import asyncio
import logging
import time

from researcher.tiers import classify_domain, TIER_RETRY_MAP

logger = logging.getLogger(__name__)

# SCRP-02: minimum content threshold. Raise to 500 if 200 proves noisy in Phase 8.
MIN_CONTENT_CHARS: int = 200


def _get_browser_conf():
    """Return a BrowserConfig instance. Deferred import for testability."""
    from crawl4ai import BrowserConfig  # noqa: PLC0415
    return BrowserConfig(
        browser_type="chromium",
        headless=True,
        use_persistent_context=False,  # no cookie/session persistence
        verbose=False,
    )


async def _fetch_once(url: str) -> tuple[bool, str, str]:
    """Single fetch attempt using a fresh browser context.

    Returns:
        (success, markdown_text, error_message)
    """
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode  # noqa: PLC0415

    browser_conf = BrowserConfig(
        browser_type="chromium",
        headless=True,
        use_persistent_context=False,
        verbose=False,
    )
    run_conf = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(url=url, config=run_conf)
    if result.success:
        text = result.markdown.raw_markdown or ""
        return True, text, ""
    return False, "", result.error_message or "unknown error"


def fetch_url(url: str) -> tuple[bool, str, str]:
    """Sync wrapper around _fetch_once. Runs the async fetch in a new event loop.

    Returns:
        (success, markdown_text, error_message)
    """
    return asyncio.run(_fetch_once(url))


def fetch_with_retry(
    url: str,
    max_attempts: int = 3,
    delay_seconds: float = 5.0,
) -> dict:
    """Fetch a URL with retry logic and content validation.

    Tier 3 URLs are skipped immediately (no fetch attempt).
    Unknown domains default to Tier 2 (1 retry).
    TIER_RETRY_MAP overrides max_attempts based on domain tier.

    Args:
        url: The URL to fetch.
        max_attempts: Maximum attempts (overridden by TIER_RETRY_MAP).
        delay_seconds: Base delay between retries (progressive: delay * attempt).

    Returns:
        dict with keys:
            success (bool): True if fetch succeeded with sufficient content.
            content (str): Fetched markdown text (empty on failure).
            error (str): Error description (empty on success).
            fetch_status (str): "ok" | "failed" | "skipped_tier3"
            attempts_used (int): Number of fetch attempts made.
    """
    tier = classify_domain(url)

    # Tier 3: skip entirely without fetching
    if tier == 3:
        logger.info("skipped tier3 url: %s", url)
        return {
            "success": False,
            "content": "",
            "error": "tier 3 domain skipped",
            "fetch_status": "skipped_tier3",
            "attempts_used": 0,
        }

    # TIER_RETRY_MAP controls effective retry count per tier
    effective_attempts = TIER_RETRY_MAP.get(tier, 1)

    last_error = ""
    for attempt in range(1, effective_attempts + 1):
        ok, text, err = fetch_url(url)
        if ok and len(text) >= MIN_CONTENT_CHARS:
            return {
                "success": True,
                "content": text,
                "error": "",
                "fetch_status": "ok",
                "attempts_used": attempt,
            }
        if ok and len(text) < MIN_CONTENT_CHARS:
            last_error = f"content too short ({len(text)} chars)"
        else:
            last_error = err or "unknown error"
        logger.warning(
            "fetch attempt %d/%d failed for %s: %s",
            attempt,
            effective_attempts,
            url,
            last_error,
        )
        if attempt < effective_attempts:
            time.sleep(delay_seconds * attempt)  # progressive delay: 5s, 10s, ...

    return {
        "success": False,
        "content": "",
        "error": last_error,
        "fetch_status": "failed",
        "attempts_used": effective_attempts,
    }
