# Phase 5: Trend Scanning + Content Gaps - Research

**Researched:** 2026-03-11
**Domain:** YouTube data scraping (autocomplete, search results), content gap analysis, convergence detection
**Confidence:** HIGH (architecture patterns), MEDIUM (YouTube scraping implementation), LOW (recency-sort availability)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **crawl4ai only** for all YouTube search/autocomplete scraping — no yt-dlp for search (yt-dlp stays for channel metadata in Phase 1)
- Keywords auto-derived from channel DNA content pillars (dark history, cults, unsolved mysteries, institutional corruption, dark web) + Phase 2 topic clusters — no manual keyword list
- Live scrape each run — no caching of autocomplete or search results
- Top 20 search results per keyword — first page of YouTube results
- With ~5-10 auto-derived keywords, expect 100-200 results per scan
- Gap = high autocomplete search demand + low/no competitor coverage + factor in performance of similar topics when covered
- Composite score: demand × opportunity, weighted by how well similar topics performed when competitors DID cover them
- Output as ranked list sorted by composite score
- Gap threshold (how many competitors = "covered") at Claude's discretion based on data patterns
- Gap report auto-injected into `cmd_topics()` context alongside competitor analysis
- Adjacency defined by Phase 2's topic clusters — 3+ competitors in same cluster within 30 days = convergence
- Fixed 30-day window — not configurable
- Cross-reference converging topics with YouTube search trends for stronger signal
- Extend `context/competitors/analysis.md` with new sections: ## Trending Topics, ## Content Gaps, ## Convergence Alerts
- New `trends` CLI subcommand — independent of `analyze`, can be run separately
- Trends command does NOT re-run competitor analysis
- Chat output: print top 3 content gaps and any convergence alerts inline, plus file path for full report

### Claude's Discretion

- Exact crawl4ai scraping implementation (page parsing, request handling)
- Gap threshold (0, 1, or 2 competitors = "underserved")
- Convergence framing (opportunity alert vs saturation warning vs neutral flag)
- How to extract and rank autocomplete volume indicators
- Internal module structure for trend scanning code
- How to merge trend sections into existing analysis.md without overwriting Phase 2 content

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ANLZ-05 | System detects content gaps by comparing search demand (YouTube autocomplete via crawl4ai) against competitor topic coverage | Autocomplete endpoint research; composite scoring design; database query patterns for competitor coverage |
| ANLZ-06 | System surfaces trending topics by scraping YouTube search results for niche keywords sorted by recency | YouTube search URL research; ytInitialData JSON parsing; recency-sort caveat documented |
| ANLZ-07 | System detects cross-channel trend convergence when 3+ competitors cover adjacent topics within a 30-day window | Database query patterns for 30-day window; topic cluster adjacency from Phase 2 heuristics; convergence framing |
</phase_requirements>

---

## Summary

Phase 5 adds a new `trends` CLI subcommand that performs three distinct data acquisition and analysis tasks: scraping YouTube autocomplete for demand signals (ANLZ-05), scraping YouTube search results to surface recently-published competitor-adjacent content (ANLZ-06), and querying the existing SQLite database to detect convergence patterns across competitor channels within a 30-day window (ANLZ-07).

The implementation follows the same `[HEURISTIC]` vs `[DETERMINISTIC]` split used throughout the codebase. crawl4ai handles all YouTube page fetching (deterministic). Claude performs gap scoring, convergence framing, and the ranked output synthesis (heuristic). The `trends` module pattern mirrors `topics.py` and `project_init.py`: pure stdlib Python functions that prepare structured data, then `cmd_trends()` in `cli.py` loads context and hands off to Claude reasoning.

**Critical constraint to plan around:** YouTube removed the native "sort by upload date" search filter in January/February 2026 and the URL-parameter workaround (`&sp=CAI%3D`) has been patched. "Recency" for ANLZ-06 must be implemented by scraping the default YouTube search results page and filtering scraped results by upload date server-side from competitor video data already in SQLite, rather than relying on a YouTube-side sort.

**Primary recommendation:** Build `trend_scanner.py` as a new deterministic module with three public functions: `scrape_autocomplete()`, `scrape_search_results()`, and `detect_convergence()`. Wire them into `cmd_trends()` in `cli.py`. Output goes to `analysis.md` via append-with-section-replacement.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| crawl4ai | 0.8.x (latest) | YouTube page fetching and HTML parsing | Locked decision; already in project stack |
| stdlib sqlite3 | Python 3.14 | Query existing competitor video data for convergence detection | Already established in database.py |
| stdlib json | Python 3.14 | Parse ytInitialData JSON blobs from YouTube pages | Zero deps, already used throughout |
| stdlib re | Python 3.14 | Extract ytInitialData script tag content, parse autocomplete response | Zero deps, already used throughout |
| stdlib datetime | Python 3.14 | 30-day window calculation for convergence detection | Already used in analyzer.py |
| stdlib difflib.SequenceMatcher | Python 3.14 | Match search result titles against competitor video titles for coverage scoring | Already used in topics.py |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| requests | stdlib urllib.request or requests | Autocomplete endpoint HTTP GET | For lightweight non-JS endpoints (autocomplete is JSON, no JS rendering needed) |

**Note on crawl4ai vs requests for autocomplete:** The Google/YouTube autocomplete endpoint (`https://clients1.google.com/complete/search?client=youtube&hl=en&q=QUERY`) returns a text/JSON response without JavaScript rendering. A plain HTTP GET via `urllib.request` (zero deps) is sufficient and faster than launching a browser. crawl4ai should be used only for the YouTube search results page which requires JavaScript rendering to populate `ytInitialData`.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| crawl4ai for search results | requests + BeautifulSoup | BS4 cannot execute JavaScript; ytInitialData requires rendered HTML |
| stdlib urllib for autocomplete | crawl4ai | crawl4ai adds unnecessary overhead for a JSON endpoint |
| Scraping search for recency | sp=CAI%3D URL param | URL param patched as of Feb 2026 — no longer forces chronological sort |

**Installation:**
```bash
# crawl4ai should already be in environment per project stack
pip install crawl4ai
```

---

## Architecture Patterns

### Recommended Project Structure

New file:
```
.claude/skills/channel-assistant/scripts/channel_assistant/
├── trend_scanner.py      # New: autocomplete, search scraping, convergence detection
├── cli.py                # Modified: add cmd_trends(), wire into argparse
├── topics.py             # Modified: load_topic_inputs() extended with gap/trend data
└── analyzer.py           # Unchanged (reuse serialize_videos_for_analysis)
```

New test file:
```
tests/test_channel_assistant/
└── test_trend_scanner.py  # Unit tests for trend_scanner module
```

New prompt file:
```
.claude/skills/channel-assistant/prompts/
└── trends_analysis.md     # Heuristic prompt: score gaps, frame convergence
```

### Pattern 1: Autocomplete Scraping via Hidden JSON Endpoint

**What:** YouTube autocomplete suggestions are available at a Google-served JSON endpoint that requires no JavaScript rendering.

**When to use:** For ANLZ-05 demand signal acquisition — run per keyword, collect all suggestions, count suggestions as proxy for search demand breadth.

**Endpoint:** `https://clients1.google.com/complete/search?client=youtube&hl=en&q={keyword}`

**Response format:** JSONP-like text, e.g.:
```
window.google.ac.h(["cult documentary",[["cult documentary",0],["dark cults history",0],["cult leaders psychology",0],...]])
```

The second element is a list of `[suggestion_string, 0]` pairs.

**Example:**
```python
# Source: reverse-engineered endpoint, verified by serpapi.com/blog/scrape-youtube-autocomplete-results-with-python/
import urllib.request
import json
import re

def scrape_autocomplete(keyword: str) -> list[str]:
    """Fetch YouTube autocomplete suggestions for a keyword."""
    url = f"https://clients1.google.com/complete/search?client=youtube&hl=en&q={urllib.parse.quote(keyword)}"
    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        text = resp.read().decode("utf-8")
    # Response is JSONP: window.google.ac.h([query, [[suggestion, 0], ...]])
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if not match:
        return []
    data = json.loads(match.group(0))
    # data[1] is the suggestions list
    suggestions = [item[0] for item in data[1] if isinstance(item, list) and item]
    return suggestions
```

### Pattern 2: YouTube Search Results Scraping via ytInitialData

**What:** YouTube search pages embed a `ytInitialData` JSON blob in a `<script>` tag. crawl4ai fetches the rendered page; regex extracts the JSON blob; jmespath/dict traversal yields video metadata.

**When to use:** For ANLZ-06 trending topics — fetch first-page results for each keyword, extract video title, upload date, channel name, view count.

**Key path in ytInitialData:**
```
ytInitialData
  -> contents
     -> twoColumnSearchResultsRenderer
        -> primaryContents
           -> sectionListRenderer
              -> contents[0]
                 -> itemSectionRenderer
                    -> contents[]
                       -> videoRenderer (each is a video result)
```

Each `videoRenderer` contains:
- `videoId`: video ID
- `title.runs[0].text`: video title
- `publishedTimeText.simpleText`: human-readable age ("3 days ago", "1 month ago")
- `shortViewCountText.simpleText`: "1.2M views"
- `ownerText.runs[0].text`: channel name

**Example:**
```python
# Source: scrapfly.io/blog/posts/how-to-scrape-youtube (verified approach)
import re
import json
from crawl4ai import AsyncWebCrawler

async def scrape_search_results(keyword: str, max_results: int = 20) -> list[dict]:
    """Scrape YouTube search result page for a keyword."""
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(keyword)}"
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)

    html = result.html
    match = re.search(r'var ytInitialData = ({.*?});</script>', html, re.DOTALL)
    if not match:
        return []

    data = json.loads(match.group(1))
    # Navigate to videoRenderer items
    try:
        section = data["contents"]["twoColumnSearchResultsRenderer"][
            "primaryContents"]["sectionListRenderer"]["contents"]
    except (KeyError, IndexError):
        return []

    videos = []
    for item in section:
        for renderer in item.get("itemSectionRenderer", {}).get("contents", []):
            vr = renderer.get("videoRenderer", {})
            if not vr:
                continue
            videos.append({
                "video_id": vr.get("videoId", ""),
                "title": vr.get("title", {}).get("runs", [{}])[0].get("text", ""),
                "channel": vr.get("ownerText", {}).get("runs", [{}])[0].get("text", ""),
                "published_text": vr.get("publishedTimeText", {}).get("simpleText", ""),
                "views_text": vr.get("shortViewCountText", {}).get("simpleText", ""),
            })
            if len(videos) >= max_results:
                break
    return videos
```

**Note on recency:** YouTube removed the native upload-date sort in January 2026 and the `sp=CAI%3D` workaround was patched in February 2026. Default search results are algorithm-ranked. "Recency" for ANLZ-06 is implemented by: (1) parsing `publishedTimeText` from scraped results to estimate age, and (2) cross-referencing titles against the SQLite competitor video database to identify videos uploaded within the last 30 days by channels we track.

### Pattern 3: Convergence Detection via SQLite

**What:** Pure database query — no scraping needed. Query existing `videos` table for all competitor uploads within the last 30 days, group by Phase 2 topic cluster adjacency, count per cluster.

**When to use:** For ANLZ-07 — runs entirely against cached database data, no network calls.

**Example:**
```python
# Source: derived from existing database.py patterns
from datetime import datetime, timedelta, timezone

def detect_convergence(db: Database, cluster_map: dict[str, str]) -> list[dict]:
    """Find topic clusters where 3+ competitors published within 30 days.

    cluster_map: {video_title_keyword -> cluster_name} derived from Phase 2 analysis.md
    Returns list of convergence dicts: {cluster, channels, video_count, video_titles}
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")

    # Get all videos from last 30 days
    conn = db.connect()
    cursor = conn.execute(
        "SELECT v.title, v.upload_date, c.name as channel_name "
        "FROM videos v JOIN channels c ON v.channel_id = c.youtube_id "
        "WHERE v.upload_date >= ?",
        (cutoff,)
    )
    recent_videos = cursor.fetchall()
    conn.close()

    # Group by cluster using SequenceMatcher keyword matching
    # ... heuristic cluster assignment passed to Claude for framing
    return recent_videos  # Claude does the grouping/framing
```

### Pattern 4: Appending Trend Sections to analysis.md

**What:** Read existing `analysis.md`, check if trend sections already exist, replace or append new sections without touching Phase 2 content.

**When to use:** Every `trends` run — overwrite only the three trend sections.

```python
def update_analysis_with_trends(
    analysis_path: Path,
    trending_md: str,
    gaps_md: str,
    convergence_md: str,
) -> None:
    """Append or replace trend sections in analysis.md."""
    content = analysis_path.read_text(encoding="utf-8") if analysis_path.exists() else ""

    # Remove existing trend sections if present
    for section_header in ["## Trending Topics", "## Content Gaps", "## Convergence Alerts"]:
        # Truncate from header to next ## or end of file
        pattern = re.compile(rf"^{re.escape(section_header)}.*?(?=^## |\Z)", re.MULTILINE | re.DOTALL)
        content = pattern.sub("", content)

    content = content.rstrip() + "\n\n"
    content += trending_md + "\n\n"
    content += gaps_md + "\n\n"
    content += convergence_md + "\n"

    analysis_path.write_text(content, encoding="utf-8")
```

### Pattern 5: cmd_trends() — Context Loader + Heuristic Handoff

**What:** Mirror of `cmd_topics()` — deterministic data loading, then Claude handles all scoring and framing.

**Structure:**
1. `[DETERMINISTIC]` Derive keywords from `channel.md` content pillars
2. `[DETERMINISTIC]` `scrape_autocomplete()` per keyword
3. `[DETERMINISTIC]` `scrape_search_results()` per keyword
4. `[DETERMINISTIC]` `detect_convergence()` from SQLite
5. Print structured context to stdout
6. `[HEURISTIC]` Claude scores gaps, frames convergence, selects top 3
7. `[DETERMINISTIC]` `update_analysis_with_trends()` writes to analysis.md

**The prompt file `trends_analysis.md`** is what Claude reads to perform steps 6-7. It receives:
- Raw autocomplete suggestions per keyword
- Search result titles per keyword
- Competitor coverage counts per cluster (from database)
- Recent videos (30-day window) with channel attribution

### Anti-Patterns to Avoid

- **Using sp=CAI%3D for recency sort:** This URL parameter was patched in February 2026 and no longer forces chronological order. Do not rely on it.
- **Importing crawl4ai synchronously:** crawl4ai v0.8.x uses async/await (`AsyncWebCrawler`). Wrap async calls in `asyncio.run()` when calling from synchronous CLI code.
- **Caching search/autocomplete results:** Locked decision — live scrape every run. No TTL or cache layer.
- **Building custom gap scoring in Python:** Scoring is heuristic — Claude weights demand × opportunity based on context. The Python layer only counts competitor coverage hits.
- **Calling LLM APIs from Python code:** Architecture Rule 1 — zero LLM API wrappers. All heuristic reasoning is Claude's native runtime.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YouTube autocomplete fetching | Custom HTTP + parser | `urllib.request` + regex on known endpoint format | Endpoint is stable JSON, a browser isn't needed |
| YouTube search page JavaScript rendering | requests + BeautifulSoup | crawl4ai `AsyncWebCrawler` | BeautifulSoup cannot execute JS; ytInitialData requires rendered page |
| Topic cluster adjacency definition | New clustering algorithm | Reuse Phase 2 `analysis.md` topic clusters (already heuristically defined) | Clusters already exist; re-deriving them wastes a Claude call |
| Competitor coverage counting | Fuzzy NLP matching library | stdlib `SequenceMatcher` (already used in topics.py) | Same pattern already in codebase, zero new deps |
| Date arithmetic for 30-day window | Custom date library | stdlib `datetime` + `timedelta` | Already used in analyzer.py |

**Key insight:** All complexity in this phase is in the data acquisition (crawl4ai) and in Claude's heuristic scoring. The Python code is plumbing — fetch, parse, count, write.

---

## Common Pitfalls

### Pitfall 1: YouTube Search Sort by Date is Gone

**What goes wrong:** Scraping `youtube.com/results?search_query=X&sp=CAI%3D` returns algorithm-ranked results, not chronological ones. Any code that assumes this URL param produces recency-sorted output will yield misleading "trends."

**Why it happens:** YouTube removed the upload-date sort filter in January 2026 (cited as part of a search filter overhaul). The URL workaround was explicitly patched in February 2026.

**How to avoid:** Do not use `sp=CAI%3D`. Instead: parse `publishedTimeText` from scraped results to estimate recency, then cross-reference with competitor video data in SQLite (upload_date column) to confirm actual recency. "Trending" in ANLZ-06 context means "recently published by channels in our niche" not "YouTube-certified trending."

**Warning signs:** If all scraped results appear well-distributed over many months rather than clustering in the last week, the sort is algorithm-based. Check for this in tests.

### Pitfall 2: ytInitialData JSON Path is Fragile

**What goes wrong:** YouTube periodically restructures the nested JSON path inside `ytInitialData`. Code using hardcoded key chains (`["contents"]["twoColumnSearchResultsRenderer"]...`) breaks silently when YouTube pushes a frontend update.

**Why it happens:** `ytInitialData` is an internal frontend data structure, not a public API. YouTube can change it at any time.

**How to avoid:** Write `scrape_search_results()` with a try/except around the full JSON traversal and log a warning when the expected path is missing. Return an empty list rather than raising. The trends command should degrade gracefully — a failed scrape for one keyword should not abort the full run.

**Warning signs:** `scrape_search_results()` returns empty lists for all keywords. Check raw HTML for `ytInitialData` presence first.

### Pitfall 3: crawl4ai Async/Sync Mismatch

**What goes wrong:** `AsyncWebCrawler.arun()` is a coroutine. Calling it from synchronous `cmd_trends()` without `asyncio.run()` raises `RuntimeError: coroutine was never awaited`.

**Why it happens:** crawl4ai v0.8.x is fully async-native.

**How to avoid:** Wrap all async crawl4ai calls in `asyncio.run()` at the boundary between sync CLI code and async scraping code. A thin `_run_async(coro)` helper in `trend_scanner.py` keeps this clean.

```python
import asyncio

def _run_async(coro):
    """Run a coroutine synchronously."""
    return asyncio.run(coro)
```

### Pitfall 4: Autocomplete Response Format Variability

**What goes wrong:** The `clients1.google.com/complete/search` endpoint returns JSONP-style text. Parsing it with `json.loads()` directly fails because of the `window.google.ac.h(...)` wrapper.

**Why it happens:** The endpoint was not designed as a public API. The wrapper function name can vary.

**How to avoid:** Use `re.search(r'\[.*\]', text, re.DOTALL)` to extract the raw JSON array, then parse that. Tested pattern: `data[1]` contains `[[suggestion_str, 0], ...]`.

### Pitfall 5: topics.py load_topic_inputs() Must be Extended, Not Replaced

**What goes wrong:** Creating a separate `load_trend_inputs()` function and not injecting it into the existing `load_topic_inputs()` flow means Claude's topic generation prompt never sees gap data — ANLZ-05's downstream value (gap-aware topic generation) is lost.

**Why it happens:** The integration point is `topics.py:load_topic_inputs()` returning a dict that `cmd_topics()` prints to stdout. If trend data isn't in that dict, it isn't in the topic generation context.

**How to avoid:** Add `"trends": str` and `"content_gaps": str` keys to the dict returned by `load_topic_inputs()`. These should be loaded from `analysis.md`'s trend sections (already written by `trends` command). Graceful degradation: if trend sections are absent (user hasn't run `trends` yet), return empty strings, do not raise.

### Pitfall 6: 30-Day Window Calculation at Month Boundaries

**What goes wrong:** String comparison `upload_date >= cutoff` works correctly for YYYY-MM-DD format but only if the date strings are well-formed. The database stores dates as `YYYY-MM-DD` from Phase 1 scraping, but some yt-dlp entries return `None` for upload_date (nullable column).

**Why it happens:** upload_date is nullable in the videos schema.

**How to avoid:** Filter `WHERE upload_date IS NOT NULL AND upload_date >= ?` in the convergence SQL query.

---

## Code Examples

### Keyword Derivation from channel.md

```python
# Source: derived from existing topics.py pattern for channel_dna loading
CONTENT_PILLAR_KEYWORDS = [
    "obscure historical crimes",
    "cults documentary",
    "unsolved disappearances mystery",
    "institutional corruption cover-up",
    "dark web crimes",
]

def derive_keywords(channel_dna: str, topic_clusters: list[str]) -> list[str]:
    """Derive search keywords from content pillars + topic clusters.

    Falls back to hardcoded pillars if channel.md parsing fails.
    Combines up to 5 pillar keywords + up to 5 cluster keywords.
    """
    # Extract pillar section from channel.md
    # ... return combined list, deduplicated
    return CONTENT_PILLAR_KEYWORDS  # floor fallback
```

### asyncio.run() Wrapper for CLI Boundary

```python
# Source: Python stdlib asyncio docs
import asyncio

def _run_async(coro):
    """Execute a coroutine synchronously. Used at CLI/async boundary."""
    return asyncio.run(coro)

# In cmd_trends():
results = _run_async(scrape_search_results(keyword))
```

### 30-Day Competitor Video Query

```python
# Source: derived from database.py patterns
from datetime import datetime, timedelta, timezone

def get_recent_competitor_videos(db: Database, days: int = 30) -> list[dict]:
    """Return all competitor videos uploaded within the last N days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    conn = db.connect()
    try:
        cursor = conn.execute(
            "SELECT v.title, v.upload_date, c.name AS channel_name "
            "FROM videos v "
            "JOIN channels c ON v.channel_id = c.youtube_id "
            "WHERE v.upload_date IS NOT NULL AND v.upload_date >= ? "
            "ORDER BY v.upload_date DESC",
            (cutoff,)
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
```

### Section Replacement in analysis.md

```python
# Source: derived from existing cmd_analyze() write pattern
import re
from pathlib import Path

TREND_SECTIONS = ["## Trending Topics", "## Content Gaps", "## Convergence Alerts"]

def _strip_trend_sections(content: str) -> str:
    """Remove existing trend sections to allow clean replacement."""
    for header in TREND_SECTIONS:
        pattern = re.compile(
            rf"^{re.escape(header)}.*?(?=^## |\Z)",
            re.MULTILINE | re.DOTALL
        )
        content = pattern.sub("", content)
    return content.rstrip()
```

### argparse Subcommand Registration

```python
# Source: derived from existing cli.py argparse pattern
# In main():
trends_parser = subparsers.add_parser(
    "trends",
    help="Scan YouTube trends and detect content gaps"
)
# No arguments — keywords are auto-derived

# In dispatch block:
elif args.command == "trends":
    cmd_trends(args, db, root)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `sp=CAI%3D` URL param for date sort | Parse publishedTimeText + SQLite cross-reference | Feb 2026 (patched by YouTube) | Must implement recency differently — no server-side sort available |
| YouTube Data API v3 for search | ytInitialData parsing or yt-dlp | Ongoing architectural decision | No API key needed; yt-dlp covers channel scraping; crawl4ai for search |
| Dedicated keyword research tools | Autocomplete endpoint scraping | N/A | Free, no API key, sufficient signal for editorial decisions |

**Deprecated/outdated:**
- `sp=CAI%3D` sort parameter: Patched Feb 2026. Do not use.
- YouTube Data API v3: Out of scope per REQUIREMENTS.md "Out of Scope" table.

---

## Open Questions

1. **crawl4ai JavaScript rendering for YouTube search**
   - What we know: crawl4ai v0.8.x uses Playwright-based browser under the hood; `AsyncWebCrawler` should render JS
   - What's unclear: Whether YouTube's anti-bot detection blocks headless Playwright without special headers/stealth; whether crawl4ai's built-in stealth mode is sufficient
   - Recommendation: In the implementation task, test with a single keyword first. If blocked, use `crawl4ai`'s `BrowserConfig` with `user_agent` override. Fallback: `requests` + custom User-Agent header for the raw HTML (YouTube search HTML may partially render without JS for basic results).

2. **Autocomplete endpoint stability**
   - What we know: `clients1.google.com/complete/search?client=youtube` has been used for years; serpapi.com documented it as of 2025
   - What's unclear: Whether Google has rate limits or CAPTCHA triggers for rapid automated requests
   - Recommendation: Add 1-2 second jittered delay between keyword autocomplete fetches, matching the existing `scraper.py` rate-limiting pattern.

3. **Phase 2 topic clusters format for convergence adjacency**
   - What we know: Topic clusters are written to `analysis.md` as a `## Topic Clusters` heuristic section by Claude after `cmd_analyze()`; they are markdown text, not structured JSON
   - What's unclear: The exact format Claude produces — is it parseable as a list of cluster names + associated keywords?
   - Recommendation: The convergence detection heuristic prompt should ask Claude to read both the `## Topic Clusters` section of `analysis.md` AND the 30-day recent videos list and determine cluster membership inline, rather than pre-parsing cluster data in Python. This avoids brittle markdown parsing.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (exists — `pytest.ini` at project root) |
| Config file | `pytest.ini` (pythonpath = .claude/skills/channel-assistant/scripts, testpaths = tests) |
| Quick run command | `pytest tests/test_channel_assistant/test_trend_scanner.py -x` |
| Full suite command | `pytest tests/` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ANLZ-05 | `scrape_autocomplete()` returns list of suggestion strings | unit | `pytest tests/test_channel_assistant/test_trend_scanner.py::TestScrapeAutocomplete -x` | Wave 0 |
| ANLZ-05 | `scrape_autocomplete()` handles JSONP wrapper parsing | unit | `pytest tests/test_channel_assistant/test_trend_scanner.py::TestScrapeAutocomplete::test_jsonp_parsing -x` | Wave 0 |
| ANLZ-05 | Competitor coverage count per keyword from SQLite | unit | `pytest tests/test_channel_assistant/test_trend_scanner.py::TestCoverageCount -x` | Wave 0 |
| ANLZ-06 | `scrape_search_results()` parses ytInitialData video list | unit | `pytest tests/test_channel_assistant/test_trend_scanner.py::TestScrapeSearchResults -x` | Wave 0 |
| ANLZ-06 | `scrape_search_results()` returns empty list gracefully when ytInitialData path missing | unit | `pytest tests/test_channel_assistant/test_trend_scanner.py::TestScrapeSearchResults::test_missing_path_returns_empty -x` | Wave 0 |
| ANLZ-07 | `get_recent_competitor_videos()` filters correctly by 30-day cutoff | unit | `pytest tests/test_channel_assistant/test_trend_scanner.py::TestConvergenceDetection -x` | Wave 0 |
| ANLZ-07 | `get_recent_competitor_videos()` excludes NULL upload_date rows | unit | `pytest tests/test_channel_assistant/test_trend_scanner.py::TestConvergenceDetection::test_null_dates_excluded -x` | Wave 0 |
| All | `update_analysis_with_trends()` replaces existing sections without corrupting Phase 2 content | unit | `pytest tests/test_channel_assistant/test_trend_scanner.py::TestUpdateAnalysis -x` | Wave 0 |
| All | `cmd_trends` wired in argparse and reachable | smoke | `pytest tests/test_channel_assistant/test_trend_scanner.py::test_cmd_trends_registered -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_channel_assistant/test_trend_scanner.py -x`
- **Per wave merge:** `pytest tests/`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_channel_assistant/test_trend_scanner.py` — covers all ANLZ-05, ANLZ-06, ANLZ-07 tests listed above
- [ ] All crawl4ai calls should be mocked (patch `channel_assistant.trend_scanner.AsyncWebCrawler`) — no live network in tests
- [ ] All urllib calls should be mocked (patch `channel_assistant.trend_scanner.urllib.request.urlopen`)

---

## Sources

### Primary (HIGH confidence)
- Existing codebase (`cli.py`, `scraper.py`, `analyzer.py`, `topics.py`, `database.py`) — integration patterns, argparse structure, database query conventions, rate-limiting approach
- `pytest.ini` + `tests/` directory — test framework confirmed, pythonpath confirmed

### Secondary (MEDIUM confidence)
- [scrapfly.io - How to Scrape YouTube in 2026](https://scrapfly.io/blog/posts/how-to-scrape-youtube) — ytInitialData JSON path and structure verified
- [serpapi.com - Scrape YouTube Autocomplete Results](https://serpapi.com/blog/scrape-youtube-autocomplete-results-with-python/) — `clients1.google.com/complete/search` endpoint confirmed
- [serpapi.com - YouTube sp Filters](https://serpapi.com/blog/youtube-sp-filters-paginating-sorting-and-filtering-with-the-youtube-api/) — sp parameter values documented

### Tertiary (LOW confidence — flagged)
- [piunikaweb.com - YouTube search filters removed](https://piunikaweb.com/2026/02/05/youtube-search-filters-missing-url-parameters-workaround/) — sp=CAI%3D patched Feb 2026; single source but corroborated by community reports and GitHub issue trackers. **Treat recency-sort as unavailable until implementation test proves otherwise.**
- [crawl4ai docs v0.8.x](https://docs.crawl4ai.com/) — AsyncWebCrawler API confirmed; stealth mode effectiveness against YouTube not verified in testing

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in project or stdlib; locked by CONTEXT.md decisions
- Architecture: HIGH — follows established codebase patterns exactly; new module mirrors existing modules
- Pitfalls: MEDIUM — YouTube scraping pitfalls well-documented; sp=CAI%3D caveat from single source but corroborated
- Recency sort availability: LOW — confirmed patched Feb 2026 but may change; implementation must be resilient

**Research date:** 2026-03-11
**Valid until:** 2026-04-11 (YouTube frontend changes fast; re-verify ytInitialData path before implementation if >2 weeks delay)
