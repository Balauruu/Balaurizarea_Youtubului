# S02: Media Acquisition Skill — Research

**Date:** 2026-03-15

## Summary

This slice builds the media acquisition skill — a [HEURISTIC] skill following the context-loader pattern (D002) that takes shotlist.json and media_urls.md as inputs, downloads assets from multiple free sources, and produces manifest.json with shot mappings and a gap list for downstream generators (S03/S04).

The core risk — "can we actually download from 10+ free sources reliably?" — has been partially retired through live API probing. Archive.org (Python lib) and Wikimedia Commons (MediaWiki API) work reliably. Pexels and Pixabay require free API keys. LOC and Smithsonian are behind Cloudflare/require keys respectively. DPLA's API docs are 404'd. The practical source count is 7-8 reliable sources plus crawl4ai fallback for direct URLs, which exceeds the "5+ sources" success criterion.

The manifest.json contract is the central coordination artifact (D011) — it must be designed carefully since S03, S04, and S05 all consume it. The gap lifecycle (R010: pending_generation → filled → unfilled) starts here.

## Recommendation

Build a thin CLI with three subcommands following the visual-orchestrator pattern:
1. **`load`** — Aggregate shotlist.json + media_urls.md + channel context, print to stdout for Claude to plan search queries
2. **`acquire`** — Execute downloads from a search plan (JSON on stdin or file), with per-source client modules, rate limiting, and retry
3. **`status`** — Read manifest.json and print gap analysis summary

The `acquire` command does the heavy lifting: per-source Python modules behind a common interface (`search(query, limit) → results[]`, `download(url, dest) → path`). Claude plans what to search for (the [HEURISTIC] part — matching visual_need to search queries). The deterministic code handles downloading, deduplication, rate limiting, and manifest bookkeeping.

Keep source client modules small and independently testable. Each source has different API patterns, auth requirements, and rate limits — a unified adapter interface prevents the CLI from becoming a mess.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Archive.org search/download | `internetarchive` (pip, already installed) | Official Python lib, handles auth, pagination, file filtering |
| HTTP requests with retries | `requests` + custom retry (already installed) | researcher/fetcher.py has proven retry pattern with progressive delay |
| Web scraping for sources without APIs | crawl4ai (already installed) | Domain-isolated browser contexts, anti-bot bypass |
| Video downloading (YouTube CC) | `yt-dlp` (already installed) | Handles CC-license filtering, format selection, rate limiting |
| Image downloading | `requests` with streaming | Simple GET + write; no special lib needed |

## Existing Code and Patterns

- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/cli.py` — **Pattern to follow**: context-loader CLI with argparse subcommands, `_get_project_root()`, `resolve_project_dir()`, `_ensure_utf8_stdout()`
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/schema.py` — **Pattern to follow**: schema validation returning `list[str]` errors with context IDs
- `.claude/skills/researcher/scripts/researcher/fetcher.py` — **Pattern to follow**: retry logic with progressive delay, tier-based attempt limits, content validation
- `.claude/skills/researcher/scripts/researcher/tiers.py` — **Pattern to follow**: domain classification for rate-limit policy
- `.claude/skills/researcher/scripts/researcher/url_builder.py` — **Reuse pattern**: `_get_project_root()` and `find_project_dir()` (note: third duplication — consider extracting if a fourth skill needs it)
- `.claude/skills/crawl4ai-scraper/scripts/scraper.py` — **Available utility**: direct URL scraping via crawl4ai
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/research/media_urls.md` — **Input format**: categorized URLs with description and source fields
- `tests/test_visual_orchestrator/test_cli.py` — **Test pattern to follow**: tmp_path fixtures, helper functions for fake project structures, capsys for stdout capture

## Constraints

- **Python only** — All scripting in Python (per project convention)
- **Free media only** — All sources must be public domain, CC0, or Creative Commons licensed
- **No LLM API calls in scripts** — Claude Code runtime handles reasoning; scripts are deterministic
- **Rate limiting required per source** — Pexels: 200 req/hr, Pixabay: similar, archive.org: be polite (1 req/sec), Wikimedia: 200 req/sec but be polite
- **Pexels/Pixabay require API keys** — Use `secure_env_collect` during execution (noted in M002-CONTEXT.md open questions)
- **Smithsonian requires API key** — Free registration at api.si.edu
- **LOC is behind Cloudflare** — Direct `requests` calls return 403; needs crawl4ai or browser-based fetching for search, though direct file URLs may work
- **Windows environment** — Must handle path separators, UTF-8 stdout encoding (same as visual-orchestrator)
- **manifest.json is a contract** — Schema must be stable before S03/S04/S05 can start; changes after this slice are expensive

## Common Pitfalls

- **Searching for exactly what's in visual_need vs searching broadly** — Documentary topics need creative query expansion. "Historical Quebec government buildings 1940s" won't find much; "Quebec 1940s orphanage" or "Duplessis premier Quebec" will. This is why the search query planning is [HEURISTIC] — Claude generates queries, not the code.
- **Downloading huge files blindly** — Archive.org items can have dozens of files (30+ per item seen in testing). Must filter by format (prefer jpg/png for photos, mp4 for video) and set size limits.
- **Rate limit violations killing the pipeline** — Need per-source rate limiters (simple `time.sleep` between requests) not global rate limiting. Each source has different thresholds.
- **Manifest.json race conditions** — Only one agent writes at a time (sequential pipeline), but the schema must support incremental updates. Use read-modify-write with atomic file writes.
- **License metadata gaps** — Not all sources provide machine-readable license info. Wikimedia is excellent (extmetadata.LicenseShortName). Archive.org has licenseurl. Pexels/Pixabay are all-free. Must handle missing license gracefully (default to "unknown — verify manually").
- **DPLA is dead** — API docs return 404. Drop from source list and replace with another source or accept 9 sources.

## Open Risks

- **LOC Cloudflare blocking** — May need crawl4ai for LOC search (not just direct `requests`). Could add complexity and slow down acquisition. Mitigation: LOC search via crawl4ai is a fallback; direct LOC item URLs may still work for downloads.
- **Pexels/Pixabay content relevance for dark mysteries** — Stock photo sites may have poor results for historical/dark topics (orphanages, abuse, institutions). More useful for b-roll (church interiors, government buildings, atmospheric shots).
- **Manifest schema stability** — If S03/S04 planning reveals gaps in the manifest contract, changes become expensive. Mitigation: define manifest schema in a dedicated schema.py with validator (same pattern as shotlist schema), get it reviewed before S03 starts.
- **media_urls.md parsing fragility** — Current format uses markdown bullets with `**URL:**`, `**Description:**`, `**Source:**` fields. If the researcher skill changes this format, parsing breaks. Need resilient parser or formalize the format.
- **Large download volumes** — A 60-100 shot shotlist could generate 200+ search queries across 8 sources. Even with rate limiting, this could take 30+ minutes. The `acquire` command should support incremental progress (resume from where it stopped).

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Media acquisition | (none relevant) | none found |
| Archive.org | (none relevant) | none found |
| Wikimedia Commons | (none relevant) | none found |
| Pexels/Pixabay | (none relevant) | none found |

No relevant professional skills exist for this domain. All source integrations will be custom Python modules.

## Sources

- Archive.org Python library works for search and download — `search_items()` returns identifiers, `get_item()` accesses metadata and files (source: live testing against `internetarchive` 5.8.0)
- Wikimedia Commons API returns search results, image URLs, sizes, MIME types, and license metadata via `imageinfo` prop with `extmetadata` — no auth required, just User-Agent header (source: [MediaWiki API:Search](https://www.mediawiki.org/wiki/API:Search))
- LOC JSON API uses `?fo=json` parameter on any loc.gov endpoint — currently blocked by Cloudflare for plain requests (source: [LOC API docs](https://loc.gov/apis/json-and-yaml/requests/))
- Pexels API: RESTful JSON, 200 req/hr, requires API key in `Authorization` header, attribution required (source: [Pexels API docs](https://www.pexels.com/api/documentation/))
- Pixabay API: RESTful JSON, requires API key as query param, all content is royalty-free (source: [Pixabay API docs](https://pixabay.com/api/docs/))
- Smithsonian Open Access API requires free API key from api.si.edu (source: live 403 response with `API_KEY_MISSING` message)
- DPLA API documentation returns 404 — service may be deprecated or restructured (source: live 404 at pro.dp.la/developers/api-overview)
- Direct media URLs from media_urls.md (e.g., cloudfront CDN, Wikimedia uploads) are downloadable with simple HEAD/GET requests (source: live testing, 200 OK with correct Content-Type)

## Architecture Notes

### Source Modules

Each source gets its own Python module under `scripts/media_acquisition/sources/`:

```
sources/
├── __init__.py          # Source registry + common interface
├── archive_org.py       # internetarchive lib wrapper
├── wikimedia.py         # MediaWiki API client
├── loc.py               # LOC JSON API (via crawl4ai if needed)
├── pexels.py            # Pexels REST API
├── pixabay.py           # Pixabay REST API  
├── smithsonian.py       # Smithsonian Open Access API
├── youtube_cc.py        # yt-dlp wrapper for CC content
├── direct_url.py        # Direct URL downloader (for media_urls.md)
└── europeana.py         # Europeana API (if Cloudflare allows)
```

Common interface per module:
```python
def search(query: str, media_type: str, limit: int = 10) -> list[SearchResult]
def download(url: str, dest_dir: Path, filename: str | None = None) -> DownloadResult
```

### manifest.json Schema (Draft)

```json
{
  "project": "The Duplessis Orphans",
  "generated": "2026-03-15T01:00:00Z",
  "updated": "2026-03-15T01:30:00Z",
  "assets": [
    {
      "filename": "maurice_duplessis_1938.png",
      "folder": "archival_photos",
      "source": "wikimedia_commons",
      "source_url": "https://upload.wikimedia.org/...",
      "description": "Portrait of Maurice Duplessis, 1938",
      "license": "Public domain",
      "mapped_shots": ["S003", "S005"],
      "acquired_by": "agent_acquisition"
    }
  ],
  "gaps": [
    {
      "shot_id": "S012",
      "visual_need": "Interior of Mont-Providence institution, 1950s",
      "shotlist_type": "archival_photo",
      "status": "pending_generation",
      "notes": "No archival photos found for this specific institution interior"
    }
  ],
  "source_summary": {
    "wikimedia_commons": {"searched": 15, "downloaded": 8},
    "archive_org": {"searched": 10, "downloaded": 3},
    "pexels": {"searched": 5, "downloaded": 2}
  }
}
```

### CLI Subcommands

| Command | Purpose | I/O |
|---------|---------|-----|
| `load` | Print aggregated context for Claude to plan search queries | shotlist.json + media_urls.md → stdout |
| `acquire` | Download assets per search plan, update manifest | search_plan.json → assets/ + manifest.json |
| `status` | Print manifest gap analysis | manifest.json → stdout summary |

### Shotlist Type → Source Routing

| shotlist_type | Primary Sources | Fallback |
|---------------|----------------|----------|
| archival_photo | Wikimedia, LOC, Archive.org, Smithsonian, media_urls.md | Pexels, Pixabay (for generic historical) |
| archival_video | Archive.org, YouTube CC, media_urls.md | Pexels (stock video) |
| document_scan | LOC, Archive.org, Wikimedia, media_urls.md | crawl4ai (direct scraping) |

### Asset Folder Structure

```
assets/
├── archival_photos/     # Downloaded archival photographs
├── archival_footage/    # Downloaded video clips  
├── documents/           # Document scans, PDFs
├── broll/               # Stock b-roll footage
├── manifest.json        # Central state tracking
└── source_licenses.json # License metadata per asset
```

### What S03/S04/S05 Need From This Slice

- **S03 (Graphics)**: Reads `manifest.json` gaps where `shotlist_type` is `animation` (non-map). Updates gap status to `filled`.
- **S04 (Animation)**: Reads `manifest.json` gaps where `shotlist_type` is `map`. Updates gap status to `filled`.
- **S05 (Asset Manager)**: Reads all files in `assets/` type folders + `manifest.json`. Numbers files, moves unmatched to `_pool/`, writes consolidated manifest.
