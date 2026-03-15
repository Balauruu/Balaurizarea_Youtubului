# S02: Media Acquisition Skill

**Goal:** A working [HEURISTIC] media acquisition skill that downloads assets from 7+ free sources and produces manifest.json with shot mappings and gap list.
**Demo:** Feed shotlist.json from Duplessis Orphans project → CLI `load` prints aggregated context, `acquire` downloads assets per search plan, `status` reports gap analysis. manifest.json has assets with shot mappings and gaps with pending_generation status.

## Must-Haves

- manifest.json schema validated by schema.py — stable contract consumed by S03/S04/S05
- CLI with `load`, `acquire`, and `status` subcommands following context-loader pattern (D002)
- Source adapter modules for at least 7 free sources (archive.org, Wikimedia, Pexels, Pixabay, Smithsonian, YouTube CC, direct URL)
- Common source interface: `search(query, media_type, limit) → list[SearchResult]`, `download(url, dest_dir) → DownloadResult`
- Per-source rate limiting (simple sleep-based)
- `acquire` reads search_plan.json → downloads assets → writes manifest.json with shot mappings
- Gap identification: shots not covered by acquired assets → gaps with status `pending_generation`
- media_urls.md parser extracts direct URLs from researcher output
- All downloads go to typed folders: `archival_photos/`, `archival_footage/`, `documents/`, `broll/`
- License metadata in manifest.json asset entries

## Proof Level

- This slice proves: contract + integration
- Real runtime required: yes (API calls to free sources during execution, but tests use mocks)
- Human/UAT required: no (visual quality assessed in S06)

## Verification

- `pytest tests/test_media_acquisition/ -v` — all tests pass
- `PYTHONPATH=.claude/skills/media-acquisition/scripts python -m media_acquisition load "Duplessis Orphans"` — exits 0, prints shotlist + media_urls context
- `PYTHONPATH=.claude/skills/media-acquisition/scripts python -m media_acquisition status "Duplessis Orphans"` — exits 0, prints gap summary (or "no manifest" message)
- manifest.json schema validator catches all invalid states (missing fields, bad status values, orphan shot references)

## Observability / Diagnostics

- Runtime signals: per-source download counts, rate limit delays, HTTP errors logged to stderr
- Inspection surfaces: `python -m media_acquisition status "<topic>"` — gap count, source summary, coverage percentage
- Failure visibility: acquire command prints per-download success/failure with source + URL + HTTP status
- Redaction constraints: API keys (Pexels, Pixabay, Smithsonian) — never logged, passed via env vars only

## Integration Closure

- Upstream surfaces consumed: `shotlist.json` (S01 contract — filters by shotlist_type), `media_urls.md` (researcher output)
- New wiring introduced in this slice: manifest.json contract (central coordination artifact for S03/S04/S05)
- What remains before the milestone is truly usable end-to-end: S03 (graphics), S04 (animation), S05 (asset manager), S06 (integration)

## Tasks

- [x] **T01: Skill scaffold with manifest schema contract, load/status CLI, and tests** `est:1h`
  - Why: Establishes the manifest.json schema contract that S03/S04/S05 depend on, plus CLI shell and media_urls.md parser
  - Files: `.claude/skills/media-acquisition/scripts/media_acquisition/cli.py`, `schema.py`, `CONTEXT.md`, `SKILL.md`, `tests/test_media_acquisition/test_schema.py`, `test_cli.py`
  - Do: Create skill directory structure following visual-orchestrator pattern. Define manifest.json schema in schema.py with `validate_manifest()` returning `list[str]` errors. Implement `load` subcommand (aggregates shotlist.json + media_urls.md + channel context). Implement `status` subcommand (reads manifest.json, prints gap analysis). Parse media_urls.md markdown format into structured list. Write CONTEXT.md (stage contract) and SKILL.md (usage guide). Write tests for schema validation (valid/invalid manifests) and CLI (load stdout content, status output, missing file errors).
  - Verify: `pytest tests/test_media_acquisition/ -v` passes, CLI `load` and `status` work on Duplessis Orphans project
  - Done when: manifest.json schema is documented, validated, and tested; load/status subcommands work

- [x] **T02: Source adapter modules with common interface and mocked tests** `est:1.5h`
  - Why: Core risk retirement — proves downloads from 7+ free sources work behind a unified interface
  - Files: `.claude/skills/media-acquisition/scripts/media_acquisition/sources/__init__.py`, `archive_org.py`, `wikimedia.py`, `pexels.py`, `pixabay.py`, `smithsonian.py`, `youtube_cc.py`, `direct_url.py`, `tests/test_media_acquisition/test_sources.py`
  - Do: Define common interface (SearchResult/DownloadResult dataclasses, source registry). Implement each source module with `search()` and `download()` methods. Per-source rate limiting via `time.sleep`. Pexels/Pixabay/Smithsonian read API keys from env vars. archive_org uses `internetarchive` lib. youtube_cc wraps yt-dlp subprocess. direct_url uses streaming `requests.get`. Write tests with mocked HTTP responses (no real API calls in tests).
  - Verify: `pytest tests/test_media_acquisition/test_sources.py -v` passes
  - Done when: all 7 source modules implement the common interface, each has at least one search + one download test

- [x] **T03: Acquire subcommand with download orchestration, manifest bookkeeping, and gap analysis** `est:1h`
  - Why: Wires sources together into the acquire command, handles manifest read-modify-write, and implements gap identification (R004)
  - Files: `.claude/skills/media-acquisition/scripts/media_acquisition/acquire.py`, `cli.py` (update), `tests/test_media_acquisition/test_acquire.py`
  - Do: Implement acquire.py orchestrator that reads search_plan.json (list of {source, query, media_type, shot_ids, dest_folder}), calls source.search() + source.download() per entry, builds manifest.json with asset entries and shot mappings. Implement gap identification: compare shotlist.json shot IDs vs manifest mapped_shots to find uncovered shots → gaps with status `pending_generation`. Atomic manifest writes (write temp + rename). Wire `acquire` subcommand into CLI. Write tests: mock sources, verify manifest output shape, verify gap identification logic.
  - Verify: `pytest tests/test_media_acquisition/test_acquire.py -v` passes; full test suite `pytest tests/test_media_acquisition/ -v` passes
  - Done when: acquire command produces valid manifest.json with assets and gaps; gap analysis correctly identifies unmatched shots

## Files Likely Touched

- `.claude/skills/media-acquisition/scripts/media_acquisition/__init__.py`
- `.claude/skills/media-acquisition/scripts/media_acquisition/__main__.py`
- `.claude/skills/media-acquisition/scripts/media_acquisition/cli.py`
- `.claude/skills/media-acquisition/scripts/media_acquisition/schema.py`
- `.claude/skills/media-acquisition/scripts/media_acquisition/acquire.py`
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/__init__.py`
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/archive_org.py`
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/wikimedia.py`
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/pexels.py`
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/pixabay.py`
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/smithsonian.py`
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/youtube_cc.py`
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/direct_url.py`
- `.claude/skills/media-acquisition/CONTEXT.md`
- `.claude/skills/media-acquisition/SKILL.md`
- `tests/test_media_acquisition/__init__.py`
- `tests/test_media_acquisition/test_schema.py`
- `tests/test_media_acquisition/test_cli.py`
- `tests/test_media_acquisition/test_sources.py`
- `tests/test_media_acquisition/test_acquire.py`
