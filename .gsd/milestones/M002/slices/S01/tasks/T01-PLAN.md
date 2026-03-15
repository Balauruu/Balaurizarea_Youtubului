---
estimated_steps: 7
estimated_files: 7
---

# T01: Build visual orchestrator skill — CLI, generation prompt, schema validator

**Slice:** S01 — Visual Orchestrator Skill
**Milestone:** M002

## Description

Create the full visual orchestrator skill following the writer skill's context-loader pattern (D002). Three deliverables: (1) CLI with `load` and `validate` subcommands, (2) generation prompt encoding shotlist.json schema + decision tree application rules, (3) schema validator for post-generation contract enforcement. Plus CONTEXT.md and SKILL.md documentation.

## Steps

1. Create `scripts/visual_orchestrator/` package structure (`__init__.py`, `__main__.py`) mirroring writer skill layout
2. Write `cli.py` with `load` subcommand — resolve project dir (reuse writer pattern), read Script.md + VISUAL_STYLE_GUIDE.md + channel.md, print labeled sections + output path (shotlist.json) + generation prompt path. Add `--guide` optional arg for specifying which VISUAL_STYLE_GUIDE to use (default: first in `context/visual-references/`). Add `validate` subcommand that reads shotlist.json from project dir and runs schema validation.
3. Write `schema.py` with `validate_shotlist(data: dict) -> list[str]` — returns list of error strings. Checks: (a) top-level required keys (project, guide_source, generated, shots), (b) each shot has required fields (id, chapter, chapter_title, narrative_context, visual_need, building_block, shotlist_type), (c) id format S001-S999 sequential, (d) shotlist_type in valid enum (archival_video, archival_photo, animation, map, text_overlay, document_scan), (e) text_content populated iff shotlist_type is text_overlay, (f) sequencing constraints (no back-to-back glitch types, max 3 consecutive text_overlay, max 3 consecutive animation with same building_block "Silhouette Figure")
4. Write `prompts/generation.md` — full generation prompt encoding: shotlist.json schema with field descriptions, decision tree application rules (process script paragraph-by-paragraph, match to IF-THEN rules from VISUAL_STYLE_GUIDE), segment granularity guidance (group by narrative beat, target 60-100 shots for a 20-min script), sequencing constraints as post-generation self-check, text overlay handling (R002: include text_content with actual quote/date/keyword text, these entries guide editorial placement but generate no assets)
5. Write `CONTEXT.md` stage contract — Inputs (Script.md, VISUAL_STYLE_GUIDE.md, channel.md), Process (CLI load → Claude reads prompt → Claude generates shotlist.json → validate), Checkpoints, Outputs (shotlist.json), Deferred
6. Write `SKILL.md` usage guide — how to invoke, example commands, what outputs look like
7. Smoke test: run `PYTHONPATH=.claude/skills/visual-orchestrator/scripts python -m visual_orchestrator load "Duplessis Orphans"` and verify labeled output

## Must-Haves

- [ ] CLI `load` prints Script.md, VISUAL_STYLE_GUIDE.md, channel.md as labeled sections with dividers
- [ ] CLI `load` prints shotlist.json output path and generation.md prompt path
- [ ] CLI `load` accepts `--guide` for selecting a specific VISUAL_STYLE_GUIDE
- [ ] CLI `validate` reads shotlist.json and returns pass/fail with error list
- [ ] Schema validator checks all required fields, valid enums, ID format, text_content rules, sequencing constraints
- [ ] Generation prompt encodes complete shotlist.json schema with all fields from research
- [ ] Generation prompt encodes decision tree application rules and segment granularity guidance
- [ ] Generation prompt handles text overlay entries per R002 (text_content populated, no asset generation)
- [ ] CONTEXT.md follows writer CONTEXT.md format exactly

## Verification

- `PYTHONPATH=.claude/skills/visual-orchestrator/scripts python -m visual_orchestrator load "Duplessis Orphans"` exits 0 and prints all expected sections
- `schema.py` can be imported and `validate_shotlist()` returns empty list for a valid fixture and non-empty list for invalid fixtures
- All files exist in expected locations

## Observability Impact

- **New signal:** `validate` subcommand provides structured error output — each error is a single line with shot ID context, grep-friendly, exits 1 on any error.
- **Inspection surface:** A future agent can run `python -m visual_orchestrator validate "<topic>"` to check shotlist.json validity without reading the file.
- **Failure visibility:** Missing input files reported on stderr with full paths. Schema violations reported as a numbered error list.

## Inputs

- `.claude/skills/writer/scripts/writer/cli.py` — CLI pattern to replicate
- `.claude/skills/writer/CONTEXT.md` — CONTEXT.md format reference
- `context/visual-references/Mexico's Most Disturbing Cult/VISUAL_STYLE_GUIDE.md` — decision tree, building blocks, sequencing rules
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/Script.md` — test input for CLI smoke test
- S01-RESEARCH.md shotlist.json schema — field definitions and schema decisions

## Expected Output

- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/cli.py` — CLI with load + validate subcommands
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/schema.py` — shotlist.json schema validator
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/__init__.py` — package init
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/__main__.py` — module entry point
- `.claude/skills/visual-orchestrator/prompts/generation.md` — generation prompt
- `.claude/skills/visual-orchestrator/CONTEXT.md` — stage contract
- `.claude/skills/visual-orchestrator/SKILL.md` — usage guide
