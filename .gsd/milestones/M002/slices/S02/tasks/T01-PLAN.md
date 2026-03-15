---
estimated_steps: 6
estimated_files: 9
---

# T01: Skill scaffold with manifest schema contract, load/status CLI, and tests

**Slice:** S02 — Media Acquisition Skill
**Milestone:** M002

## Description

Establish the media acquisition skill following the visual-orchestrator context-loader pattern (D002). The critical deliverable is the manifest.json schema — it's the central coordination artifact (D011) consumed by S03 (graphics), S04 (animation), and S05 (asset manager). Getting this contract right and validated before source modules are built prevents expensive rework.

Also implements `load` (aggregates shotlist.json + media_urls.md for Claude to plan search queries) and `status` (reads manifest.json and prints gap analysis summary) subcommands, plus media_urls.md parsing.

## Steps

1. Create skill directory structure: `.claude/skills/media-acquisition/scripts/media_acquisition/` with `__init__.py`, `__main__.py`
2. Implement `schema.py` with `validate_manifest()` — validates manifest.json against the contract (required fields, valid statuses, shot ID format, folder names). Return `list[str]` errors matching visual-orchestrator pattern.
3. Implement `cli.py` with `load` and `status` subcommands plus `parse_media_urls()` helper. `load` reads shotlist.json + media_urls.md + channel.md and prints labeled sections. `status` reads manifest.json and prints coverage stats, gap count, per-source summary.
4. Write `CONTEXT.md` (stage contract: inputs, process, checkpoints, outputs) and `SKILL.md` (usage guide with CLI examples).
5. Write `tests/test_media_acquisition/test_schema.py` — valid manifest, missing fields, bad status values, invalid shot IDs, empty arrays, gap lifecycle states.
6. Write `tests/test_media_acquisition/test_cli.py` — load stdout content, status output, missing file errors, media_urls parsing.

## Must-Haves

- [ ] manifest.json schema validated: required top-level keys (project, generated, updated, assets, gaps, source_summary)
- [ ] Per-asset validation: filename, folder, source, source_url, description, license, mapped_shots, acquired_by
- [ ] Per-gap validation: shot_id (S001-S999 format), visual_need, shotlist_type, status (pending_generation|filled|unfilled)
- [ ] Valid folder names: archival_photos, archival_footage, documents, broll, vectors, animations
- [ ] `load` subcommand prints shotlist.json + media_urls.md + channel.md in labeled sections
- [ ] `status` subcommand reads manifest.json and prints gap count + source summary
- [ ] media_urls.md parser extracts URL, description, source, and category from markdown format
- [ ] Tests cover both valid and invalid manifest states

## Verification

- `pytest tests/test_media_acquisition/test_schema.py -v` — all pass
- `pytest tests/test_media_acquisition/test_cli.py -v` — all pass
- `PYTHONPATH=.claude/skills/media-acquisition/scripts python -m media_acquisition load "Duplessis Orphans"` — exits 0

## Observability Impact

- Signals added: `status` subcommand outputs structured gap/coverage summary to stdout
- How a future agent inspects this: `python -m media_acquisition status "<topic>"`
- Failure state exposed: CLI stderr messages with full file paths for missing inputs

## Inputs

- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/cli.py` — pattern to follow for CLI structure, `_get_project_root()`, `resolve_project_dir()`, `_ensure_utf8_stdout()`
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/schema.py` — pattern to follow for schema validation
- `projects/1. The Duplessis Orphans Quebec's Stolen Children/research/media_urls.md` — input format to parse
- S02-RESEARCH.md manifest.json schema draft — starting point for schema definition
- S01 Forward Intelligence — shotlist.json field names and valid shotlist_types

## Expected Output

- `.claude/skills/media-acquisition/scripts/media_acquisition/cli.py` — CLI with load + status subcommands
- `.claude/skills/media-acquisition/scripts/media_acquisition/schema.py` — manifest.json validator
- `.claude/skills/media-acquisition/CONTEXT.md` — stage contract
- `.claude/skills/media-acquisition/SKILL.md` — usage guide
- `tests/test_media_acquisition/test_schema.py` — ~10 schema validation tests
- `tests/test_media_acquisition/test_cli.py` — ~8 CLI tests
