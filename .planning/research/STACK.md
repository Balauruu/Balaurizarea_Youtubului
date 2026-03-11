# Stack Research

**Domain:** YouTube Channel Assistant / Competitor Intelligence
**Researched:** 2026-03-11
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.14.2 | Runtime | Already installed on system. All project scripting is Python-only per constraints. |
| SQLite (stdlib `sqlite3`) | 3.52.0 (bundled) | Competitor data storage | Zero dependencies (built into Python). Queryable, supports JSON columns, ACID-safe. Beats JSON files for anything beyond trivial datasets. See detailed rationale below. |
| yt-dlp | 2026.2.4 | YouTube metadata extraction | Already installed. Industry standard for YouTube data. Extracts channel/video metadata without downloading via `extract_info(download=False)`. |
| crawl4ai | 0.8.x | Web scraping (search results, trend pages) | Specified in Architecture.md. Async Playwright-based. Handles JS-rendered pages. Install on-demand for scraping tasks. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sqlite-utils | 3.39 | SQLite convenience layer | Pipe JSON directly into SQLite tables. Auto-schema creation. Upsert support. Dramatically reduces boilerplate vs raw `sqlite3`. |
| tabulate | 0.9.0 | Markdown/terminal table formatting | When Claude Code needs to display competitor data as formatted tables in chat. Lightweight, no dependencies. |
| python-dateutil | 2.9.x | Date parsing and relative dates | Parse YouTube upload dates (varied formats). Calculate "days since upload", "uploads per month" metrics. |
| pathlib | stdlib | File path handling | Always use `pathlib.Path` over string concatenation per project conventions (Windows compatibility). |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| sqlite3 CLI | Direct DB inspection | Ships with Python. Run `python -m sqlite3 competitors.db` to inspect data interactively. |
| sqlite-utils CLI | Quick DB operations | `sqlite-utils tables competitors.db`, `sqlite-utils query competitors.db "SELECT ..."` from shell. |
| yt-dlp CLI | Test metadata extraction | `yt-dlp --dump-json --flat-playlist "channel_url"` to verify data before coding. |

## The JSON vs SQLite Decision

**Recommendation: SQLite. Strongly.**

This is the pivotal stack decision for this project. Here is the full analysis for this specific use case.

### Why SQLite Wins for Competitor Intelligence

| Criterion | JSON Files | SQLite |
|-----------|-----------|--------|
| **Querying** | Load entire file into memory, filter with Python loops | SQL queries: `SELECT title, view_count FROM videos WHERE channel='X' ORDER BY view_count DESC LIMIT 10` |
| **Partial reads** | Must load entire file even for one record | Reads only needed rows/pages via indexes |
| **Concurrent safety** | Risk of corruption on failed writes | ACID transactions, atomic writes |
| **Schema evolution** | Manual migration, easy to break | `ALTER TABLE ADD COLUMN` or just add new columns via sqlite-utils |
| **Aggregation** | Write custom Python code every time | `SELECT channel, AVG(view_count), COUNT(*) FROM videos GROUP BY channel` |
| **Claude Code integration** | Claude must write Python to parse/filter | Claude can write SQL directly -- faster, more expressive, fewer bugs |
| **Data size** | Gets slow past ~1MB, ~5000 records | Handles millions of records without breaking a sweat |
| **Cross-session state** | File locking issues on Windows | Built-in locking, WAL mode for concurrent reads |
| **Visualization prep** | Export to CSV/JSON manually | `sqlite-utils query db.sqlite "..." --csv` one-liner |

### Why NOT JSON Files

- **The "queryability" requirement kills JSON.** The user explicitly wants querying, visualization, and analysis. JSON forces you to write Python code for every query. SQLite gives you SQL for free.
- **Claude Code writes better SQL than ad-hoc Python filtering.** When the user asks "show me competitor X's top videos by views", Claude can write a SQL query directly instead of writing a Python script that loads JSON, parses it, filters, sorts, and formats.
- **Windows file locking.** JSON files on Windows with Git Bash have known issues with concurrent reads/writes. SQLite handles this natively.

### Where JSON Still Makes Sense

- **Config files** (channel.md, past_topics.md) -- human-readable, rarely queried programmatically
- **One-off exports** -- `sqlite-utils query ... --json` when you need to pipe data somewhere
- **Schema-free scratch data** -- temporary files in `.claude/scratch/`

### Database Schema (Recommended Starting Point)

```sql
-- Channels we track
CREATE TABLE channels (
    id TEXT PRIMARY KEY,          -- YouTube channel ID
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    subscriber_count INTEGER,
    video_count INTEGER,
    description TEXT,
    niche_tags TEXT,              -- JSON array: ["dark history", "true crime"]
    last_scraped TEXT,            -- ISO 8601 timestamp
    added_at TEXT DEFAULT (datetime('now'))
);

-- Individual videos from tracked channels
CREATE TABLE videos (
    id TEXT PRIMARY KEY,          -- YouTube video ID
    channel_id TEXT REFERENCES channels(id),
    title TEXT NOT NULL,
    description TEXT,
    upload_date TEXT,             -- YYYY-MM-DD
    duration INTEGER,            -- seconds
    view_count INTEGER,
    like_count INTEGER,
    comment_count INTEGER,
    tags TEXT,                    -- JSON array
    thumbnail_url TEXT,
    scraped_at TEXT DEFAULT (datetime('now'))
);

-- Topics we've generated or covered
CREATE TABLE topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    hook TEXT,
    complexity_score INTEGER,
    obscurity_score INTEGER,
    shock_factor INTEGER,
    estimated_runtime INTEGER,   -- minutes
    status TEXT DEFAULT 'proposed',  -- proposed | selected | rejected | produced
    source_brief TEXT,           -- full JSON of topic brief
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_videos_channel ON videos(channel_id);
CREATE INDEX idx_videos_upload ON videos(upload_date);
CREATE INDEX idx_videos_views ON videos(view_count DESC);
```

### sqlite-utils Usage Patterns

```python
import sqlite_utils

db = sqlite_utils.Database("context/competitors/competitors.db")

# Upsert channel data (idempotent -- safe to re-scrape)
db["channels"].upsert(channel_data, pk="id")

# Bulk insert videos from yt-dlp JSON output
db["videos"].upsert_all(video_list, pk="id")

# Query from Python
top_videos = list(db["videos"].rows_where(
    "channel_id = ? ORDER BY view_count DESC LIMIT 10",
    [channel_id]
))

# Or just use raw SQL for complex analysis
results = db.execute("""
    SELECT c.name, COUNT(v.id) as video_count, AVG(v.view_count) as avg_views
    FROM channels c JOIN videos v ON c.id = v.channel_id
    WHERE v.upload_date > date('now', '-90 days')
    GROUP BY c.id ORDER BY avg_views DESC
""").fetchall()
```

## Installation

```bash
# Core data layer
pip install sqlite-utils tabulate python-dateutil

# Scraping (yt-dlp already installed)
pip install crawl4ai

# That's it. yt-dlp, sqlite3, pathlib, json are already available.
```

**Total new dependencies: 3 packages** (sqlite-utils, tabulate, python-dateutil). crawl4ai is installed separately when scraping tasks begin because it pulls in Playwright and browser binaries.

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|------------------------|
| SQLite + sqlite-utils | TinyDB | Never for this project. TinyDB is a document store for tiny apps. No SQL, no joins, no aggregation. |
| SQLite + sqlite-utils | Raw JSON files | Only for human-readable config (channel.md, past_topics.md). Never for queryable data. |
| SQLite + sqlite-utils | DuckDB | If you need analytical queries over millions of rows or Parquet files. Overkill here -- competitor data is thousands of rows at most. |
| SQLite + sqlite-utils | PostgreSQL | If you needed multi-user access or a server. This is a single-user CLI tool. SQLite is the right tool. |
| sqlite-utils | Raw sqlite3 | If sqlite-utils has compatibility issues with Python 3.14. Raw sqlite3 is stdlib and always works. sqlite-utils is a convenience layer, not a hard dependency. |
| tabulate | Rich | If you want colored/styled terminal output. Rich is heavier (12MB+). tabulate is 50KB and outputs clean markdown that Claude Code renders well. |
| python-dateutil | Pendulum | If you need timezone-heavy operations. Overkill for "parse upload date, compute days ago". dateutil is lighter and sufficient. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| pandas | 30MB+ dependency. Pulls in numpy. Massive for what amounts to SQL queries on small datasets. | sqlite-utils + SQL queries |
| MongoDB / any server DB | Requires running a server process. This is a CLI tool. | SQLite (serverless, zero-config) |
| TinyDB | No SQL, no joins, poor query performance at scale. Looks simple but limits you fast. | SQLite via sqlite-utils |
| YouTube Data API v3 | Requires API key, has quota limits (10,000 units/day), rate limiting. yt-dlp has no such limits. | yt-dlp with `extract_info(download=False)` |
| Scrapy | Enterprise web crawler framework. Massive overhead for targeted YouTube scraping. | crawl4ai for web pages, yt-dlp for YouTube |
| Any LLM API wrapper | Architecture.md explicitly forbids this. Claude Code IS the reasoning engine. | Claude Code native reasoning |
| Node.js / JavaScript | Project constraint: Python only. | Python for all scripting |

## yt-dlp Usage Patterns for This Project

### Extract Channel Video List (Flat, No Download)

```python
import yt_dlp

def get_channel_videos(channel_url: str) -> list[dict]:
    """Extract metadata for all videos from a YouTube channel."""
    opts = {
        'extract_flat': 'in_playlist',
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)
        return info.get('entries', [])
```

### Extract Full Video Metadata (Per Video)

```python
def get_video_details(video_id: str) -> dict:
    """Extract full metadata for a single video."""
    opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(
            f"https://www.youtube.com/watch?v={video_id}",
            download=False
        )
```

### Key Metadata Fields Available

| Field | Type | Notes |
|-------|------|-------|
| `id` | str | YouTube video ID |
| `title` | str | Video title |
| `description` | str | Full description text |
| `upload_date` | str | YYYYMMDD format |
| `duration` | int | Seconds |
| `view_count` | int | Total views |
| `like_count` | int | Likes (may be hidden) |
| `comment_count` | int | Comments |
| `tags` | list | Video tags |
| `categories` | list | YouTube categories |
| `channel_id` | str | Channel ID |
| `channel` | str | Channel name |
| `thumbnail` | str | Thumbnail URL |
| `channel_follower_count` | int | Subscriber count |

## Version Compatibility

| Component | Required Python | Status |
|-----------|----------------|--------|
| Python | 3.14.2 | Installed |
| yt-dlp 2026.2.4 | >= 3.10 | Compatible |
| sqlite-utils 3.39 | >= 3.10 | Compatible (verify on install -- Python 3.14 is new) |
| crawl4ai 0.8.x | >= 3.10 | Compatible |
| tabulate 0.9.0 | >= 3.7 | Compatible |
| python-dateutil 2.9.x | >= 3.6 | Compatible |
| sqlite3 (stdlib) | any | Always available |

**Risk note:** sqlite-utils 3.39 lists Python 3.10-3.14 support. If it fails on 3.14, fall back to raw `sqlite3` module (stdlib, zero risk). The convenience is nice but not a hard dependency.

## Sources

- [yt-dlp PyPI](https://pypi.org/project/yt-dlp) - Version and compatibility info
- [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp) - Documentation and metadata fields
- [sqlite-utils GitHub](https://github.com/simonw/sqlite-utils) - Library capabilities and API
- [sqlite-utils PyPI](https://pypi.org/project/sqlite-utils/) - Version 3.39
- [Crawl4AI Documentation](https://docs.crawl4ai.com/) - v0.8.x features
- [SQLite JSON Functions](https://sqlite.org/json1.html) - JSON column support in SQLite
- [Rich Tables Documentation](https://rich.readthedocs.io/en/stable/tables.html) - Alternative to tabulate
- [tabulate PyPI](https://pypi.org/project/tabulate/) - Lightweight table formatting
- [When JSON Sucks or The Road To SQLite Enlightenment](https://pl-rants.net/posts/when-not-json/) - JSON vs SQLite analysis
