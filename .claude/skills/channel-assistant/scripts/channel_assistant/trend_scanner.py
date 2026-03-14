"""Trend scanner module for channel assistant.

Provides deterministic data acquisition and processing functions for
trend scanning: YouTube autocomplete scraping, search result parsing,
competitor video convergence queries, analysis.md section management,
and keyword derivation from channel DNA.

Note on rate limiting: callers are responsible for adding delays between
scrape_autocomplete() calls (e.g. time.sleep(random.uniform(0.5, 1.5)))
to avoid hammering the endpoint. Keeping delays outside the function
ensures these functions remain easily testable.
"""

import asyncio
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

from .database import Database

try:
    from crawl4ai import AsyncWebCrawler  # type: ignore
except ImportError:  # pragma: no cover
    AsyncWebCrawler = None  # type: ignore

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

CONTENT_PILLAR_KEYWORDS: list[str] = [
    # Pillar 1: Obscure Historical Crimes
    "historical crimes",
    "obscure crimes",
    "cold case mystery",
    "unsolved murders history",
    # Pillar 2: Cults & Psychological Control
    "cult documentary",
    "cult psychology",
    "religious cult dark history",
    "mind control",
    # Pillar 3: Unsolved Disappearances & Mysteries
    "disappearances unsolved",
    "missing persons mystery",
    "unexplained disappearance",
    # Pillar 4: Institutional Corruption & Cover-ups
    "government cover up documentary",
    "institutional corruption",
    "conspiracy cover up true story",
    # Pillar 5: Dark Web & Internet Underbelly
    "dark web documentary",
    "internet crime",
    "online mystery",
]

_AUTOCOMPLETE_URL = (
    "https://clients1.google.com/complete/search?client=youtube&hl=en&q={keyword}"
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _run_async(coro) -> object:
    """Run an async coroutine synchronously using asyncio.run()."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scrape_autocomplete(keyword: str) -> list[str]:
    """Fetch YouTube autocomplete suggestions for a keyword.

    Uses Google's YouTube autocomplete endpoint (clients1.google.com),
    which returns JSONP. Parses the embedded JSON array and returns the
    list of suggestion strings from data[1].

    Args:
        keyword: Search keyword to get suggestions for.

    Returns:
        List of suggestion strings. Returns empty list on any error.
    """
    url = _AUTOCOMPLETE_URL.format(keyword=urllib.parse.quote(keyword))
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            raw_bytes = resp.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        return []

    try:
        text = raw_bytes.decode("utf-8", errors="replace")
        # JSONP payload: window.google.ac.h([...]) or similar wrapper
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return []
        data = json.loads(match.group(0))
        # data[1] contains the list of suggestion strings
        suggestions = data[1]
        if not isinstance(suggestions, list):
            return []
        # Google returns nested lists: [text, 0, [512]] or plain strings
        result = []
        for item in suggestions:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, list) and item and isinstance(item[0], str):
                result.append(item[0])
        return result
    except (json.JSONDecodeError, IndexError, TypeError):
        return []


async def _fetch_search_html(keyword: str, max_results: int) -> str:
    """Async helper: fetch YouTube search page HTML via crawl4ai."""
    search_url = (
        f"https://www.youtube.com/results?search_query={urllib.parse.quote(keyword)}"
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=search_url)
        return result.html or ""


def scrape_search_results(keyword: str, max_results: int = 20) -> list[dict]:
    """Scrape YouTube search results for a keyword.

    Uses crawl4ai AsyncWebCrawler to render the YouTube search page, then
    extracts ytInitialData from the page HTML. Navigates the JSON path:
      contents > twoColumnSearchResultsRenderer > primaryContents >
      sectionListRenderer > contents[N] > itemSectionRenderer > contents[] >
      videoRenderer

    Args:
        keyword: Search keyword.
        max_results: Maximum number of results to return.

    Returns:
        List of dicts with keys: video_id, title, channel, published_text,
        views_text. Returns empty list on any error or missing data.
    """
    if AsyncWebCrawler is None:
        return []

    try:
        html = _run_async(_fetch_search_html(keyword, max_results))
    except Exception:
        return []

    if not html:
        return []

    # Extract ytInitialData JSON from page source
    match = re.search(r"var ytInitialData\s*=\s*(\{.*?\});\s*(?:var|</script>|$)",
                      html, re.DOTALL)
    if not match:
        # Try more permissive pattern
        match = re.search(r"ytInitialData\s*=\s*(\{.*\})", html, re.DOTALL)
        if not match:
            return []

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []

    try:
        sections = (
            data["contents"]
            ["twoColumnSearchResultsRenderer"]
            ["primaryContents"]
            ["sectionListRenderer"]
            ["contents"]
        )
    except (KeyError, TypeError):
        return []

    videos = []
    for section in sections:
        try:
            items = section["itemSectionRenderer"]["contents"]
        except (KeyError, TypeError):
            continue

        for item in items:
            try:
                renderer = item["videoRenderer"]
            except (KeyError, TypeError):
                continue

            try:
                video_id = renderer.get("videoId", "")
                title = renderer["title"]["runs"][0]["text"]
                channel = renderer["longBylineText"]["runs"][0]["text"]
                published_text = renderer.get("publishedTimeText", {}).get(
                    "simpleText", ""
                )
                views_text = renderer.get("viewCountText", {}).get("simpleText", "")

                videos.append(
                    {
                        "video_id": video_id,
                        "title": title,
                        "channel": channel,
                        "published_text": published_text,
                        "views_text": views_text,
                    }
                )
            except (KeyError, IndexError, TypeError):
                continue

            if len(videos) >= max_results:
                return videos

    return videos


def get_recent_competitor_videos(db: Database, days: int = 30) -> list[dict]:
    """Query SQLite for competitor videos uploaded within the last N days.

    Excludes rows where upload_date IS NULL. Returns newest first.

    Args:
        db: Database instance.
        days: Look-back window in days (default 30).

    Returns:
        List of dicts with keys: title, upload_date, channel_name.
    """
    cutoff = (date.today() - timedelta(days=days)).isoformat()

    conn = db.connect()
    try:
        cursor = conn.execute(
            """
            SELECT v.title, v.upload_date, c.name AS channel_name
            FROM videos v
            JOIN channels c ON v.channel_id = c.youtube_id
            WHERE v.upload_date IS NOT NULL
              AND v.upload_date >= ?
            ORDER BY v.upload_date DESC
            """,
            (cutoff,),
        )
        rows = cursor.fetchall()
        return [
            {
                "title": row["title"],
                "upload_date": row["upload_date"],
                "channel_name": row["channel_name"],
            }
            for row in rows
        ]
    finally:
        conn.close()


def derive_keywords(channel_dna: str, topic_clusters: list[str]) -> list[str]:
    """Derive search keywords from channel DNA content pillars and topic clusters.

    Parses the channel DNA text for the "Core Content Pillars" section and
    extracts pillar names as keywords. Combines with up to 5 topic cluster
    strings. Falls back to CONTENT_PILLAR_KEYWORDS constant if parsing fails.

    Args:
        channel_dna: Full text of channel.md (channel DNA).
        topic_clusters: List of topic cluster strings from competitor analysis.

    Returns:
        Deduplicated list of keyword strings.
    """
    pillar_keywords: list[str] = []

    if channel_dna:
        # Try to extract content pillar names from channel DNA
        # Matches numbered list items like: 1. **Pillar Name** — description
        pillar_pattern = re.compile(
            r"\d+\.\s+\*\*([^*]+)\*\*", re.MULTILINE
        )
        # Also look for section heading variants
        matches = pillar_pattern.findall(channel_dna)
        if matches:
            # Convert pillar names to search-friendly lowercase keywords
            for pillar in matches:
                # Simplify: "Obscure Historical Crimes" -> "obscure historical crimes"
                pillar_keywords.append(pillar.strip().lower())

    # Fall back to module constant if pillar extraction yielded nothing
    if not pillar_keywords:
        pillar_keywords = list(CONTENT_PILLAR_KEYWORDS)

    # Take up to 5 topic clusters
    cluster_sample = list(topic_clusters[:5])

    # Combine and deduplicate while preserving order
    seen: set[str] = set()
    result: list[str] = []
    for kw in pillar_keywords + cluster_sample:
        if kw not in seen:
            seen.add(kw)
            result.append(kw)

    return result


def update_analysis_with_trends(
    analysis_path: Path,
    trending_md: str,
    gaps_md: str,
    convergence_md: str,
) -> None:
    """Append or replace trend sections in analysis.md.

    Reads existing content, strips any existing ## Trending Topics,
    ## Content Gaps, and ## Convergence Alerts sections, then appends
    the new sections. Preserves all Phase 2 content (## Channel Stats,
    ## Outlier Videos, ## Topic Clusters, ## Title Patterns).

    Creates the file if it does not exist.

    Args:
        analysis_path: Path to analysis.md file.
        trending_md: Markdown content for the Trending Topics section.
        gaps_md: Markdown content for the Content Gaps section.
        convergence_md: Markdown content for the Convergence Alerts section.
    """
    analysis_path = Path(analysis_path)

    # Read existing content (empty string if file absent)
    if analysis_path.exists():
        existing = analysis_path.read_text(encoding="utf-8")
    else:
        existing = ""

    # Strip existing trend sections using regex
    # A section starts at "## SectionName" and runs until the next "##" heading or EOF
    _TREND_SECTIONS = [
        "Trending Topics",
        "Content Gaps",
        "Convergence Alerts",
    ]
    pattern = re.compile(
        r"(?m)^## (?:" + "|".join(re.escape(s) for s in _TREND_SECTIONS) + r").*?"
        r"(?=^## |\Z)",
        re.DOTALL | re.MULTILINE,
    )
    cleaned = pattern.sub("", existing)

    # Normalise trailing whitespace
    cleaned = cleaned.rstrip() + "\n" if cleaned.strip() else ""

    # Append new sections
    new_content = (
        cleaned
        + "\n"
        + trending_md.rstrip()
        + "\n\n"
        + gaps_md.rstrip()
        + "\n\n"
        + convergence_md.rstrip()
        + "\n"
    )

    analysis_path.parent.mkdir(parents=True, exist_ok=True)
    analysis_path.write_text(new_content, encoding="utf-8")
