---
name: channel-assistant
description: Competitor intelligence, topic ideation, and project initialization for the dark mysteries YouTube channel. Use this skill when the user wants to add/scrape/analyze competitor channels, generate scored topic briefs, scan YouTube trends and content gaps, or initialize a new video project directory. Also use when the user mentions competitors, topic ideas, trend scanning, content gaps, starting a new video project, or asks "what should I make a video about". Even if the user just says "give me topics" or "analyze competitors" — this skill handles it.
---

# channel-assistant

## How It Works

This skill provides Python CLI tools for [DETERMINISTIC] data work (scraping, database queries, stats). Claude handles all [HEURISTIC] reasoning (topic generation, scoring, gap analysis) natively — no LLM API calls in the code.

## Workflows

### Full Refresh (new topic cycle)

Run this when starting fresh or when competitor data is stale. Each step builds on the previous.

```
1. scrape          → refresh all competitor video data from YouTube
2. analyze         → compute stats + outliers + trend scan + write analysis.md
3. [HEURISTIC]     → Claude completes Topic Clusters + Title Patterns in analysis.md
4. topics          → load context for topic generation
5. [HEURISTIC]     → Claude generates 5 scored briefs, writes topic_briefs.md
6. [DISPLAY]       → Claude outputs formatted markdown cards directly in chat
7. User selects    → picks a topic number from chat
8. [HEURISTIC]     → Claude generates title variants + description
9. [DETERMINISTIC] → init_project() creates project directory + metadata.md
```

**Checkpoints:**
| After Step | Agent Presents | Human Decides |
|------------|---------------|---------------|
| Step 6 | 5 scored topic cards with briefs | Which topic to pursue (or regenerate) |
| Step 8 | 3-5 title variants + YouTube description | Final title for project init |

### Quick Topic Generation (data already fresh)

Skip scraping if competitor data is recent (< 7 days old — analyze warns if stale).

```
1. analyze --no-trends  → stats + outliers only (fast, no HTTP calls)
2. topics               → load context → Claude generates briefs
```

### Add New Competitor

```
1. add <url>    → register channel in competitors.json
2. scrape       → fetch all video data for new + existing channels
```

## Commands

All commands require PYTHONPATH set to the scripts directory:

```bash
PYTHONPATH=.claude/skills/channel-assistant/scripts python -m channel_assistant.cli <command> [args]
```

### `add <url>`

Register a new competitor channel. Resolves channel name via yt-dlp, adds to `competitors.json`.

```bash
python -m channel_assistant.cli add "https://www.youtube.com/@ChannelHandle"
```

### `scrape [name]`

Scrape video metadata via yt-dlp. Omit name to scrape all channels. Uses 3-8s jittered delays, retries up to 2 times, falls back to cached data on failure.

```bash
python -m channel_assistant.cli scrape            # all channels
python -m channel_assistant.cli scrape "barely"   # single channel (partial match)
```

### `analyze [--no-trends]`

Full competitor analysis pipeline in one command:
1. Prints channel status table (video counts, scrape dates)
2. Computes per-channel stats and outlier detection (2x median threshold)
3. Writes `strategy/competitors/analysis.md` with stats + outliers + placeholder sections
4. Writes `.claude/scratch/video_data_for_analysis.md` for Claude heuristic reasoning
5. Runs trend scanning: autocomplete suggestions, YouTube search results, 30-day competitor convergence

Use `--no-trends` to skip step 5 (useful when you only need stats, or when offline).

```bash
python -m channel_assistant.cli analyze             # full analysis + trends
python -m channel_assistant.cli analyze --no-trends  # stats only, no HTTP calls
```

After analyze completes, Claude should:
- Read `.claude/scratch/video_data_for_analysis.md`
- Complete the Topic Clusters and Title Patterns sections in `analysis.md`
- If trends were scanned, use the trends analysis prompt to score content gaps and frame convergence alerts
- Write trend results via `update_analysis_with_trends()` from `channel_assistant.trend_scanner`

### `topics`

Loads all context needed for topic generation and prints it to stdout. Claude then performs the [HEURISTIC] generation using the topic generation prompt.

```bash
python -m channel_assistant.cli topics
```

After running, Claude should:
1. Read the generation prompt: `.claude/skills/channel-assistant/prompts/topic_generation.md`
2. Generate 5 scored topic briefs using the loaded context
3. Run dedup: `check_duplicates(title, past_topics, threshold=0.85)` for each brief
4. Write briefs via `write_topic_briefs()` from `channel_assistant.topics`
5. Call `format_chat_cards(briefs)` and **output the returned markdown directly in the chat response** — do NOT print it via bash or show raw Python dicts
6. When user selects topic N: call `load_project_inputs(root, N)`, read project_init prompt, generate metadata, call `init_project()`

**IMPORTANT: All user-facing output must be formatted markdown displayed in chat, never raw data structures or bash stdout.**

## Display Rules

All user-facing output from this skill must be **formatted markdown displayed directly in chat**. Never show raw Python data structures, JSON dumps, or unformatted bash stdout to the user.

- **Topic cards:** Use `format_chat_cards(briefs)` and paste the markdown into your response
- **Analyze results:** Summarize key findings in a brief markdown table (channels, video counts, outlier highlights)
- **Scrape results:** Report as a clean summary line (e.g. "Scraped 3 channels, 245 videos total")
- **Errors:** Report as clear sentences, not tracebacks

When a command prints structured data to stdout (for Claude to reason over), do NOT show that raw output to the user. Instead, summarize it in readable markdown.

## Prompts

| Prompt | Used By | Purpose |
|--------|---------|---------|
| `prompts/topic_generation.md` | `topics` command | Scoring rubric, generation instructions, output format |
| `prompts/trends_analysis.md` | `analyze` command | Content gap scoring, convergence framing |
| `prompts/project_init.md` | After topic selection | Title variant generation, description writing |

## File Locations

| File | Purpose |
|------|---------|
| `strategy/competitors/competitors.json` | Competitor channel registry |
| `strategy/competitors/analysis.md` | Full analysis report (stats + outliers + trends) |
| `strategy/topics/topic_briefs.md` | Generated topic briefs |
| `data/channel_assistant.db` | SQLite database (channels + videos tables) |
| `.claude/scratch/video_data_for_analysis.md` | Serialized video data for heuristic analysis |

## Key Modules

| Module | Purpose |
|--------|---------|
| `cli.py` | Entry point — 4 subcommands |
| `models.py` | `Channel`, `Video` dataclasses |
| `registry.py` | Read/write/validate competitors.json |
| `database.py` | SQLite schema, upserts, queries |
| `scraper.py` | yt-dlp channel scraping with retry + fallback |
| `analyzer.py` | Channel stats, outlier detection, formatting |
| `topics.py` | Topic loading, dedup checking, brief writing |
| `trend_scanner.py` | Autocomplete, search scraping, keyword derivation |
| `project_init.py` | Project directory creation and metadata |

## Schema Notes

- **Channel fields:** name, youtube_id, handle, url, subscribers, total_views (nullable), description (nullable), scraped_at
- **Video fields:** video_id, channel_id, title, url, views, upload_date, description, duration, tags (JSON array), likes, scraped_at
- Tags stored as JSON strings in SQLite, deserialized to Python lists on read
- Upserts are idempotent: re-scraping updates existing records without duplicates

## Dependencies

- Python 3.14+ (stdlib only: sqlite3, json, argparse, pathlib, subprocess, random, datetime)
- yt-dlp (installed in environment)
- crawl4ai (optional — trend search results require it, autocomplete works without it)
