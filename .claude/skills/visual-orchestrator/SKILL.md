---
name: visual-orchestrator
description: Generate structured shot lists from finished documentary scripts. Use this skill when the user wants to create a shot list, generate a shotlist, parse a script into shots, or says things like "create shot list", "generate shotlist", "parse script into shots", "visual plan for [topic]", "shotlist for [topic]". This is a [HEURISTIC] skill — zero Python, Claude does all reasoning. Requires a completed Script.md in the project directory.
---

# Visual Orchestrator

Script -> structured shot list for the asset pipeline.

## Workflow

1. **Resolve project directory** — Topic is a case-insensitive substring match against `projects/` directory names. Multiple matches: list all, ask user which one. No match: error with guidance to check spelling or use `cmd_init_project`. Found: read `projects/N. [Title]/Script.md`. If Script.md is missing: stop and tell user to run the writer skill first (trigger phrase: "write the script for [topic]").

2. **Read the generation prompt** — `.claude/skills/visual-orchestrator/prompts/generation.md`

3. **Generate the shot list** — Follow the prompt instructions. Write output to `projects/N. [Title]/shotlist.json`, overwriting any existing file without prompt.

## Prerequisites

- `projects/N. [Title]/Script.md` — from the writer skill
- `.claude/skills/visual-orchestrator/prompts/generation.md` — shot generation rules

## Output

`projects/N. [Title]/shotlist.json` — JSON array of shot objects. Full overwrite on re-run; previous versions preserved in git history.
