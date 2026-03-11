# Phase 1: Scraping Infrastructure + Data Model - Research

**Researched:** 2026-03-11
**Domain:** yt-dlp YouTube metadata extraction, SQLite data storage, Python CLI skill
**Confidence:** HIGH

## Summary

Phase 1 builds a competitor channel registry (JSON config) and a yt-dlp-based scraper that populates a SQLite database with video metadata. The research validates that yt-dlp 2026.02.04 provides all required video fields (title, views, upload_date, description, duration, tags, likes) via full extraction mode. Flat-playlist mode is NOT viable -- it lacks upload_date, tags, and like_count. Full extraction takes approximately 1.3 seconds per video, meaning a 50-video channel takes ~65 seconds.

Channel-level metadata is limited: yt-dlp provides channel name, channel_id, channel_url, and subscriber count (channel_follower_count) but NOT channel description or total_views. The schema should reflect what is actually extractable. Python 3.14's stdlib sqlite3 (SQLite 3.50.4) fully supports UPSERT syntax, making sqlite-utils unnecessary.

**Primary recommendation:** Use stdlib sqlite3 with ON CONFLICT upserts, full (non-flat) yt-dlp extraction per channel, and the existing `.claude/skills/` pattern for the channel-assistant skill.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Single JSON config file: `context/competitors/competitors.json`
- Fields per channel: name, youtube_id (handle), url, notes, added (date)
- Seed with 3 existing competitors: Barely Sociable, Unnamed TV, Fredrik Knudsen
- Migrate existing data (Barely Sociable.json, unnamedTV.csv, competitors.md) into the new format
- Delete old files after migration -- single source of truth
- Database location: `data/channel_assistant.db`
- Committed to git (scraping is slow/rate-limited, data should persist)
- Two tables: `channels` (channel-level metadata) and `videos` (video metadata)
- Curated fields only -- no raw yt-dlp JSON storage
- Video fields: title, video_id, url, views, upload_date, description, duration, tags, likes, scraped_at
- Channel fields: name, youtube_id, url, subscribers, total_views, description, scraped_at
- Latest data only -- no historical snapshots
- Idempotent upserts on re-scrape
- Fetch ALL videos per channel
- Also grab channel-level metadata (subscribers, total views, description)
- Retry each channel up to 2 times with backoff on failure
- On persistent failure: skip channel, fall back to cached data, continue
- Report failures at end -- never crash mid-run
- 3-8 second jittered delay between channels
- Per-channel progress output during scrape
- Single `/channel-assistant` skill with subcommands
- Phase 1 subcommands: `add <url>`, `scrape`, `scrape <name>`, `status`
- `add` registers only -- no auto-scrape on add
- Progress output format: `Scraping N channels... / checkmark Channel: N videos (M new) / x Channel: reason (retries) / -> Using cached data (N videos from date)`
- Status table format: `Channel | Videos | Last Scraped | Latest Upload`

### Claude's Discretion
- Exact SQLite index strategy
- yt-dlp extraction parameters and metadata field mapping
- Error message wording and formatting
- Internal module structure and file organization
- Whether to use sqlite-utils or stdlib sqlite3

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DATA-01 | User can define a competitor watchlist in a JSON config file with channel name, YouTube channel ID/URL, and notes | Validated: JSON config at `context/competitors/competitors.json`. Existing data in 3 formats (JSON, CSV, MD) available for migration. |
| DATA-02 | System scrapes video metadata (title, views, upload date, description, duration, tags) for all channels in the registry via yt-dlp | Validated: yt-dlp 2026.02.04 full extraction provides all required fields. Flat-playlist mode lacks critical fields -- must use full mode. ~1.3s per video. |
| DATA-03 | Scraped data is stored in SQLite with `channels` and `videos` tables, each record timestamped with `scraped_at` | Validated: Python 3.14 stdlib sqlite3 (SQLite 3.50.4) supports UPSERT. No third-party dependency needed. |
| DATA-04 | Scraper uses rate limiting (jittered delays) and falls back to cached data on yt-dlp failure | Design validated: random.uniform(3, 8) between channels. On failure after 2 retries, skip and report. Cached = existing DB rows. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| yt-dlp | 2026.02.04 | YouTube metadata extraction | Already installed, project standard per Architecture.md |
| sqlite3 (stdlib) | SQLite 3.50.4 | Database storage | Zero dependency, Python 3.14 built-in, full UPSERT support |
| json (stdlib) | - | Competitor registry config | Zero dependency |
| argparse (stdlib) | - | CLI subcommands | Project pattern (crawl4ai-scraper uses it) |
| pathlib (stdlib) | - | Path handling | CLAUDE.md mandates pathlib over string concatenation |
| random (stdlib) | - | Jittered delays | random.uniform(3, 8) for rate limiting |
| subprocess (stdlib) | - | yt-dlp invocation | Run yt-dlp as subprocess, parse JSON output |
| datetime (stdlib) | - | Timestamps | scraped_at fields, date formatting |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib sqlite3 | sqlite-utils | sqlite-utils is not installed, Python 3.14 compat unverified. stdlib is zero-dep and fully sufficient. **Use stdlib.** |
| subprocess for yt-dlp | yt-dlp Python API | yt-dlp Python API exists but is underdocumented and couples tightly to internal APIs. subprocess + JSON output is more stable and debuggable. **Use subprocess.** |

**Installation:**
```bash
# No installation needed - all stdlib + yt-dlp already installed
```

## Architecture Patterns

### Recommended Project Structure
```
.claude/skills/channel-assistant/
  SKILL.md                    # Skill definition (subcommand docs)
  scripts/
    channel_assistant/
      __init__.py
      cli.py                  # argparse entry point with subcommands
      registry.py             # competitors.json read/write/validate
      scraper.py              # yt-dlp invocation, retry logic, delays
      database.py             # SQLite schema, upserts, queries
      models.py               # Dataclasses for Channel, Video
context/competitors/
  competitors.json            # Competitor registry (single source of truth)
data/
  channel_assistant.db        # SQLite database (git-committed)
```

### Pattern 1: Subprocess yt-dlp with JSON Output
**What:** Invoke yt-dlp as subprocess, capture stdout line-by-line (one JSON object per video)
**When to use:** All video metadata extraction
**Example:**
```python
# Verified via direct testing against yt-dlp 2026.02.04
import subprocess, json

def scrape_channel_videos(channel_url: str) -> list[dict]:
    """Extract all video metadata from a channel. Returns list of video dicts."""
    cmd = [
        "yt-dlp",
        "--dump-json",       # Output JSON per video to stdout
        "--skip-download",   # Don't download media
        "--no-warnings",     # Suppress warnings
        channel_url + "/videos"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr[:200]}")

    videos = []
    for line in result.stdout.strip().split("\n"):
        if line:
            videos.append(json.loads(line))
    return videos
```

**Critical: yt-dlp outputs one JSON object PER LINE, not a JSON array.** Each line must be parsed independently.

### Pattern 2: SQLite Upsert with ON CONFLICT
**What:** Insert-or-update pattern using SQLite UPSERT
**When to use:** Every scrape operation (idempotent updates)
**Example:**
```python
# Verified: Python 3.14 sqlite3 with SQLite 3.50.4 supports this syntax
conn.execute("""
    INSERT INTO videos (video_id, channel_id, title, url, views, upload_date,
                        description, duration, tags, likes, scraped_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(video_id) DO UPDATE SET
        views = excluded.views,
        likes = excluded.likes,
        title = excluded.title,
        description = excluded.description,
        tags = excluded.tags,
        scraped_at = excluded.scraped_at
""", params)
```

### Pattern 3: Skill Subcommand Structure
**What:** Single CLI entry point with subcommands via argparse
**When to use:** channel-assistant skill
**Example:**
```python
# Follows project pattern from crawl4ai-scraper
parser = argparse.ArgumentParser(description="Channel Assistant")
subparsers = parser.add_subparsers(dest="command")

add_parser = subparsers.add_parser("add", help="Register a competitor channel")
add_parser.add_argument("url", help="YouTube channel URL or handle")

scrape_parser = subparsers.add_parser("scrape", help="Scrape all or specific channel")
scrape_parser.add_argument("name", nargs="?", help="Channel name (optional)")

subparsers.add_parser("status", help="Show channel summary")
```

### Anti-Patterns to Avoid
- **Using flat-playlist mode:** Loses upload_date, tags, like_count. Always use full extraction.
- **Storing raw yt-dlp JSON:** User explicitly decided curated fields only. Extract and map specific fields.
- **Single INSERT without ON CONFLICT:** Causes duplicate key errors on re-scrape. Always use UPSERT.
- **Using yt-dlp Python API directly:** Underdocumented internal API. Use subprocess + JSON parsing.
- **Crashing on channel failure:** Must catch, retry, skip, and report at end.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YouTube metadata extraction | Custom scraper/API client | yt-dlp subprocess | Handles auth, rate limits, format changes automatically |
| JSON-lines parsing | Custom stream parser | `line.split("\n")` + `json.loads()` per line | yt-dlp outputs well-formed JSON per line |
| Retry with backoff | Custom retry decorator | Simple for-loop with `time.sleep(delay * attempt)` | Only 2 retries needed, no library warranted |
| SQLite migrations | Migration framework | `CREATE TABLE IF NOT EXISTS` + `CREATE INDEX IF NOT EXISTS` | Single-version schema, no migration history needed |

**Key insight:** This phase is entirely stdlib Python + yt-dlp subprocess. No third-party Python packages are needed.

## Common Pitfalls

### Pitfall 1: Flat-Playlist Mode Missing Fields
**What goes wrong:** Using `--flat-playlist` for speed, but output lacks upload_date, tags, like_count
**Why it happens:** Flat mode only fetches playlist-level metadata, not per-video details
**How to avoid:** Always use full extraction (`--dump-json --skip-download`)
**Warning signs:** `None` or `MISSING` values for upload_date, tags, like_count

### Pitfall 2: yt-dlp Timeout on Large Channels
**What goes wrong:** Subprocess hangs indefinitely for channels with 200+ videos
**Why it happens:** yt-dlp fetches sequentially, each video takes ~1.3s
**How to avoid:** Set `timeout=300` on subprocess.run (5 minutes). For the target channels (20-100 videos), this is generous.
**Warning signs:** Scrape taking >5 minutes for a single channel

### Pitfall 3: upload_date Format
**What goes wrong:** Assuming ISO format, but yt-dlp returns `YYYYMMDD` string (e.g., `"20231031"`)
**Why it happens:** yt-dlp convention, not ISO 8601
**How to avoid:** Parse with `datetime.strptime(date_str, "%Y%m%d")` and store as ISO `YYYY-MM-DD`
**Warning signs:** Date sorting/display errors

### Pitfall 4: Tags as JSON Array in SQLite
**What goes wrong:** Trying to store Python list directly in SQLite TEXT column
**Why it happens:** SQLite has no native array type
**How to avoid:** Serialize tags as JSON string: `json.dumps(tags)`. Deserialize on read.
**Warning signs:** `[list]` string appearing in output instead of actual tags

### Pitfall 5: Channel-Level Metadata Gaps
**What goes wrong:** Schema expects `total_views` and `description` for channels, but yt-dlp doesn't provide them from the videos endpoint
**Why it happens:** yt-dlp extracts per-video data; channel description and total views aren't in video JSON
**How to avoid:** Make `total_views` and `description` nullable in the channels table. Populate what is available: name, youtube_id, url, subscribers (from `channel_follower_count`). Leave others NULL.
**Warning signs:** Empty columns in channels table

### Pitfall 6: Windows Path Handling
**What goes wrong:** Hardcoded forward slashes or backslashes breaking cross-platform
**Why it happens:** Project runs on Windows 11 with Git Bash
**How to avoid:** Use `pathlib.Path` everywhere (per CLAUDE.md mandate). Paths resolve correctly on Windows.
**Warning signs:** FileNotFoundError on path operations

### Pitfall 7: Existing Data Migration Field Mapping
**What goes wrong:** Field name mismatches between existing JSON/CSV and new schema
**Why it happens:** Barely Sociable.json uses `viewCount` not `views`, `date` not `upload_date`, `numberOfSubscribers` not `subscribers`
**How to avoid:** Write explicit field mapping during migration:
```python
# Barely Sociable.json field mapping
mapping = {
    "viewCount": "views",
    "id": "video_id",
    "date": "upload_date",  # ISO format, needs reformatting to YYYY-MM-DD
    "likes": "likes",       # String like "83000" in source
    "numberOfSubscribers": "subscribers",
    "duration": "duration", # HH:MM:SS format, convert to seconds
}
```
**Warning signs:** NULL values in migrated data, type errors

## Code Examples

### yt-dlp Field Mapping (Verified)
```python
# Verified via direct yt-dlp 2026.02.04 extraction on 2026-03-11
# These are the actual field names in yt-dlp full extraction JSON output

VIDEO_FIELD_MAP = {
    # yt-dlp field        -> our schema field
    "id":                   "video_id",
    "title":                "title",
    "webpage_url":          "url",
    "view_count":           "views",
    "upload_date":          "upload_date",    # Format: "YYYYMMDD"
    "description":          "description",
    "duration":             "duration",       # Integer seconds
    "tags":                 "tags",           # List of strings
    "like_count":           "likes",          # Integer
}

CHANNEL_FIELD_MAP = {
    # Available from any video in the channel
    "channel":                "name",
    "channel_id":             "youtube_id",     # e.g. "UC9PIn6-XuRKZ5HmYeu46AIw"
    "uploader_id":            "handle",         # e.g. "@BarelySociable"
    "channel_url":            "url",
    "channel_follower_count": "subscribers",    # Integer
    # NOT AVAILABLE via yt-dlp:
    # - channel description (video `description` is per-video)
    # - total_views (would need YouTube API)
}
```

### SQLite Schema (Recommended)
```sql
-- channels table
CREATE TABLE IF NOT EXISTS channels (
    youtube_id TEXT PRIMARY KEY,      -- channel ID (e.g. UC9PIn6-XuRKZ5HmYeu46AIw)
    name TEXT NOT NULL,
    handle TEXT,                      -- @handle
    url TEXT,
    subscribers INTEGER,
    total_views INTEGER,             -- NULL (not available from yt-dlp)
    description TEXT,                -- NULL (not available from yt-dlp)
    scraped_at TEXT NOT NULL         -- ISO 8601 timestamp
);

-- videos table
CREATE TABLE IF NOT EXISTS videos (
    video_id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT,
    views INTEGER,
    upload_date TEXT,                -- YYYY-MM-DD format
    description TEXT,
    duration INTEGER,               -- seconds
    tags TEXT,                       -- JSON array string
    likes INTEGER,
    scraped_at TEXT NOT NULL,        -- ISO 8601 timestamp
    FOREIGN KEY (channel_id) REFERENCES channels(youtube_id)
);

-- Recommended indexes
CREATE INDEX IF NOT EXISTS idx_videos_channel ON videos(channel_id);
CREATE INDEX IF NOT EXISTS idx_videos_views ON videos(views DESC);
CREATE INDEX IF NOT EXISTS idx_videos_upload_date ON videos(upload_date DESC);
```

### Competitors Registry Schema
```json
{
  "channels": [
    {
      "name": "Barely Sociable",
      "youtube_id": "@BarelySociable",
      "url": "https://www.youtube.com/@BarelySociable",
      "notes": "Dark web + true crime crossover. Investigative journalist tone.",
      "added": "2026-03-11"
    }
  ]
}
```

### Migration: Existing Barely Sociable.json
```python
# Source format (existing):
# {"title": "...", "id": "1R97tphpD_M", "viewCount": 3147729,
#  "date": "2021-08-30T20:35:05.000Z", "likes": 83000,
#  "duration": "00:48:04"}

# Key transformations needed:
# 1. viewCount -> views (int, already int)
# 2. id -> video_id
# 3. date -> upload_date (parse ISO, output YYYY-MM-DD)
# 4. likes -> likes (int, but source has int like 83000)
# 5. duration -> duration (parse "HH:MM:SS" to seconds)
```

### Migration: Existing unnamedTV.csv
```python
# Source columns: ID, TITLE, DESCRIPTION, DURATION, STATUS, DATE PUBLISHED,
#                 KEYWORDS, VIDIQ SCORE, VIEWS, YT LIKES, YT COMMENTS, ...

# Key transformations:
# 1. ID -> video_id
# 2. VIEWS -> views (int, e.g. 2212672)
# 3. DATE PUBLISHED -> upload_date (format: "7/12/2024" -> "2024-07-12")
# 4. YT LIKES -> likes (string like "67K" -> parse to int 67000)
# 5. DURATION -> duration (format: "20:29" -> 1229 seconds)
# 6. KEYWORDS -> tags (comma-separated string -> JSON array)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| YouTube Data API v3 | yt-dlp | Ongoing | No API key needed, same data, simpler setup |
| sqlite-utils | stdlib sqlite3 | SQLite 3.24+ (2018) | UPSERT support in stdlib eliminates need for wrapper |
| requests + BeautifulSoup | yt-dlp | N/A | yt-dlp handles YouTube's anti-scraping measures |

## Open Questions

1. **Channel description and total_views not available via yt-dlp**
   - What we know: yt-dlp video extraction includes subscriber count but NOT channel description or total_views
   - What's unclear: Whether the user strictly needs these fields populated
   - Recommendation: Make columns nullable, populate what we can. Note in SKILL.md. If needed later, could scrape channel page with crawl4ai.

2. **yt-dlp rate limiting by YouTube**
   - What we know: 3-8 second jitter between channels helps. No per-video delay needed since extraction is sequential.
   - What's unclear: Whether YouTube throttles after many channel scrapes in one session
   - Recommendation: The 3 seed channels are well within safe limits. Monitor if registry grows beyond ~15 channels.

3. **Large likes values in unnamedTV.csv**
   - What we know: Likes stored as "67K", "1.1K" etc. -- need parsing to integers
   - What's unclear: All format variations (K, M, etc.)
   - Recommendation: Parse with multiplier detection: `67K -> 67000`, `1.1K -> 1100`

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (standard Python testing) |
| Config file | none -- Wave 0 |
| Quick run command | `python -m pytest tests/test_channel_assistant/ -x -q` |
| Full suite command | `python -m pytest tests/test_channel_assistant/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | Add channel to registry JSON, validate fields | unit | `python -m pytest tests/test_channel_assistant/test_registry.py -x` | No -- Wave 0 |
| DATA-02 | yt-dlp extracts video metadata with correct field mapping | integration | `python -m pytest tests/test_channel_assistant/test_scraper.py -x` | No -- Wave 0 |
| DATA-03 | SQLite upsert creates/updates records with scraped_at | unit | `python -m pytest tests/test_channel_assistant/test_database.py -x` | No -- Wave 0 |
| DATA-04 | Retry logic, jittered delays, graceful failure fallback | unit | `python -m pytest tests/test_channel_assistant/test_scraper.py::test_retry_logic -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_channel_assistant/ -x -q`
- **Per wave merge:** `python -m pytest tests/test_channel_assistant/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_channel_assistant/test_registry.py` -- covers DATA-01 (JSON read/write/validate)
- [ ] `tests/test_channel_assistant/test_database.py` -- covers DATA-03 (schema creation, upserts, queries)
- [ ] `tests/test_channel_assistant/test_scraper.py` -- covers DATA-02, DATA-04 (yt-dlp extraction, retry, delays)
- [ ] `tests/test_channel_assistant/conftest.py` -- shared fixtures (temp DB, sample data)
- [ ] `pytest.ini` or `pyproject.toml` [tool.pytest] -- test configuration
- [ ] Framework install: `pip install pytest` -- if not already installed

## Sources

### Primary (HIGH confidence)
- Direct yt-dlp 2026.02.04 testing on live YouTube channels (Barely Sociable) -- field availability, extraction speed, output format
- Direct Python 3.14 sqlite3 testing -- UPSERT syntax, Row factory, SQLite 3.50.4
- Existing project files: `Barely Sociable.json`, `unnamedTV.csv`, `competitors.md` -- migration source format

### Secondary (MEDIUM confidence)
- yt-dlp --help and output format conventions (JSON-lines output)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all tools directly tested and verified working
- Architecture: HIGH -- follows established project skill patterns, all stdlib
- Pitfalls: HIGH -- discovered through direct testing (flat-playlist gaps, field name mismatches)
- Migration: MEDIUM -- CSV parsing edge cases (K/M suffixes) need validation during implementation

**Research date:** 2026-03-11
**Valid until:** 2026-04-11 (stable tools, no fast-moving dependencies)
