# Channel Assistant (Agent 1.1)

## What This Is

A Claude Code skill that acts as a strategic channel assistant for a dark mysteries YouTube documentary channel. It discovers competitors, analyzes their content strategy, identifies trending topics in the niche, and generates scored topic briefs for upcoming videos. After the user selects a topic, it creates a project directory with metadata (multiple title variants + description) ready for the next pipeline stages.

## Core Value

Surface obscure, high-impact documentary topics that the channel hasn't covered and competitors have missed — backed by data, not guesswork.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Competitor discovery and tracking (find channels in the dark mysteries niche, curate a watchlist)
- [ ] Competitor data scraping via yt-dlp + crawl4ai (video titles, descriptions, view counts, upload dates, tags)
- [ ] Cached competitor data with on-demand refresh capability
- [ ] Competitor analysis (topic selection patterns, title strategies, content gaps, performance signals)
- [ ] Topic generation — 5 scored briefs per run using the Topic Brief Schema (title, hook, timeline, complexity/obscurity/shock scores, estimated runtime)
- [ ] Duplicate rejection against `context/channel/past_topics.md`
- [ ] Trend awareness — surface what's currently trending in the niche (YouTube search, recent uploads)
- [ ] Topic selection flow — user picks from chat, system creates `projects/N. [Video Title]/` with metadata file
- [ ] Metadata generation — 3-5 YouTube title variants + 1 description per selected topic
- [ ] Competitor data storage — structured database (JSON or SQLite, to be researched) optimized for querying, visualization, and analysis

### Out of Scope

- Upload scheduling or publishing automation — not part of this agent's scope
- Video production pipeline (Agents 1.2–2.4) — separate agents handle research, writing, visuals
- Real-time monitoring or notifications — this runs on demand, not as a background service
- Social media analysis (Reddit, Twitter/X) — YouTube-only data sources for v1
- Third-party analytics integration (SocialBlade, VidIQ) — adds complexity without clear ROI for v1

## Context

This is **Agent 1.1** in the channel's documentary video generation pipeline (see `Architecture.md`). It's the first agent to be built. The pipeline is orchestrated entirely through Claude Code — no application entry point exists. All scripting is Python.

**Channel profile:** Dark history, true crime, unsolved mysteries. 20-50 min documentaries. Neutral, cinematic tone. Target audience: 22-38, intellectually curious. See `context/channel/channel.md` for full DNA.

**Existing infrastructure:**
- `context/channel/channel.md` — Channel DNA (voice, tone, style, audience)
- `context/channel/past_topics.md` — Previously covered topics (currently empty)
- `context/competitors/` — Competitor data directory (to be structured)
- `context/visual-references/` — Visual reference material (separate concern)
- Skills available: `yt-dlp`, `crawl4ai`, `remotion`

**Data flow:** This agent's output (selected topic + brief) feeds into Agent 1.2 (Deep Research) in future pipeline phases, but for now it just saves to disk.

## Constraints

- **Language:** Python only — no Node.js or JavaScript for scripting
- **No LLM API wrappers:** All reasoning handled natively by Claude Code runtime
- **Scraping tools:** yt-dlp for video/channel metadata, crawl4ai for web pages and search results
- **Storage:** Must support easy querying and visualization when prompted in Claude Code
- **Output location:** `projects/N. [Video Title]/` at repo root

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| yt-dlp + crawl4ai for scraping | Already available as skills, no API quota limits, proven in this repo | — Pending |
| Cached competitor data with refresh | Balance between freshness and speed — don't re-scrape every run | — Pending |
| 5 topics per run | Focused shortlist, easier to choose without decision fatigue | — Pending |
| JSON vs SQLite for competitor DB | Needs research — user wants queryability + visualization + analysis | — Pending |
| Project dirs at `projects/N. Title/` | Clean separation from context and pipeline code | — Pending |
| Multiple title variants (3-5) + single description | Titles need A/B thinking; description is more stable | — Pending |

---
*Last updated: 2026-03-11 after initialization*
