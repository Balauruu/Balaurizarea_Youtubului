---
id: T01
parent: S01
milestone: M002
provides:
  - Visual orchestrator CLI with load and validate subcommands
  - shotlist.json schema validator
  - Generation prompt encoding decision tree, schema, and sequencing rules
  - CONTEXT.md and SKILL.md documentation
key_files:
  - .claude/skills/visual-orchestrator/scripts/visual_orchestrator/cli.py
  - .claude/skills/visual-orchestrator/scripts/visual_orchestrator/schema.py
  - .claude/skills/visual-orchestrator/prompts/generation.md
key_decisions:
  - Duplicated _get_project_root() and resolve_project_dir() from writer skill (small functions, no shared lib needed yet)
  - Added _ensure_utf8_stdout() to handle Windows charmap encoding for Unicode characters in context files
  - Glitch building blocks set includes common name variants (e.g., "Static Noise" and "Static Noise / Corruption") for guide flexibility
patterns_established:
  - Visual orchestrator follows exact same context-loader pattern as writer (D002)
  - Schema validation returns list[str] errors with shot ID context for grep-friendly output
observability_surfaces:
  - "python -m visual_orchestrator validate <topic>" — structured error output, exits 1 on failure
  - CLI stderr messages include full file paths for missing inputs
duration: 45min
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Build visual orchestrator skill — CLI, generation prompt, schema validator

**Built complete visual orchestrator skill: CLI with load/validate subcommands, generation prompt encoding the full decision tree and shotlist.json schema, and schema validator with sequencing constraint checking.**

## What Happened

Created the visual orchestrator skill under `.claude/skills/visual-orchestrator/` following the writer skill's context-loader pattern (D002). Seven files total:

1. **Package structure** — `__init__.py` and `__main__.py` mirror the writer layout exactly.
2. **CLI** (`cli.py`) — Two subcommands: `load` aggregates Script.md + VISUAL_STYLE_GUIDE.md + channel.md into labeled sections with dividers, printing output path and generation prompt path. `validate` reads shotlist.json and runs schema validation. Added `--guide` flag for selecting which VISUAL_STYLE_GUIDE to use (defaults to first found). Added `_resolve_guide_path()` for guide directory resolution. Added `_ensure_utf8_stdout()` to handle Windows encoding issues with Unicode in context files.
3. **Schema validator** (`schema.py`) — `validate_shotlist(data) -> list[str]` checks: required top-level keys, required per-shot fields, S001-S999 sequential ID format, valid shotlist_type enum (6 values), text_content populated iff text_overlay (R002), and three sequencing constraints (no back-to-back glitch, max 3 consecutive text_overlay, max 3 consecutive Silhouette Figure animation).
4. **Generation prompt** (`prompts/generation.md`) — Full specification: shotlist.json schema with field descriptions, valid type routing table, paragraph-by-paragraph processing instructions, decision tree precedence rules, segment granularity guidance (60-100 shots for 20-min script), sequencing constraints as post-generation self-check, text overlay handling per R002, and example output fragment.
5. **CONTEXT.md** — Stage contract matching writer format (Inputs → Process → Checkpoints → Outputs → Deferred).
6. **SKILL.md** — Usage guide with commands, arguments, exit codes, and schema contract summary.

## Verification

- `PYTHONPATH=... python -m visual_orchestrator load "Duplessis Orphans"` — exits 0, prints all three labeled sections (Script, Visual Style Guide, Channel DNA), output path, and generation prompt path ✓
- `validate_shotlist()` returns empty list for valid fixture (2 shots with correct fields) ✓
- `validate_shotlist()` returns 4 errors for invalid fixture (bad shotlist_type, missing field, empty text_content on overlay, out-of-sequence ID) ✓
- All 7 expected files exist at correct paths ✓

### Slice-level verification status

- `pytest tests/test_visual_orchestrator/ -v` — **not yet passing** (no tests written yet, that's T02)
- CLI smoke test — **passing** ✓
- All files exist — **passing** ✓

## Diagnostics

- Run `python -m visual_orchestrator validate "<topic>"` to check any shotlist.json. Exits 0 = valid, exits 1 = prints numbered error list to stderr.
- Each error includes shot ID context (e.g., "Shot S003: missing required field 'building_block'").
- Sequencing errors include shot ID ranges (e.g., "Shots S012-S013: back-to-back glitch elements").

## Deviations

- Added `_ensure_utf8_stdout()` — not in the plan, but required for Windows environments where channel.md contains `→` characters that can't be encoded with the default charmap codec.
- Added `_resolve_guide_path()` helper — extracted guide resolution logic into its own function for testability and error clarity. Not explicitly in the plan but a natural decomposition.

## Known Issues

- Only one VISUAL_STYLE_GUIDE exists (Mexico's Most Disturbing Cult). Guide variability untested — the design handles it but hasn't been validated against a second guide.

## Files Created/Modified

- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/__init__.py` — Package init
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/__main__.py` — Module entry point
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/cli.py` — CLI with load + validate subcommands
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/schema.py` — shotlist.json schema validator
- `.claude/skills/visual-orchestrator/prompts/generation.md` — Generation prompt with full schema + decision tree rules
- `.claude/skills/visual-orchestrator/CONTEXT.md` — Stage contract
- `.claude/skills/visual-orchestrator/SKILL.md` — Usage guide
- `tests/test_visual_orchestrator/__init__.py` — Test package init (empty, scaffolding for T02)
- `.gsd/milestones/M002/slices/S01/S01-PLAN.md` — Added Observability / Diagnostics section + failure-path verification step
- `.gsd/milestones/M002/slices/S01/tasks/T01-PLAN.md` — Added Observability Impact section
