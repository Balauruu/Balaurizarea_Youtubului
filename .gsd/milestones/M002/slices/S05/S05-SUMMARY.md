---
id: S05
parent: M002
milestone: M002
provides:
  - asset-manager skill with load/organize/status CLI
  - Sequential numbering of assets by shotlist order (001_, 002_, ...)
  - Unmapped asset pooling to _pool/ with manifest cleanup
  - Gap finalization (pending_generation → unfilled)
  - Idempotent re-runs via prefix strip-and-reapply
requires:
  - slice: S01
    provides: shotlist.json schema and shot ordering
  - slice: S02
    provides: manifest.json schema and validate_manifest(), type folders with acquired assets
  - slice: S03
    provides: generated graphics in assets/vectors/ with manifest updates
  - slice: S04
    provides: rendered animations in assets/animations/ with manifest updates
affects:
  - S06
key_files:
  - .claude/skills/asset-manager/scripts/asset_manager/cli.py
  - tests/test_asset_manager/test_organize.py
  - tests/test_asset_manager/test_cli.py
  - .claude/skills/asset-manager/CONTEXT.md
  - .claude/skills/asset-manager/SKILL.md
key_decisions:
  - D023: Unmapped assets removed from manifest — _pool/ is outside the pipeline, not tracked
  - D024: Prefix strip-and-reapply for idempotent re-runs rather than skip-if-numbered
patterns_established:
  - Same D002 context-loader CLI pattern with load/organize/status subcommands
  - Cross-skill import of validate_manifest from media_acquisition.schema via PYTHONPATH
observability_surfaces:
  - "cmd_status" diagnostic command prints numbered/unnumbered/pool counts and gap breakdown
  - stderr trace during organize logs each rename, pool move, gap finalization, and validation result
  - Non-zero exit on validation or I/O failure
drill_down_paths:
  - .gsd/milestones/M002/slices/S05/tasks/T01-SUMMARY.md
duration: 20m
verification_result: passed
completed_at: 2026-03-15
---

# S05: Asset Manager Skill

**Complete asset-manager skill that numbers assets by shotlist order, pools unmapped files, finalizes gaps, and validates manifest integrity — with 28 passing tests.**

## What Happened

Built the asset-manager skill as a single task (T01) — the logic is deterministic file operations with no external dependencies or natural split point.

Core organize pipeline in `cli.py`:
1. `_build_shot_order()` maps shot IDs to 1-based sequence numbers from shotlist.json
2. `_compute_numbering()` assigns each asset its earliest mapped shot's sequence number; assets with no valid mapped shots become unmapped
3. `_strip_existing_prefix()` / `_add_prefix()` handle idempotent prefix management via regex
4. `cmd_organize()` orchestrates: validate manifest → compute numbering → rename files in-place → pool unmapped → remove pooled from manifest → finalize gaps → validate → atomic write

Edge cases handled: cross-folder numbering (global sequence, not per-folder), multiple assets on same shot (shared prefix), multi-shot assets (earliest wins), pool directory collision avoidance, re-run idempotency via strip-and-reapply.

CLI follows D002 pattern: `load` (prints shotlist + manifest + channel context), `organize` (runs the pipeline), `status` (reports numbered/unnumbered/pool counts and gap breakdown).

## Verification

- `pytest tests/test_asset_manager/ -v` — **28 passed** covering: numbering assignment, multi-shot earliest-wins, same-shot sharing, pool moves, gap finalization, idempotency, manifest validity, CLI routing, load/status output format
- `pytest tests/ -v` — **473 passed, 1 failed** (pre-existing `test_ddg_links_extraction` from crawl4ai API change, unrelated)
- CLI smoke: `python -m asset_manager status "Duplessis Orphans"` exits 1 with "No manifest.json found" (correct: upstream S02 hasn't run)

## Requirements Advanced

- R008 (Sequential asset numbering) — Numbering by shotlist order implemented with multi-shot earliest-wins logic, validated by 19 organize tests
- R009 (Unmatched assets to _pool/) — Pool move + manifest removal implemented, tested
- R010 (Gap lifecycle tracking) — pending_generation → unfilled finalization implemented, tested
- R011 (Raw assets without pre-styling) — No content modification of any asset file; organize only renames

## Requirements Validated

- R008 — 19 tests prove sequential numbering, multi-shot, same-shot, cross-folder, and idempotency
- R009 — Tests prove unmapped assets move to _pool/ and are removed from manifest
- R010 — Tests prove gap finalization from pending_generation to unfilled
- R011 — Organize only renames files (prefix changes); no content modification code exists

## New Requirements Surfaced

- None

## Requirements Invalidated or Re-scoped

- None

## Deviations

- `status "Duplessis Orphans"` exits 1 instead of plan's expected exit 0 — correct behavior since no manifest.json exists yet (S02 hasn't run on this project). The plan's verification expectation was optimistic about upstream state.

## Known Limitations

- `resolve_project_dir` is duplicated across 5 skills — noted for future shared-utils extraction
- Live pipeline validation deferred to S06 (no real manifest exists in Duplessis project yet)

## Follow-ups

- S06 end-to-end integration will prove the full chain: shotlist → acquire → generate → animate → organize

## Files Created/Modified

- `.claude/skills/asset-manager/scripts/asset_manager/__init__.py` — Package init
- `.claude/skills/asset-manager/scripts/asset_manager/__main__.py` — CLI entry point
- `.claude/skills/asset-manager/scripts/asset_manager/cli.py` — Complete CLI with organize logic
- `.claude/skills/asset-manager/CONTEXT.md` — Stage contract
- `.claude/skills/asset-manager/SKILL.md` — Usage guide
- `tests/test_asset_manager/__init__.py` — Test package init
- `tests/test_asset_manager/test_organize.py` — 19 tests for core organize logic
- `tests/test_asset_manager/test_cli.py` — 9 tests for CLI routing and output format
- `pytest.ini` — Added asset-manager scripts to pythonpath

## Forward Intelligence

### What the next slice should know
- Asset manager imports `validate_manifest` from `media_acquisition.schema` — PYTHONPATH must include both skill script dirs
- The organize command expects manifest.json and shotlist.json to already exist in the project's assets/ directory
- Numbering is global across all type folders, not per-folder — the sequence is driven entirely by shotlist order

### What's fragile
- Cross-skill import path (`media_acquisition.schema`) — if media-acquisition restructures, asset-manager breaks
- `resolve_project_dir` duplication across 5 skills — any behavior change must be replicated manually

### Authoritative diagnostics
- `python -m asset_manager status "Topic"` — shows organized/unorganized/pool counts and gap breakdown; first thing to check after running organize
- stderr output during organize — logs every rename, pool move, and gap finalization

### What assumptions changed
- Plan assumed `status "Duplessis Orphans"` would exit 0 — actually exits 1 because no manifest exists yet (correct behavior, upstream dependency)
