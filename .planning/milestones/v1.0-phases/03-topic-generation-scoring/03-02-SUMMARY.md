---
phase: 03-topic-generation-scoring
plan: 02
subsystem: cli
tags: [python, argparse, prompt-engineering, topics, channel-assistant, heuristic]

# Dependency graph
requires:
  - phase: 03-topic-generation-scoring
    plan: 01
    provides: "topics.py module (load_topic_inputs, write_topic_briefs, format_chat_cards)"
provides:
  - "topics subcommand wired into channel-assistant CLI (cmd_topics)"
  - "topic_generation.md anchored scoring rubric prompt (235 lines)"
affects:
  - 04-project-init (invokes topics subcommand to generate topic_briefs.md)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Context-loader CLI pattern: cmd_topics() prints structured context to stdout for Claude to reason over"
    - "Prompt file as calibration artifact: topic_generation.md stores anchored rubric so scoring is consistent across runs"
    - "Section extraction from markdown: pillar section extracted from channel_dna by header landmark"

key-files:
  created:
    - ".claude/skills/channel-assistant/prompts/topic_generation.md"
  modified:
    - ".claude/skills/channel-assistant/scripts/channel_assistant/cli.py"

key-decisions:
  - "cmd_topics is a context-loader not an orchestrator: prints structured context to stdout, Claude does all heuristic generation"
  - "Prompt file stores rubric anchors verbatim from 03-RESEARCH.md: Jack the Ripper=Obscurity 1 through obscure regional cults=Obscurity 5"
  - "topics subparser takes no required args: all inputs are read from default file locations (analysis.md, channel.md, past_topics.md)"
  - "Competitor analysis printed to first 50 lines in stdout summary: full file still readable at known path"
  - "Pillar section extracted from channel_dna by ## Core Content Pillars landmark: reduces noise in stdout output"

requirements-completed: [ANLZ-04, OUTP-01]

# Metrics
duration: 4min
completed: 2026-03-11
---

# Phase 3 Plan 2: Topic Generation CLI + Scoring Rubric Summary

**Topics subcommand wired into channel-assistant CLI; anchored 1-5 rubric prompt calibrated to dark mysteries niche with Matamoros cult as canonical scoring example**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-11T17:18:30Z
- **Completed:** 2026-03-11T17:22:30Z
- **Tasks:** 2
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments

- `topic_generation.md` prompt file (235 lines) with anchored 1-5 rubric across all 4 dimensions (Obscurity, Complexity, Shock Factor, Verifiability)
- Each rubric level has 1-3 anchor examples calibrated to the dark mysteries niche (Jack the Ripper=1, Heaven's Gate=2, Matamoros pre-viral=3, Mesa Verde=4, obscure regional cults=5)
- Generation instructions: 10-15 candidates from 3 sources (competitor gaps, channel pillars, tavily-mcp web research)
- Tiebreaker rules: shock_factor desc, then obscurity desc, then verifiability desc
- Anti-patterns section covering: generic scoring, filtering, mainstream topics, silent dedup drops
- Both output formats documented: compact chat cards and full Topic Brief Schema with canonical Matamoros example
- `cmd_topics()` function in cli.py: loads all 3 input sources, prints structured 5-section context summary to stdout
- `topics` subparser added to argparse main() with dispatch to cmd_topics()
- `from .topics import load_topic_inputs` import added at top of cli.py
- All 80 non-scraper tests pass with no regressions

## Task Commits

Each task committed atomically:

1. **Task 1: Create anchored scoring rubric and generation prompt** - `1f99d21` (feat)
2. **Task 2: Wire topics subcommand into CLI** - `a3b5539` (feat)

## Files Created/Modified

- `.claude/skills/channel-assistant/prompts/topic_generation.md` - Heuristic prompt for Claude to use during topic generation; contains anchored scoring rubric and output format spec
- `.claude/skills/channel-assistant/scripts/channel_assistant/cli.py` - Added cmd_topics() function (88 lines) and topics subparser with dispatch

## Decisions Made

- `cmd_topics` is a context-loader only — it prints structured output to stdout for Claude to reason over, then Claude performs all heuristic generation (topic ideation, scoring, dedup judgment). This follows Architecture.md Rule 1 (zero LLM API wrappers) exactly.
- Prompt file uses verbatim rubric anchors from 03-RESEARCH.md — all 4 dimensions have 5 anchor levels each, totaling 20 anchor examples across all dimensions
- Topics subparser takes no required arguments — all input paths are derived from the project root, consistent with existing subcommand patterns (analyze, status, migrate)
- Competitor analysis output is truncated to first 50 lines in the stdout summary to avoid flooding the context window; full file is referenced at its known path

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

Pre-existing test failure in `test_scraper.py::TestScrapeChannel::test_raises_scrape_error_after_retries_exhausted` (call_count 6 vs expected 3). This was present before this plan's changes (scraper.py was already modified in the working tree per git status). Out of scope for this plan.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `channel-assistant topics` subcommand is ready to invoke
- `topic_generation.md` prompt is ready for Claude to load and use during generation
- `write_topic_briefs()` and `format_chat_cards()` from `channel_assistant.topics` are ready to receive generated output
- Output path `context/topics/topic_briefs.md` will be created on first `topics` run

---
*Phase: 03-topic-generation-scoring*
*Completed: 2026-03-11*
