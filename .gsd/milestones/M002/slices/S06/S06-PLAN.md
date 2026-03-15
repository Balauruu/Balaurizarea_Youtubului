# S06: End-to-End Integration

**Goal:** Full pipeline proven on Duplessis Orphans project — Script.md → organized numbered asset folder with valid manifest
**Demo:** `pytest tests/test_integration/ -v` passes, validating that shotlist.json, manifest.json, numbered assets, and gap lifecycle are all correct in the Duplessis project

## Must-Haves

- pytest.ini includes visual-orchestrator pythonpath (unblocks 20 broken tests)
- Real shotlist.json generated from Duplessis Script.md (replaces 1-shot stub)
- Media acquisition executed with at least one source producing real downloads
- Graphics generator executed (--code-gen-only acceptable if ComfyUI unavailable)
- Asset manager organize produces numbered files and finalized manifest
- Integration test suite validates all pipeline output contracts post-hoc
- All existing tests still pass (no regressions)

## Proof Level

- This slice proves: final-assembly
- Real runtime required: yes (live API calls, file I/O, subprocess rendering)
- Human/UAT required: no (visual quality review is separate — this proves the pipeline mechanics)

## Verification

- `pytest tests/test_integration/ -v` — post-hoc validation of pipeline outputs (shotlist schema, manifest schema, numbered assets, gap lifecycle)
- `pytest tests/ -v -m "not integration"` — full unit test suite passes including previously broken visual-orchestrator tests
- Duplessis project `assets/` contains numbered files in type folders and valid `manifest.json`
- Schema validators produce grep-friendly error output when given invalid data: `python -c "from visual_orchestrator.schema import validate_shotlist; print(validate_shotlist({}))"` returns non-empty error list

## Observability / Diagnostics

- Runtime signals: each skill CLI prints stderr progress (per-shot, per-source, per-rename logs)
- Inspection surfaces: `python -m asset_manager status "Duplessis"` shows final organized state; `python -m media_acquisition status "Duplessis"` shows gap coverage
- Failure visibility: schema validators on shotlist and manifest produce grep-friendly error lists with shot/asset IDs

## Integration Closure

- Upstream surfaces consumed: shotlist.json (S01), manifest.json (S02-S04), assets/ type folders (S02-S04), shotlist order (S05)
- New wiring introduced: integration test suite that validates cross-skill contracts on real data
- What remains before the milestone is truly usable end-to-end: nothing — this slice is the milestone's definition of done

## Tasks

- [x] **T01: Fix pytest config and write integration validation test suite** `est:25m`
  - Why: pytest.ini missing visual-orchestrator pythonpath breaks 20 tests; integration tests needed as the objective stopping condition for the pipeline run
  - Files: `pytest.ini`, `tests/test_integration/__init__.py`, `tests/test_integration/test_pipeline.py`
  - Do: Add visual-orchestrator/scripts to pytest.ini pythonpath. Write test_pipeline.py with `@pytest.mark.integration` marker that validates Duplessis project outputs: shotlist.json passes `validate_shotlist()`, manifest.json passes `validate_manifest()`, numbered assets exist in type folders with 3-digit prefix pattern, gaps are terminal (filled or unfilled), _pool/ exists. Tests skip gracefully if pipeline hasn't run yet (missing files).
  - Verify: `pytest tests/ -v -m "not integration" --co` collects all tests including 20 visual-orchestrator tests; `pytest tests/test_integration/ -v` runs (tests skip until pipeline artifacts exist)
  - Done when: all existing tests collect without import errors; integration test file exists with ≥6 test functions

- [x] **T02: Execute full pipeline on Duplessis Orphans and pass integration tests** `est:45m`
  - Why: This is the actual end-to-end proof — running each skill in sequence on real data and validating the output chain
  - Files: `projects/1. The Duplessis Orphans.../shotlist.json`, `projects/1. The Duplessis Orphans.../assets/manifest.json`, `projects/1. The Duplessis Orphans.../assets/**`
  - Do: (1) Run visual orchestrator `load` → generate real shotlist.json with 60-100 shots → `validate`. (2) Author search_plan.json from shotlist + media_urls.md → run `acquire` using keyless sources (archive.org, Wikimedia, direct_url) → verify manifest.json. (3) Run graphics generator `generate --code-gen-only` for animation-type shots. (4) Run animation skill (0 map shots = valid exit 0). (5) Run asset manager `organize` → verify numbered files + finalized manifest. (6) Run `pytest tests/test_integration/ -v` — all tests pass.
  - Verify: `pytest tests/test_integration/ -v` — all integration tests pass; `python -m asset_manager status "Duplessis"` shows organized state
  - Done when: integration tests pass, manifest.json is schema-valid with at least some filled assets, numbered files exist in project assets/

## Files Likely Touched

- `pytest.ini`
- `tests/test_integration/__init__.py`
- `tests/test_integration/test_pipeline.py`
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/shotlist.json`
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/manifest.json`
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/search_plan.json`
