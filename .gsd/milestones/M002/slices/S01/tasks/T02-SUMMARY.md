---
id: T02
parent: S01
milestone: M002
provides:
  - Pytest test suite proving shotlist.json schema contract (20 tests across CLI + schema)
key_files:
  - tests/test_visual_orchestrator/test_cli.py
  - tests/test_visual_orchestrator/test_schema.py
key_decisions: []
patterns_established:
  - Visual orchestrator tests follow writer test pattern exactly (tmp_path, capsys, mock _get_project_root)
  - Schema tests use a shared valid_shotlist pytest fixture, each test modifies it minimally to trigger one error class
observability_surfaces:
  - "Run `pytest tests/test_visual_orchestrator/ -v` to verify all schema contract clauses"
duration: 15min
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Write tests and validate schema contract

**20 pytest tests covering CLI context loading (10) and schema validation (10), all passing. Full suite 272/273 pass (1 pre-existing failure unrelated).**

## What Happened

Created test_cli.py with 10 tests: 4 for resolve_project_dir (substring match, case-insensitive, scratch fallback, ambiguous raises ValueError) and 6 for cmd_load (script content, visual guide content, channel DNA content, shotlist.json output path, generation prompt path, missing Script.md exits 1). Followed writer test patterns exactly — tmp_path fixtures, capsys for stdout, mock `_get_project_root`.

Created test_schema.py with 10 tests: valid fixture passes, missing top-level key, missing shot field, invalid shotlist_type enum, invalid ID format, text_overlay without text_content, non-text_overlay with text_content, back-to-back glitch shots, >3 consecutive text_overlay, >3 consecutive Silhouette Figure animation. Each test uses a shared `valid_shotlist` fixture and makes one minimal change to trigger exactly one error.

## Verification

- `pytest tests/test_visual_orchestrator/ -v` — **20 passed in 0.11s**
- `pytest tests/ -v` — **272 passed, 1 failed** (pre-existing `test_ddg_links_extraction` failure due to crawl4ai API change — unrelated to this slice)
- Slice-level checks:
  - ✅ `pytest tests/test_visual_orchestrator/ -v` — all tests pass
  - ✅ Tests cover: project dir resolution, CLI stdout content, schema validation, sequencing enforcement, text overlay validation

## Diagnostics

- Run `pytest tests/test_visual_orchestrator/ -v` to verify the shotlist.json contract after any schema.py or cli.py change
- Each test function name encodes the exact condition tested — pytest failure output identifies which contract clause broke

## Deviations

None.

## Known Issues

- Pre-existing `test_ddg_links_extraction` failure in researcher test suite (crawl4ai `extract_links` parameter removed in newer version). Not related to this task or slice.

## Files Created/Modified

- `tests/test_visual_orchestrator/test_cli.py` — 10 CLI tests (resolve_project_dir + cmd_load)
- `tests/test_visual_orchestrator/test_schema.py` — 10 schema validator tests (valid/invalid fixtures, sequencing)
- `.gsd/milestones/M002/slices/S01/tasks/T02-PLAN.md` — Added Observability Impact section (pre-flight fix)
