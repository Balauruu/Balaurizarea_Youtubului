---
phase: 05-trend-scanning-content-gaps
plan: 02
subsystem: channel-assistant
tags: [cli, trends, content-gaps, context-loader, heuristic-prompt]
dependency_graph:
  requires: [trend_scanner.py (05-01), cli.py, topics.py, database.py]
  provides: [cmd_trends() CLI subcommand, trends_analysis.md prompt, extended load_topic_inputs()]
  affects: [topic generation context, analysis.md trend sections]
tech_stack:
  added: []
  patterns: [context-loader pattern (no LLM API), jittered scrape delay, section injection into analysis.md]
key_files:
  created:
    - .claude/skills/channel-assistant/prompts/trends_analysis.md
  modified:
    - .claude/skills/channel-assistant/scripts/channel_assistant/cli.py
    - .claude/skills/channel-assistant/scripts/channel_assistant/topics.py
    - tests/test_channel_assistant/test_topics.py
decisions:
  - "_extract_section() added to both topics.py and cli.py independently — avoids cross-module import while keeping extraction logic consistent"
  - "Trend data printed before competitor analysis in cmd_topics() — Claude sees content gaps first to prioritize underserved topics"
  - "Graceful degradation: topics command works without prior trends run — empty strings for missing sections"
  - "trends_analysis.md prompt instructs three distinct analyses (gap detection ANLZ-05, trending topics ANLZ-06, convergence alerts ANLZ-07)"
  - "Topic cluster extraction in cmd_trends() uses bold-text pattern from analysis.md ## Topic Clusters section"
metrics:
  duration_min: 12
  completed_date: "2026-03-11"
  tasks_completed: 2
  files_created: 1
  files_modified: 3
---

# Phase 05 Plan 02: trends CLI Subcommand + Prompt + Topic Injection Summary

**One-liner:** `trends` CLI subcommand wired to trend_scanner.py with jittered scrape loop, structured stdout context for Claude, 86-line heuristic prompt for gap/convergence/trending analysis, and load_topic_inputs() extended to auto-inject trend data into topic generation context.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | cmd_trends() in cli.py + trends argparse subcommand | 2d783c9 | cli.py |
| 2 | trends_analysis.md prompt + extended topics.py | 5b83aa5 | trends_analysis.md, topics.py, cli.py, test_topics.py |

## What Was Built

**`cmd_trends(args, db, root)`** in cli.py — context-loader following the `cmd_topics()` pattern:
1. Loads channel DNA from `context/channel/channel.md` (exits with error if missing)
2. Extracts `## Topic Clusters` from `analysis.md` via `_extract_section()`, parses bold-text cluster names
3. Calls `derive_keywords(channel_dna, topic_clusters)` to get keyword list
4. Loops over keywords with `random.uniform(0.5, 1.5)` jittered delay; calls `scrape_autocomplete()` + `scrape_search_results()` per keyword, printing progress to stderr
5. Calls `get_recent_competitor_videos(db, days=30)` for convergence window
6. Prints structured blocks to stdout: `## Autocomplete Suggestions`, `## Search Results`, `## Recent Competitor Videos (30-day window)`, `## Prompt`, `## Output Target`, instruction line

**`trends_analysis.md`** (86 lines) — heuristic prompt for Claude's post-trends reasoning:
- Section 1: Content Gap Detection with composite score formula (demand × opportunity)
- Section 2: Trending Topics from published_text recency signals
- Section 3: Convergence Alerts requiring 3+ competitor channels in 30-day window with framing: Opportunity / Saturation warning / Neutral flag
- Output format: `update_analysis_with_trends()` call + inline chat summary (top 3 gaps, alerts, file path)

**Extended `load_topic_inputs()`** in topics.py:
- Added `_extract_section()` internal helper
- Returns two new keys: `"trends"` and `"content_gaps"` — text from `## Trending Topics` and `## Content Gaps` in analysis.md
- Empty strings when those sections are absent (trends not yet run)
- `cmd_topics()` in cli.py prints `## Trend Data` block (Content Gaps first, then Trending Topics) when either is non-empty — auto-injected into topic generation context

## Key Decisions

- **_extract_section() in both cli.py and topics.py:** Avoids importing topics.py internals into cli.py. Both implementations are identical — if the regex logic changes, both files update together.
- **Trend data printed before analysis in cmd_topics():** Ensures Claude sees underserved content gaps at the top of context before scanning 50+ lines of competitor analysis.
- **Graceful degradation is explicit in docstring:** `load_topic_inputs()` now documents that `trends` and `content_gaps` are empty strings when trends has not been run — callers can safely use `.get("trends", "")` or direct key access.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_returns_dict_with_expected_keys asserted old key set**
- **Found during:** Task 2 — running test suite after extending load_topic_inputs()
- **Issue:** Existing test asserted `set(inputs.keys()) == {"analysis", "channel_dna", "past_topics"}` which failed with the two new keys
- **Fix:** Updated assertion to include `"trends"` and `"content_gaps"`; added type assertions for both new keys
- **Files modified:** tests/test_channel_assistant/test_topics.py
- **Commit:** 5b83aa5

## Test Results

- 161 tests pass (all tests excluding pre-existing scraper regression)
- 67 tests in test_topics.py + test_trend_scanner.py: all pass
- Pre-existing failure in test_scraper.py (call_count 6 vs 3) — logged in deferred-items.md from 05-01, unrelated to this plan

## Self-Check: PASSED

- trends_analysis.md: FOUND (86 lines, > 30 minimum)
- cli.py contains cmd_trends: FOUND
- topics.py load_topic_inputs returns trends/content_gaps: VERIFIED
- Commit 2d783c9 (Task 1): FOUND
- Commit 5b83aa5 (Task 2): FOUND
