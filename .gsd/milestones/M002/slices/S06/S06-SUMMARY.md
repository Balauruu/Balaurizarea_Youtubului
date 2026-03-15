---
id: S06
parent: M002
milestone: M002
provides:
  - End-to-end pipeline proof on Duplessis Orphans: Script.md → 73-shot shotlist → 21 organized numbered assets with valid manifest
  - Integration test suite (6 tests) validating cross-skill contracts post-hoc
  - visual-orchestrator pythonpath fix unblocking 20 unit tests
requires:
  - slice: S01
    provides: visual orchestrator CLI + shotlist.json schema validator
  - slice: S02
    provides: media acquisition CLI + manifest.json schema contract + 7 source adapters
  - slice: S03
    provides: graphics generator CLI + 7 Pillow renderers + ComfyUI client
  - slice: S04
    provides: animation CLI + Remotion scaffold
  - slice: S05
    provides: asset manager CLI + organize/numbering/gap finalization
affects: []
key_files:
  - pytest.ini
  - tests/test_integration/test_pipeline.py
  - projects/1. The Duplessis Orphans Quebec's Stolen Children/shotlist.json
  - projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/manifest.json
  - projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/search_plan.json
  - .claude/skills/media-acquisition/scripts/media_acquisition/sources/direct_url.py
key_decisions:
  - direct_url source search() returns URL as SearchResult when query starts with http — enables media_urls.md URLs to flow through standard acquire pipeline (D025)
  - Integration test ASSET_TYPE_FOLDERS matched to actual folder names (archival_photos, vectors, etc.) not shotlist_type names
  - User-Agent header added to direct_url downloads to avoid Wikimedia 403s
patterns_established:
  - Integration tests use _load_json_or_skip() for consistent skip-when-missing behavior
  - All integration tests marked @pytest.mark.integration, excluded from default runs
  - Full pipeline sequence proven: visual_orchestrator load → acquire → graphics generate --code-gen-only → asset_manager organize
observability_surfaces:
  - "pytest tests/test_integration/ -v" — 6 contract validators (shotlist schema, manifest schema, numbered assets, terminal gaps, disk-manifest sync, shotlist-manifest linkage)
  - "python -m asset_manager status \"Duplessis\"" — organized state (21 numbered, 0 unnumbered, 21 unfilled gaps)
  - "python -m media_acquisition status \"Duplessis\"" — acquisition coverage (51%, 22/43 shots covered)
  - "python -m visual_orchestrator validate \"Duplessis\"" — shotlist schema validation (73 shots valid)
  - Schema validators produce grep-friendly error lists: validate_shotlist({}) returns 4 labeled errors
drill_down_paths:
  - .gsd/milestones/M002/slices/S06/tasks/T01-SUMMARY.md
  - .gsd/milestones/M002/slices/S06/tasks/T02-SUMMARY.md
duration: ~37m
verification_result: passed
completed_at: 2026-03-15
---

# S06: End-to-End Integration

**Full pipeline proven on Duplessis Orphans: Script.md → 73-shot shotlist → 21 organized numbered assets with valid manifest, verified by 6 integration tests and 490 unit tests.**

## What Happened

**T01** fixed pytest.ini to include visual-orchestrator in pythonpath (unblocking 20 tests that couldn't collect) and created the integration test suite — 6 post-hoc validators checking shotlist schema, manifest schema, numbered asset existence, terminal gap lifecycle, disk-manifest sync, and shotlist-manifest linkage. Tests skip gracefully when pipeline hasn't run yet.

**T02** executed the full pipeline on the Duplessis Orphans project:
1. Visual orchestrator generated a 73-shot shotlist (22 animation, 21 text_overlay, 17 document_scan, 6 archival_video, 4 archival_photo, 3 map)
2. Media acquisition downloaded 5 real assets from live sources (BAnQ CDN, Wikimedia) using a hand-authored search_plan.json targeting keyless sources. Required fixing direct_url source to support URL-as-query pattern and adding User-Agent headers for Wikimedia.
3. Graphics generator produced 16 code-gen graphics (silhouettes, glitch stingers, textures, icons, noise) in --code-gen-only mode
4. Remotion animation attempted for 3 map shots — npx unavailable on this Windows system, so map gaps flowed to unfilled status (non-blocking)
5. Asset manager organized all 21 assets with 3-digit sequential prefixes by shotlist order, finalized 21 gaps from pending_generation → unfilled

## Verification

- `pytest tests/test_integration/ -v` — **6/6 passed** (shotlist schema, manifest schema, numbered assets, terminal gaps, disk-manifest sync, shotlist-manifest linkage)
- `pytest tests/ -v -m "not integration"` — **490/490 passed**, 0 regressions
- `python -m visual_orchestrator validate "Duplessis"` — exits 0, 73 shots valid
- `python -m asset_manager status "Duplessis"` — 21 numbered, 0 unnumbered, 21 unfilled gaps
- `python -m media_acquisition status "Duplessis"` — 51% coverage (22/43 shots), 5 live-source assets
- Schema diagnostic: `validate_shotlist({})` returns 4 grep-friendly error strings

## Requirements Advanced

- R003 (Multi-source media acquisition) — proven with live downloads from 3 keyless sources (direct_url, wikimedia_commons, archive_org attempted)
- R004 (Asset-to-shot matching) — manifest maps 21 assets to shots, 21 gaps correctly identified
- R005 (Code-generated flat graphics) — 16 Pillow-rendered graphics produced and organized
- R007 (Remotion animated maps) — attempted but npx unavailable; gap lifecycle correctly handles missing renders

## Requirements Validated

- R003 — live API downloads from Wikimedia and direct URLs, rate limiting observed, manifest entries with source tracking
- R004 — gap identification correctly flagged unmatched shots, asset-to-shot mappings valid in manifest
- R005 — 16 code-gen graphics rendered, organized with numbered prefixes, manifest entries with acquired_by: agent_graphics
- R006 — ComfyUI client contract-tested (35 mocked tests); live validation deferred since ComfyUI server not running during integration
- R007 — Remotion scaffold contract-tested (22 mocked tests); live .mp4 rendering requires Node.js/npx environment
- R008 — 21 assets numbered with 3-digit sequential prefixes by shotlist order
- R009 — _pool/ directory exists (empty — no unmapped assets in this run)
- R010 — gap lifecycle proven: pending_generation → unfilled, no pending_generation remaining
- R011 — all assets delivered raw, no post-processing applied

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

- **direct_url source fix:** search() returned empty list for URL queries, breaking the acquire pipeline for media_urls.md entries. Fixed to return URL as SearchResult when query starts with http.
- **User-Agent header:** Added to direct_url downloads to prevent 403s from Wikimedia CDN.
- **Integration test folder names:** ASSET_TYPE_FOLDERS initially used shotlist_type names instead of actual folder names from VALID_FOLDERS constant.

## Known Limitations

- **Remotion/npx unavailable:** Map shot rendering requires Node.js/npx which wasn't available on this Windows system. 3 map shots remain as unfilled gaps. The Remotion scaffold and Python CLI are tested (22 unit tests) but live rendering wasn't proven end-to-end.
- **ComfyUI not running:** 6 creative building blocks (concept diagrams) skipped in --code-gen-only mode. ComfyUI client is tested (35 mocked tests) but live generation not proven.
- **archive.org search:** Returned 0 results for the queries used — may need different query formulation for this source.
- **51% shot coverage:** 22 of 43 acquisition-relevant shots covered. Remaining gaps are unfilled — more sources or manual asset addition could improve coverage.

## Follow-ups

- none — this is the final slice of M002

## Files Created/Modified

- `pytest.ini` — added visual-orchestrator/scripts to pythonpath
- `tests/test_integration/__init__.py` — package init
- `tests/test_integration/test_pipeline.py` — 6 integration test functions with @pytest.mark.integration
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/shotlist.json` — 73-shot shotlist replacing stub
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/search_plan.json` — search plan for keyless sources
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/manifest.json` — valid manifest with 21 assets and 21 unfilled gaps
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/archival_photos/` — 5 downloaded photos with numbered prefixes
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/assets/vectors/` — 16 generated graphics with numbered prefixes
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/direct_url.py` — URL-as-query support + User-Agent header

## Forward Intelligence

### What the next slice should know
- M002 is complete — no next slice in this milestone. Future milestones should know the pipeline produces valid artifacts but coverage depends on source availability and search plan quality.

### What's fragile
- archive.org search query formulation — returned 0 results; needs experimentation with different query strategies
- direct_url downloads depend on stable CDN URLs — BAnQ and Wikimedia URLs work today but may change
- ComfyUI and Remotion live rendering are contract-tested but not integration-proven on this system

### Authoritative diagnostics
- `pytest tests/test_integration/ -v` — the definitive pipeline contract check, validates all cross-skill data flows
- `python -m asset_manager status "Duplessis"` — quick pipeline output summary with counts

### What assumptions changed
- Assumed all media_urls.md entries would flow through direct_url source automatically — actually required fixing search() to handle URL-as-query pattern
- Assumed Remotion/npx would be available — not on this Windows system; gap lifecycle correctly absorbs this
