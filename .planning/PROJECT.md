# Channel Assistant (Agent 1.1)

## What This Is

A Claude Code skill that acts as a strategic channel assistant for a dark mysteries YouTube documentary channel. It scrapes competitor data, analyzes content strategy (outliers, topic clusters, title patterns), scans YouTube trends for content gaps, and generates scored topic briefs. After topic selection, it creates a project directory with YouTube-optimized metadata (title variants + description).

## Core Value

Surface obscure, high-impact documentary topics that the channel hasn't covered and competitors have missed — backed by data, not guesswork.

## Requirements

### Validated

- Competitor discovery and tracking (JSON registry, yt-dlp scraping, SQLite storage) — v1.0
- Cached competitor data with on-demand refresh (rate limiting, jittered delays, failure fallback) — v1.0
- Competitor analysis (per-channel stats, outlier detection, topic clustering, title patterns) — v1.0
- Topic generation (5 scored briefs per run, anchored rubrics, past-topic deduplication) — v1.0
- Trend awareness (YouTube autocomplete, search results, cross-channel convergence) — v1.0
- Topic selection flow (project directory creation, sequential numbering, metadata.md) — v1.0
- Metadata generation (3-5 title variants, 1 description per topic) — v1.0

### Active

(None yet — define with `/gsd:new-milestone`)

### Out of Scope

- Upload scheduling or publishing automation — not part of this agent's scope
- Video production pipeline (Agents 1.2–2.4) — separate agents handle research, writing, visuals
- Real-time monitoring or notifications — this runs on demand, not as a background service
- Social media analysis (Reddit, Twitter/X) — YouTube-only data sources for v1
- Third-party analytics integration (SocialBlade, VidIQ) — adds complexity without clear ROI

## Context

This is **Agent 1.1** in the channel's documentary video generation pipeline (see `Architecture.md`). The pipeline is orchestrated entirely through Claude Code — no application entry point exists. All scripting is Python.

**Current state (v1.0 shipped):**
- 7,018 LOC Python across 7 modules + CLI
- 175 passing tests (100% coverage of deterministic code)
- SQLite database with 37 migrated competitor videos from 3 channels
- Full pipeline: `scrape → analyze → trends → topics → project init`

**Channel profile:** Dark history, true crime, unsolved mysteries. 20-50 min documentaries. Neutral, cinematic tone. Target audience: 22-38, intellectually curious. See `context/channel/channel.md`.

## Constraints

- **Language:** Python only — no Node.js or JavaScript for scripting
- **No LLM API wrappers:** All reasoning handled natively by Claude Code runtime
- **Scraping tools:** yt-dlp for video/channel metadata, crawl4ai for web pages and search results
- **Storage:** SQLite via stdlib sqlite3 (zero external dependencies)
- **Output location:** `projects/N. [Video Title]/` at repo root

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| SQLite over JSON for competitor DB | Queryable, handles growth, stdlib support | Good |
| yt-dlp subprocess over Python API | More stable, debuggable, consistent JSON output | Good |
| stdlib-only dependencies (statistics, difflib, sqlite3) | Zero install friction, no version conflicts | Good |
| Context-loader CLI pattern | CLI prints structured data, Claude does all reasoning | Good |
| Anchored scoring rubrics in prompt files | Consistent scoring across runs without code gates | Good |
| 5 topics per run | Focused shortlist, no decision fatigue | Good |
| Heuristic/deterministic separation | Matches Architecture.md Rule 2 perfectly | Good |
| TDD red-green for all deterministic code | 175 tests caught regressions early | Good |
| Section extraction duplicated in topics.py and cli.py | Avoids cross-module coupling, both identical | Acceptable |
| check_duplicates via instruction text | Keeps dedup as heuristic evaluation, not hard gate | Acceptable |

---
*Last updated: 2026-03-12 after v1.0 milestone*
