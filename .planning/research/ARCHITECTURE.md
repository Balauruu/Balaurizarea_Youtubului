# Architecture Research

**Domain:** YouTube Channel Assistant / Competitor Intelligence
**Researched:** 2026-03-11
**Confidence:** HIGH

This architecture follows the proven skill pattern established by `visual-style-extractor` in this repo: SKILL.md orchestration instructions, Python scripts for deterministic work, prompt files for heuristic work. Data storage uses SQLite (not JSON files) based on the queryability, analysis, and visualization requirements in PROJECT.md.

## System Overview

```
                          CLAUDE CODE (Orchestrator)
                                    |
                    reads SKILL.md for instructions
                                    |
           +------------------------+------------------------+
           |                        |                        |
    [Competitor Intel]      [Topic Ideation]         [Project Setup]
     Subagent(s)             Main Agent               Main Agent
           |                        |                        |
    +------+------+          +------+------+          +------+------+
    | yt-dlp      |          | Channel DNA |          | Create dir  |
    | crawl4ai    |          | Past topics |          | Write meta  |
    | Parse/store |          | Comp. data  |          | Update past |
    +------+------+          | Trend data  |          +-------------+
           |                 +------+------+
           v                        |
    context/competitors/            v
    competitors.db           .claude/scratch/
    (SQLite database)        (topic briefs)
                                    |
                                    v
                             User picks topic
                                    |
                                    v
                             projects/N. Title/
                             (metadata.md)
```

## Component Responsibilities

### Component 1: Competitor Scraper (`scrape.py`)
**Type:** DETERMINISTIC
**Responsibility:** Fetch raw channel and video data from YouTube using yt-dlp. No analysis, no filtering -- just structured data acquisition.
**Inputs:** Channel URL or handle
**Outputs:** Upserted records in SQLite `channels` and `videos` tables
**Tools:** yt-dlp (channel metadata, video list, individual video metadata)

Key operations:
- `scrape_channel_metadata(handle)` -- subscriber count, description, upload frequency
- `scrape_video_list(handle, limit=50)` -- titles, views, dates, durations, tags
- `scrape_video_details(video_id)` -- description, tags, engagement metrics

### Component 2: Data Store (`store.py`)
**Type:** DETERMINISTIC
**Responsibility:** Normalize raw yt-dlp output and upsert into SQLite. Handle deduplication, timestamping, and cache freshness checks.
**Inputs:** Raw dict from yt-dlp `extract_info()`
**Outputs:** Records in `context/competitors/competitors.db`

Uses sqlite-utils for convenience:
```python
import sqlite_utils

db = sqlite_utils.Database("context/competitors/competitors.db")
db["channels"].upsert(channel_record, pk="id", alter=True)
db["videos"].upsert_all(video_records, pk="id", alter=True)
```

Freshness check:
```python
def is_stale(handle: str, max_age_days: int = 7) -> bool:
    row = db.execute(
        "SELECT last_scraped FROM channels WHERE id = ?", [handle]
    ).fetchone()
    if not row:
        return True
    last = datetime.fromisoformat(row[0])
    return (datetime.now(timezone.utc) - last).days > max_age_days
```

### Component 3: Query & Format (`query.py`)
**Type:** DETERMINISTIC
**Responsibility:** Run SQL queries against the DB and format results for Claude Code consumption. Outputs markdown tables or writes to `.claude/scratch/` for large results.
**Inputs:** Query type (top videos, channel stats, recent uploads, etc.)
**Outputs:** Formatted text to stdout or `.claude/scratch/`

Example queries the skill will need:
```sql
-- Channel overview
SELECT name, subscriber_count, video_count, last_scraped FROM channels;

-- Top performing videos across all competitors
SELECT c.name, v.title, v.view_count, v.upload_date
FROM videos v JOIN channels c ON v.channel_id = c.id
ORDER BY v.view_count DESC LIMIT 20;

-- Upload frequency per channel (last 6 months)
SELECT c.name, COUNT(*) as uploads, AVG(v.view_count) as avg_views
FROM videos v JOIN channels c ON v.channel_id = c.id
WHERE v.upload_date > date('now', '-180 days')
GROUP BY c.id ORDER BY uploads DESC;

-- Content gap: topics with high views that our channel hasn't covered
-- (Claude Code interprets results, not the SQL)
SELECT v.title, v.view_count, v.tags
FROM videos v
WHERE v.view_count > (SELECT AVG(view_count) * 2 FROM videos)
ORDER BY v.view_count DESC;
```

### Component 4: Competitor Analyzer (Prompt-driven)
**Type:** HEURISTIC
**Responsibility:** Claude Code reads formatted competitor data (from query.py output) and channel DNA, then generates strategic insights.
**Inputs:** Pre-aggregated stats from query.py, `context/channel/channel.md`
**Outputs:** Analysis written to `.claude/scratch/competitor_analysis.md`

The analysis prompt should ask for:
- Topic selection patterns per competitor (what niches do they cluster in?)
- Title strategies (length, keywords, emotional triggers)
- Content gaps (topics none of the competitors have covered)
- Performance signals (what types of videos get disproportionate views?)
- Upload cadence and trends

### Component 5: Trend Scanner (`trends.py`)
**Type:** DETERMINISTIC
**Responsibility:** Scrape YouTube search results and recent uploads in the niche to surface trending topics. Uses crawl4ai for YouTube search pages.
**Inputs:** Search queries derived from channel pillars (from channel.md)
**Outputs:** Trend data inserted into a `trends` table in the same SQLite DB

### Component 6: Topic Generator (Prompt-driven)
**Type:** HEURISTIC
**Responsibility:** The core ideation engine. Claude Code synthesizes all available context (channel DNA, competitor analysis, trend data, past topics) to generate 5 scored topic briefs.
**Inputs:** All context files + pre-aggregated DB data
**Outputs:** Topic briefs presented in chat, then saved to `.claude/scratch/topic_briefs.json`

### Component 7: Project Initializer (`init_project.py`)
**Type:** DETERMINISTIC
**Responsibility:** After user selects a topic, create the project directory with metadata.
**Inputs:** Selected topic brief + user confirmation
**Outputs:** `projects/N. {Title}/metadata.md` with title variants and description

## Recommended Project Structure

```
.claude/skills/channel-assistant/
+-- SKILL.md                          # Orchestration instructions (Claude reads this)
+-- scripts/
|   +-- requirements.txt              # Python deps: sqlite-utils, tabulate, python-dateutil
|   +-- channel_assistant/
|       +-- __init__.py
|       +-- scrape.py                 # Component 1: yt-dlp wrapper for channel/video data
|       +-- store.py                  # Component 2: Normalize + upsert into SQLite
|       +-- query.py                  # Component 3: SQL queries + formatting
|       +-- trends.py                 # Component 5: YouTube search scraping via crawl4ai
|       +-- init_project.py           # Component 7: Create project dirs + metadata files
|       +-- tests/
|           +-- __init__.py
|           +-- test_scrape.py
+-- prompts/
|   +-- competitor_analysis.txt       # Component 4: Strategic analysis prompt
|   +-- topic_generation.txt          # Component 6: Topic ideation prompt
|   +-- metadata_generation.txt       # Title variants + description prompt
+-- docs/
    +-- plans/                        # Design docs
```

### Data Storage Layout

```
context/competitors/
+-- competitors.db                    # THE data store (SQLite, single file)

context/channel/
+-- channel.md                        # Channel DNA (read-only)
+-- past_topics.md                    # Previously covered topics (append)

context/trends/                       # Optional: trend scan history
+-- (managed via trends table in competitors.db)

projects/
+-- 1. Video Title/
|   +-- metadata.md
+-- 2. Another Video/
    +-- metadata.md
```

### Why SQLite Over JSON Files

The previous draft recommended JSON files. This is revised based on STACK.md research and Pitfalls analysis (Pitfall 4). The deciding factors:

1. **Claude Code writes SQL faster than ad-hoc Python.** When the user asks "show me top videos", Claude writes a SQL query. With JSON, Claude must write a Python script that loads files, parses, filters, and sorts.
2. **Aggregation is built-in.** `AVG(view_count)`, `COUNT(*)`, `GROUP BY channel` -- all free with SQL. With JSON, every aggregation is custom Python code.
3. **The data IS relational.** Channels have videos. Videos have metrics over time. This is a textbook relational structure.
4. **Single file, zero server.** `competitors.db` is one file, works on Windows, no config needed.
5. **sqlite-utils makes it as easy as JSON.** `db["videos"].upsert_all(data, pk="id")` is simpler than managing JSON files, index files, and dedup logic.

JSON remains appropriate for: human-readable config (channel.md), scratch files, export formats.

## Data Flow

### Flow 1: Competitor Data Refresh

```
User: "refresh competitor data" or "add competitor @ChannelHandle"
  |
  v
SKILL.md instructs Claude Code:
  |
  +---> scrape.py: fetch raw data via yt-dlp
  |       |
  |       v
  +---> store.py: normalize + upsert into competitors.db
  |       |
  |       v
  +---> query.py: generate summary stats
  |       |
  |       v
  +---> .claude/scratch/competitor_summary.txt (if large)
  |
  +---> Spawn subagent with competitor_analysis.txt prompt
          |
          v
        .claude/scratch/competitor_analysis.md
```

### Flow 2: Topic Ideation

```
User: "suggest topics"
  |
  v
SKILL.md instructs Claude Code:
  |
  +---> query.py: check data freshness (warn if > 7 days old)
  |
  +---> [Optional] trends.py: scrape current YouTube trends
  |
  +---> query.py: pre-aggregate competitor data for context
  |       |
  |       v
  |     .claude/scratch/competitor_summary.txt
  |
  +---> Claude reads all context:
  |       - context/channel/channel.md
  |       - context/channel/past_topics.md
  |       - .claude/scratch/competitor_analysis.md
  |       - .claude/scratch/competitor_summary.txt
  |
  +---> topic_generation.txt prompt drives ideation
  |       |
  |       v
  |     5 topic briefs presented in chat
  |
  +---> User picks a topic (from chat)
  |
  +---> init_project.py: create project dir
  |       |
  |       v
  |     projects/N. {Title}/metadata.md
  |
  +---> Update context/channel/past_topics.md
```

### Flow 3: Downstream Handoff (to Agent 1.2)

```
projects/N. {Title}/
+-- metadata.md          # Title variants, description, topic brief
+-- (Agent 1.2 will add research.md here later)
```

The project directory is the handoff point. Agent 1.2 (Deep Research) reads `metadata.md` to know what to research. Agents communicate through the filesystem.

## Architectural Patterns

### Pattern 1: Cache-First with Staleness Check
**What:** Always check local data before scraping. Only re-scrape when data is stale or user explicitly requests refresh.
**Why:** yt-dlp scraping is slow (5-15 seconds per channel). Competitor data doesn't change hourly.
**Implementation:** `last_scraped` column in `channels` table. SKILL.md instructs Claude to check freshness before triggering scrape.

### Pattern 2: Normalization Layer Between yt-dlp and Storage
**What:** Never pass raw yt-dlp JSON directly to the database. Always normalize through a function that handles missing fields, type coercion, and defaults.
**Why:** yt-dlp output schema is unstable between versions. Fields appear, disappear, or change type.

### Pattern 3: Subagent for Analysis, Script for Data
**What:** Python scripts handle all data fetching and structuring. LLM subagents handle all strategic analysis and content generation.
**Why:** This is the HEURISTIC vs DETERMINISTIC split mandated by Architecture.md.

### Pattern 4: Pre-Aggregation Before LLM Context
**What:** SQL queries summarize data before passing to Claude. The LLM receives "Competitor X: 45 videos, avg 500K views, top tags: [cult, mystery]" not 1000 raw video records.
**Why:** Raw data floods context window. Summaries are more actionable.

### Pattern 5: Idempotent Upserts
**What:** All data writes use upsert (INSERT or UPDATE). Re-scraping a channel updates existing records, never creates duplicates.
**Why:** Users will re-scrape frequently. Duplicates corrupt all aggregation queries.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Monolithic Scraper
**What:** One script that scrapes, normalizes, analyzes, and generates topics.
**Why bad:** Violates HEURISTIC/DETERMINISTIC separation. Makes partial re-runs impossible.
**Instead:** Separate scrape, store, query, and analysis into independent components.

### Anti-Pattern 2: LLM-Driven Scraping
**What:** Asking Claude Code to "go find competitors" by browsing the web in an unstructured way.
**Why bad:** Unreliable, non-reproducible, slow.
**Instead:** Use deterministic scripts (yt-dlp, crawl4ai) with structured output.

### Anti-Pattern 3: Embedding Raw Data in Prompts
**What:** Copying all competitor video titles into the topic generation prompt.
**Why bad:** 15 competitors x 50 videos = context window bloat. LLM loses focus.
**Instead:** Pre-aggregate with SQL, feed summaries to prompts.

### Anti-Pattern 4: Over-Engineering the Data Layer
**What:** SQLAlchemy ORM, Alembic migrations, connection pooling, data classes for every table.
**Why bad:** This is a single-user CLI tool with 3 tables. sqlite-utils IS the right abstraction level.
**Instead:** sqlite-utils for convenience, raw SQL for complex queries.

## Integration Points

### With Existing Repo

| Integration | How |
|---|---|
| `context/channel/channel.md` | Read-only. Topic generation uses this as constraints. |
| `context/channel/past_topics.md` | Read + append. Checked during ideation, updated after topic selection. |
| `context/competitors/` | Owned by this skill. Contains `competitors.db`. |
| `projects/` | Write-only. Creates new project dirs on topic selection. |
| `.claude/scratch/` | Transient storage for large intermediate data. |

### With Downstream Pipeline

| Consumer | What They Need | Where They Get It |
|---|---|---|
| Agent 1.2 (Research) | Topic brief, key questions | `projects/N. Title/metadata.md` |
| Agent 1.3 (Writer) | Topic context | Same project dir (after research fills it) |
| Future: Channel analytics | Competitor tracking over time | `competitors.db` historical data |

## Build Order (Dependencies)

```
Phase 1: scrape.py + store.py + DB schema
    (foundation -- everything else needs data)
    |
Phase 2: query.py + Competitor analysis prompt + SKILL.md (basic flow)
    (can now do: add competitor, refresh data, view stats, get analysis)
    |
Phase 3: Topic generation prompt + init_project.py
    (can now do: full ideation flow, project creation)
    |
Phase 4: trends.py
    (enhances ideation with real-time data, not blocking)
    |
Phase 5: Metadata generation prompt (title variants + description)
    (polish step)
```

Phase 1-2 are the minimum viable skill. Phase 3 completes the core flow. Phases 4-5 are enhancements.

## Sources

- Existing skill pattern: `.claude/skills/visual-style-extractor/SKILL.md` (HIGH confidence -- direct codebase reference)
- Architecture rules: `Architecture.md` in repo root (HIGH confidence -- project constraints)
- Project requirements: `.planning/PROJECT.md` (HIGH confidence -- validated requirements)
- [sqlite-utils documentation](https://sqlite-utils.datasette.io/en/stable/) -- Upsert and query patterns
- [yt-dlp extraction pipeline](https://deepwiki.com/yt-dlp/yt-dlp/2.2-information-extraction-pipeline) -- Metadata extraction
- [SQLite JSON Functions](https://sqlite.org/json1.html) -- JSON column support
