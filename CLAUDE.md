# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **agentic documentary video generation pipeline** for a YouTube channel focused on dark mysteries content. Claude Code itself is the orchestrator — it spawns sub-agents with skills to complete each phase. There is no application entry point; the pipeline is driven entirely through Claude Code skill invocations.

## Folder Map

```
Channel-automation V3/
├── CLAUDE.md                     # Project instructions (you are here)
├── Architecture.md               # Full pipeline spec (Phases 1-2)
├── context/                      # Persistent reference material (read-only)
│   ├── channel/
│   │   ├── channel.md            # Channel DNA: voice, tone, pillars, audience
│   │   ├── past_topics.md        # Previously covered topics (dedup safety)
│   │   └── writting_style_guide.md  # Narration style rules
│   ├── competitors/
│   │   ├── competitors.json      # Registered channel registry
│   │   └── analysis.md           # Stats, outliers, trends, topic clusters
│   ├── script-references/        # Full reference scripts (style extraction)
│   ├── topics/
│   │   └── topic_briefs.md       # Generated topic briefs
│   └── visual-references/        # Extracted visual style guides per video
│       └── [Video Name]/
│           └── VISUAL_STYLE_GUIDE.md
├── projects/                     # Per-video project directories
│   └── N. [Video Title]/
│       ├── metadata.md           # Topic brief, title variants, description
│       └── research/             # Research dossier outputs
│           ├── Research.md       # 9-section narrative dossier
│           ├── media_urls.md     # Visual media catalog
│           └── source_manifest.json
├── .claude/
│   ├── skills/                   # Agent skills (deterministic code + prompts)
│   │   ├── channel-assistant/    # Agent 1.1: Topics, competitors, project init
│   │   ├── researcher/           # Agent 1.2: Two-pass research pipeline
│   │   ├── visual-style-extractor/  # Frame analysis → visual patterns
│   │   └── crawl4ai-scraper/     # Web scraping utility
│   └── scratch/                  # Transient data (gitignored, ephemeral)
├── data/
│   └── channel_assistant.db      # SQLite: competitors & videos
├── tests/                        # pytest test suite
└── docs/                         # Plans, specs, documentation
```

## Context & Routing

### Task Routing

| Task | Skill | Entry Point |
|------|-------|-------------|
| Add/scrape/analyze competitors | channel-assistant | `cmd_add`, `cmd_scrape`, `cmd_analyze` |
| Generate topic ideas | channel-assistant | `cmd_topics` + Claude heuristic |
| Initialize video project | channel-assistant | `cmd_init_project` |
| Research a topic | researcher | `survey` → evaluate → `deepen` → `write` |
| Extract visual style | visual-style-extractor | 6-stage pipeline |
| Write script | *(not yet implemented)* | — |
| Create shot list | *(not yet implemented)* | — |

### What to Load

| Task | Load | Skip (and why) |
|------|------|----------------|
| Topic ideation | channel.md, past_topics.md, analysis.md, channel-assistant/CONTEXT.md | visual-references/, script-references/ — not relevant to topic selection |
| Research | channel.md, researcher/CONTEXT.md, projects/N/metadata.md | competitors/, visual-references/ — research is topic-focused |
| Style extraction | visual-style-extractor/CONTEXT.md, target video/URL | Everything else — self-contained pipeline |
| Script writing *(future)* | channel.md, writting_style_guide.md, script-references/, projects/N/research/Research.md | competitors/ — writer needs voice + research, not strategy |
| Visual planning *(future)* | visual-references/*/VISUAL_STYLE_GUIDE.md, projects/N/script.md | competitors/, channel.md — director needs visuals + script |

### Reference Files

- `Architecture.md` — Full pipeline specification (Phases 1-2)
- `context/channel/channel.md` — Channel DNA (voice, tone, pillars, audience)
- `context/channel/past_topics.md` — Past topics to avoid duplication

## Skills

### Pipeline Skills

| Skill | Agent | Purpose |
|-------|-------|---------|
| `channel-assistant` | 1.1 | Competitor intel, topic ideation, project init |
| `researcher` | 1.2 | Two-pass web research → narrative dossier |
| `visual-style-extractor` | — | Reference video → visual pattern toolkit |

### Utility Skills

| Skill | Purpose |
|-------|---------|
| `crawl4ai-scraper` | Web scraping (used by researcher) |
| `yt-dlp` | Video/audio downloading |
| `remotion` | Animation best practices (future) |

## Conventions

### Docs Over Outputs
Reference docs (`prompts/`, `context/`) are authoritative sources of truth. Previous project outputs (`projects/*/research/`) are artifacts, NOT templates. Agents never read other projects' outputs to learn patterns — they use prompt files and context files.

### Stage Contracts
Every skill has a `CONTEXT.md` that defines its Inputs, Process, Checkpoints, and Outputs. When invoking a skill as an agent, load `CONTEXT.md` for routing — load `SKILL.md` only when the user needs usage help.

### Canonical Sources
Every piece of information has ONE home. Other files point to it — they don't duplicate it. Channel voice rules live in `context/channel/channel.md`, not repeated in prompts or skill docs.

## Context Engineering

### Scratch Pad
- When tool output exceeds ~1500 tokens, write it to `.claude/scratch/` with a descriptive filename
- Return only a 1-2 line summary in conversation context
- Read back specific sections with grep or line ranges when needed
- Sub-agents can read/write to `.claude/scratch/` for collaboration
- Files in `.claude/scratch/` are transient — not committed, can be deleted between sessions

## Coding Standards

- **Language:** All scripts must be written in Python. Do not use Node.js or JavaScript for scripting tasks.

## Other Notes

- I am editing in Davinci Resolve
