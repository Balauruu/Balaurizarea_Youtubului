---
id: T03
parent: S04
milestone: M002
provides:
  - Mocked pytest suite (22 tests) covering animation CLI subcommands, manifest merge, and error paths
key_files:
  - tests/test_animation/test_cli.py
  - tests/test_animation/test_manifest.py
  - tests/test_animation/__init__.py
key_decisions:
  - Used cmd[5] index for output path in subprocess mock side_effect — matches actual CLI command layout [npx, remotion, render, entry, MapComposition, output_path, --props=...]
patterns_established:
  - Animation test fixture includes mixed shotlist_type entries (map + animation) to verify filtering — same pattern available for future shotlist_type additions
observability_surfaces:
  - "pytest tests/test_animation/ -v --tb=short" — quick contract regression check
duration: 15m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T03: Add pytest suite for animation CLI and manifest merge

**22 mocked tests covering resolve_project_dir, cmd_load map filtering, cmd_render subprocess orchestration, manifest merge contract, and error paths — all pass with no regressions.**

## What Happened

Created `tests/test_animation/` package mirroring graphics-generator test patterns. Test fixtures create tmp_path project dirs with mixed shotlist entries (2 map + 1 animation type) to verify the `shotlist_type == "map"` filter. `pytest.ini` already had animation scripts on pythonpath from T02.

Tests break down:
- **test_cli.py** (15 tests): resolve_project_dir (4: substring, case-insensitive, scratch fallback, ambiguous raises), cmd_load (6: MAP_SHOTS section, excludes non-map, CHANNEL_DNA, manifest absent, missing shotlist exits 1, no map shots message), cmd_render (5: subprocess called with correct args+cwd, manifest merged with agent_animation attribution, subprocess failure exits 1, missing shotlist exits 1, no map shots exits 0)
- **test_manifest.py** (7 tests): TestManifestMerge (6: creates when absent, appends without overwriting, skips duplicates, gap status update, atomic write valid JSON, required fields verified), TestEmptyManifest (1: correct skeleton)

Also added Observability Impact section to T03-PLAN.md per pre-flight requirement.

## Verification

- `pytest tests/test_animation/ -v` — 22 passed in 0.17s ✓
- `pytest tests/test_graphics_generator/ tests/test_animation/ -v` — 91 passed in 4.48s, no regressions ✓
- Slice verification: `pytest tests/test_animation/ -v` — ✅ all tests pass
- Slice verification: `python -m animation load` and `python -m animation status` — deferred (require project data, covered by T02)

## Diagnostics

- `pytest tests/test_animation/ -v --tb=short` — quick contract regression check for animation CLI
- Test names map 1:1 to CLI behaviors: test names include function under test + scenario
- Failed render tests verify stderr contains error messages (TypeScript errors, file-not-found)

## Deviations

Initial subprocess mock used `cmd[4]` for output path but actual command layout puts output at `cmd[5]` (after MapComposition). Fixed immediately after first test run.

## Known Issues

- `tests/test_visual_orchestrator/` has pre-existing import errors (ModuleNotFoundError: visual_orchestrator) — unrelated to this task, existed before S04.

## Files Created/Modified

- `tests/test_animation/__init__.py` — Test package init
- `tests/test_animation/test_cli.py` — 15 tests for resolve_project_dir, cmd_load, cmd_render with mocked subprocess
- `tests/test_animation/test_manifest.py` — 7 tests for _merge_manifest and _empty_manifest
- `.gsd/milestones/M002/slices/S04/tasks/T03-PLAN.md` — Added Observability Impact section
