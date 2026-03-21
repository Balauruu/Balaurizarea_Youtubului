# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

Agentic documentary video generation pipeline for a YouTube channel focused on dark mysteries content. Claude Code is the orchestrator — it invokes skills to complete each pipeline phase. There is no application entry point; the pipeline is driven entirely through skill invocations.

## Folder Map

```
Channel-automation V4/
├── CLAUDE.md                     # You are here (always loaded)
├── CONTEXT.md                    # Task router — start here for any task
├── strategy/                     # Channel intel, competitors, topic ideation
│   ├── CONTEXT.md
│   ├── channel/
│   │   ├── channel.md            # Channel DNA: voice, tone, pillars, audience
│   │   └── past_topics.md        # Previously covered topics (dedup safety)
│   ├── competitors/
│   │   ├── competitors.json      # Registered channel registry
│   │   └── analysis.md           # Stats, outliers, trends, topic clusters
│   └── topics/
│       └── topic_briefs.md       # Generated topic briefs
├── reference/                    # Stable reference material (loaded on demand)
│   ├── CONTEXT.md
│   ├── Architecture.md           # Pipeline architecture, infrastructure, Asset Library
│   ├── voice/
│   │   └── WRITTING_STYLE_PROFILE.md   # Channel voice behavioral ruleset
│   ├── scripts/                  # Full reference scripts (style extraction source)
│   └── visuals/
│       └── VISUAL_STYLE_GUIDE.md # Visual building blocks + register definitions
├── projects/                     # Per-video working directories
│   └── N. [Video Title]/
│       ├── metadata.md           # Topic brief, title variants, description
│       ├── research/             # researcher skill output
│       ├── script/               # writer skill output (new projects)
│       ├── visuals/              # visual-orchestrator + broll-curator output (new projects)
│       └── assets/               # Acquired media assets
├── .claude/
│   ├── skills/                   # Agent skills
│   ├── tests/                    # pytest test suite
│   └── scratch/                  # Transient data (gitignored)
└── data/
    └── channel_assistant.db      # SQLite: competitors & videos
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
| Create shot list | visual-orchestrator | SKILL.md (heuristic, no CLI) |
| Discover media assets | media-scout | Manual workflow (crawl4ai + yt-dlp) |
| Find b-roll candidates | broll-curator | Manual workflow (IA + LanceDB) |

**For detailed task routing with load/skip tables, read `CONTEXT.md`.**

## Pipeline Flow

```
strategy (channel-assistant)
    ↓ topic brief + metadata.md
research (researcher)
    ↓ Research.md + entity_index.json
writing (writer)
    ↓ Script.md
visual planning (visual-orchestrator + media-scout)
    ↓ shotlist.json + media_leads.json
asset discovery (broll-curator)
    ↓ broll_candidates.json
```

## Conventions

### Docs Over Outputs
Reference docs (`prompts/`, `reference/`) are authoritative sources of truth. Previous project outputs are artifacts, NOT templates. Agents never read other projects' outputs to learn patterns.

### Canonical Sources
Every piece of information has ONE home. Other files point to it — they don't duplicate it.

### Scratch Pad
- When tool output exceeds ~1500 tokens, write it to `.claude/scratch/` with a descriptive filename
- Return only a 1-2 line summary in conversation context
- Files in `.claude/scratch/` are transient — not committed, can be deleted between sessions

## Architecture Rules

1. **ZERO LLM API WRAPPERS:** Never write code that initializes LLM SDKs (`@anthropic-ai/sdk`, `openai`, etc.). All reasoning and orchestration is handled natively by Claude Code. LLM API wrappers are allowed only if part of an essential external tool.

2. **SEPARATION OF CONCERNS — PROMPT VS. CODE:**
   Before executing any task, classify it as:
   - **[HEURISTIC]:** Requires logic, narrative design, or evaluation → solved via Claude Code skills and prompt files. No code written.
   - **[DETERMINISTIC]:** Requires structured data manipulation, scraping, or media rendering → solved via code.

3. **CONTEXT.MD MAINTENANCE:** When any structural change is made to a directory (files added, removed, renamed, or moved), update that directory's `CONTEXT.md` to reflect the new state. This applies to all directories that have a `CONTEXT.md` file.

4. **FOLDER MAP MAINTENANCE:** When a structural change affects a directory or file that is represented in the `CLAUDE.md` Folder Map, update the Folder Map to match. New projects and skills are NOT relevant (they are dynamic content). Relevant changes include adding, removing, or renaming persistent reference files, data stores, or top-level directories.

## Coding Standards

- **Language:** All scripts must be written in Python. Do not use Node.js or JavaScript unless it is absolutely necessary.

## Other Notes

- I am editing in DaVinci Resolve
