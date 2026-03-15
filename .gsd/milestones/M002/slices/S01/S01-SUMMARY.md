---
id: S01
parent: M002
milestone: M002
provides:
  - Visual orchestrator skill with load/validate CLI subcommands
  - shotlist.json schema contract (stable for all downstream S02-S05 skills)
  - Generation prompt encoding VISUAL_STYLE_GUIDE decision tree, schema, and sequencing rules
  - Schema validator with sequencing constraint enforcement
  - CONTEXT.md stage contract and SKILL.md usage guide
requires: []
affects:
  - S02
  - S03
  - S04
  - S05
key_files:
  - .claude/skills/visual-orchestrator/scripts/visual_orchestrator/cli.py
  - .claude/skills/visual-orchestrator/scripts/visual_orchestrator/schema.py
  - .claude/skills/visual-orchestrator/prompts/generation.md
  - .claude/skills/visual-orchestrator/CONTEXT.md
  - .claude/skills/visual-orchestrator/SKILL.md
key_decisions:
  - "D012: Single shotlist_type + building_block per shot (not suggested_types array) — cleaner downstream filtering"
  - "D013: CLI accepts --guide flag, defaults to first guide in context/visual-references/ — works with any valid guide"
  - "Duplicated _get_project_root() and resolve_project_dir() from writer skill (small functions, no shared lib yet)"
  - "Added _ensure_utf8_stdout() for Windows charmap encoding of Unicode in context files"
patterns_established:
  - Visual orchestrator follows exact same context-loader pattern as writer (D002)
  - Schema validation returns list[str] errors with shot ID context for grep-friendly output
  - Schema tests use shared valid_shotlist fixture, each test modifies minimally to trigger one error class
observability_surfaces:
  - "python -m visual_orchestrator validate <topic> — structured error output, exits 1 on failure"
  - "CLI stderr messages include full file paths for missing inputs"
  - "pytest tests/test_visual_orchestrator/ -v — verifies all schema contract clauses"
drill_down_paths:
  - .gsd/milestones/M002/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M002/slices/S01/tasks/T02-SUMMARY.md
duration: 1h
verification_result: passed
completed_at: 2026-03-15
---

# S01: Visual Orchestrator Skill

**Working [HEURISTIC] skill that transforms Script.md + VISUAL_STYLE_GUIDE.md into a validated shotlist.json with building block assignments, text overlay entries, and sequencing constraint enforcement.**

## What Happened

Built the visual orchestrator skill under `.claude/skills/visual-orchestrator/` following the writer's context-loader pattern (D002). Two tasks:

**T01** created the full skill: CLI with `load` and `validate` subcommands, schema validator (`schema.py`), generation prompt (`prompts/generation.md`), and documentation (CONTEXT.md + SKILL.md). The `load` command aggregates Script.md + VISUAL_STYLE_GUIDE.md + channel.md into labeled sections with output path and generation prompt path. The `validate` command runs the schema validator against shotlist.json. The generation prompt encodes the complete shotlist.json schema, decision tree application rules, segment granularity guidance (60-100 shots for 20-min script), sequencing constraints, and text overlay handling per R002. The `--guide` flag allows selecting which VISUAL_STYLE_GUIDE to use.

**T02** wrote 20 pytest tests: 10 for CLI (resolve_project_dir resolution + cmd_load stdout content + missing-file error path) and 10 for schema validation (valid/invalid fixtures covering every contract clause including sequencing constraints). All tests follow the writer test patterns exactly.

## Verification

- `pytest tests/test_visual_orchestrator/ -v` — **20 passed in 0.07s**
- `python -m visual_orchestrator load "Duplessis Orphans"` — exits 0, prints all labeled sections ✓
- `python -m visual_orchestrator validate` — structured error output, exits 1 on invalid shotlist ✓
- Schema validates valid fixtures and rejects invalid ones (bad types, missing fields, sequencing violations) ✓

## Requirements Advanced

- R001 (Script-to-shotlist mapping) — Fully implemented: CLI loads Script.md + VISUAL_STYLE_GUIDE, generation prompt encodes decision tree application, schema validator enforces the contract
- R002 (Text overlay entries) — Fully implemented: shotlist schema includes text_content field, validator enforces text_content populated iff shotlist_type is text_overlay

## Requirements Validated

- R001 — 20 passing tests prove CLI loads correct inputs, schema validates correct outputs, sequencing constraints enforced
- R002 — Schema tests prove text_content is required for text_overlay entries and rejected for non-text_overlay entries

## New Requirements Surfaced

- None

## Requirements Invalidated or Re-scoped

- None

## Deviations

- Added `_ensure_utf8_stdout()` — not planned, but required for Windows environments where context files contain Unicode characters (→) that fail with default charmap codec.
- Added `_resolve_guide_path()` helper — natural decomposition extracted during implementation for testability.

## Known Limitations

- Only one VISUAL_STYLE_GUIDE exists (Mexico's Most Disturbing Cult). Guide variability is designed for but untested against a second guide.
- shotlist.json generation quality depends on Claude's reasoning — the generation prompt provides guidance but output quality is assessed during S06 integration.

## Follow-ups

- None — downstream skills (S02-S05) consume the shotlist.json contract established here.

## Files Created/Modified

- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/__init__.py` — Package init
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/__main__.py` — Module entry point
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/cli.py` — CLI with load + validate subcommands
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/schema.py` — shotlist.json schema validator
- `.claude/skills/visual-orchestrator/prompts/generation.md` — Generation prompt with full schema + decision tree
- `.claude/skills/visual-orchestrator/CONTEXT.md` — Stage contract
- `.claude/skills/visual-orchestrator/SKILL.md` — Usage guide
- `tests/test_visual_orchestrator/__init__.py` — Test package init
- `tests/test_visual_orchestrator/test_cli.py` — 10 CLI tests
- `tests/test_visual_orchestrator/test_schema.py` — 10 schema validator tests

## Forward Intelligence

### What the next slice should know
- shotlist.json schema: each shot has `id` (S001-S999), `chapter`, `narrative_context`, `visual_need`, `building_block`, `shotlist_type` (archival_video|archival_photo|animation|map|text_overlay|document_scan), `suggested_sources`, and optional `text_content` (required iff text_overlay)
- Downstream skills filter by `shotlist_type` — S02 takes archival_video/archival_photo/document_scan, S03 takes animation (non-map), S04 takes map
- The `--guide` flag on the CLI selects which VISUAL_STYLE_GUIDE to use. Default is alphabetically first directory in `context/visual-references/`

### What's fragile
- `_get_project_root()` and `resolve_project_dir()` are duplicated from writer — if a third skill needs them, extract to a shared utility
- Glitch building block matching uses a hardcoded set of name variants that must stay in sync with future VISUAL_STYLE_GUIDE additions

### Authoritative diagnostics
- `python -m visual_orchestrator validate "<topic>"` — exits 0/1 with structured errors, grep-friendly shot IDs
- `pytest tests/test_visual_orchestrator/ -v` — 20 tests covering every schema contract clause

### What assumptions changed
- No assumptions changed — implementation matched the plan closely
