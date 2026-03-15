# S02: Media Acquisition Skill — UAT

**Milestone:** M002
**Written:** 2026-03-15

## UAT Type

- UAT mode: mixed (artifact-driven for schema/CLI, live-runtime for source adapters during S06)
- Why this mode is sufficient: All source adapters are mocked in tests — real API validation is explicitly deferred to S06 integration. Schema, CLI, and acquire logic are fully testable from artifacts.

## Preconditions

- Python 3.10+ with `requests`, `internetarchive` installed
- `pytest.ini` has `.claude/skills/media-acquisition/scripts` in pythonpath
- `projects/1. The Duplessis Orphans.../shotlist.json` exists (minimal fixture)
- `projects/1. The Duplessis Orphans.../research/media_urls.md` exists
- `context/channel/channel.md` exists

## Smoke Test

```bash
cd "D:\Youtube\D. Mysteries Channel\1.2 Agents\Channel-automation V3"
pytest tests/test_media_acquisition/ -v
# Expected: 102 passed
```

## Test Cases

### 1. Schema validates correct manifest

1. Run `pytest tests/test_media_acquisition/test_schema.py::TestValidManifest -v`
2. **Expected:** All 4 tests pass — valid manifest, empty assets/gaps, all valid folders, all valid gap statuses accepted

### 2. Schema rejects invalid manifests

1. Run `pytest tests/test_media_acquisition/test_schema.py::TestTopLevelKeys -v`
2. Run `pytest tests/test_media_acquisition/test_schema.py::TestAssetValidation -v`
3. Run `pytest tests/test_media_acquisition/test_schema.py::TestGapValidation -v`
4. **Expected:** All 25 tests pass — missing keys, invalid folders, bad shot IDs, invalid gap statuses all caught with descriptive error strings

### 3. CLI load aggregates project context

1. Run `PYTHONPATH=.claude/skills/media-acquisition/scripts python -m media_acquisition load "Duplessis Orphans"`
2. **Expected:** Exit code 0. Output contains three labeled sections: `=== Shotlist ===`, `=== Media URLs ===`, `=== Channel DNA ===`. Each section has real content from the project files. Footer shows project directory, assets directory, and manifest path.

### 4. CLI status reports pre-acquisition state

1. Run `PYTHONPATH=.claude/skills/media-acquisition/scripts python -m media_acquisition status "Duplessis Orphans"`
2. **Expected:** Exit code 1. Stderr contains "No manifest found" with full path to expected manifest.json location.

### 5. CLI status reports post-acquisition state

1. Create a valid manifest.json in `projects/1. The Duplessis Orphans.../assets/manifest.json` with at least 1 asset and 1 gap
2. Run `python -m media_acquisition status "Duplessis Orphans"`
3. **Expected:** Exit code 0. Output includes asset count, shot coverage ratio, gap breakdown by status (pending_generation/filled/unfilled), coverage percentage, and per-source download summary.

### 6. All 7 source modules importable with correct interface

1. Run `pytest tests/test_media_acquisition/test_sources.py::TestSourceRegistry -v`
2. **Expected:** 4 tests pass. Registry contains exactly: archive_org, wikimedia, pexels, pixabay, smithsonian, youtube_cc, direct_url. Each module has `search()` and `download()` functions.

### 7. Source search returns SearchResult objects

1. Run `pytest tests/test_media_acquisition/test_sources.py::TestArchiveOrg -v`
2. Run `pytest tests/test_media_acquisition/test_sources.py::TestWikimedia -v`
3. Run `pytest tests/test_media_acquisition/test_sources.py::TestPexels -v`
4. **Expected:** All tests pass. Search results are SearchResult dataclasses with url, title, description, source, license, media_type fields.

### 8. API key sources raise on missing keys

1. Run `pytest tests/test_media_acquisition/test_sources.py::TestPexels::test_missing_api_key -v`
2. Run `pytest tests/test_media_acquisition/test_sources.py::TestPixabay::test_missing_api_key -v`
3. Run `pytest tests/test_media_acquisition/test_sources.py::TestSmithsonian::test_missing_api_key -v`
4. **Expected:** All pass. Each raises ValueError with message containing the env var name (PEXELS_API_KEY, PIXABAY_API_KEY, SMITHSONIAN_API_KEY).

### 9. Acquire pipeline produces valid manifest

1. Run `pytest tests/test_media_acquisition/test_acquire.py::TestRunAcquire::test_full_pipeline -v`
2. **Expected:** Pass. The produced manifest.json passes `validate_manifest()` with zero errors. Contains assets with mapped_shots and gaps with pending_generation status.

### 10. Gap identification flags only acquisition-relevant types

1. Run `pytest tests/test_media_acquisition/test_acquire.py::TestIdentifyGaps -v`
2. **Expected:** All 5 tests pass. Shots with shotlist_type in (archival_photo, archival_video, document_scan) that have no matching asset appear as gaps. Shots with type animation or map are NOT flagged as gaps.

### 11. Incremental acquisition deduplicates

1. Run `pytest tests/test_media_acquisition/test_acquire.py::TestRunAcquire::test_incremental_merge -v`
2. Run `pytest tests/test_media_acquisition/test_acquire.py::TestRunAcquire::test_incremental_adds_new -v`
3. **Expected:** Both pass. Same source_url in two runs → no duplicate assets. Different URLs → additive merge. Existing assets take priority.

### 12. Atomic manifest writes leave no temp files

1. Run `pytest tests/test_media_acquisition/test_acquire.py::TestWriteManifestAtomic -v`
2. **Expected:** All 3 tests pass. Write creates file, overwrites existing, and no temp files remain in directory after write.

## Edge Cases

### Missing shotlist.json

1. Run `python -m media_acquisition load "nonexistent topic"`
2. **Expected:** Exit code 1. Stderr message identifies missing shotlist.json with full path.

### Empty search plan

1. Run `pytest tests/test_media_acquisition/test_acquire.py::TestLoadSearchPlan -v`
2. **Expected:** Invalid plans (missing fields, non-array, invalid JSON) all raise ValueError with descriptive messages.

### Rate limiter independence

1. Run `pytest tests/test_media_acquisition/test_sources.py::TestRateLimiter -v`
2. **Expected:** 3 tests pass. First call has no delay. Second call respects per-source delay. Different sources have independent timers.

### Content-Type rejection

1. Run `pytest tests/test_media_acquisition/test_sources.py::TestStreamingDownload::test_content_type_rejection -v`
2. **Expected:** Pass. HTML responses are rejected even if URL looks like an image.

## Failure Signals

- Any test in `pytest tests/test_media_acquisition/ -v` failing (should be 102/102)
- `load` CLI exit code ≠ 0 on valid project
- `status` CLI exit code = 0 when no manifest exists
- manifest.json produced by acquire that fails `validate_manifest()`
- Gap identification flagging animation or map shots as acquisition gaps
- Temp files remaining after atomic write

## Requirements Proved By This UAT

- R003 (Multi-source media acquisition) — 7 sources implemented with mocked tests proving interface contract. Live API proof deferred to S06.
- R004 (Asset-to-shot matching with gap identification) — Test cases 9-10 prove gap identification logic with correct type filtering.

## Not Proven By This UAT

- Real API responses from any source (mocked only — live validation in S06)
- Visual quality of downloaded assets (human review in S06)
- Search plan authoring quality (Claude heuristic, not tested programmatically)
- Rate limiting effectiveness under real load (only unit-tested with sleep mocks)

## Notes for Tester

- All tests use mocks — no API keys or network needed to run the test suite.
- The `acquire` CLI subcommand requires a `search_plan.json` which is authored by Claude during the [HEURISTIC] phase — there's no auto-generation from shotlist.
- The Duplessis Orphans project has a minimal shotlist.json fixture (1 shot) — real shotlists will have 30-80+ shots.
- `_get_project_root()` is duplicated across 4 skills — functional but should be extracted if pattern continues.
