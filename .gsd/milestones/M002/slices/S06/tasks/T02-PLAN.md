---
estimated_steps: 6
estimated_files: 4
---

# T02: Execute full pipeline on Duplessis Orphans and pass integration tests

**Slice:** S06 — End-to-End Integration
**Milestone:** M002

## Description

Run each skill CLI in sequence on the Duplessis Orphans project to produce a complete organized asset folder. This involves [HEURISTIC] stages (shotlist generation, search plan authoring) where Claude reasons about the content, interleaved with deterministic CLI execution. The task ends when `pytest tests/test_integration/ -v` passes — proving all cross-skill contracts hold on real data.

## Steps

1. **Generate real shotlist.json:** Run `python -m visual_orchestrator load "Duplessis"` to get context. Using the loaded Script.md + VISUAL_STYLE_GUIDE, generate a proper shotlist.json with 60-100 shots covering all chapters (replacing the 1-shot stub). Run `python -m visual_orchestrator validate "Duplessis"` — must exit 0.
2. **Author search_plan.json and run acquisition:** Read the shotlist + media_urls.md. Author `search_plan.json` with entries targeting keyless sources first (archive.org, Wikimedia, direct_url from media_urls.md). Sources requiring API keys (Pexels, Pixabay, Smithsonian) are optional — use if keys are available, skip if not. Run `python -m media_acquisition acquire "Duplessis"`. Verify manifest.json created with `python -m media_acquisition status "Duplessis"`.
3. **Run graphics generator:** Run `python -m graphics_generator generate "Duplessis" --code-gen-only` for any animation-type shots needing code-gen graphics. If no animation shots exist in shotlist, this exits 0 with a message — that's valid.
4. **Run animation skill:** Run `python -m animation render "Duplessis"`. If 0 map shots in the shotlist, exits 0 with "No map shots" — valid. If map shots exist, Remotion renders .mp4 clips.
5. **Run asset manager:** Run `python -m asset_manager organize "Duplessis"`. Verify numbered files exist, manifest finalized, _pool/ created for any unmatched assets. Check with `python -m asset_manager status "Duplessis"`.
6. **Run integration tests:** `pytest tests/test_integration/ -v` — all tests must pass. Also run `pytest tests/ -v -m "not integration"` to confirm no regressions.

## Must-Haves

- [ ] shotlist.json has ≥20 shots and passes schema validation
- [ ] manifest.json exists and passes schema validation
- [ ] At least one real asset downloaded from a live source
- [ ] Asset manager organize produces numbered files with 3-digit prefixes
- [ ] All manifest gaps are terminal (filled or unfilled)
- [ ] `pytest tests/test_integration/ -v` — all tests pass
- [ ] No regression in existing unit tests

## Verification

- `python -m visual_orchestrator validate "Duplessis"` exits 0
- `python -m media_acquisition status "Duplessis"` shows gap coverage
- `python -m asset_manager status "Duplessis"` shows organized state
- `pytest tests/test_integration/ -v` — all pass
- `pytest tests/ -v -m "not integration"` — no regressions

## Observability Impact

- Signals added/changed: none (using existing skill CLI stderr output)
- How a future agent inspects this: `python -m asset_manager status "Duplessis"` for final state; `pytest tests/test_integration/ -v` for contract validation
- Failure state exposed: schema validators produce shot-ID-labeled error lists; each CLI exits non-zero on failure

## Inputs

- `tests/test_integration/test_pipeline.py` — from T01, the validation tests that define "done"
- `projects/1. The Duplessis Orphans.../Script.md` — 123-line narrated script
- `projects/1. The Duplessis Orphans.../research/media_urls.md` — visual media catalog with direct URLs
- `context/visual-references/*/VISUAL_STYLE_GUIDE.md` — building block decision framework
- All 5 skill CLIs installed via pytest.ini pythonpath

## Expected Output

- `projects/1. The Duplessis Orphans.../shotlist.json` — real 60-100 shot shotlist (replaces stub)
- `projects/1. The Duplessis Orphans.../assets/manifest.json` — schema-valid manifest with assets and terminal gaps
- `projects/1. The Duplessis Orphans.../assets/search_plan.json` — search plan used for acquisition
- `projects/1. The Duplessis Orphans.../assets/` — type folders with numbered assets
- Green `pytest tests/test_integration/ -v` run
