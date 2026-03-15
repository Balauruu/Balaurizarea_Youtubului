---
id: T02
parent: S02
milestone: M002
provides:
  - Common source interface (SearchResult/DownloadResult dataclasses, SOURCE_REGISTRY, rate limiter)
  - 7 source adapter modules (archive_org, wikimedia, pexels, pixabay, smithsonian, youtube_cc, direct_url)
  - Shared streaming download with Content-Type validation and size limits
  - 32 mocked tests covering all source modules
key_files:
  - .claude/skills/media-acquisition/scripts/media_acquisition/sources/__init__.py
  - .claude/skills/media-acquisition/scripts/media_acquisition/sources/archive_org.py
  - .claude/skills/media-acquisition/scripts/media_acquisition/sources/wikimedia.py
  - .claude/skills/media-acquisition/scripts/media_acquisition/sources/pexels.py
  - .claude/skills/media-acquisition/scripts/media_acquisition/sources/pixabay.py
  - .claude/skills/media-acquisition/scripts/media_acquisition/sources/smithsonian.py
  - .claude/skills/media-acquisition/scripts/media_acquisition/sources/youtube_cc.py
  - .claude/skills/media-acquisition/scripts/media_acquisition/sources/direct_url.py
  - tests/test_media_acquisition/test_sources.py
key_decisions:
  - "Shared _streaming_download() in __init__.py handles all HTTP downloads — source modules call it instead of reimplementing"
  - "requests imported at module level in sources/__init__.py for mockability — all download tests patch media_acquisition.sources.requests.get"
  - "API key sources raise ValueError with env var name on missing key — no silent degradation"
  - "direct_url.search() returns empty list by design — direct URLs come from media_urls.md, not search"
  - "YouTube CC uses yt-dlp subprocess with --match-filter license=Creative Commons for CC-only content"
patterns_established:
  - All source modules follow search(query, media_type, limit) → list[SearchResult] and download(url, dest_dir, filename) → DownloadResult
  - rate_limit(source_name) called before each HTTP request — per-source independent delays
  - _log_download() writes source + URL + size + status to stderr for observability
  - _get_api_key() centralizes env var reads with clear ValueError for missing keys
observability_surfaces:
  - "Each download logs [source] OK/FAIL url (size KB) to stderr"
  - "Missing API key raises ValueError with source name + env var name"
  - "DownloadResult.error contains HTTP status + message on failure"
  - "SearchResult includes license metadata from each source"
duration: 15m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Source adapter modules with common interface and mocked tests

**7 source adapter modules behind a common SearchResult/DownloadResult interface with shared streaming download, per-source rate limiting, and 32 mocked tests — no real API calls.**

## What Happened

Built `sources/__init__.py` with the common interface: `SearchResult` dataclass (url, title, description, source, license, media_type, thumbnail_url), `DownloadResult` dataclass (success, filepath, filename, size_bytes, error), `SOURCE_REGISTRY` mapping 7 source names to modules, per-source `rate_limit()` with configurable delays, and `_streaming_download()` shared by all HTTP-based sources.

Implemented 7 source modules:
- **archive_org** — wraps `internetarchive` lib, filters by format (JPEG/PNG/MP4), respects size limits
- **wikimedia** — MediaWiki API search + imageinfo with extmetadata license extraction, User-Agent header
- **pexels** — REST API with Authorization header, supports photo + video search
- **pixabay** — REST API with key query param, supports photo + video search
- **smithsonian** — REST API with api_key param, parses nested descriptiveNonRepeating structure
- **youtube_cc** — yt-dlp subprocess with CC license filter, mp4 ≤720p format selection
- **direct_url** — streaming download with Content-Type allowlist, no search (URLs from media_urls.md)

Key design: `_streaming_download()` in `__init__.py` handles the common download pattern (streaming with size limit, Content-Type validation, filename derivation, logging). Source modules only implement search logic and call the shared download.

## Verification

- `pytest tests/test_media_acquisition/test_sources.py -v` — **32 passed in 1.84s**
  - 4 dataclass tests, 4 registry tests, 3 rate limiter tests, 4 streaming download tests
  - 2 archive_org, 2 wikimedia, 3 pexels, 2 pixabay, 2 smithsonian, 3 youtube_cc, 3 direct_url
- `pytest tests/test_media_acquisition/ -v` — **75 passed** (43 T01 + 32 T02)
- No real API calls during tests — all HTTP mocked via `unittest.mock.patch`
- Each source module importable and has `search()` + `download()` functions (verified by `test_all_sources_importable`)

### Slice-level verification status (T02 is task 2 of 3):
- ✅ `pytest tests/test_media_acquisition/ -v` — 75 pass
- ✅ `load "Duplessis Orphans"` — exits 0, prints context
- ✅ `status "Duplessis Orphans"` — exits 1 with "no manifest" (correct pre-acquisition state)
- ✅ Schema validator catches invalid states
- ⬜ `acquire` command — not yet implemented (T03)

## Diagnostics

- Each download logs `[source] OK/FAIL url (size KB)` to stderr
- Missing API key raises `ValueError` with env var name (e.g., "Missing API key for pexels: set PEXELS_API_KEY")
- DownloadResult.error contains HTTP status + message on failure
- Import any source module → call search() → inspect SearchResult list

## Deviations

None.

## Known Issues

- `internetarchive` must be installed at module level (not deferred) for archive_org to import — this means `get_source("archive_org")` fails if the lib isn't installed. Acceptable since it's a required dependency.

## Files Created/Modified

- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/__init__.py` — Registry + dataclasses + rate limiter + shared download
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/archive_org.py` — Archive.org adapter
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/wikimedia.py` — Wikimedia Commons adapter
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/pexels.py` — Pexels adapter
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/pixabay.py` — Pixabay adapter
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/smithsonian.py` — Smithsonian adapter
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/youtube_cc.py` — YouTube CC adapter
- `.claude/skills/media-acquisition/scripts/media_acquisition/sources/direct_url.py` — Direct URL adapter
- `tests/test_media_acquisition/test_sources.py` — 32 mocked tests
