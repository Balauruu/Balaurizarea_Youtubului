---
estimated_steps: 4
estimated_files: 3
---

# T01: Fix pytest config and write integration validation test suite

**Slice:** S06 — End-to-End Integration
**Milestone:** M002

## Description

Two problems to solve: (1) pytest.ini is missing visual-orchestrator/scripts in pythonpath, causing 20 tests to fail on collection, and (2) the integration test suite that validates pipeline outputs doesn't exist yet. The tests are post-hoc validators — they read files from the Duplessis project directory and check schema validity, file existence, and contract compliance. They skip gracefully when pipeline artifacts are missing.

## Steps

1. Add `.claude/skills/visual-orchestrator/scripts` to pytest.ini pythonpath. Run `pytest tests/test_visual_orchestrator/ -v` to confirm the 20 tests now collect and pass.
2. Create `tests/test_integration/__init__.py` and `tests/test_integration/test_pipeline.py`.
3. Write test functions using `@pytest.mark.integration` marker:
   - `test_shotlist_exists_and_valid` — shotlist.json exists, passes `validate_shotlist()` with 0 errors, has ≥20 shots
   - `test_manifest_exists_and_valid` — manifest.json exists, passes `validate_manifest()` with 0 errors
   - `test_numbered_assets_exist` — at least one file in assets/ type folders matches `\d{3}_` prefix pattern
   - `test_gaps_are_terminal` — all gaps in manifest have status "filled" or "unfilled" (no "pending_generation" remaining)
   - `test_asset_folders_match_manifest` — every asset in manifest has a corresponding file on disk
   - `test_shotlist_drives_manifest` — every shot_id referenced in manifest assets exists in shotlist.json
   - Each test skips with `pytest.skip()` if the required input file doesn't exist (graceful pre-pipeline behavior)
4. Add `integration` marker to pytest.ini markers list if not already there. Run `pytest tests/test_integration/ -v` to confirm tests collect and skip (artifacts don't exist yet).

## Must-Haves

- [ ] visual-orchestrator/scripts in pytest.ini pythonpath
- [ ] ≥6 integration test functions in test_pipeline.py
- [ ] All tests use `@pytest.mark.integration` marker
- [ ] Tests skip gracefully when pipeline artifacts are missing
- [ ] `pytest tests/ --co -m "not integration"` collects all tests without import errors

## Verification

- `pytest tests/test_visual_orchestrator/ -v` — 20 tests pass (previously broken)
- `pytest tests/ --co -m "not integration"` — full collection with no import errors
- `pytest tests/test_integration/ -v` — tests collect, skip with clear messages

## Inputs

- `pytest.ini` — current config missing visual-orchestrator pythonpath
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/schema.py` — `validate_shotlist()` function
- `.claude/skills/media-acquisition/scripts/media_acquisition/schema.py` — `validate_manifest()` function
- S06-RESEARCH.md — constraint that tests validate outputs, not re-run the pipeline

## Expected Output

- `pytest.ini` — updated with visual-orchestrator pythonpath
- `tests/test_integration/__init__.py` — package init
- `tests/test_integration/test_pipeline.py` — ≥6 integration test functions

## Observability Impact

- **New signal:** `pytest tests/test_integration/ -v` provides pass/fail/skip status for each pipeline contract (shotlist schema, manifest schema, numbered assets, gap lifecycle, cross-reference integrity)
- **Failure inspection:** Each test prints the specific validation errors or missing files on failure, making root-cause attribution immediate
- **Pre-pipeline state:** All integration tests skip with descriptive messages when artifacts don't exist yet — a future agent can distinguish "not yet run" from "run and broken"
