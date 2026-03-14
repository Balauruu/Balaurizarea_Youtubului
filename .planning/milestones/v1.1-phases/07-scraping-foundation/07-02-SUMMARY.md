---
phase: 07-scraping-foundation
plan: 02
subsystem: scraping
tags: [crawl4ai, duckduckgo, cli, url-builder, playwright, python]

# Dependency graph
requires:
  - phase: 07-01
    provides: fetcher.py (fetch_with_retry) and tiers.py (classify_domain) which cli.py and url_builder.py import

provides:
  - url_builder.py with project directory resolution and DuckDuckGo URL construction
  - cli.py with cmd_survey subcommand (fetch -> write src_NNN.json + source_manifest.json)
  - Integration test suite validating crawl4ai 0.8.0 API and DDG scraping
  - Both STATE.md blockers resolved with documented outcomes

affects:
  - Phase 8 (Researcher Pass 1 expansion — builds on cmd_survey and url_builder)
  - Any agent using crawl4ai for web scraping

# Tech tracking
tech-stack:
  added:
    - crawl4ai==0.8.0 (with lxml 6.0.2 — works despite ~5.3 pin)
    - playwright chromium (via python -m playwright install chromium)
    - ddgs==9.11.3 (renamed from duckduckgo-search)
  patterns:
    - resolve_output_dir: project-mode (research/ subdir) vs standalone-mode (.claude/scratch/researcher/)
    - Integration test mock isolation: _clear_crawl4ai_mock() removes test_fetcher mock before real crawl4ai calls
    - pytest.ini markers block for custom marks (integration)

key-files:
  created:
    - .claude/skills/researcher/scripts/researcher/url_builder.py
    - .claude/skills/researcher/scripts/researcher/cli.py
    - tests/test_researcher/test_url_builder.py
    - tests/test_researcher/test_cli.py
    - tests/test_researcher/test_integration.py
  modified:
    - .claude/skills/researcher/SKILL.md (updated setup, modules, key decisions)
    - pytest.ini (added integration marker registration)

key-decisions:
  - "crawl4ai 0.8.0 result.markdown is StringCompatibleMarkdown (str subclass) — access content via result.markdown.raw_markdown (NOT a MarkdownGenerationResult)"
  - "DDG HTML endpoint works (html.duckduckgo.com) — primary search path confirmed, ddgs library installed as documented fallback"
  - "duckduckgo-search package renamed to ddgs — update all install instructions and imports accordingly"
  - "resolve_output_dir: standalone mode uses .claude/scratch/researcher/ when no project dir matches"
  - "Integration tests guard against test_fetcher.py module-level mock via _clear_crawl4ai_mock() function"

patterns-established:
  - "cmd_survey pattern: resolve root -> resolve output dir -> clean old artifacts -> build URLs -> fetch each -> write src_NNN.json -> write manifest"
  - "Test isolation: crawl4ai mock in unit tests removed before integration test imports"

requirements-completed:
  - RSRCH-01

# Metrics
duration: 7min
completed: 2026-03-12
---

# Phase 7 Plan 2: URL Builder, CLI Survey, and crawl4ai Validation Summary

**url_builder.py + cli.py cmd_survey wired end-to-end, crawl4ai 0.8.0 API confirmed, DDG HTML endpoint validated — both STATE.md blockers resolved**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-12T13:26:16Z
- **Completed:** 2026-03-12T13:34:03Z
- **Tasks:** 2
- **Files modified:** 8 (5 created, 3 modified)

## Accomplishments

- Implemented `url_builder.py` with case-insensitive project dir resolution, output dir routing, and DuckDuckGo URL construction
- Implemented `cli.py` `cmd_survey` skeleton that wires resolve_output_dir -> build_survey_urls -> fetch_with_retry -> write JSON artifacts
- Installed crawl4ai 0.8.0 + Playwright chromium + ddgs, confirmed all dependencies working on Windows 11
- Validated crawl4ai markdown API: `result.markdown` is `StringCompatibleMarkdown` (str subclass), `result.markdown.raw_markdown` is the correct content field
- Validated DDG HTML endpoint via crawl4ai — returns full results for "Jonestown Massacre" query
- Resolved both STATE.md blockers with documented outcomes and passing integration tests

## Task Commits

Each task was committed atomically:

1. **Task 1: url_builder.py + cli.py with cmd_survey skeleton and tests** - `e2356a0` (feat)
2. **Task 2: Install crawl4ai and validate DDG + crawl4ai field names** - `218f420` (feat)

## Files Created/Modified

- `.claude/skills/researcher/scripts/researcher/url_builder.py` — find_project_dir, resolve_output_dir, make_ddg_url, build_survey_urls
- `.claude/skills/researcher/scripts/researcher/cli.py` — main, cmd_survey with argparse subcommand
- `tests/test_researcher/test_url_builder.py` — 9 unit tests for url_builder
- `tests/test_researcher/test_cli.py` — smoke test for cmd_survey wiring
- `tests/test_researcher/test_integration.py` — 3 integration tests (crawl4ai field access, DDG HTML, DDG library)
- `.claude/skills/researcher/SKILL.md` — updated setup instructions, modules table, key decisions
- `pytest.ini` — added integration marker registration

## Decisions Made

- **crawl4ai 0.8.0 markdown API:** `result.markdown` is `StringCompatibleMarkdown` (str subclass). Plan assumed `MarkdownGenerationResult` — actual API is `result.markdown.raw_markdown`. fetcher.py already used the correct path, tests updated to reflect reality.
- **DDG HTML endpoint:** Works without fallback needed. Primary path confirmed. `ddgs` library (renamed from `duckduckgo-search`) installed as documented fallback.
- **lxml compatibility:** crawl4ai 0.8.0 pins `lxml~=5.3` but works with `lxml>=6.0` despite pip warning. No action needed.
- **Integration test isolation:** test_fetcher.py installs a module-level crawl4ai mock. Added `_clear_crawl4ai_mock()` guard so integration tests can access real crawl4ai when run together.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed incorrect crawl4ai markdown API assertion in integration test**
- **Found during:** Task 2 (integration test for crawl4ai field access)
- **Issue:** Plan specified `assert not isinstance(result.markdown, str)` but crawl4ai 0.8.0 returns `StringCompatibleMarkdown` which IS a str subclass — assertion was inverted
- **Fix:** Updated test to assert `isinstance(result.markdown, str)` and verify `.raw_markdown` attribute exists
- **Files modified:** `tests/test_researcher/test_integration.py`
- **Verification:** test_crawl4ai_field_access passes, confirms `result.markdown.raw_markdown` is correct access path
- **Committed in:** 218f420 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed duckduckgo-search package rename in fallback test**
- **Found during:** Task 2 (DDG library fallback test)
- **Issue:** `duckduckgo-search` package was renamed to `ddgs`. Old import `from duckduckgo_search import DDGS` returned 0 results with deprecation warning
- **Fix:** Updated test to import from `ddgs`, installed `ddgs==9.11.3`, updated SKILL.md setup instructions
- **Files modified:** `tests/test_researcher/test_integration.py`, `.claude/skills/researcher/SKILL.md`
- **Verification:** test_ddg_library_fallback passes with 3+ results
- **Committed in:** 218f420 (Task 2 commit)

**3. [Rule 2 - Missing Critical] Added integration test mock isolation guard**
- **Found during:** Task 2 (running full test suite together)
- **Issue:** Running all researcher tests together caused integration tests to fail — test_fetcher.py's module-level crawl4ai mock intercepted crawl4ai imports in integration tests
- **Fix:** Added `_clear_crawl4ai_mock()` function called at start of each integration test to remove the mock before importing real crawl4ai
- **Files modified:** `tests/test_researcher/test_integration.py`
- **Verification:** All 33 tests pass when run together
- **Committed in:** 218f420 (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 missing critical)
**Impact on plan:** All auto-fixes necessary for test correctness. No scope creep.

## Issues Encountered

- crawl4ai 0.8.0 requires `lxml~=5.3` but only `lxml>=6.0` is available as a binary wheel. Installed 6.0.2 and confirmed crawl4ai imports and runs correctly — the version constraint is conservative.
- crawl4ai's rich logger uses Unicode arrow characters that fail on Windows cp1252 terminal. Does not affect functionality; only affects console output. The `PYTHONUTF8=1` environment variable (documented in SKILL.md) mitigates this.

## Next Phase Readiness

- `cmd_survey` skeleton is functional: resolves output dir, fetches Wikipedia + DDG for any topic, writes `src_NNN.json` and `source_manifest.json`
- Phase 8 can expand `build_survey_urls()` to add more source domains and implement the evaluation prompt
- crawl4ai 0.8.0 is installed and validated — no setup blockers remain
- DDG scraping confirmed — Phase 8 can use `html.duckduckgo.com/html/` directly

---
*Phase: 07-scraping-foundation*
*Completed: 2026-03-12*
