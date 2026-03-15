# S01: Visual Orchestrator Skill

**Goal:** A working [HEURISTIC] skill that transforms Script.md + VISUAL_STYLE_GUIDE.md into a validated shotlist.json with building block assignments and text overlay entries.
**Demo:** Run `PYTHONPATH=.claude/skills/visual-orchestrator/scripts python -m visual_orchestrator load "Duplessis Orphans"` → prints labeled context + output path + prompt path. After Claude generates shotlist.json, run `python -m visual_orchestrator validate "Duplessis Orphans"` → exits 0 with valid schema, correct shotlist_types, and sequencing rules passing.

## Must-Haves

- Context-loader CLI (`load` subcommand) resolves project dir, reads Script.md + VISUAL_STYLE_GUIDE.md + channel.md, prints labeled sections + output path + generation prompt path
- `validate` subcommand checks shotlist.json against the schema contract (valid IDs, required fields, valid shotlist_types, sequencing constraints)
- Generation prompt encodes shotlist.json schema, decision tree application rules, segment granularity guidance, sequencing validation rules, and text overlay handling (R002)
- CONTEXT.md stage contract (Inputs → Process → Checkpoints → Outputs → Deferred)
- shotlist.json schema is the stable contract for all downstream S02-S05 skills
- Text overlay entries include `text_content` field with actual quote/date/keyword text (R002)
- Schema validator checks sequencing constraints from the guide (no back-to-back glitch, max 3 consecutive text, etc.)

## Proof Level

- This slice proves: contract (shotlist.json schema + CLI behavior)
- Real runtime required: no (CLI is data aggregation; generation is Claude reasoning; validation is structural)
- Human/UAT required: no (schema validation proves contract; visual quality of generated shotlist is assessed during S06 integration)

## Verification

- `pytest tests/test_visual_orchestrator/ -v` — all tests pass
- Tests cover: project dir resolution, CLI stdout content (labeled sections, paths), schema validation (valid/invalid shotlist fixtures), sequencing constraint enforcement, text overlay entry validation
- `python -m visual_orchestrator load "Duplessis Orphans"` prints expected labeled sections (manual smoke test during development)
- `python -m visual_orchestrator validate "<topic>"` with an invalid shotlist fixture exits 1 and prints structured error list to stderr (failure-path verification)

## Observability / Diagnostics

- **CLI exit codes:** `load` exits 0 on success, 1 on missing input files (with stderr listing which files). `validate` exits 0 on valid shotlist, 1 on validation errors (errors printed to stderr as structured list).
- **Schema validation errors:** `validate_shotlist()` returns a `list[str]` — each string is a human-readable error with shot ID context (e.g., `"Shot S003: missing required field 'building_block'"`). Empty list = valid.
- **Sequencing constraint violations:** Reported as individual errors with shot ID ranges (e.g., `"Shots S012-S013: back-to-back glitch elements"`).
- **Failure state inspection:** Run `python -m visual_orchestrator validate "<topic>"` after any generation to get a structured error report. Errors are deterministic and grep-friendly.
- **No secrets or credentials** involved in this skill.

## Integration Closure

- Upstream surfaces consumed: `projects/N/Script.md` (writer skill), `context/visual-references/*/VISUAL_STYLE_GUIDE.md` (visual-style-extractor), `context/channel/channel.md`
- New wiring introduced in this slice: shotlist.json schema contract consumed by S02-S05
- What remains before the milestone is truly usable end-to-end: S02 (media acquisition), S03 (graphics), S04 (animation), S05 (asset manager), S06 (integration)

## Tasks

- [x] **T01: Build visual orchestrator skill — CLI, generation prompt, schema validator** `est:2h`
  - Why: Creates the entire skill following the writer pattern (D002). CLI aggregates context, generation prompt encodes the decision tree and schema, schema validator enforces the shotlist.json contract.
  - Files: `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/cli.py`, `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/schema.py`, `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/__init__.py`, `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/__main__.py`, `.claude/skills/visual-orchestrator/prompts/generation.md`, `.claude/skills/visual-orchestrator/CONTEXT.md`, `.claude/skills/visual-orchestrator/SKILL.md`
  - Do: (1) Create CLI with `load` and `validate` subcommands — `load` reads Script.md, VISUAL_STYLE_GUIDE.md, channel.md and prints labeled sections + output path for shotlist.json + generation prompt path. `validate` reads shotlist.json and checks schema + sequencing rules. Reuse `_get_project_root()` and `resolve_project_dir()` patterns from writer CLI. (2) Write generation.md prompt encoding: shotlist.json schema with all fields, decision tree application instructions (paragraph-by-paragraph, ~60-100 shots for 20min script), segment granularity rules (group by narrative beat not sentence), sequencing constraints, text overlay handling (R002 — include text_content, no asset generation). (3) Write schema.py with `validate_shotlist(data)` returning list of errors — checks required fields, valid shotlist_types enum, valid ID format (S001-S999), text_content populated iff shotlist_type is text_overlay, sequencing constraints. (4) Write CONTEXT.md stage contract and SKILL.md usage guide. CLI must accept optional `--guide` flag to specify which VISUAL_STYLE_GUIDE to use (defaults to first found in `context/visual-references/`).
  - Verify: `python -m visual_orchestrator load "Duplessis Orphans"` prints Script.md content, VISUAL_STYLE_GUIDE content, channel.md content, shotlist.json output path, and generation.md prompt path
  - Done when: CLI prints all labeled sections without error, schema.py validates a hand-crafted valid fixture and rejects an invalid one, generation.md is complete with schema + decision tree rules + sequencing constraints

- [x] **T02: Write tests and validate schema contract** `est:1h`
  - Why: Proves the CLI and schema validator work correctly. Tests are the objective stopping condition — they verify the shotlist.json contract that all downstream skills depend on.
  - Files: `tests/test_visual_orchestrator/__init__.py`, `tests/test_visual_orchestrator/test_cli.py`, `tests/test_visual_orchestrator/test_schema.py`
  - Do: (1) test_cli.py — test resolve_project_dir (substring match, case-insensitive, fallback), test cmd_load stdout (prints Script.md content, VISUAL_STYLE_GUIDE content, channel.md content, shotlist.json output path, generation.md prompt path), test cmd_load with missing Script.md exits 1. Follow writer test patterns exactly (tmp_path, capsys, mock _get_project_root). (2) test_schema.py — test valid shotlist fixture passes, test missing required fields caught, test invalid shotlist_type caught, test invalid ID format caught, test text_overlay without text_content caught, test non-text_overlay with text_content caught, test sequencing violations (back-to-back glitch, >3 consecutive text, silhouette >3 consecutive). Use pytest fixtures with minimal valid/invalid shotlist dicts.
  - Verify: `pytest tests/test_visual_orchestrator/ -v` — all tests pass
  - Done when: All tests pass, covering CLI resolution + stdout content + schema validation + sequencing enforcement

## Files Likely Touched

- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/cli.py`
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/schema.py`
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/__init__.py`
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/__main__.py`
- `.claude/skills/visual-orchestrator/prompts/generation.md`
- `.claude/skills/visual-orchestrator/CONTEXT.md`
- `.claude/skills/visual-orchestrator/SKILL.md`
- `tests/test_visual_orchestrator/__init__.py`
- `tests/test_visual_orchestrator/test_cli.py`
- `tests/test_visual_orchestrator/test_schema.py`
