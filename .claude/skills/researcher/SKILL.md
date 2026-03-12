# Researcher Skill

**Purpose:** Agent 1.2 — The Researcher. Executes web scraping to build factual foundations for documentary videos.

**Status:** Phase 7 modules implemented. Phase 8-10 modules planned.

---

## Invocation

```bash
# Run a subcommand (Phase 8+)
PYTHONPATH=.claude/skills/researcher/scripts python -m researcher <subcommand>

# Subcommands (planned):
#   survey  — Pass 1: bulk topic scraping
#   deepen  — Pass 2: targeted deep dives
#   write   — Output research dossier
```

---

## Setup (first run only)

```bash
pip install crawl4ai==0.8.0
python -m playwright install chromium   # installs ~300MB Playwright browser binaries — run once
pip install ddgs   # DuckDuckGo search library (duckduckgo-search renamed to ddgs)
```

Environment variable for non-Latin source content:
```bash
export PYTHONUTF8=1
```

---

## Modules

### Phase 7 (implemented)

| Module | Purpose | Exports |
|--------|---------|---------|
| `tiers.py` | Source tier constants and domain classification | `TIER_1_DOMAINS`, `TIER_2_DOMAINS`, `TIER_3_DOMAINS`, `TIER_RETRY_MAP`, `classify_domain` |
| `fetcher.py` | crawl4ai wrapper with domain isolation, retry, content validation | `fetch_url`, `fetch_with_retry` |

### Phase 7 Plan 2 (implemented)

| Module | Purpose | Exports |
|--------|---------|---------|
| `url_builder.py` | Project directory resolution and URL construction | `find_project_dir`, `resolve_output_dir`, `make_ddg_url`, `build_survey_urls` |
| `cli.py` | CLI entry point with `survey` subcommand | `main`, `cmd_survey` |

### Phase 8-10 (planned)

| Module | Purpose | Status |
|--------|---------|--------|
| `deepen` command | Pass 2: targeted deep dives | Phase 8 |
| `write` command | Output research dossier | Phase 9+ |

---

## Tier System

| Tier | Behavior | Retries | Examples |
|------|----------|---------|---------|
| 1 | Authoritative — fetch with full retry | 3 | archive.org, loc.gov, en.wikipedia.org |
| 2 | General / unknown — attempt once | 1 | bbc.com, reuters.com, unknown domains |
| 3 | Social / do-not-fetch — skip entirely | 0 | facebook.com, x.com, reddit.com |

Unknown domains default to Tier 2.

---

## Output Schema (Phase 8+)

**Per-source file:** `src_001.json`, `src_002.json`, ...
```json
{
    "index": 1,
    "url": "https://en.wikipedia.org/wiki/Jonestown",
    "domain": "en.wikipedia.org",
    "tier": 1,
    "word_count": 4523,
    "fetch_status": "ok",
    "error": "",
    "content": "..."
}
```

**Source manifest (lightweight index):** `source_manifest.json`
```json
{
    "topic": "Jonestown Massacre",
    "run_timestamp": "2026-03-12T10:00:00Z",
    "sources": [
        {"index": 1, "filename": "src_001.json", "url": "...", "tier": 1, "word_count": 4523, "fetch_status": "ok"}
    ]
}
```

---

## Key Decisions

- **Fresh AsyncWebCrawler per fetch call** — no session_id reuse across domains (domain isolation)
- **Minimum content length:** 200 chars — fetches below threshold trigger retry (anti-bot detection)
- **Tier 3 domains:** Skipped before any fetch attempt, logged as `skipped_tier3`
- **DuckDuckGo:** Use `html.duckduckgo.com/html/?q=...` (static endpoint); fall back to `ddgs` library if blocked
- **Do NOT install** `crawl4ai[torch]` or `crawl4ai[transformer]` — violates Architecture.md Rule 1
- **crawl4ai 0.8.0 markdown API:** `result.markdown` is `StringCompatibleMarkdown` (str subclass). Access content via `result.markdown.raw_markdown` (str, full markdown) or use directly as string. Both are equivalent.
- **lxml version:** crawl4ai 0.8.0 requires `lxml~=5.3` but works with `lxml>=6.0` despite pip warning.
- **duckduckgo-search renamed:** Package renamed to `ddgs`. Use `pip install ddgs` and `from ddgs import DDGS`.
- **resolve_output_dir:** Returns `projects/N. Title/research/` if project found, else `.claude/scratch/researcher/` (standalone mode). Creates dir automatically.
- **Integration test isolation:** Run `pytest tests/test_researcher/test_integration.py` separately — test_fetcher.py installs a module-level crawl4ai mock that interferes if tests run together without the `_clear_crawl4ai_mock()` guard.
