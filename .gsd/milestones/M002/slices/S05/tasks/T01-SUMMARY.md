---
id: T01
parent: S05
milestone: M002
provides:
  - asset-manager skill with load/organize/status CLI
  - Sequential numbering of assets by shotlist order
  - Unmapped asset pooling and gap finalization
key_files:
  - .claude/skills/asset-manager/scripts/asset_manager/cli.py
  - tests/test_asset_manager/test_organize.py
  - tests/test_asset_manager/test_cli.py
key_decisions:
  - Unmapped assets removed from manifest (not tracked with folder "_pool") — _pool/ is outside the pipeline
  - Prefix strip-and-reapply strategy for idempotent re-runs rather than skip-if-numbered
patterns_established:
  - Same CLI pattern (D002) with load/organize/status subcommands
  - Cross-skill import of validate_manifest via PYTHONPATH
observability_surfaces:
  - "cmd_status" diagnostic command prints numbered/unnumbered/pool counts and gap breakdown
  - stderr trace during organize logs each rename, pool move, gap finalization, and validation result
  - Non-zero exit on any validation or I/O failure
duration: 20m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Implement asset-manager skill with CLI, organize logic, and tests

**Built complete asset-manager skill: CLI with load/organize/status commands, sequential numbering by shotlist order, unmapped pooling, gap finalization, and 28 passing tests.**

## What Happened

Created the asset-manager skill scaffold following the established D002 CLI pattern. Core organize logic in `cli.py` implements:

1. `_build_shot_order()` — maps shot IDs to 1-based sequence numbers from shotlist array
2. `_compute_numbering()` — assigns each asset its earliest mapped shot's sequence number; assets with no valid mapped shots become unmapped
3. `_strip_existing_prefix()` / `_add_prefix()` — idempotent prefix management via regex
4. `cmd_organize()` — full orchestrator: validate manifest → compute numbering → rename in-place → pool unmapped → remove from manifest → finalize gaps → validate → atomic write
5. `cmd_load()` — prints SHOTLIST, MANIFEST, CHANNEL_DNA labeled sections
6. `cmd_status()` — reads manifest + scans folders, reports organization state

Edge cases handled: cross-folder numbering (global, not per-folder), multiple assets on same shot (same prefix), multi-shot assets (earliest wins), pool directory collision avoidance, re-run idempotency.

## Verification

- `pytest tests/test_asset_manager/ -v` — **28 passed** covering all must-haves: numbering, multi-shot, same-shot, pool, gap finalization, idempotency, manifest validity, CLI routing, load/status output format
- `pytest tests/ -v` — **473 passed, 1 failed** (pre-existing `test_ddg_links_extraction` failure from crawl4ai API change, unrelated)
- CLI smoke test: `python -m asset_manager status "Duplessis Orphans"` — exits 1 with "No manifest.json found" (correct: no manifest exists yet in the project; upstream skills haven't run)
- `python -m asset_manager --help` — shows all three subcommands

Slice-level verification:
- ✅ `pytest tests/test_asset_manager/ -v` — all 28 pass
- ⚠️ `status "Duplessis Orphans"` exits 1 (no manifest in project yet — prerequisite artifact from S02)
- ✅ No regressions: 473 passed across all suites

## Diagnostics

- Run `python -m asset_manager status "Topic"` to inspect organization state after organize
- stderr output during `cmd_organize` shows rename/pool/gap trace
- Manifest validity checked pre and post organize; invalid post-state prevents write

## Deviations

- `status` smoke test exits 1 instead of 0 because the Duplessis project has no manifest.json yet (S02 media-acquisition hasn't run). The CLI behavior is correct — it reports the missing file clearly.

## Known Issues

- `resolve_project_dir` is now duplicated across 5 skills. Not blocking but noted for future shared-utils extraction.

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
- `.gsd/milestones/M002/slices/S05/S05-PLAN.md` — Added Observability section
- `.gsd/milestones/M002/slices/S05/tasks/T01-PLAN.md` — Added Observability Impact section
