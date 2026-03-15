---
id: S02
parent: M002
milestone: M002
provides:
  - manifest.json schema contract (6 top-level keys, per-asset/gap validation, folder/status enums)
  - CLI with load (context aggregation), status (gap analysis), and acquire (download orchestration) subcommands
  - 7 source adapter modules behind common SearchResult/DownloadResult interface
  - Shared streaming download with Content-Type validation, size limits, per-source rate limiting
  - media_urls.md parser extracting URL, description, source, and category
  - acquire pipeline: search_plan.json → source search/download → manifest.json with shot mappings + gap identification
  - Atomic manifest writes, incremental acquisition with source_url deduplication
requires:
  - slice: S01
    provides: shotlist.json schema contract (shot entries with shotlist_type for routing)
affects:
  - S03
  - S04
  - S05
key_files:
  - .claude/skills/media-acquisition/scripts/media_acquisition/schema.py
  - .claude/skills/media-acquisition/scripts/media_acquisition/cli.py
  - .claude/skills/media-acquisition/scripts/media_acquisition/acquire.py
  - .claude/skills/media-acquisition/scripts/media_acquisition/sources/__init__.py
  - .claude/skills/media-acquisition/scripts/media_acquisition/sources/archive_org.py
  - .claude/skills/media-acquisition/scripts/media_acquisition/sources/wikimedia.py
  - .claude/skills/media-acquisition/scripts/media_acquisition/sources/pexels.py
  - .claude/skills/media-acquisition/scripts/media_acquisition/sources/pixabay.py
  - .claude/skills/media-acquisition/scripts/media_acquisition/sources/smithsonian.py
  - .claude/skills/media-acquisition/scripts/media_acquisition/sources/youtube_cc.py
  - .claude/skills/media-acquisition/scripts/media_acquisition/sources/direct_url.py
  - .claude/skills/media-acquisition/CONTEXT.md
  - .claude/skills/media-acquisition/SKILL.md
  - tests/test_media_acquisition/test_schema.py
  - tests/test_media_acquisition/test_cli.py
  - tests/test_media_acquisition/test_sources.py
  - tests/test_media_acquisition/test_acquire.py
key_decisions:
  - "D014: 7 sources (archive.org, Wikimedia, Pexels, Pixabay, Smithsonian, YouTube CC, direct URL) — supersedes D010's 10+ target after DPLA/Europeana proved unreliable"
  - "D015: License metadata in manifest.json asset entries, not separate source_licenses.json"
  - "Gap identification only flags acquisition-relevant shotlist_types — animation/map gaps are expected and handled by S03/S04"
  - "Shared _streaming_download() in sources/__init__.py handles all HTTP downloads — source modules implement search only"
  - "Incremental merge deduplicates by source_url with existing assets taking priority"
patterns_established:
  - Media acquisition CLI follows context-loader pattern (D002) — CLI prints data, Claude reasons
  - All source modules follow search(query, media_type, limit) → list[SearchResult] and download(url, dest_dir, filename) → DownloadResult
  - Schema validation returns list[str] errors with asset/gap context labels for grep-friendly output
  - rate_limit(source_name) called before each HTTP request — per-source independent delays
  - Atomic manifest writes via tempfile.mkstemp + rename (Windows-safe with unlink-first)
observability_surfaces:
  - "python -m media_acquisition status <topic> — gap count, coverage %, per-source summary"
  - "python -m media_acquisition load <topic> — prints shotlist + media_urls + channel context"
  - "Each download logs [source] OK/FAIL url (size KB) to stderr"
  - "Missing API key raises ValueError with source name + env var name"
  - "pytest tests/test_media_acquisition/ -v — 102 tests"
drill_down_paths:
  - .gsd/milestones/M002/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M002/slices/S02/tasks/T02-SUMMARY.md
  - .gsd/milestones/M002/slices/S02/tasks/T03-SUMMARY.md
duration: 50m
verification_result: passed
completed_at: 2026-03-15
---

# S02: Media Acquisition Skill

**Complete media acquisition skill with 7 source adapters, manifest.json schema contract, acquire/load/status CLI, and 102 passing tests — proves bulk download + gap identification pipeline.**

## What Happened

Built the media acquisition skill across 3 tasks:

**T01 — Schema + CLI scaffold:** Defined manifest.json schema in `schema.py` with `validate_manifest()` enforcing 6 required top-level keys, 8 per-asset fields, 4 per-gap fields, folder/status enums, and shot ID format validation. Implemented `load` (aggregates shotlist.json + media_urls.md + channel.md) and `status` (reads manifest.json, prints gap analysis with coverage percentage) subcommands. Built `parse_media_urls()` to extract structured data from researcher's markdown format.

**T02 — Source adapters:** Implemented 7 source modules behind a common `SearchResult`/`DownloadResult` interface: archive_org (internetarchive lib), wikimedia (MediaWiki API), pexels (REST API + auth header), pixabay (REST API + key param), smithsonian (REST API), youtube_cc (yt-dlp subprocess with CC filter), direct_url (streaming with Content-Type allowlist). Shared `_streaming_download()` in `__init__.py` handles all HTTP downloads. Per-source rate limiting via configurable `time.sleep`. API keys read from env vars with clear ValueError on missing.

**T03 — Acquire command:** Built the `acquire` orchestrator that reads `search_plan.json`, calls source search/download per entry, produces schema-valid `manifest.json` with asset-to-shot mappings, and identifies gaps. Gap identification only flags acquisition-relevant types (archival_photo, archival_video, document_scan) — animation/map gaps are expected and handled by S03/S04. Supports incremental runs with source_url deduplication. Atomic manifest writes via temp+rename.

## Verification

- `pytest tests/test_media_acquisition/ -v` — **102 passed** (29 schema + 14 CLI + 32 sources + 27 acquire)
- `python -m media_acquisition load "Duplessis Orphans"` — exits 0, prints shotlist + media_urls + channel context ✓
- `python -m media_acquisition status "Duplessis Orphans"` — exits 1 with "No manifest found" message (correct pre-acquisition state) ✓
- Schema validator catches all invalid states: missing fields, bad status values, invalid shot IDs, orphan shot references ✓
- All source modules importable, implement search() + download(), have mocked tests with no real API calls ✓

## Requirements Advanced

- R003 (Multi-source media acquisition) — 7 source adapters implemented with unified interface, rate limiting, and mocked tests. Exceeds the 5-source success criterion. Real API validation deferred to S06 integration.
- R004 (Asset-to-shot matching with gap identification) — Gap identification compares shotlist shots against manifest mapped_shots, outputs unmatched acquisition-relevant shots as pending_generation gaps.

## Requirements Validated

- none — R003 and R004 require live API calls in S06 to fully validate

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- R003 re-scoped from "10+ sources" to 7 reliable sources (D014). DPLA returns 404, Europeana blocked by Cloudflare, LOC blocked by Cloudflare. 7 sources exceeds the 5-source success criterion.

## Deviations

- Created minimal `shotlist.json` fixture in Duplessis Orphans project for CLI verification — would normally be generated by visual-orchestrator at runtime.
- Added `.claude/skills/media-acquisition/scripts` to `pytest.ini` pythonpath — not in original plan but required for test discovery.
- License metadata stored in manifest.json asset entries instead of separate `source_licenses.json` (D015) — simpler, single source of truth.

## Known Limitations

- Source adapters are tested with mocks only — real API validation happens in S06 integration.
- `_get_project_root()` / `resolve_project_dir()` duplicated across 4 skills now. Should extract to shared util if a 5th needs them.
- `internetarchive` must be installed at module level for archive_org to import — `get_source("archive_org")` fails if lib missing.
- Search plan (search_plan.json) must be authored by Claude during the acquire [HEURISTIC] phase — no auto-generation from shotlist.

## Follow-ups

- S03 (Graphics Generator) consumes manifest.json gaps with pending_generation status
- S04 (Remotion Animation) consumes shotlist entries with animation/map types
- S05 (Asset Manager) reads all assets/ type folders + manifest.json for numbering and consolidation

## Files Created/Modified

- `.claude/skills/media-acquisition/scripts/media_acquisition/__init__.py` — Package init
- `.claude/skills/media-acquisition/scripts/media_acquisition/__main__.py` — Entry point
- `.claude/skills/media-acquisition/scripts/media_acquisition/schema.py` — manifest.json validator
- `.claude/skills/media-acquisition/scripts/media_acquisition/cli.py` — CLI with load/status/acquire subcommands
- `.claude/skills/media-acquisition/scripts/media_acquisition/acquire.py` — Download orchestrator
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/__init__.py` — Registry + dataclasses + rate limiter + shared download
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/archive_org.py` — Archive.org adapter
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/wikimedia.py` — Wikimedia Commons adapter
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/pexels.py` — Pexels adapter
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/pixabay.py` — Pixabay adapter
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/smithsonian.py` — Smithsonian adapter
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/youtube_cc.py` — YouTube CC adapter
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/direct_url.py` — Direct URL adapter
- `.claude/skills/media-acquisition/CONTEXT.md` — Stage contract
- `.claude/skills/media-acquisition/SKILL.md` — Usage guide
- `tests/test_media_acquisition/__init__.py` — Test package init
- `tests/test_media_acquisition/test_schema.py` — 29 schema validation tests
- `tests/test_media_acquisition/test_cli.py` — 14 CLI tests
- `tests/test_media_acquisition/test_sources.py` — 32 source adapter tests
- `tests/test_media_acquisition/test_acquire.py` — 27 acquire pipeline tests
- `projects/1. The Duplessis Orphans.../shotlist.json` — Minimal fixture for CLI verification
- `pytest.ini` — Added media-acquisition scripts to pythonpath

## Forward Intelligence

### What the next slice should know
- manifest.json is the central coordination artifact — S03/S04 read it to find gaps, S05 reads it for final consolidation
- Gap entries carry `visual_need`, `shotlist_type`, and `shot_id` — sufficient for downstream skills to decide what to generate
- The acquire command expects `search_plan.json` authored by Claude during the [HEURISTIC] phase — not auto-generated
- Source adapters are stateless — each call is independent, no session management needed

### What's fragile
- API key handling — Pexels/Pixabay/Smithsonian raise ValueError on missing env var, but there's no graceful degradation or skip-and-continue
- `internetarchive` lib import at module level — if not installed, archive_org adapter fails to import entirely

### Authoritative diagnostics
- `python -m media_acquisition status "<topic>"` — reads manifest.json and reports gap count, coverage %, per-source stats. Trustworthy because it re-validates schema on read.
- `pytest tests/test_media_acquisition/ -v` — 102 tests covering schema, CLI, all 7 sources, and acquire pipeline. All use mocks, run in <3s.

### What assumptions changed
- D010 assumed 10+ sources — actual implementation has 7 after DPLA/Europeana/LOC proved unreliable (D014). 7 still exceeds the 5-source success criterion.
- Architecture.md suggested separate source_licenses.json — consolidated into manifest.json asset entries (D015) for simplicity.
