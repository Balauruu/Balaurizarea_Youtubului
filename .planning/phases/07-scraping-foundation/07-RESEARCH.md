# Phase 7: Scraping Foundation - Research

**Researched:** 2026-03-12
**Domain:** crawl4ai web scraping, domain isolation, source tiering, CLI project resolution
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- New skill directory: `.claude/skills/researcher/` with SKILL.md, scripts/researcher/, and prompts/
- CLI pattern: `PYTHONPATH=.claude/skills/researcher/scripts python -m researcher <subcommand>`
- Subcommands planned: `survey` (Pass 1), `deepen` (Pass 2), `write` (dossier output)
- crawl4ai-scraper skill remains as standalone one-off URL scraper — different use case
- Fresh implementation — do NOT import from channel-assistant's trend_scanner.py
- Python constants in a tiers.py module (not JSON config)
- Three tiers: tier_1 (reliable, 3 retries), tier_2 (attempt, 1 retry), tier_3 (do-not-attempt, skip and log)
- Unknown domains default to Tier 2 behavior
- DuckDuckGo HTML scraping via crawl4ai as primary search engine — needs validation testing in this phase
- Output: one .json file per scraped URL (`src_001.json`, `src_002.json`, etc.) with metadata + content field
- Separate `source_manifest.json` as lightweight index (no content)
- Clean `.claude/scratch/researcher/` at start of each new survey run
- Topic provided as CLI string: `python -m researcher survey "Jonestown Massacre"`
- Fuzzy case-insensitive substring match against `projects/N. [Title]/` directories
- Multiple matches: error and list them. Zero matches: standalone mode
- Standalone mode: output to `.claude/scratch/researcher/` only
- Auto-create `projects/N. [Title]/research/` if project dir exists but research/ doesn't

### Claude's Discretion
- Domain-only vs domain+path tier matching — pick what's practical
- Minimum content length threshold (SCRP-02 says >200 chars, Claude can raise if testing shows 200 is too noisy)
- Exact tier domain lists — populate based on research use cases

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCRP-01 | Agent can scrape web pages using crawl4ai with domain-isolated browser contexts | crawl4ai 0.8 `session_id` + `CacheMode.BYPASS` pattern; each arun() call without session_id gets independent context |
| SCRP-02 | Agent retries failed fetches and validates minimum content length (>200 chars) per response | `result.success` + `len(result.markdown.raw_markdown)` check; retry loop with progressive delay adapted from channel-assistant scraper.py |
| SCRP-03 | Agent categorizes sources into access tiers before scraping | `tiers.py` module with domain-keyed dict; classify before any request; Tier 3 logged and skipped |
| RSRCH-01 | Agent accepts a manual topic input and locates the corresponding project directory | `projects/` dir scan with case-insensitive substring match; pattern from `project_init.py` and `_get_project_root()` in cli.py |
</phase_requirements>

---

## Summary

Phase 7 builds the scraping foundation for Agent 1.2 (The Researcher). It delivers two modules — `fetcher.py` and `url_builder.py` — plus a `tiers.py` constants file, all inside a new `.claude/skills/researcher/` skill. The phase also validates whether DuckDuckGo HTML scraping via crawl4ai is viable before Phase 8 depends on it.

**Key finding:** crawl4ai 0.8 is available (pip shows 0.8.0 as latest). The result object uses `result.markdown.raw_markdown` to get text content (not `result.markdown` directly as a string). Domain isolation is achieved by not reusing `session_id` across arun() calls — each call without a session_id gets a fresh browser context. `BrowserConfig(use_persistent_context=False)` with `CrawlerRunConfig(cache_mode=CacheMode.BYPASS)` is the correct combination for clean per-domain fetches.

**DuckDuckGo validation concern (from STATE.md):** DuckDuckGo's HTML endpoint (`https://html.duckduckgo.com/html/?q=...`) is a static no-JS page, which crawl4ai handles without issue. The standard `duckduckgo-search` Python library (v8.1.1) is an alternative if crawl4ai scraping of DDG proves unreliable — it requires no browser and has no anti-bot issues. Phase 7 must test both approaches and pick one.

**Primary recommendation:** Use `AsyncWebCrawler(config=BrowserConfig(use_persistent_context=False))` with a new `CrawlerRunConfig(cache_mode=CacheMode.BYPASS)` per arun() call. Do not reuse session_id across domains. Wrap each call in `asyncio.run()` via a sync wrapper (matching channel-assistant's `_run_async` pattern) so the CLI stays synchronous.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| crawl4ai | 0.8.0 | Browser-based web scraping to markdown | Already used in project (crawl4ai-scraper skill, trend_scanner.py); handles JS-rendered pages |
| playwright | (installed by crawl4ai-setup) | Headless browser backend | Required by crawl4ai; Chromium via `crawl4ai-setup` |
| Python stdlib (asyncio, pathlib, json, argparse, re) | 3.14 | Async wrapper, file I/O, CLI | stdlib-only policy for non-scraping modules |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| duckduckgo-search | 8.1.1 | Programmatic DDG search without browser | If crawl4ai DDG HTML scraping fails anti-bot; DDGS().text() returns structured JSON |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| crawl4ai AsyncWebCrawler | requests + BeautifulSoup | BS4 can't handle JS-rendered pages (archive.org, many news sites) |
| duckduckgo-search library | crawl4ai scraping html.duckduckgo.com | DDG library requires no browser but adds a dependency; crawl4ai approach reuses existing infra |

**Installation:**
```bash
pip install crawl4ai==0.8.0
crawl4ai-setup   # installs ~300MB Playwright browser binaries — run once
# Optional fallback:
pip install duckduckgo-search
```

**CRITICAL:** Do NOT install `crawl4ai[torch]` or `crawl4ai[transformer]` — violates Architecture.md Rule 1 (no LLM SDK wrappers).

---

## Architecture Patterns

### Recommended Skill Structure
```
.claude/skills/researcher/
├── SKILL.md                        # Skill index
├── scripts/
│   └── researcher/
│       ├── __init__.py
│       ├── __main__.py             # python -m researcher entry point
│       ├── cli.py                  # CLI: survey/deepen/write subcommands
│       ├── fetcher.py              # crawl4ai wrapper (SCRP-01, SCRP-02)
│       ├── tiers.py                # source tier constants (SCRP-03)
│       └── url_builder.py          # URL construction + project resolution (RSRCH-01)
└── prompts/
    └── (placeholder — Phase 8+ fills these)
```

### Pattern 1: Domain-Isolated Fetching

**What:** Each arun() call uses a fresh browser context. No session_id reuse across different domains. BrowserConfig is created once per fetcher session; CrawlerRunConfig is created fresh per call with BYPASS cache to prevent contamination from previous visits.

**When to use:** Every fetch in fetcher.py — all calls are domain-isolated by default.

```python
# Source: https://docs.crawl4ai.com/core/quickstart/ + SDK reference
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

_browser_conf = BrowserConfig(
    browser_type="chromium",
    headless=True,
    use_persistent_context=False,   # no cookie/session persistence
    verbose=False,
)

async def _fetch_once(url: str) -> tuple[bool, str, str]:
    """Single fetch attempt. Returns (success, markdown_text, error_message)."""
    run_conf = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(config=_browser_conf) as crawler:
        result = await crawler.arun(url=url, config=run_conf)
    if result.success:
        text = result.markdown.raw_markdown or ""
        return True, text, ""
    return False, "", result.error_message or "unknown error"

def fetch_url(url: str) -> tuple[bool, str, str]:
    """Sync wrapper — called by CLI (synchronous context)."""
    return asyncio.run(_fetch_once(url))
```

**Domain isolation mechanism:** `use_persistent_context=False` prevents any cookies/storage from persisting. Each `async with AsyncWebCrawler(...)` instantiation starts a fresh browser process — opening a new context block per call ensures no shared state between domains.

### Pattern 2: Retry with Content Validation (SCRP-02)

**What:** Wrap the fetch in a retry loop. Check both `result.success` AND minimum content length. A "successful" fetch with < threshold characters is treated as a failed fetch (anti-bot soft-block detection).

**When to use:** Every fetch call in fetcher.py goes through this wrapper.

```python
# Adapted from channel-assistant's _run_ytdlp() pattern
import time
import logging

MIN_CONTENT_CHARS = 200   # SCRP-02 minimum; raise to 500 if 200 proves noisy

logger = logging.getLogger(__name__)

def fetch_with_retry(url: str, max_attempts: int, delay_seconds: float) -> dict:
    """Fetch url with retry and content validation.

    Returns a result dict: {success, content, error, attempts_used}
    """
    last_error = ""
    for attempt in range(1, max_attempts + 1):
        ok, text, err = fetch_url(url)
        if ok and len(text) >= MIN_CONTENT_CHARS:
            return {"success": True, "content": text, "error": "", "attempts_used": attempt}
        if ok and len(text) < MIN_CONTENT_CHARS:
            last_error = f"content too short ({len(text)} chars)"
        else:
            last_error = err
        logger.warning("fetch attempt %d/%d failed for %s: %s", attempt, max_attempts, url, last_error)
        if attempt < max_attempts:
            time.sleep(delay_seconds * attempt)   # progressive delay

    return {"success": False, "content": "", "error": last_error, "attempts_used": max_attempts}
```

### Pattern 3: Source Tier Classification (SCRP-03)

**What:** A `tiers.py` constants module maps domain names to tier levels. Classification happens before any request. Tier 3 domains are logged as do-not-attempt and skipped entirely.

**When to use:** Call `classify_domain(url)` in url_builder.py before passing URLs to fetcher.py.

```python
# tiers.py — Python constants, not JSON config (user decision)
from urllib.parse import urlparse

TIER_1_DOMAINS: frozenset[str] = frozenset({
    "archive.org",
    "loc.gov",
    "archives.gov",
    "commons.wikimedia.org",
    "en.wikipedia.org",
    "images.nasa.gov",
    "nps.gov",
    "nationalarchives.gov.uk",
    "publicdomainreview.org",
})

TIER_2_DOMAINS: frozenset[str] = frozenset({
    "britannica.com",
    "bbc.com",
    "theguardian.com",
    "nytimes.com",
    "reuters.com",
    "apnews.com",
    "html.duckduckgo.com",
    "duckduckgo.com",
})

TIER_3_DOMAINS: frozenset[str] = frozenset({
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "tiktok.com",
    "reddit.com",    # frequently blocks scrapers
    "pinterest.com",
})

TIER_RETRY_MAP: dict[int, int] = {1: 3, 2: 1, 3: 0}

def classify_domain(url: str) -> int:
    """Return tier (1, 2, or 3) for a URL. Unknown domains default to 2."""
    host = urlparse(url).hostname or ""
    # strip www. prefix for matching
    host = host.removeprefix("www.")
    if host in TIER_1_DOMAINS:
        return 1
    if host in TIER_3_DOMAINS:
        return 3
    return 2   # unknown defaults to Tier 2 (user decision)
```

### Pattern 4: Project Directory Resolution (RSRCH-01)

**What:** Given a topic string, find the matching `projects/N. [Title]/` directory using case-insensitive substring match. Adapted from `_get_project_root()` in channel-assistant's cli.py.

**When to use:** `cmd_survey()` in cli.py calls this at startup to determine output path.

```python
# url_builder.py (or cli.py)
from pathlib import Path
import re

def find_project_dir(root: Path, topic: str) -> Path | None:
    """Find a project directory matching topic string.

    Returns the matched Path, or None if no match.
    Raises ValueError if multiple directories match.
    """
    projects_dir = root / "projects"
    if not projects_dir.exists():
        return None
    topic_lower = topic.lower()
    matches = [
        d for d in projects_dir.iterdir()
        if d.is_dir() and topic_lower in d.name.lower()
    ]
    if len(matches) > 1:
        names = [d.name for d in matches]
        raise ValueError(f"Multiple project directories match '{topic}': {names}")
    return matches[0] if matches else None

def resolve_output_dir(root: Path, topic: str) -> Path:
    """Return the research output directory for a topic.

    - If a project dir is found: returns projects/N. Title/research/ (created if missing)
    - If no project dir: returns .claude/scratch/researcher/ (standalone mode)
    """
    try:
        project_dir = find_project_dir(root, topic)
    except ValueError:
        raise   # bubble up, CLI will print the list and exit
    if project_dir is not None:
        research_dir = project_dir / "research"
        research_dir.mkdir(parents=True, exist_ok=True)
        return research_dir
    # Standalone mode
    scratch_dir = root / ".claude" / "scratch" / "researcher"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    return scratch_dir
```

### Pattern 5: Source Manifest Schema

**What:** Two-file output system. `src_NNN.json` holds one scraped URL's full content. `source_manifest.json` is a lightweight index (no content) that Claude loads into context.

**When to use:** fetcher.py writes both after every successful or failed fetch.

```python
# src_001.json schema
{
    "index": 1,
    "url": "https://en.wikipedia.org/wiki/Jonestown",
    "domain": "en.wikipedia.org",
    "tier": 1,
    "word_count": 4523,
    "fetch_status": "ok",          # "ok" | "failed" | "skipped_tier3"
    "error": "",
    "content": "# Jonestown\n\n..."
}

# source_manifest.json schema (no content field)
{
    "topic": "Jonestown Massacre",
    "run_timestamp": "2026-03-12T10:00:00Z",
    "sources": [
        {
            "index": 1,
            "filename": "src_001.json",
            "url": "https://en.wikipedia.org/wiki/Jonestown",
            "domain": "en.wikipedia.org",
            "tier": 1,
            "word_count": 4523,
            "fetch_status": "ok"
        }
    ]
}
```

### Anti-Patterns to Avoid

- **Reusing session_id across domains:** crawl4ai's session reuse preserves cookies and browser state. A failed/blocked fetch on one domain can corrupt the session state for the next domain. Always use a fresh context per domain.
- **Sharing a single AsyncWebCrawler instance across all fetches:** While possible, this requires explicit session management to ensure isolation. Simpler and safer to open/close the context block per-fetch (matches existing crawl4ai-scraper pattern in this project).
- **Using `result.markdown` as a string directly:** In crawl4ai 0.8, `result.markdown` is a `MarkdownGenerationResult` object, not a string. Access text via `result.markdown.raw_markdown`. The existing `crawl4ai-scraper/scripts/scraper.py` uses `result.markdown` directly — this is a bug that will print the object repr, not text content.
- **Silently dropping short responses:** A response with `result.success=True` but < 200 chars often indicates an anti-bot redirect page (Cloudflare challenge, CAPTCHA, bot detection). Log it as a failed fetch, not a successful empty one.
- **Installing crawl4ai[torch] or crawl4ai[transformer]:** These install LLM SDK wrappers — direct Architecture.md Rule 1 violation.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DuckDuckGo search results | Custom HTML parser for DDG SERP | `duckduckgo-search` library (DDGS) | DDG changes HTML structure frequently; library handles it; stdlib alternative is `html.duckduckgo.com` static page via crawl4ai |
| Domain name extraction from URL | String splitting on "." | `urllib.parse.urlparse(url).hostname` | Edge cases: subdomains, IPs, ports, Unicode domains |
| Progressive retry delay | Custom sleep formula | `time.sleep(delay * attempt)` from channel-assistant pattern | Already proven in this project; no new dependency needed |
| Markdown text extraction from crawl4ai | Manual HTML parsing | `result.markdown.raw_markdown` | crawl4ai already does this; don't duplicate |

**Key insight:** The existing `crawl4ai-scraper` skill (28 lines) is a one-off URL scraper. The researcher fetcher needs retries, content validation, domain isolation, and manifest writing — a different problem. Don't reuse the one-off script; build a proper module.

---

## Common Pitfalls

### Pitfall 1: crawl4ai Markdown Field Access
**What goes wrong:** Accessing `result.markdown` directly as a string prints the object repr (`<MarkdownGenerationResult ...>`), not the actual text. The existing `crawl4ai-scraper/scripts/scraper.py` has this bug: `print(result.markdown)` will not print usable text in crawl4ai 0.8.
**Why it happens:** In older crawl4ai versions, `result.markdown` was a plain string. In 0.8, it is a `MarkdownGenerationResult` object with sub-fields.
**How to avoid:** Always use `result.markdown.raw_markdown` for plain text. Verify during Phase 7 implementation by printing `type(result.markdown)` after install.
**Warning signs:** Output contains `<MarkdownGenerationResult` or very short content despite a successful fetch.

### Pitfall 2: crawl4ai Not Installed
**What goes wrong:** `ModuleNotFoundError: No module named 'crawl4ai'` — crawl4ai is NOT currently installed in this environment (verified: pip3/pip both show no crawl4ai package).
**Why it happens:** The project lists crawl4ai as a dependency but it has not been pip-installed in the Python 3.14 environment (`C:\Python314`).
**How to avoid:** Wave 0 task must `pip install crawl4ai==0.8.0` and `crawl4ai-setup` before any fetcher.py code runs.
**Warning signs:** Import errors on any module that does `from crawl4ai import AsyncWebCrawler`.

### Pitfall 3: DuckDuckGo Anti-Bot Blocks
**What goes wrong:** Scraping `https://duckduckgo.com/` (the JS-rendered main site) via crawl4ai may trigger bot detection. The HTML endpoint (`https://html.duckduckgo.com/html/?q=...`) is static and more reliable.
**Why it happens:** DuckDuckGo's main site requires JavaScript execution and may detect headless browsers. The HTML endpoint is a legacy no-JS version intentionally kept accessible.
**How to avoid:** Use `html.duckduckgo.com/html/?q=<query>` as the search URL. If still blocked, fall back to `duckduckgo-search` library (`DDGS().text(query, max_results=10)`).
**Warning signs:** Empty or very short content from DuckDuckGo fetches; redirect to captcha page.

### Pitfall 4: Playwright Browser Binaries Not Installed
**What goes wrong:** crawl4ai imports succeed but `AsyncWebCrawler.arun()` fails with Playwright errors about missing browser binaries.
**Why it happens:** `pip install crawl4ai` does not install the browser binaries. `crawl4ai-setup` (or `playwright install chromium`) must be run separately.
**How to avoid:** Run `crawl4ai-setup` after pip install. Document this in Wave 0 setup steps.
**Warning signs:** `playwright._impl._errors.Error: Browser is not downloaded` or `executable doesn't exist`.

### Pitfall 5: Scratch Dir Not Cleaned Before New Run
**What goes wrong:** Previous run's `src_001.json` through `src_015.json` files mix with new run's output. Source manifest indexes collide. Claude reads stale sources.
**Why it happens:** No cleanup at run start.
**How to avoid:** `cmd_survey()` must delete all `src_*.json` and `source_manifest.json` from `.claude/scratch/researcher/` at startup (before any fetching). User decision from CONTEXT.md.
**Warning signs:** Source counts higher than expected; manifest references topics from previous run.

### Pitfall 6: pytest.ini pythonpath Only Covers channel-assistant
**What goes wrong:** Tests for researcher skill fail with `ModuleNotFoundError: No module named 'researcher'`.
**Why it happens:** `pytest.ini` currently sets `pythonpath = .claude/skills/channel-assistant/scripts` only. New researcher skill needs its scripts path added.
**How to avoid:** Add `.claude/skills/researcher/scripts` to `pythonpath` in pytest.ini (space-separated values supported by pytest).
**Warning signs:** Import errors in test files that do `from researcher import ...`.

---

## Code Examples

### Minimal Verified crawl4ai Fetch Pattern
```python
# Source: https://docs.crawl4ai.com/core/quickstart/
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def _fetch(url: str) -> tuple[bool, str, str]:
    conf = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler(
        config=BrowserConfig(use_persistent_context=False, headless=True)
    ) as crawler:
        result = await crawler.arun(url=url, config=conf)
    if result.success:
        return True, result.markdown.raw_markdown or "", ""
    return False, "", result.error_message or "unknown"
```

### DuckDuckGo HTML Endpoint Pattern
```python
# Static (no-JS) DDG search — more reliable than main site
import urllib.parse

def make_ddg_url(query: str) -> str:
    return f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"

# Or with duckduckgo-search library as fallback:
# from duckduckgo_search import DDGS
# results = DDGS().text(query, max_results=10)
# returns list of dicts: {"title": ..., "href": ..., "body": ...}
```

### Project Directory Resolution (adapted from cli.py `_get_project_root`)
```python
# Source: channel-assistant/cli.py _get_project_root() pattern
from pathlib import Path

def _get_project_root() -> Path:
    """Find the project root via CLAUDE.md marker."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "CLAUDE.md").exists():
            return parent
    return Path.cwd()
```

### Existing Retry Pattern (from channel-assistant scraper.py)
```python
# Source: .claude/skills/channel-assistant/scripts/channel_assistant/scraper.py
# _run_ytdlp() — adapt this pattern for crawl4ai fetcher
max_attempts = 3
delay = 5
for attempt in range(max_attempts):
    result = subprocess.run(cmd, ...)
    if result.returncode == 0 and result.stdout.strip():
        return result
    if attempt < max_attempts - 1:
        time.sleep(delay * (attempt + 1))   # progressive: 5s, 10s
raise ScrapeError(f"failed after {max_attempts} attempts")
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `result.markdown` as string | `result.markdown.raw_markdown` (MarkdownGenerationResult object) | crawl4ai 0.4+ | All existing code using `result.markdown` directly must be updated |
| Per-crawl AsyncWebCrawler instantiation | Single BrowserConfig + per-call CrawlerRunConfig | crawl4ai 0.6+ | More efficient; BrowserConfig created once, CrawlerRunConfig varies per call |
| `playwright install` manually | `crawl4ai-setup` | crawl4ai 0.3+ | crawl4ai-setup handles all browser binary setup in one command |

**Deprecated/outdated:**
- `result.markdown` as direct string: Older pattern from crawl4ai < 0.4. Now a MarkdownGenerationResult object.
- `AsyncWebCrawler(verbose=True)` as constructor arg: Moved to BrowserConfig(verbose=True) in newer versions.

---

## Open Questions

1. **DuckDuckGo crawl4ai reliability**
   - What we know: html.duckduckgo.com is a static page with no JS; crawl4ai can fetch static pages reliably; the duckduckgo-search library is a proven fallback.
   - What's unclear: Whether html.duckduckgo.com implements rate limiting or IP blocking for Playwright user agents.
   - Recommendation: Phase 7 plan 07-02 must include a validation task — run a test fetch of `https://html.duckduckgo.com/html/?q=test` and verify content length > 500 chars. If blocked, use `duckduckgo-search` library instead.

2. **crawl4ai 0.8 actual markdown field name**
   - What we know: SDK reference says `result.markdown.raw_markdown` for plain text. The existing crawl4ai-scraper uses `result.markdown` directly (likely a bug).
   - What's unclear: Whether `result.markdown` has a `__str__` that returns the text (some versions did this).
   - Recommendation: Verify with a single test fetch immediately after installing crawl4ai 0.8. Print `type(result.markdown)` and `result.markdown.raw_markdown[:100]`. Document the confirmed field name in the plan.

3. **MIN_CONTENT_CHARS threshold**
   - What we know: SCRP-02 specifies > 200 chars. Claude's discretion allows raising it.
   - What's unclear: Whether 200 chars catches all anti-bot redirects or whether some bot detection pages return > 200 chars of "Access Denied" content.
   - Recommendation: Set 200 chars as initial threshold. Log all fetches with char count. Review during Phase 8 integration testing and raise if false positives appear.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already in project) |
| Config file | `pytest.ini` (exists at project root) |
| Quick run command | `PYTHONPATH=".claude/skills/researcher/scripts" pytest tests/test_researcher/ -x --tb=short` |
| Full suite command | `PYTHONPATH=".claude/skills/channel-assistant/scripts .claude/skills/researcher/scripts" pytest -x --tb=short` |

**Note:** `pytest.ini` currently has `pythonpath = .claude/skills/channel-assistant/scripts` only. Must add researcher scripts path before tests run.

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCRP-01 | Each arun() call uses BrowserConfig(use_persistent_context=False) and CrawlerRunConfig(cache_mode=BYPASS) — no session_id reuse | unit (mock crawl4ai) | `pytest tests/test_researcher/test_fetcher.py::test_domain_isolation -x` | Wave 0 |
| SCRP-02 | Fetch returning < MIN_CONTENT_CHARS triggers retry and logs failed; not silently dropped | unit (mock crawl4ai) | `pytest tests/test_researcher/test_fetcher.py::test_content_length_validation -x` | Wave 0 |
| SCRP-02 | fetch_with_retry retries max_attempts times then returns failed dict | unit (mock crawl4ai) | `pytest tests/test_researcher/test_fetcher.py::test_retry_exhaustion -x` | Wave 0 |
| SCRP-03 | classify_domain() returns correct tier for known domains and 2 for unknown | unit (pure Python) | `pytest tests/test_researcher/test_tiers.py::test_classify_domain -x` | Wave 0 |
| SCRP-03 | Tier 3 URL is skipped before arun() is called — no fetch attempt | unit (mock crawl4ai) | `pytest tests/test_researcher/test_fetcher.py::test_tier3_skipped -x` | Wave 0 |
| RSRCH-01 | find_project_dir() returns correct path for substring match | unit (tmp_path) | `pytest tests/test_researcher/test_url_builder.py::test_find_project_dir -x` | Wave 0 |
| RSRCH-01 | find_project_dir() raises ValueError on multiple matches | unit (tmp_path) | `pytest tests/test_researcher/test_url_builder.py::test_find_project_dir_multiple_matches -x` | Wave 0 |
| RSRCH-01 | find_project_dir() returns None when no match; resolve_output_dir returns scratch path | unit (tmp_path) | `pytest tests/test_researcher/test_url_builder.py::test_standalone_mode -x` | Wave 0 |
| RSRCH-01 | cmd_survey smoke test: invoke with valid topic, no crash | integration (filesystem) | `pytest tests/test_researcher/test_cli.py::test_cmd_survey_smoke -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `PYTHONPATH=".claude/skills/researcher/scripts" pytest tests/test_researcher/ -x --tb=short`
- **Per wave merge:** `pytest -x --tb=short` (full suite)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_researcher/__init__.py` — test package marker
- [ ] `tests/test_researcher/test_fetcher.py` — covers SCRP-01, SCRP-02 (mock AsyncWebCrawler)
- [ ] `tests/test_researcher/test_tiers.py` — covers SCRP-03
- [ ] `tests/test_researcher/test_url_builder.py` — covers RSRCH-01
- [ ] `tests/test_researcher/test_cli.py` — smoke test for cmd_survey
- [ ] Update `pytest.ini` pythonpath to include `.claude/skills/researcher/scripts`
- [ ] Install crawl4ai: `pip install crawl4ai==0.8.0 && crawl4ai-setup`

---

## Sources

### Primary (HIGH confidence)
- https://docs.crawl4ai.com/complete-sdk-reference/ — BrowserConfig, CrawlerRunConfig, CrawlResult field definitions
- https://docs.crawl4ai.com/core/quickstart/ — arun() usage, result.markdown.raw_markdown pattern, multi-URL loop
- https://docs.crawl4ai.com/core/browser-crawler-config/ — BrowserConfig parameters, use_persistent_context, browser_mode
- `.claude/skills/channel-assistant/scripts/channel_assistant/scraper.py` — retry pattern adapted for fetcher.py
- `.claude/skills/channel-assistant/scripts/channel_assistant/cli.py` — _get_project_root(), PYTHONPATH CLI pattern
- `.claude/skills/channel-assistant/scripts/channel_assistant/project_init.py` — directory naming and _next_project_number() pattern
- `pytest.ini` — existing test configuration (pythonpath, testpaths)

### Secondary (MEDIUM confidence)
- https://pypi.org/project/duckduckgo-search/ — duckduckgo-search library v8.1.1, DDGS().text() API
- `pip install crawl4ai --dry-run` — confirmed 0.8.0 is the available version
- https://docs.crawl4ai.com/api/parameters/ — session_id behavior, use_persistent_context description

### Tertiary (LOW confidence)
- WebSearch: DuckDuckGo HTML endpoint reliability — unverified, flagged as needing Phase 7 validation test
- WebSearch: crawl4ai context isolation per-domain — `create_isolated_context` mentioned in multiple sources but not confirmed in official SDK reference

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — crawl4ai 0.8.0 confirmed via pip dry-run; existing usage in project
- Architecture: HIGH — patterns adapted from verified existing code in this project (scraper.py, cli.py, project_init.py)
- API fields (result.markdown.raw_markdown): HIGH — confirmed via official crawl4ai docs quickstart and SDK reference
- DuckDuckGo scraping: MEDIUM — static HTML endpoint is reliable but anti-bot behavior is untested in this environment
- Pitfalls: HIGH — crawl4ai not installed (verified), markdown field change (documented in SDK), Playwright binary requirement (documented in crawl4ai install docs)

**Research date:** 2026-03-12
**Valid until:** 2026-04-12 (crawl4ai 0.8 stable; DuckDuckGo behavior may change faster — revalidate if blocked)
