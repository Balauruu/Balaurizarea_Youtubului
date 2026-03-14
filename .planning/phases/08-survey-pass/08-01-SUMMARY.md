---
phase: 08-survey-pass
plan: 01
subsystem: testing
tags: [pytest, tdd, tiers, url_builder, reddit, duckduckgo, crawl4ai]

# Dependency graph
requires:
  - phase: 07-scraping-foundation
    provides: tiers.py domain classification, url_builder.py survey URL construction, cli.py cmd_survey

provides:
  - Failing unit tests for all Phase 8 new behaviors (test_cli.py RED baseline)
  - reddit.com and old.reddit.com reclassified to Tier 2 in tiers.py
  - build_survey_urls refactored to return Wikipedia URL only in url_builder.py
  - DDG link extraction integration test in test_integration.py
affects:
  - 08-02 (Plan 02 will make test_cli.py Phase 8 tests go GREEN)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD RED-GREEN pattern: failing tests committed before implementation"
    - "Superseded test update: old behavior tests updated/renamed when design changes intentionally"

key-files:
  created:
    - tests/test_researcher/test_integration.py (extended with test_ddg_links_extraction)
  modified:
    - tests/test_researcher/test_tiers.py
    - tests/test_researcher/test_url_builder.py
    - tests/test_researcher/test_cli.py
    - .claude/skills/researcher/scripts/researcher/tiers.py
    - .claude/skills/researcher/scripts/researcher/url_builder.py

key-decisions:
  - "reddit.com and old.reddit.com moved from TIER_3 to TIER_2 — Reddit has useful community research value and anti-bot behavior is not as severe as pure social media"
  - "build_survey_urls returns Wikipedia URL only — DDG URL expansion handled separately in cmd_survey after link extraction to keep URL building and DDG expansion concerns separate"
  - "Superseded tests (test_classify_domain_reddit_is_tier3) updated to reflect Phase 8 behavior rather than deleted — preserves test intent with corrected assertion"

patterns-established:
  - "Phase 8 TDD pattern: write all failing tests first, commit RED, then implement GREEN"
  - "Integration test isolation: _clear_crawl4ai_mock() call at test start removes unit test mock before real crawl4ai access"

requirements-completed: [RSRCH-02, RSRCH-04]

# Metrics
duration: 3min
completed: 2026-03-14
---

# Phase 8 Plan 01: Survey Pass Prerequisites Summary

**TDD baseline: failing tests for all Phase 8 CLI behaviors, reddit Tier 2 reclassification, and build_survey_urls Wikipedia-only refactor**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-14T17:19:34Z
- **Completed:** 2026-03-14T17:21:57Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Wrote failing Phase 8 tests in test_tiers.py, test_url_builder.py, test_cli.py, and test_integration.py (TDD RED baseline)
- Implemented Reddit reclassification: reddit.com and old.reddit.com moved from TIER_3 to TIER_2 in tiers.py — all 16 tiers tests GREEN
- Refactored build_survey_urls to return [wikipedia_url] only — DDG expansion now handled in cmd_survey — all 12 url_builder tests GREEN
- 3 test_cli.py Phase 8 tests remain RED as expected (test_summary_table_columns, test_domain_field_in_src_json, test_manifest_schema_fields) — Plan 02 work

## Task Commits

Each task was committed atomically:

1. **Task 1: Write failing tests for all Phase 8 behaviors** - `b04e4b3` (test)
2. **Task 2: Implement tiers.py Reddit reclassification and url_builder.py refactor** - `c0013b1` (feat)

_Note: TDD tasks have two commits (test RED → feat GREEN)_

## Files Created/Modified

- `tests/test_researcher/test_tiers.py` - Added 4 Reddit Tier 2 tests; updated 2 superseded Phase 7 tests
- `tests/test_researcher/test_url_builder.py` - Added 3 build_survey_urls Wikipedia-only tests
- `tests/test_researcher/test_cli.py` - Added 6 Phase 8 behavior tests (3 RED, 3 GREEN)
- `tests/test_researcher/test_integration.py` - Added test_ddg_links_extraction integration test
- `.claude/skills/researcher/scripts/researcher/tiers.py` - reddit.com and old.reddit.com added to TIER_2, removed from TIER_3
- `.claude/skills/researcher/scripts/researcher/url_builder.py` - build_survey_urls returns [wikipedia_url] only

## Decisions Made

- **Reddit Tier 2 reclassification:** reddit.com moved from Tier 3 (skip) to Tier 2 (1 retry). Reddit threads and community research posts are useful documentary sources; anti-bot risk is lower than pure social media (Facebook, Instagram).
- **build_survey_urls Wikipedia-only:** DDG URL is no longer in the initial URL list — cli.py handles DDG as a separate link-extraction step. This keeps URL construction (url_builder.py) separate from the DDG crawl-and-parse workflow (cli.py).
- **Superseded test update:** test_classify_domain_reddit_is_tier3 renamed to test_classify_domain_reddit_is_tier2 and assertion updated. test_tier3_domains_has_expected_entries updated to assert reddit.com NOT in TIER_3. Preserves test coverage intent with corrected behavior.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02 (cmd_survey expansion) can begin: failing test_cli.py Phase 8 tests are in place as the acceptance criteria
- Reddit domain is now Tier 2 — cmd_survey will fetch Reddit URLs from DDG results
- build_survey_urls now returns only Wikipedia URL — cmd_survey must add DDG link-extraction step for full expansion

---
*Phase: 08-survey-pass*
*Completed: 2026-03-14*
