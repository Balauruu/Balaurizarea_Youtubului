# Project

## What This Is

An agentic documentary video generation pipeline for a YouTube channel focused on dark mysteries content. Claude Code itself is the orchestrator — it spawns sub-agents with skills to complete each phase. The pipeline covers the full arc from competitor analysis through narrated script to organized visual assets ready for DaVinci Resolve editing.

## Core Value

Surface obscure, high-impact documentary topics backed by competitor data and deep web research, then automate the entire visual asset pipeline — from script to organized, numbered media folder ready for timeline assembly.

## Current State

**v1.2 shipped (M001 complete):**
- Agent 1.1 (Channel Assistant): 7,018 LOC Python, 175 tests, full pipeline `scrape → analyze → trends → topics → project init`
- Agent 1.2 (The Researcher): 1,737 LOC Python + prompts, two-pass research `survey → deepen → write`, validated on real topic
- Agent 1.3 (The Writer): stdlib-only CLI + generation prompt, style extraction skill, `load → generate → Script.md`
- STYLE_PROFILE.md: 371-line channel voice behavioral ruleset
- Visual Style Extractor: 6-stage pipeline producing VISUAL_STYLE_GUIDE.md from reference videos
- SQLite database with 37 migrated competitor videos from 3 channels
- End-to-end validated: Duplessis Orphans topic from competitor analysis → research dossier → narrated script
- Full test suite passing across all agents (252/253, 1 external dep issue)

**M002 in progress (S01-S03 complete):**
- Visual Orchestrator skill: context-loader CLI + shotlist.json schema validator, 20 tests
- Media Acquisition skill: 7 source adapters, manifest.json schema contract, acquire/load/status CLI, 102 tests
- Graphics Generator skill: 7 Pillow renderers + ComfyUI REST client with 4 workflow templates, load/generate/status CLI, 69 tests
- shotlist.json → manifest.json pipeline contract established for downstream S04-S05 skills

**Channel profile:** Dark history, true crime, unsolved mysteries. 20-50 min documentaries. Neutral, cinematic tone. Target audience: 22-38, intellectually curious.

## Architecture / Key Patterns

- **Skills:** Each agent is a Claude Code skill with CONTEXT.md (stage contract), SKILL.md (usage), scripts/, prompts/
- **Separation of concerns:** [HEURISTIC] tasks (reasoning, narrative) via Claude + prompts. [DETERMINISTIC] tasks (scraping, file ops) via Python code.
- **Context-loader CLI pattern:** Python prints structured data to stdout, Claude does all reasoning
- **No LLM API wrappers:** All reasoning handled natively by Claude Code runtime
- **Language:** Python for all scripting. Remotion (Node.js) is the sole exception, for animated maps/diagrams.
- **Scraping:** crawl4ai for web pages, yt-dlp for video/channel metadata
- **Storage:** SQLite via stdlib sqlite3
- **Output:** `projects/N. [Video Title]/` at repo root
- **Editor:** DaVinci Resolve — pipeline delivers raw assets, editor handles styling/effects

## Capability Contract

See `.gsd/REQUIREMENTS.md` for the explicit capability contract, requirement status, and coverage mapping.

## Milestone Sequence

- [x] M001: Migration — Full narrative pipeline from competitor analysis through narrated script (3 agents, 253 tests)
- [ ] M002: Asset Pipeline — Script-to-organized-asset-folder pipeline (5 new skills: visual orchestrator, media acquisition, graphics generator, animation, asset manager)
