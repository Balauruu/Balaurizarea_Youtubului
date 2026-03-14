---
phase: 09-deep-dive-pass
plan: 01
subsystem: researcher-cli
tags: [researcher, cli, pass2, deep-dive, tdd]
dependency_graph:
  requires: [08-survey-pass]
  provides: [cmd_deepen, pass2_NNN.json, pass2_sources manifest key]
  affects: [researcher skill, source_manifest.json]
tech_stack:
  added: []
  patterns: [two-pass research pipeline, budget guard, URL dedup]
key_files:
  created: []
  modified:
    - .claude/skills/researcher/scripts/researcher/cli.py
    - .claude/skills/researcher/SKILL.md
    - tests/test_researcher/test_cli.py
decisions:
  - "Budget guard enforces max 15 total source files (src_*.json + pass2_*.json combined)"
  - "Sources without verdict key are treated as skip — same as explicit skip verdict"
  - "Re-run cleanup: delete pass2_*.json at start of cmd_deepen, never delete src_*.json"
  - "Tier 3 filtering applied in _collect_deep_dive_urls via classify_domain"
  - "Dedup against Pass 1 via _get_fetched_urls reads url field from src_*.json files"
metrics:
  duration: ~10 min
  completed: 2026-03-14T18:12:17Z
  tasks_completed: 2
  files_changed: 3
---

# Phase 9 Plan 01: cmd_deepen Implementation Summary

**One-liner:** Pass 2 deep-dive CLI command with budget guard, URL dedup against Pass 1, and Tier 3 filtering, completing the two-pass researcher pipeline.

---

## What Was Built

`cmd_deepen` is a new CLI subcommand that completes the two-pass researcher architecture. After `cmd_survey` (Pass 1) fetches a broad survey of sources and Claude evaluates them, `cmd_deepen` reads the annotated `source_manifest.json` and fetches the targeted primary sources that Claude identified during evaluation.

**Key behaviors:**

- Reads only sources with `verdict == "recommended"` (missing verdict treated as skip)
- Collects `deep_dive_urls` across all recommended sources, deduplicates preserving manifest order
- Filters Tier 3 domains via `classify_domain`
- Deduplicates against Pass 1 URLs (`src_*.json` files) via `_get_fetched_urls`
- Budget guard: total `src_*.json + pass2_*.json` must not exceed 15
- Cleans old `pass2_*.json` files on re-run (but never touches `src_*.json`)
- Exits cleanly with informative message if no fetchable URLs remain
- Writes `pass2_NNN.json` files with same schema as `src_NNN.json`
- Prints summary table (reuses `_print_summary_table`)
- Updates `source_manifest.json` with `pass2_sources` key

---

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write cmd_deepen test stubs (RED phase) | 14742e0 | test_cli.py, cli.py (stub) |
| 2 | Implement cmd_deepen, register subcommand, update SKILL.md | 8b25368 | cli.py, SKILL.md |

---

## Deviations from Plan

None — plan executed exactly as written.

---

## Verification Results

1. All 11 deepen-specific tests pass: `pytest tests/test_researcher/test_cli.py -k deepen` — PASSED
2. Full researcher test suite (54 tests, excluding live integration tests): PASSED
3. CLI help shows deepen subcommand: `python -m researcher --help` — CONFIRMED
4. SKILL.md contains Pass 2 workflow section: CONFIRMED

**Note:** `tests/test_researcher/test_integration.py` failure is pre-existing — requires live network/Playwright. Excluded from standard test suite per SKILL.md design (run separately).

---

## Self-Check: PASSED

- `.claude/skills/researcher/scripts/researcher/cli.py` — FOUND (cmd_deepen implemented)
- `tests/test_researcher/test_cli.py` — FOUND (11 test_cmd_deepen_* tests)
- `.claude/skills/researcher/SKILL.md` — FOUND (Pass 2 workflow section present)
- Commit 14742e0 — FOUND
- Commit 8b25368 — FOUND
