---
phase: 10-dossier-output
plan: "01"
subsystem: researcher-cli
tags: [writer, aggregation, synthesis-input, tdd]
dependency_graph:
  requires: [09-01]
  provides: [synthesis_input.md, cmd_write]
  affects: [researcher-cli]
tech_stack:
  added: []
  patterns: [json-glob-sort, skipped-section-header, argparse-subcommand]
key_files:
  created:
    - .claude/skills/researcher/scripts/researcher/writer.py
    - tests/test_researcher/test_writer.py
  modified:
    - .claude/skills/researcher/scripts/researcher/cli.py
decisions:
  - "Failed/empty sources listed in Skipped section at top — not silently dropped and not rendered as full source sections"
  - "build_synthesis_input partitions sources into good/skipped at build time — no pre-filtering in caller"
  - "cmd_write prints to stdout before raising ValueError for no-sources case — consistent with other cmd_* error patterns"
metrics:
  duration: 2 min
  completed: 2026-03-14
  tasks_completed: 2
  files_changed: 3
---

# Phase 10 Plan 01: Writer Module and cmd_write Subcommand Summary

**One-liner:** Source file aggregation into synthesis_input.md via writer.py module and cmd_write CLI subcommand with TDD.

## What Was Built

### writer.py module

Three exported functions:

- `load_source_files(output_dir)` — globs `src_*.json` and `pass2_*.json`, returns sorted `(pass1, pass2)` tuple
- `build_synthesis_input(topic, pass1, pass2, output_dir)` — formats sources into flat markdown with header (topic/timestamp/counts/output_dir), skipped/failed section, and per-source sections separated by `---`
- `write_synthesis_input(output_dir, content)` — writes `synthesis_input.md` and returns the path

### cmd_write subcommand

Added to `cli.py` following the established `cmd_survey` / `cmd_deepen` pattern:
- Resolves project root + output dir via existing `url_builder` functions
- Raises `ValueError("No source files found")` with a print when output dir is empty
- Prints synthesis input path, source counts, synthesis prompt path, and aggregation instruction

### Test coverage

10 unit tests in `test_writer.py`:
- 3 `load_source_files` tests (both passes, no pass2, empty dir)
- 4 `build_synthesis_input` tests (basic, failed skip, output dir included, skipped ordering)
- 1 `write_synthesis_input` test (file creation + path return)
- 3 `cmd_write` tests (smoke, prompt path print, no-sources ValueError)

## Verification

- All 10 writer tests pass
- Full researcher suite (64 tests) green — no regressions
- CLI `--help` lists `write` subcommand

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

Files created/modified:
- FOUND: `.claude/skills/researcher/scripts/researcher/writer.py`
- FOUND: `tests/test_researcher/test_writer.py`
- FOUND: `.claude/skills/researcher/scripts/researcher/cli.py` (modified)

Commits:
- FOUND: `1724938` (feat(10-01): add writer.py aggregation module and unit tests)
- FOUND: `c0ec9b0` (feat(10-01): add cmd_write subcommand to cli.py)
