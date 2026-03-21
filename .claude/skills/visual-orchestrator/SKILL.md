---
name: visual-orchestrator
description: Generate structured shot lists from finished documentary scripts. Use this skill when the user wants to create a shot list, generate a shotlist, parse a script into shots, or says things like "create shot list", "generate shotlist", "parse script into shots", "visual plan for [topic]", "shotlist for [topic]". This is a [HEURISTIC] skill — zero Python, Claude does all reasoning. Requires a completed Script.md in the project directory.
---

# Visual Orchestrator

Script -> structured shot list for the asset pipeline.

## Workflow

1. **Resolve project directory** — Topic is a case-insensitive substring match against `projects/` directory names. Multiple matches: list all, ask user which one. No match: error with guidance to check spelling or use `cmd_init_project`. Found: read `projects/N. [Title]/Script.md`. If Script.md is missing: stop and tell user to run the writer skill first (trigger phrase: "write the script for [topic]").

2. **Read inputs** — Load `.claude/skills/visual-orchestrator/prompts/generation.md` (schema and field rules), `reference/visuals/VISUAL_STYLE_GUIDE.md` (building block vocabulary, visual register definitions, equilibrium rules), and `projects/N. [Title]/research/media_leads.json` (if present — real-world media assets for source field decisions).

3. **Generate the shot list** — Follow the prompt instructions. Write output to `projects/N. [Title]/shotlist.json`, overwriting any existing file without prompt.

## Prerequisites

- `projects/N. [Title]/Script.md` — from the writer skill
- `.claude/skills/visual-orchestrator/prompts/generation.md` — shot generation rules and fused schema definition
- `reference/visuals/VISUAL_STYLE_GUIDE.md` — canonical visual vocabulary, building blocks, and equilibrium rules
- `projects/N. [Title]/research/media_leads.json` — optional; media assets discovered during research (informs source field choices)

## Output

`projects/N. [Title]/shotlist.json` — JSON wrapper object (`{ broll_themes: [...], shots: [...] }`) containing thematic b-roll groupings and the sequential shot array. Full overwrite on re-run; previous versions preserved in git history.

## Pipeline-Reset Invariant

`shotlist.json` is the source of truth for the asset pipeline. Any change to `Script.md` — including edits to chapter structure, shot-bearing prose, or scene intent — invalidates the existing `shotlist.json` and requires full regeneration. Downstream artifacts (e.g., `broll_candidates.json`) derived from the shot list are likewise stale and must be rebuilt.

There is no partial or chapter-level regeneration in v1.3. All shots are regenerated in a single pass because sequential shot IDs (`S001`, `S002`, ...) are assigned globally across the entire script. Re-invoking the skill always regenerates in full.

## Deferred

- **SHOT-08:** Two-pass generation — annotate narrative beats first, then assign shot types
- **SHOT-10:** Shot density calibration proportional to chapter word count
- Chapter-level regeneration without requiring a full re-run
