---
phase: 08-survey-pass
plan: 02
subsystem: researcher-cli
tags: [cli, crawl4ai, duckduckgo, domain-field, noise-stripping, survey-evaluation, heuristic]

# Dependency graph
requires:
  - phase: 08-survey-pass
    plan: 01
    provides: failing test_cli.py Phase 8 tests (RED baseline), reddit Tier 2, build_survey_urls Wikipedia-only

provides:
  - cmd_survey fetches 10-15 real source pages (Wikipedia + DDG URL expansion)
  - domain field on every src_NNN.json and source_manifest.json entry
  - _strip_wiki_noise removes Wikipedia boilerplate (50% pitfall guard)
  - _print_summary_table: aligned table with #, Domain, Tier, Words, Status columns
  - survey_evaluation.md: heuristic evaluation prompt for Claude post-survey
  - SKILL.md: Workflow section with auto-evaluate step wiring to survey_evaluation.md
  - Phase 9 contract satisfied: manifest schema documented with verdict and deep_dive_urls

affects:
  - Phase 9 (cmd_deepen reads recommended sources + deep_dive_urls from annotated manifest)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "asyncio.run() wraps async crawl4ai call from sync cmd_survey"
    - "DDG redirect URL decode: /l/?uddg=<encoded> parsed via urllib.parse.parse_qs"
    - "ddgs library ImportError-safe fallback for DDG URL extraction"
    - "urlparse(url).hostname.removeprefix('www.') domain extraction pattern"
    - "50% word-count pitfall guard for noise stripping"

key-files:
  created:
    - .claude/skills/researcher/prompts/survey_evaluation.md
  modified:
    - .claude/skills/researcher/scripts/researcher/cli.py
    - .claude/skills/researcher/SKILL.md

key-decisions:
  - "asyncio.run() used in cmd_survey to call async _fetch_ddg_with_links — keeps cmd_survey sync, no asyncio.get_event_loop() complexity"
  - "DDG redirect decode: DDG wraps result URLs as /l/?uddg=<encoded> — urllib.parse.parse_qs extracts the real URL from the uddg param"
  - "50% pitfall guard in _strip_wiki_noise: if stripping removes > 50% of word count, full content returned unchanged — prevents accidental destruction of short articles"
  - "TIER_3_DOMAINS imported directly in _parse_ddg_result_urls for set-membership check without calling classify_domain for every link"

# Metrics
duration: 4min
completed: 2026-03-14
---

# Phase 8 Plan 02: Survey Pass Implementation Summary

**cmd_survey expanded to fetch 10-15 real source pages via DDG URL extraction, with domain fields, noise stripping, formatted summary table, and heuristic evaluation prompt wiring**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-14T17:23:58Z
- **Completed:** 2026-03-14T17:27:37Z
- **Tasks:** 2
- **Files modified:** 3 (cli.py, SKILL.md, survey_evaluation.md created)

## Accomplishments

- Rewrote cli.py cmd_survey to fetch Wikipedia + DDG result URLs (up to 12 external URLs extracted from DDG HTML via crawl4ai extract_links=True)
- Added _fetch_ddg_with_links (async crawl4ai), _parse_ddg_result_urls (DDG redirect decode + Tier 3 filtering), _strip_wiki_noise (boilerplate removal with 50% pitfall guard), _print_summary_table (aligned columns)
- Added domain field to src_NNN.json and source_manifest.json entries
- All 7 test_cli.py Phase 8 tests now GREEN (were RED after Plan 01)
- Full unit suite: 43 tests passing
- Created survey_evaluation.md with primary source, local journalism, contradiction criteria and manifest annotation instructions
- Updated SKILL.md: corrected Tier 2/3 table (reddit now Tier 2), added Workflow section with auto-evaluate step, updated manifest schema example, fixed Phase 9-10 module table

## Task Commits

| Task | Name | Commit |
|------|------|--------|
| 1 | Expand cli.py — DDG URL extraction, domain field, noise stripping, summary table | ababd88 |
| 2 | Write survey_evaluation.md prompt and update SKILL.md workflow | 8fcb878 |

## Files Created/Modified

- `.claude/skills/researcher/scripts/researcher/cli.py` — Full rewrite with DDG expansion, domain field, noise stripping, summary table
- `.claude/skills/researcher/prompts/survey_evaluation.md` — Evaluation prompt for post-survey heuristic step
- `.claude/skills/researcher/SKILL.md` — Workflow section, corrected Tier table, updated manifest schema, Phase 9-10 labels

## Decisions Made

- **asyncio.run() for DDG fetch:** Keeps cmd_survey synchronous while using async crawl4ai. No event loop complexity leaks into the rest of the CLI.
- **DDG redirect decode:** DDG wraps external URLs as `/l/?uddg=<encoded_url>`. parse_qs extracts the real URL from the `uddg` parameter. Links that fail this decode are silently skipped.
- **50% pitfall guard in noise stripping:** If a Wikipedia article has very few content sections above the References heading, stripping would remove most of the article. Guard prevents this by returning full content when stripped word count < 50% of original.
- **TIER_3_DOMAINS for link filtering:** Domain filtering in _parse_ddg_result_urls uses direct set membership against TIER_3_DOMAINS rather than calling classify_domain() for performance.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 9 (cmd_deepen) can begin: manifest schema documented with verdict and deep_dive_urls fields
- survey_evaluation.md provides the evaluation rubric; SKILL.md wires it into the post-survey workflow
- cmd_survey produces a fully annotated manifest after the heuristic evaluation step — cmd_deepen reads recommended sources + deep_dive_urls without ambiguity

---
*Phase: 08-survey-pass*
*Completed: 2026-03-14*
