# Phase 1: Scraping Infrastructure + Data Model - Context

**Gathered:** 2026-03-11
**Status:** Ready for planning

<domain>
## Phase Boundary

User can register competitor channels and scrape their video metadata into a reliable, queryable SQLite database. Covers DATA-01 through DATA-04: competitor registry, yt-dlp scraping, SQLite storage, and resilience (rate limiting + fallback). Analysis, topic generation, and trend scanning are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Competitor Registry
- Single JSON config file: `context/competitors/competitors.json`
- Fields per channel: name, youtube_id (handle), url, notes, added (date)
- Seed with 3 existing competitors: Barely Sociable, Unnamed TV, Fredrik Knudsen
- Migrate existing data (Barely Sociable.json, unnamedTV.csv, competitors.md) into the new format
- Delete old files after migration — single source of truth

### SQLite Schema
- Database location: `data/channel_assistant.db`
- Committed to git (scraping is slow/rate-limited, data should persist)
- Two tables: `channels` (channel-level metadata) and `videos` (video metadata)
- Curated fields only — no raw yt-dlp JSON storage
- Video fields: title, video_id, url, views, upload_date, description, duration, tags, likes, scraped_at
- Channel fields: name, youtube_id, url, subscribers, total_views, description, scraped_at
- Latest data only — no historical snapshots (v1 simplicity)
- Idempotent upserts on re-scrape (update existing, don't duplicate)

### Scraping Behavior
- Fetch ALL videos per channel (most channels have 20-100 videos)
- Also grab channel-level metadata (subscribers, total views, description) — nearly free with yt-dlp
- Retry each channel up to 2 times with backoff on failure
- On persistent failure: skip channel, fall back to cached data, continue with remaining channels
- Report failures at end — never crash mid-run
- 3-8 second jittered delay between channels
- Per-channel progress output during scrape

### Skill Invocation UX
- Single `/channel-assistant` skill with subcommands
- Phase 1 subcommands: `add <url>`, `scrape`, `scrape <name>`, `status`
- `add` registers only — no auto-scrape on add
- `scrape` shows per-channel progress: `✓ Channel: N videos (M new)`
- `status` shows summary table: channel name, video count, last scraped, latest upload
- Future phases add more subcommands (analyze, topics, etc.)

### Claude's Discretion
- Exact SQLite index strategy
- yt-dlp extraction parameters and metadata field mapping
- Error message wording and formatting
- Internal module structure and file organization
- Whether to use sqlite-utils or stdlib sqlite3

</decisions>

<specifics>
## Specific Ideas

- Progress output format explicitly decided:
  ```
  Scraping 3 channels...
  ✓ Barely Sociable: 47 videos (12 new)
  ✗ Unnamed TV: yt-dlp timeout (2 retries)
    → Using cached data (23 videos from 2026-03-05)
  ✓ Fredrik Knudsen: 39 videos (0 new)

  Done. 1 channel failed (cached data used).
  ```
- Status table format explicitly decided:
  ```
  Channel            Videos  Last Scraped   Latest Upload
  ──────────────────────────────────────────────────────
  Barely Sociable     47      2026-03-11     2026-02-15
  ```

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `context/competitors/Barely Sociable.json`: Existing video data with title, id, url, viewCount, date, likes, channelName, duration — can seed SQLite
- `context/competitors/unnamedTV.csv`: CSV competitor data — migrate to SQLite
- `context/competitors/competitors.md`: Manual competitor notes with subscriber counts, style analysis — inform registry notes field
- `.claude/skills/crawl4ai-scraper/scripts/scraper.py`: Basic crawl4ai URL→markdown scraper (not needed for Phase 1 but shows skill pattern)

### Established Patterns
- Skills live in `.claude/skills/<name>/` with SKILL.md and scripts/
- Python scripts with argparse for CLI tools (see crawl4ai scraper)
- yt-dlp skill already available in the environment

### Integration Points
- `context/competitors/` is the home for competitor data
- `data/` directory will be created for SQLite database
- Skill will be at `.claude/skills/channel-assistant/`
- Future phases extend the same skill with additional subcommands

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-scraping-infrastructure-data-model*
*Context gathered: 2026-03-11*
