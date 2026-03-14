---
phase: 07-scraping-foundation
plan: "01"
subsystem: researcher-skill
tags: [crawl4ai, scraping, tiers, fetcher, tdd]
dependency_graph:
  requires: []
  provides: [researcher.tiers, researcher.fetcher]
  affects: [phase-08, phase-09, phase-10]
tech_stack:
  added: []
  patterns: [crawl4ai-domain-isolation, tier-based-retry, tdd-with-mocked-deps]
key_files:
  created:
    - .claude/skills/researcher/SKILL.md
    - .claude/skills/researcher/scripts/researcher/__init__.py
    - .claude/skills/researcher/scripts/researcher/__main__.py
    - .claude/skills/researcher/scripts/researcher/tiers.py
    - .claude/skills/researcher/scripts/researcher/fetcher.py
    - .claude/skills/researcher/prompts/.gitkeep
    - tests/test_researcher/__init__.py
    - tests/test_researcher/test_tiers.py
    - tests/test_researcher/test_fetcher.py
  modified:
    - pytest.ini
decisions:
  - Defer crawl4ai imports to function level so fetcher.py is importable and testable without crawl4ai installed
  - TIER_RETRY_MAP controls effective_attempts (tier is the authority, not the caller-supplied max_attempts)
  - Module-level sys.modules mock in test_fetcher.py: install fake crawl4ai before importing fetcher to avoid ModuleNotFoundError
metrics:
  duration_minutes: 7
  completed_date: "2026-03-12"
  tasks_completed: 2
  tasks_total: 2
  files_created: 9
  files_modified: 1
---

# Phase 7 Plan 01: Researcher Skill Scaffold + Scraping Foundation Summary

**One-liner:** crawl4ai fetcher with per-domain browser isolation and three-tier retry policy, fully tested with mocked crawl4ai (no browser install required for tests).

---

## What Was Built

### Task 1: Researcher Skill Scaffold + tiers.py

Created the `.claude/skills/researcher/` directory with all required structure. `tiers.py` implements three source tiers:

- **Tier 1** (authoritative): archive.org, loc.gov, en.wikipedia.org, etc. — 3 retries
- **Tier 2** (general/unknown): bbc.com, reuters.com, unknown domains — 1 retry (default for unknowns)
- **Tier 3** (social/blocked): facebook.com, x.com, reddit.com — 0 retries, skip before fetch

`classify_domain()` strips `www.` prefix and returns tier int. `SKILL.md` documents invocation pattern, setup steps, tier table, and output schema.

### Task 2: fetcher.py

`fetch_with_retry()` is the single entry point for all web fetches in the pipeline. Key behaviors:

- **Domain isolation:** Fresh `AsyncWebCrawler` context per call via `BrowserConfig(use_persistent_context=False)` + `CrawlerRunConfig(cache_mode=CacheMode.BYPASS)`
- **Tier gate:** Tier 3 URLs return `{"fetch_status": "skipped_tier3", "attempts_used": 0}` without touching crawl4ai
- **Content validation:** Fetches returning < 200 chars (anti-bot redirect detection) trigger retry, not silent drop
- **Progressive delay:** `time.sleep(delay * attempt)` between retries (5s, 10s for Tier 1)

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Module-level crawl4ai import blocked test collection**

- **Found during:** Task 2 GREEN phase
- **Issue:** fetcher.py originally imported from crawl4ai at module level. Since crawl4ai is not installed in the test environment, `python -m pytest` failed at collection with `ModuleNotFoundError`.
- **Fix:** Moved crawl4ai imports inside `_fetch_once()` (deferred/lazy imports). Also restructured `test_fetcher.py` to install a `sys.modules` mock for crawl4ai before importing fetcher, so the deferred imports resolve to mocks.
- **Files modified:** `.claude/skills/researcher/scripts/researcher/fetcher.py`, `tests/test_researcher/test_fetcher.py`
- **Commit:** c73a712

---

## Test Results

```
tests/test_researcher/test_fetcher.py ........  (8 passed)
tests/test_researcher/test_tiers.py ............  (12 passed)
Total: 20 passed
```

All must-have truths verified:
- `fetch_with_retry` creates a fresh `AsyncWebCrawler` per call with `use_persistent_context=False` and `CacheMode.BYPASS`
- Content < 200 chars triggers retry and logs warning, not silent drop
- Tier 3 URLs skipped before fetch, logged as `skipped_tier3`
- `classify_domain()` returns 1 for Tier 1, 3 for Tier 3, 2 for unknowns
- `TIER_RETRY_MAP[1] == 3`, `TIER_RETRY_MAP[2] == 1`, `TIER_RETRY_MAP[3] == 0`

---

## Commits

| Hash | Message |
|------|---------|
| df38c58 | feat(07-01): researcher skill scaffold + tiers.py with tests |
| c73a712 | feat(07-01): fetcher.py with domain isolation, retry, and content validation |

---

## Self-Check: PASSED
