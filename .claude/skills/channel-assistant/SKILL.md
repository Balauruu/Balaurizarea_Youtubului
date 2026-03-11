# channel-assistant

## Description

Competitor intelligence and topic ideation for the dark mysteries YouTube channel. Manages a competitor channel registry, scrapes video metadata via yt-dlp into a SQLite database, and provides query/analysis capabilities for topic selection.

## Instructions

1. This skill relies on native Python script execution. Do not make LLM API calls inside the execution.
2. Use the `Bash` or shell execution tool to run subcommands.
3. The competitor registry is stored at `context/competitors/competitors.json` (single source of truth).
4. The SQLite database is stored at `data/channel_assistant.db` (committed to git -- scraping is slow/rate-limited).

## Subcommands

### `add <url>`

Register a new competitor channel. Validates the URL/handle, adds to `competitors.json`. Does NOT auto-scrape.

```bash
python -m channel_assistant.cli add "https://www.youtube.com/@ChannelHandle"
```

### `scrape`

Scrape all registered competitor channels. Fetches all video metadata via yt-dlp and stores in SQLite. Uses 3-8 second jittered delays between channels. Retries up to 2 times per channel on failure, falls back to cached data.

```bash
python -m channel_assistant.cli scrape
```

Output format:
```
Scraping 3 channels...
* Barely Sociable: 47 videos (12 new)
x Unnamed TV: yt-dlp timeout (2 retries)
  -> Using cached data (23 videos from 2026-03-05)
* Fredrik Knudsen: 39 videos (0 new)

Done. 1 channel failed (cached data used).
```

### `scrape <name>`

Scrape a specific channel by name (case-insensitive partial match).

```bash
python -m channel_assistant.cli scrape "barely"
```

### `status`

Show summary table of all tracked channels with video counts and scrape status.

```bash
python -m channel_assistant.cli status
```

Output format:
```
Channel            Videos  Last Scraped   Latest Upload
-----------------------------------------------------
Barely Sociable     47      2026-03-11     2026-02-15
Unnamed TV          23      2026-03-05     2026-01-20
Fredrik Knudsen     39      2026-03-11     2025-12-01
```

### `analyze`

Run competitor analysis: channel stats, outlier detection, topic clustering, title patterns. Generates `context/competitors/analysis.md` and writes serialized video data to `.claude/scratch/video_data_for_analysis.md` for Claude heuristic reasoning.

```bash
python -m channel_assistant.cli analyze
```

### `topics`

Load context for topic generation: competitor analysis, channel DNA, past topics, trend data. Prints structured context to stdout for Claude to generate scored topic briefs. After context is printed, Claude performs the [HEURISTIC] generation, scoring, and deduplication steps using `check_duplicates()`.

```bash
python -m channel_assistant.cli topics
```

### `trends`

Scan YouTube for trending topics and content gaps. Scrapes autocomplete suggestions and recent search results for niche keywords, detects cross-channel convergence, updates `analysis.md` with trend sections.

```bash
python -m channel_assistant.cli trends
```

## File Locations

| File | Purpose |
|------|---------|
| `context/competitors/competitors.json` | Competitor channel registry |
| `data/channel_assistant.db` | SQLite database (channels + videos tables) |
| `.claude/skills/channel-assistant/scripts/channel_assistant/` | Python modules |

## Key Modules

| Module | Exports | Purpose |
|--------|---------|---------|
| `models.py` | `Channel`, `Video` | Dataclasses for channel and video metadata |
| `registry.py` | `Registry` | Read/write/validate competitors.json |
| `database.py` | `Database` | SQLite schema creation, upserts, queries |
| `cli.py` | (entry point) | Argparse CLI with subcommands |
| `analyzer.py` | `compute_channel_stats`, `detect_outliers`, `format_stats_table`, `serialize_videos_for_analysis` | Channel statistics and outlier detection |
| `topics.py` | `load_topic_inputs`, `check_duplicates`, `write_topic_briefs`, `format_chat_cards` | Topic generation helpers and dedup |
| `trend_scanner.py` | `scrape_autocomplete`, `scrape_search_results`, `get_recent_competitor_videos`, `derive_keywords` | YouTube trend scanning |
| `project_init.py` | `load_project_inputs`, `init_project` | Project directory creation and metadata |

## Schema Notes

- **Channel fields:** name, youtube_id, handle, url, subscribers, total_views (nullable), description (nullable), scraped_at
- **Video fields:** video_id, channel_id, title, url, views, upload_date, description, duration, tags (JSON array), likes, scraped_at
- `total_views` and `description` on channels are nullable -- yt-dlp does not provide these from the videos endpoint
- Tags are stored as JSON strings in SQLite and deserialized to Python lists on read
- Upserts are idempotent: re-scraping updates existing records without creating duplicates

## Dependencies

- Python 3.14+ (stdlib only: sqlite3, json, argparse, pathlib, subprocess, random, datetime)
- yt-dlp (installed in environment)

## Entry Point

```bash
python -m channel_assistant.cli <subcommand> [args]
```
