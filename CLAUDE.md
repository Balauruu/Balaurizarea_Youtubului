# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

Agentic documentary video generation pipeline for a YouTube channel focused on dark mysteries content. Claude Code is the orchestrator — it invokes skills to complete each pipeline phase. There is no application entry point; the pipeline is driven entirely through skill invocations.

## Folder Map

```
Channel-automation V4/
├── CLAUDE.md                     # You are here (always loaded)
├── CONTEXT.md                    # Task router — start here for any task
├── channel/                      # Channel identity: voice, style, visual rules
│   ├── channel.md                # Channel DNA: voice, tone, pillars, audience
│   ├── past_topics.md            # Previously covered topics (dedup safety)
│   ├── voice/
│   │   └── WRITTING_STYLE_PROFILE.md   # Channel voice behavioral ruleset
│   ├── scripts/                  # Full reference scripts (style extraction source)
│   └── visuals/
│       └── VISUAL_STYLE_GUIDE.md # Visual building blocks + register definitions
├── strategy/                     # Competitive intel and topic generation
│   ├── CONTEXT.md
│   ├── competitors/
│   │   ├── competitors.json      # Registered channel registry
│   │   └── analysis.md           # Stats, outliers, trends, topic clusters
│   └── topic_briefs.md           # Generated topic briefs
├── projects/                     # Per-video working directories
│   └── N. [Video Title]/
│       ├── metadata.md           # Topic brief, title variants, description
│       ├── research/             # researcher skill output
│       ├── script/               # writer skill output
│       │   └── Script.md
│       ├── visuals/              # visual planning output
│       │   ├── shotlist.json
│       │   └── media_leads.json
│       └── assets/               # Acquired media assets
│           └── screenshots/
├── .claude/
│   ├── Architecture.md           # Pipeline architecture, infrastructure
│   ├── SKILL_CRAFTING_GUIDE.md   # Handbook for creating/improving skills
│   ├── skills/                   # Agent skills
│   └── scratch/                  # Transient data (gitignored)
└── data/
    ├── channel_assistant.db      # SQLite: competitors & videos
    └── asset_catalog.db          # SQLite: video clip catalog
```

## Skill Routing

| Task | Skill | Entry Point |
|------|-------|-------------|
| Add/scrape/analyze competitors | channel-assistant | `add`, `scrape`, `analyze` |
| Generate topic ideas | channel-assistant | `topics` + Claude heuristic |
| Initialize video project | channel-assistant | `init_project()` |
| Research a topic | researcher | `survey` → evaluate → `deepen` → `write` |
| Extract channel voice style | style-extraction | SKILL.md (heuristic, no CLI) |
| Write script | writer | `load` + Claude heuristic |
| Create shot list | shot-planner | SKILL.md (heuristic, no CLI) |
| Discover media assets | media-scout | Manual workflow (crawl4ai + yt-dlp) |
| Find b-roll candidates | shot-planner | B-roll discovery step in shotlist generation |
| Analyze/catalog video assets | asset-analyzer | standalone or project mode |

**For detailed task routing with load/skip tables, read `CONTEXT.md`.**

## Pipeline Flow

```
strategy (channel-assistant)
    ↓ topic brief + metadata.md
research (researcher)
    ↓ Research.md + entity_index.json
writing (writer)
    ↓ script/Script.md
visual planning (shot-planner + media-scout)
    ↓ visuals/shotlist.json + visuals/media_leads.json + downloads
asset acquisition (asset-analyzer)
    ↓ video_analysis.json + extracted clips + catalog entries
```

## Conventions

### Docs Over Outputs
Reference docs (`channel/`) are authoritative sources of truth. Previous project outputs are artifacts, NOT templates. Agents never read other projects' outputs to learn patterns.

### Canonical Sources
Every piece of information has ONE home. Other files point to it — they don't duplicate it.

### Scratch Pad
`.claude/scratch/` is **disposable by definition** — any file there can be deleted at any time without consequence. This is enforced by routing files to the right home based on purpose, not size.

**Decision tree — where does this file go?**

| Purpose | Location | Example |
|---------|----------|---------|
| Intermediate data consumed once this session | `.claude/scratch/` | `crawl_results.json`, `image_urls.json` |
| Per-run input for bundled scripts | `.claude/scratch/` | `wiki_pages.json` (fed to `scripts/wiki_screenshots.py`) |
| Cache that must survive across sessions | `data/` | `ia_cache.json`, any API response cache |
| Reusable tool script | Skill's `scripts/` directory | `crawl_images.py`, `wiki_screenshots.py` |
| Project artifact (research, plans, media leads) | `projects/N. [Title]/` | `Research.md`, `media_leads.json` |
| Reference doc for a skill | Skill's `references/` directory | Domain knowledge, API docs |

**Rules:**
- Never put caches, persistent state, or reusable scripts in scratch
- When tool output exceeds ~1500 tokens, write to scratch only if it's truly disposable — otherwise route to the correct home above
- Return only a 1-2 line summary in conversation context

### Plans and Context Hygiene
Plans are session-scoped coordination tools. They should use **tasks** (TaskCreate/TaskUpdate), not files. A 15KB plan file that gets re-read 3 times burns 45KB of context for information that fits in 10 task entries.

- **Simple plans** (< 10 steps): Use tasks directly, no file needed
- **Complex plans** (needs human review before execution): Write a short bullet-point plan to the **project directory** (it's a project artifact), present it for approval, then convert approved steps to tasks. Do not re-read the plan file — tasks track position from that point forward
- **Never write plans to scratch** — if a plan is worth writing, it's a project artifact; if it's not, use tasks

## Architecture Rules

1. **ZERO LLM API WRAPPERS:** Never write code that initializes LLM SDKs (`@anthropic-ai/sdk`, `openai`, etc.). All reasoning and orchestration is handled natively by Claude Code. LLM API wrappers are allowed only if part of an essential external tool.

2. **SEPARATION OF CONCERNS — PROMPT VS. CODE:**
   Before executing any task, classify it as:
   - **[HEURISTIC]:** Requires logic, narrative design, or evaluation → solved via Claude Code skills and prompt files. No code written.
   - **[DETERMINISTIC]:** Requires structured data manipulation, scraping, or media rendering → solved via code.

3. **CONTEXT.MD MAINTENANCE:** When any structural change is made to a directory (files added, removed, renamed, or moved), update that directory's `CONTEXT.md` to reflect the new state. This applies to all directories that have a `CONTEXT.md` file.

4. **FOLDER MAP MAINTENANCE:** When a structural change affects a directory or file that is represented in the `CLAUDE.md` Folder Map, update the Folder Map to match. New projects and skills are NOT relevant (they are dynamic content). Relevant changes include adding, removing, or renaming persistent reference files, data stores, or top-level directories.

5. **PIPELINE PRIORITY:** End-to-end flow over per-skill perfection. Each skill should produce output that the next skill can consume (unless end of pipeline). Optimize for completing the full pipeline, not for polishing individual skills. Human review checkpoints gate quality; the pipeline doesn't need to be perfect, it needs to be runnable.

## Coding Standards

- **Language:** All scripts must be written in Python. Do not use Node.js or JavaScript unless it is absolutely necessary.

## Other Notes

- I am editing in DaVinci Resolve
