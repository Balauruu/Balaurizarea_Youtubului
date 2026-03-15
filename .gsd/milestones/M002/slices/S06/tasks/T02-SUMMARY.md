---
id: T02
parent: S06
milestone: M002
provides:
  - Full pipeline execution on Duplessis Orphans producing 73-shot shotlist, 21 organized assets, valid manifest
  - direct_url source adapter now supports URL-as-query pattern for search→download flow
key_files:
  - projects/1. The Duplessis Orphans Quebec's Stolen Children/shotlist.json
  - projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/manifest.json
  - projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/search_plan.json
key_decisions:
  - Fixed direct_url source search() to return URL as SearchResult when query is a URL — enables media_urls.md entries to flow through standard acquire pipeline
  - Fixed ASSET_TYPE_FOLDERS in integration tests to match actual folder names (archival_photos, vectors, etc.) rather than shotlist_type names
  - Added User-Agent header to direct_url downloads to avoid 403s from Wikimedia
patterns_established:
  - Shotlist generation covers prologue + all chapters, targeting 60-100 shots with sequencing constraints validated
  - Search plan uses direct_url for known URLs from media_urls.md, wikimedia_commons and archive_org for searches
observability_surfaces:
  - "python -m asset_manager status \"Duplessis\"" — shows final organized state (21 numbered, 21 unfilled gaps)
  - "python -m media_acquisition status \"Duplessis\"" — shows acquisition coverage (22%, 5 live-source assets)
  - "python -m visual_orchestrator validate \"Duplessis\"" — shotlist schema validation
  - "pytest tests/test_integration/ -v" — 6 integration tests validating cross-skill contracts
duration: ~25 minutes
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Execute full pipeline on Duplessis Orphans and pass integration tests

**Ran all 5 skill CLIs on the Duplessis project: 73-shot shotlist → 5 live-source downloads + 16 generated graphics → 21 numbered assets with valid manifest. All 6 integration tests and 490 unit tests pass.**

## What Happened

1. **Shotlist generation:** Created 73-shot shotlist covering prologue + 7 chapters. Distribution: 22 animation, 21 text_overlay, 17 document_scan, 6 archival_video, 4 archival_photo, 3 map. Passes schema validation with zero errors.

2. **Search plan + acquisition:** Authored search_plan.json targeting keyless sources. Fixed direct_url source adapter to support URL-as-query pattern (previously search() returned empty list, breaking the acquire pipeline for direct URLs). Added User-Agent header to fix Wikimedia 403s. Downloaded 5 real assets from live sources (2 from BAnQ CDN, 2 from Wikimedia Special:FilePath, 1 from Wikimedia Commons search).

3. **Graphics generator:** Generated 16 code-gen graphics (silhouettes, glitch stingers, textures, icons, noise). 6 ComfyUI blocks (concept diagrams) correctly skipped in --code-gen-only mode.

4. **Animation:** Attempted Remotion render for 3 map shots — failed with FileNotFoundError (npx not available on this Windows system). Non-blocking: map gaps flow to unfilled status.

5. **Asset manager organize:** All 21 assets numbered with 3-digit prefixes by shotlist order. Zero unmapped assets. 21 gaps finalized from pending_generation → unfilled.

6. **Integration tests:** Fixed ASSET_TYPE_FOLDERS in test_pipeline.py to match actual folder names (archival_photos/vectors/etc. vs. the shotlist_type names the test was using). All 6 tests pass. All 490 unit tests pass with no regressions.

## Verification

- `python -m visual_orchestrator validate "Duplessis"` — exits 0 (73 shots valid)
- `python -m media_acquisition status "Duplessis"` — 5 assets, 22% coverage, 21 gaps
- `python -m asset_manager status "Duplessis"` — 21 numbered, 0 unnumbered, 21 unfilled gaps
- `pytest tests/test_integration/ -v` — 6/6 passed
- `pytest tests/ -v -m "not integration"` — 490/490 passed, 0 failures

## Diagnostics

- `python -m asset_manager status "Duplessis"` for organized state
- `python -m media_acquisition status "Duplessis"` for gap coverage
- `pytest tests/test_integration/ -v` for contract validation
- Schema validators produce shot-ID-labeled error lists on invalid data

## Deviations

- **direct_url source fix:** search() was returning empty list, making direct_url entries in search_plan useless. Fixed to return the URL as a SearchResult when query starts with http.
- **User-Agent header:** Added to direct_url downloads to prevent 403s from Wikimedia.
- **Integration test folder names:** Fixed ASSET_TYPE_FOLDERS to match actual folder names from VALID_FOLDERS (archival_photos, archival_footage, vectors, animations, documents, broll) instead of shotlist_type names.
- **Remotion unavailable:** npx not available — 3 map shots remain as unfilled gaps. Not a blocker since gaps are terminal.

## Known Issues

- publications.gc.ca PDF returns text/html (redirect page), so the Law Commission document wasn't downloaded. Minor — alternate sourcing possible in future.
- archive_org search returned 0 results for the queries used — the archive.org API may need different query formulation.
- Remotion/npx not available on this system — map shot rendering requires Node.js environment.

## Files Created/Modified

- `projects/1. The Duplessis Orphans Quebec's Stolen Children/shotlist.json` — 73-shot shotlist replacing 1-shot stub
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/search_plan.json` — search plan targeting keyless sources
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/manifest.json` — valid manifest with 21 assets and 21 unfilled gaps
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/archival_photos/` — 5 downloaded photos with numbered prefixes
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/vectors/` — 16 generated graphics with numbered prefixes
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/direct_url.py` — fixed search() to support URL-as-query; added User-Agent header
- `tests/test_integration/test_pipeline.py` — fixed ASSET_TYPE_FOLDERS to match actual folder names
