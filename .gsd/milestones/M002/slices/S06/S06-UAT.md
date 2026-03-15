# S06: End-to-End Integration — UAT

**Milestone:** M002
**Written:** 2026-03-15

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: Pipeline produces file artifacts (shotlist.json, manifest.json, numbered assets) that can be validated by schema checks and filesystem inspection. No live UI or running server.

## Preconditions

- Pipeline has been executed on Duplessis Orphans project (T02 completed)
- PYTHONPATH includes all skill script directories (set via pytest.ini for tests, or manually for CLI)
- Python 3.13+ available with pytest installed

## Smoke Test

Run `pytest tests/test_integration/ -v` — all 6 tests should pass in under 1 second.

## Test Cases

### 1. Shotlist schema validation

1. Run: `PYTHONPATH=".claude/skills/visual-orchestrator/scripts" python -m visual_orchestrator validate "Duplessis"`
2. **Expected:** Exit code 0, output says "Validation PASSED" with 73 shots

### 2. Shotlist shot count and distribution

1. Open `projects/1. The Duplessis Orphans Quebec's Stolen Children/shotlist.json`
2. Count entries in the `shots` array
3. Check `shotlist_type` distribution includes: archival_photo, archival_video, document_scan, animation, text_overlay, map
4. **Expected:** 73 shots total, all 6 types present, every shot has id/chapter/narrative_context/visual_need/building_block/shotlist_type

### 3. Manifest schema and asset count

1. Run: `PYTHONPATH=".claude/skills/media-acquisition/scripts:.claude/skills/asset-manager/scripts" python -m asset_manager status "Duplessis"`
2. **Expected:** 21 numbered assets, 0 unnumbered, 21 unfilled gaps, 0 pending_generation

### 4. Numbered assets on disk

1. List files in `projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/archival_photos/`
2. List files in `projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/vectors/`
3. **Expected:** Every file starts with a 3-digit prefix (e.g., `001_`, `014_`). At least 5 files in archival_photos, at least 16 in vectors.

### 5. Gap lifecycle terminal state

1. Open `projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/manifest.json`
2. Inspect the `gaps` array
3. **Expected:** Every gap has status "unfilled" or "filled". Zero gaps with status "pending_generation".

### 6. Manifest-to-disk consistency

1. For each entry in manifest.json `assets` array, check that `folder/filename` exists on disk
2. **Expected:** Every manifest asset has a corresponding file. No orphan manifest entries.

### 7. Shotlist drives manifest

1. Collect all `shot_id` values from manifest.json assets (in `mapped_shots` arrays)
2. Collect all `id` values from shotlist.json shots
3. **Expected:** Every shot_id in the manifest exists in the shotlist. No phantom shot references.

### 8. Unit test regression check

1. Run: `pytest tests/ -v -m "not integration"`
2. **Expected:** 490 tests pass, 0 failures, 0 errors

### 9. Schema validator diagnostic output

1. Run: `PYTHONPATH=".claude/skills/visual-orchestrator/scripts" python -c "from visual_orchestrator.schema import validate_shotlist; print(validate_shotlist({}))" `
2. **Expected:** Returns a list of 4 error strings, each identifying a missing required key. Output is grep-friendly (one error per list element).

## Edge Cases

### Empty shotlist input to schema validator

1. Run: `PYTHONPATH=".claude/skills/visual-orchestrator/scripts" python -c "from visual_orchestrator.schema import validate_shotlist; print(validate_shotlist({'generated':'x','guide_source':'x','project':'x','shots':[]}))" `
2. **Expected:** Returns error list including "shots array is empty" or similar

### Missing pipeline artifacts

1. Temporarily rename `projects/1. The Duplessis Orphans Quebec's Stolen Children/shotlist.json` to `shotlist.json.bak`
2. Run: `pytest tests/test_integration/test_pipeline.py::test_shotlist_exists_and_valid -v`
3. **Expected:** Test reports SKIPPED (not FAILED) with message about missing file
4. Rename back to `shotlist.json`

### Re-running asset manager organize (idempotency)

1. Run asset manager organize on the already-organized Duplessis project
2. **Expected:** Same 21 numbered files, same manifest. No duplicate prefixes, no files renamed incorrectly.

## Failure Signals

- Any integration test in `pytest tests/test_integration/ -v` reports FAILED
- `python -m asset_manager status "Duplessis"` shows pending_generation > 0
- Numbered files missing 3-digit prefix or have duplicate numbers
- manifest.json references files that don't exist on disk
- Unit test count drops below 490 or any test fails

## Requirements Proved By This UAT

- R001 — shotlist.json generated from Script.md with building block assignments (test case 1, 2)
- R002 — text overlay entries present in shotlist with no generated assets (test case 2)
- R003 — multi-source media acquisition with live downloads (test case 3, 4)
- R004 — asset-to-shot matching with gap identification (test case 5, 7)
- R005 — code-generated flat graphics (test case 4 — vectors/ folder)
- R008 — sequential asset numbering (test case 4)
- R009 — _pool/ for unmatched assets (test case 3 — 0 unnumbered confirms no strays)
- R010 — gap lifecycle tracking (test case 5)
- R011 — raw assets without pre-styling (test case 4 — files are raw downloads/renders)

## Not Proven By This UAT

- R006 — ComfyUI creative asset generation (server not running, --code-gen-only mode used)
- R007 — Remotion animated map rendering (npx not available on this system)
- Visual quality of generated assets (requires human editorial review in DaVinci Resolve)
- archive.org search effectiveness (returned 0 results — query formulation needs work)

## Notes for Tester

- All CLI commands require PYTHONPATH set to include the relevant skill scripts directories. pytest handles this via pytest.ini, but manual CLI invocations need: `PYTHONPATH=".claude/skills/asset-manager/scripts:.claude/skills/media-acquisition/scripts:.claude/skills/visual-orchestrator/scripts"`
- The 21 unfilled gaps are expected — they represent shots where no source had matching content or where ComfyUI/Remotion would have filled them
- The Duplessis project path has spaces and an apostrophe-less name: `projects/1. The Duplessis Orphans Quebec's Stolen Children/`
