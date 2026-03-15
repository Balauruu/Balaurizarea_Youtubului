---
id: T03
parent: S02
milestone: M002
provides:
  - acquire subcommand with search→download→manifest→gap pipeline
  - Gap identification comparing shotlist.json vs manifest mapped_shots
  - Incremental acquisition with source_url deduplication
  - Atomic manifest writes via temp file + rename
key_files:
  - .claude/skills/media-acquisition/scripts/media_acquisition/acquire.py
  - .claude/skills/media-acquisition/scripts/media_acquisition/cli.py
  - tests/test_media_acquisition/test_acquire.py
key_decisions:
  - "Gap identification only flags acquisition-relevant types (archival_photo, archival_video, document_scan) — animation/map gaps are expected and handled by S03/S04"
  - "Incremental merge deduplicates by source_url with existing assets taking priority"
  - "Atomic writes use tempfile.mkstemp in same directory + rename; on Windows, target is unlinked first"
patterns_established:
  - execute_plan() separates search/download orchestration from gap analysis and manifest building — each is independently testable
  - All tests mock at the get_source() boundary — no real HTTP calls, no SOURCE_REGISTRY patching needed
observability_surfaces:
  - Per-entry search/download progress logged to stderr via source adapter _log_download
  - source_summary in manifest.json tracks searched/downloaded counts per source
  - `python -m media_acquisition status "<topic>"` reads manifest and prints gap count, coverage %, source stats
  - Schema validation warnings printed to stderr if manifest has issues post-build
duration: 15min
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T03: Acquire subcommand with download orchestration, manifest bookkeeping, and gap analysis

**Built the `acquire` CLI subcommand that reads search_plan.json, executes searches/downloads via source adapters, produces schema-valid manifest.json with asset-to-shot mappings, and identifies acquisition gaps as pending_generation.**

## What Happened

Implemented `acquire.py` as a self-contained orchestrator with clear function boundaries: `load_search_plan()` validates the plan, `execute_plan()` iterates entries calling source search/download, `identify_gaps()` compares shotlist shots against manifest mapped_shots, `merge_assets()` deduplicates by source_url for incremental runs, and `write_manifest_atomic()` uses temp+rename for safe writes.

Gap identification only flags shots with acquisition-relevant `shotlist_type` values (archival_photo, archival_video, document_scan). Animation, motion_graphic, and other types are expected gaps handled by downstream slices.

Added `acquire` subcommand to `cli.py` that takes topic + search_plan path, creates the four asset subdirectories, and runs the full pipeline. Also added `pytest.ini` pythonpath entry for media-acquisition scripts so tests discover the module.

## Verification

- `pytest tests/test_media_acquisition/test_acquire.py -v` — **27 passed**
- `pytest tests/test_media_acquisition/ -v` — **102 passed** (T01: 31, T02: 32 + sources, T03: 27, all clean)
- Manifest output from `run_acquire()` passes `validate_manifest()` in integration test
- Incremental merge verified: same URLs → no duplicates; different URLs → additive
- Slice CLI checks: `load "Duplessis Orphans"` exits 0; `status "Duplessis Orphans"` exits 1 with "no manifest" message (correct pre-acquisition)

## Diagnostics

- `python -m media_acquisition status "<topic>"` — gap count, coverage %, source summary, per-status breakdown
- `python -m media_acquisition acquire "<topic>" search_plan.json` — prints per-source download counts on completion
- stderr during acquire shows `[source] OK/FAIL url (size KB)` per download
- Schema validation warnings appear on stderr if built manifest has issues
- Each gap in manifest.json carries `visual_need` and `shotlist_type` for downstream triage

## Deviations

- Added `.claude/skills/media-acquisition/scripts` to `pytest.ini` pythonpath — needed for test discovery; wasn't in the plan but required for the test infrastructure to work.

## Known Issues

None.

## Files Created/Modified

- `.claude/skills/media-acquisition/scripts/media_acquisition/acquire.py` — download orchestrator with plan loading, search/download execution, gap identification, merge, and atomic manifest write
- `.claude/skills/media-acquisition/scripts/media_acquisition/cli.py` — added `acquire` subcommand with topic + search_plan args
- `tests/test_media_acquisition/test_acquire.py` — 27 tests covering plan loading, execution, gap identification, merge, manifest validation, atomic writes, incremental runs, CLI wiring
- `pytest.ini` — added media-acquisition scripts to pythonpath
- `.gsd/milestones/M002/slices/S02/tasks/T03-PLAN.md` — added Observability Impact section
