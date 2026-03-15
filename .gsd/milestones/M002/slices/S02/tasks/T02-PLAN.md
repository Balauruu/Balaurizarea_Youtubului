---
estimated_steps: 4
estimated_files: 9
---

# T02: Source adapter modules with common interface and mocked tests

**Slice:** S02 — Media Acquisition Skill
**Milestone:** M002

## Description

Build the 7 source adapter modules that retire the core risk of this slice: "can we download from multiple free sources reliably?" Each module implements a common interface (`search()` and `download()`) with per-source rate limiting. Tests use mocked HTTP — no real API calls.

Sources: archive.org (Python lib), Wikimedia Commons (MediaWiki API), Pexels (REST, needs key), Pixabay (REST, needs key), Smithsonian (REST, needs key), YouTube CC (yt-dlp subprocess), and direct URL downloader (for media_urls.md URLs).

## Steps

1. Define common interface in `sources/__init__.py`: `SearchResult` and `DownloadResult` dataclasses, `SOURCE_REGISTRY` dict mapping source names to module-level `search`/`download` functions, per-source rate limit config.
2. Implement source modules. Each follows the same pattern: `search(query, media_type, limit) → list[SearchResult]` and `download(url, dest_dir, filename=None) → DownloadResult`. Specifics:
   - `archive_org.py` — wraps `internetarchive.search_items()` and `internetarchive.get_item()`. Filter files by format (jpg/png/mp4). Size limits.
   - `wikimedia.py` — MediaWiki API `action=query&list=search` + `action=query&prop=imageinfo` with `extmetadata` for license. User-Agent header required.
   - `pexels.py` — REST API with `Authorization: {PEXELS_API_KEY}` header. 200 req/hr limit.
   - `pixabay.py` — REST API with `key={PIXABAY_API_KEY}` query param.
   - `smithsonian.py` — REST API with `api_key={SMITHSONIAN_API_KEY}` query param.
   - `youtube_cc.py` — `yt-dlp` subprocess with CC license filter, format selection (mp4 ≤720p).
   - `direct_url.py` — streaming `requests.get` with Content-Type validation and size limit.
3. Add per-source rate limiting: `time.sleep()` between requests, configurable per source (archive.org: 1s, Wikimedia: 0.5s, Pexels: 0.5s, etc.).
4. Write `tests/test_media_acquisition/test_sources.py` — for each source: one search test + one download test with mocked HTTP responses. Test rate limiter. Test missing API key handling (skip gracefully, don't crash).

## Must-Haves

- [ ] Common `SearchResult` dataclass: url, title, description, source, license, media_type, thumbnail_url
- [ ] Common `DownloadResult` dataclass: success, filepath, filename, size_bytes, error
- [ ] All 7 source modules implement `search()` and `download()` following the interface
- [ ] `SOURCE_REGISTRY` maps source name strings to module references
- [ ] Per-source rate limiting via `time.sleep` (configurable delay)
- [ ] API key sources (pexels, pixabay, smithsonian) read from env vars, raise clear error if missing
- [ ] File size limits on downloads (configurable, default 50MB)
- [ ] Tests use mocked HTTP (unittest.mock.patch or responses library)

## Verification

- `pytest tests/test_media_acquisition/test_sources.py -v` — all pass
- No real API calls during tests (all HTTP mocked)
- Each source module importable and has search + download functions

## Observability Impact

- Signals added: each download logs source + URL + size + success/failure to stderr
- How a future agent inspects this: import source module, call search() with a query, inspect SearchResult list
- Failure state exposed: DownloadResult.error contains HTTP status + message on failure; missing API key raises ValueError with source name

## Inputs

- T01 schema.py — manifest.json schema for understanding what fields acquire will need to populate
- S02-RESEARCH.md — API details, rate limits, auth requirements per source
- `.claude/skills/researcher/scripts/researcher/fetcher.py` — retry pattern reference

## Expected Output

- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/__init__.py` — registry + dataclasses
- 7 source modules in `sources/` directory
- `tests/test_media_acquisition/test_sources.py` — ~15 tests (2 per source + rate limiter + error handling)
