---
phase: 04-project-initialization-metadata
plan: 01
subsystem: pipeline
tags: [pathlib, pytest, tdd, file-io, project-scaffold]

# Dependency graph
requires:
  - phase: 03-topic-generation-scoring
    provides: topics.py with _load_past_topics() canonical format and write_topic_briefs() numbered sections
provides:
  - project_init.py module with init_project(), load_project_inputs(), and all internal helpers
  - 48 unit tests covering all deterministic project-init behaviors
affects:
  - 04-02 (cli extension for topics → project handoff)
  - downstream phases that read projects/N. Title/metadata.md

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Sequential directory numbering: scan projects/ with regex r'^(\\d+)\\.', return max+1"
    - "Windows NTFS sanitization: re.sub(r'[<>:\"/\\\\|?*]', '', title).strip()"
    - "_append_past_topic() writes canonical format matching _load_past_topics() parser contract"
    - "metadata.md written as pure pathlib.Path.write_text() with markdown table for variants"
    - "load_project_inputs() extracts numbered brief section via section_pattern.finditer()"

key-files:
  created:
    - .claude/skills/channel-assistant/scripts/channel_assistant/project_init.py
    - tests/test_channel_assistant/test_project_init.py
  modified: []

key-decisions:
  - "title_variants >70 chars: warn to stderr, do not raise — heuristic constraint enforced by Claude before calling init_project()"
  - "load_project_inputs() returns empty string for title_patterns when analysis.md absent — no FileNotFoundError, graceful degradation"
  - "Brief section extraction uses finditer() on section headings, not line-by-line parsing — robust to variable content between sections"
  - "past_topics.md created if missing — _append_past_topic() opens in 'a' mode, which creates the file"

patterns-established:
  - "Pattern: _append_past_topic() -> _load_past_topics() round-trip test verifies format contract"
  - "Pattern: All project_init helpers use stdlib only (pathlib, re, datetime, sys) — zero new dependencies"

requirements-completed: [OUTP-03, OUTP-06]

# Metrics
duration: 8min
completed: 2026-03-11
---

# Phase 04 Plan 01: Project Initialization + Metadata Summary

**project_init.py module with TDD: deterministic functions for sequential project directory creation, Windows-safe scaffolding, metadata.md write with RECOMMENDED-labeled title variants table, and past_topics.md append that round-trips through _load_past_topics()**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-11T18:22:00Z
- **Completed:** 2026-03-11T18:30:06Z
- **Tasks:** 2 (RED + GREEN per TDD)
- **Files modified:** 2

## Accomplishments
- 48-test suite covering all deterministic behaviors: _next_project_number, _sanitize_dir_name, _create_scaffold, _append_past_topic, _write_metadata, init_project, load_project_inputs
- project_init.py implemented with full public API matching the spec — stdlib only
- past_topics.md round-trip verified: _append_past_topic() output is correctly parsed by _load_past_topics()
- Windows NTFS forbidden character stripping confirmed for all 9 forbidden chars (< > : " / \ | ? *)
- load_project_inputs() extracts numbered brief section by regex section-marker scan and gracefully handles missing analysis.md

## Task Commits

Each task was committed atomically:

1. **RED: Failing tests for project_init module** - `cc36fb6` (test)
2. **GREEN: Implement project_init module** - `ab59be9` (feat)

_Note: TDD tasks have two commits (test → feat). No refactor step needed — implementation was clean._

## Files Created/Modified
- `.claude/skills/channel-assistant/scripts/channel_assistant/project_init.py` - New module: init_project(), load_project_inputs(), and 5 internal helpers
- `tests/test_channel_assistant/test_project_init.py` - 48 unit tests across 7 test classes

## Decisions Made
- Title variant >70 char check: emits `print(..., file=sys.stderr)` warning rather than raising — the 70-char limit is a channel editorial convention enforced during Claude's heuristic generation step; init_project() is a backstop, not a hard gate
- load_project_inputs() title_patterns defaults to empty string when analysis.md is absent (not FileNotFoundError) — topics flow can proceed without competitor data if user hasn't run analyze yet
- Brief extraction via `re.compile(r"^## \\d+\\.", re.MULTILINE).finditer()` instead of line-by-line parsing — more robust when brief sections contain variable content

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing test failure in test_scraper.py (test_raises_scrape_error_after_retries_exhausted) caused by unstaged changes to scraper.py not part of this plan. Logged to deferred-items.md. Our 48 tests all pass; 128/128 tests pass excluding the pre-existing broken scraper test.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- project_init.py is ready for Phase 04-02 to extend cli.py with the topics → project handoff flow
- init_project() public API signature is locked: (root, title, hook, title_variants, description, brief_markdown) -> Path
- load_project_inputs() ready for Claude to use during topics session continuation

---
*Phase: 04-project-initialization-metadata*
*Completed: 2026-03-11*
