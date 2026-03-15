---
id: T01
parent: S06
milestone: M002
provides:
  - visual-orchestrator pythonpath fix in pytest.ini (unblocks 20 tests)
  - integration test suite with 6 post-hoc pipeline validators
key_files:
  - pytest.ini
  - tests/test_integration/test_pipeline.py
key_decisions:
  - Tests that find existing stub artifacts (1-shot shotlist, empty assets/) fail rather than skip — correct behavior since skip means "artifact missing" not "artifact incomplete"
patterns_established:
  - Integration tests use _load_json_or_skip() helper for consistent skip-when-missing behavior
  - All integration tests marked @pytest.mark.integration, excluded from default runs via -m "not integration"
observability_surfaces:
  - "pytest tests/test_integration/ -v" shows pass/fail/skip per pipeline contract
  - Each test prints specific validation errors or missing files on failure
  - Pre-pipeline state: all tests skip with descriptive messages when artifacts don't exist
duration: 12m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Fix pytest config and write integration validation test suite

**Added visual-orchestrator to pytest.ini pythonpath (20 tests unblocked) and created 6-test integration suite validating pipeline output contracts.**

## What Happened

1. Added `.claude/skills/visual-orchestrator/scripts` to pytest.ini pythonpath. All 20 visual-orchestrator tests now collect and pass.

2. Created `tests/test_integration/test_pipeline.py` with 6 integration test functions:
   - `test_shotlist_exists_and_valid` — schema validation + ≥20 shots
   - `test_manifest_exists_and_valid` — schema validation
   - `test_numbered_assets_exist` — ≥1 file with `\d{3}_` prefix in type folders
   - `test_gaps_are_terminal` — no "pending_generation" status remaining
   - `test_asset_folders_match_manifest` — every manifest asset has a file on disk
   - `test_shotlist_drives_manifest` — every manifest shot_id exists in shotlist

   Tests import `validate_shotlist()` and `validate_manifest()` from the real schema modules. Each test skips via `pytest.skip()` when required files are missing.

3. Pre-flight fixes applied: added failure-path verification to S06-PLAN.md, added Observability Impact section to T01-PLAN.md.

## Verification

- `pytest tests/test_visual_orchestrator/ -v` — **20/20 passed** (previously broken on collection)
- `pytest tests/ --co -m "not integration"` — **490 tests collected**, 0 import errors
- `pytest tests/test_integration/ -v` — **6 tests collected** (4 skip, 2 fail on stub data — expected)
- Schema validator diagnostic: `validate_shotlist({})` returns 4 error strings (grep-friendly)

### Slice-level verification status (T01 is intermediate):
- ✅ `pytest tests/ -v -m "not integration" --co` — full collection passes
- ⏳ `pytest tests/test_integration/ -v` — tests exist, will pass after T02 runs pipeline
- ⏳ Duplessis `assets/` numbered files + valid manifest — pending T02

## Diagnostics

- Run `pytest tests/test_integration/ -v` to see pass/fail/skip status for each contract
- Failed tests print specific error lists (shot IDs, missing files, validation errors)
- Skip messages distinguish "not yet run" from "run and broken"

## Deviations

None.

## Known Issues

- Two integration tests (shotlist_exists_and_valid, numbered_assets_exist) currently fail because the Duplessis project has a 1-shot stub shotlist and empty asset type folders. This is correct behavior — T02 will generate real pipeline outputs.

## Files Created/Modified

- `pytest.ini` — added visual-orchestrator/scripts to pythonpath
- `tests/test_integration/__init__.py` — package init (empty)
- `tests/test_integration/test_pipeline.py` — 6 integration test functions with @pytest.mark.integration
- `.gsd/milestones/M002/slices/S06/S06-PLAN.md` — added failure-path verification step
- `.gsd/milestones/M002/slices/S06/tasks/T01-PLAN.md` — added Observability Impact section
