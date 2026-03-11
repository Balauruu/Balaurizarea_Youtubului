---
phase: 03-topic-generation-scoring
plan: 01
subsystem: testing
tags: [python, difflib, pathlib, pytest, tdd, topics, channel-assistant]

# Dependency graph
requires:
  - phase: 02-query-layer-competitor-analysis
    provides: "analyzer.py, cli.py patterns, pytest.ini config"
provides:
  - "topics.py module with _load_past_topics, check_duplicates, load_topic_inputs, write_topic_briefs, format_chat_cards"
  - "34 passing tests covering all deterministic topic helper functions"
affects:
  - 03-02-topic-generation-cli (reads topics.py as dependency)
  - 04-project-init (reads context/topics/topic_briefs.md written by write_topic_briefs)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD RED-GREEN cycle: failing tests committed before implementation"
    - "stdlib-only modules: difflib.SequenceMatcher for fuzzy dedup, re for markdown parsing"
    - "Output overwrite pattern: write_topic_briefs always overwrites (latest-snapshot semantics)"

key-files:
  created:
    - ".claude/skills/channel-assistant/scripts/channel_assistant/topics.py"
    - "tests/test_channel_assistant/test_topics.py"
  modified: []

key-decisions:
  - "SequenceMatcher over fuzzywuzzy/rapidfuzz: stdlib, zero dependencies, sufficient accuracy for title dedup"
  - "Near-duplicates flagged with warning rather than silently dropped: user sees all candidates with context"
  - "load_topic_inputs raises FileNotFoundError for analysis.md and channel.md (required), returns [] for missing past_topics.md (optional)"
  - "write_topic_briefs uses overwrite semantics: latest snapshot only, no history file"

patterns-established:
  - "Bold-title extraction pattern: re.compile(r'\\*\\*(.+?)\\*\\*') handles both '- **T**' and '**T**' line prefixes"
  - "Score display format: O:X C:X S:X V:X = N/20 (used consistently in both write_topic_briefs and format_chat_cards)"

requirements-completed: [OUTP-01, OUTP-02]

# Metrics
duration: 8min
completed: 2026-03-11
---

# Phase 3 Plan 1: Topic Generation Helper Functions Summary

**Stdlib-only topics.py module with fuzzy dedup (SequenceMatcher), bold-title parser, and markdown writer, backed by 34 passing TDD tests**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-11T17:05:00Z
- **Completed:** 2026-03-11T17:13:00Z
- **Tasks:** 2 (RED + GREEN, no refactor needed)
- **Files modified:** 2

## Accomplishments

- `_load_past_topics` parses bold-markdown formatted titles from `past_topics.md` using regex, handles missing/empty files
- `check_duplicates` uses `difflib.SequenceMatcher` ratio for near-duplicate detection with configurable threshold (default 0.85)
- `load_topic_inputs` loads analysis.md, channel.md, past_topics.md — raises FileNotFoundError for required files, returns [] for optional
- `write_topic_briefs` writes full Topic Brief Schema markdown with numbered headings, score lines, justification, and timestamps
- `format_chat_cards` returns compact numbered cards (title -- hook, score line O:X C:X, runtime, pillar, optional dup/tag warnings)
- All 34 tests pass; full suite of 80 tests passes with zero regressions

## Task Commits

Each task was committed atomically following TDD protocol:

1. **RED: Failing tests for topics.py** - `ffbbb10` (test)
2. **GREEN: Implement topics.py** - `bb73380` (feat)

## Files Created/Modified

- `.claude/skills/channel-assistant/scripts/channel_assistant/topics.py` - Deterministic helper functions for topic generation workflow
- `tests/test_channel_assistant/test_topics.py` - 34 tests: TestLoadPastTopics, TestCheckDuplicates, TestLoadTopicInputs, TestWriteTopicBriefs, TestFormatChatCards

## Decisions Made

- `difflib.SequenceMatcher` chosen over third-party fuzzy libraries (fuzzywuzzy, rapidfuzz) — stdlib only, zero new dependencies, accurate enough for title-length strings
- Near-duplicates are flagged with a warning tag rather than silently dropped — user retains full visibility of all candidates
- `load_topic_inputs` raises `FileNotFoundError` for `analysis.md` and `channel.md` (both required), but returns empty list for missing `past_topics.md` (new channels have no past topics)
- `write_topic_briefs` uses overwrite semantics — file is always the latest snapshot, no history accumulated (aligns with Phase 4 reading the file as current state)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `topics.py` is ready as a dependency for 03-02 (CLI subcommand integration)
- `write_topic_briefs` output path `context/topics/topic_briefs.md` is compatible with Phase 4 input expectations
- All functions import cleanly from `channel_assistant.topics`

---
*Phase: 03-topic-generation-scoring*
*Completed: 2026-03-11*
