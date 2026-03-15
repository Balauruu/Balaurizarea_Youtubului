---
estimated_steps: 7
estimated_files: 9
---

# T01: Implement asset-manager skill with CLI, organize logic, and tests

**Slice:** S05 — Asset Manager Skill
**Milestone:** M002

## Description

Build the complete asset-manager skill in a single task. This is deterministic file manipulation — no APIs, no heuristics, no external dependencies. The skill reads shotlist.json for shot ordering and manifest.json for asset-to-shot mappings, then: assigns sequential `001_` prefixes based on shotlist order, renames files in-place within type folders, moves unmapped assets to `_pool/`, finalizes remaining gaps to `unfilled`, and writes an updated schema-valid manifest.

## Steps

1. Create skill scaffold: `__init__.py`, `__main__.py` (argparse with load/organize/status subcommands), CONTEXT.md (stage contract), SKILL.md (usage guide). Mirror animation skill structure.

2. Implement core organize logic in `cli.py`:
   - `_build_shot_order(shotlist)` — returns dict mapping shot_id → sequence number (1-based) from shotlist array order
   - `_compute_numbering(manifest_assets, shot_order)` — for each asset, find its earliest mapped_shot in shot_order, assign that sequence number as prefix. Assets with no mapped_shots are "unmapped"
   - `_strip_existing_prefix(filename)` — regex to remove existing `\d{3}_` prefix for idempotent re-runs
   - `cmd_organize(topic)` — orchestrator: load shotlist + manifest → validate manifest → compute numbering → rename files → move unmapped to `_pool/` → remove unmapped from manifest assets → set remaining `pending_generation` gaps to `unfilled` → validate manifest → atomic write

3. Implement `cmd_load(topic)` — prints SHOTLIST, MANIFEST, CHANNEL_DNA labeled sections (same pattern as other skills).

4. Implement `cmd_status(topic)` — reads manifest + scans type folders, reports: total assets, numbered, unnumbered, pool count, gap summary (filled/unfilled/pending).

5. Handle edge cases: multiple assets on same shot (all get same prefix), asset mapped to multiple shots (use earliest shot's number), already-numbered files on re-run (strip prefix first), `_pool/` directory creation.

6. Write `tests/test_organize.py`: numbering from shotlist order, multi-shot asset gets first-appearance number, same-shot assets share prefix, unmapped → `_pool/` + removed from manifest, gap finalization, idempotent re-run, manifest validity via `validate_manifest()`, empty manifest/shotlist edge cases.

7. Write `tests/test_cli.py`: subcommand routing, `resolve_project_dir` matching, `cmd_load`/`cmd_status` output format. Add `asset-manager/scripts` to pytest.ini pythonpath.

## Must-Haves

- [ ] Sequential numbering (001_, 002_) by shotlist order with first-appearance rule for multi-shot assets
- [ ] Unmapped assets moved to `_pool/` and removed from manifest assets array
- [ ] `pending_generation` gaps finalized to `unfilled`
- [ ] Manifest passes `validate_manifest()` after organize
- [ ] Idempotent re-runs produce same result
- [ ] CLI with load/organize/status subcommands
- [ ] CONTEXT.md and SKILL.md
- [ ] All tests pass, no regressions

## Observability Impact

- **New `status` command** — Adds a diagnostic surface for asset organization state: numbered vs unnumbered counts, pool count, gap breakdown. Future agents call `status "Topic"` after organize to verify success.
- **stderr organize trace** — Each rename/move/finalization logged to stderr during `cmd_organize`. Enables debugging from CLI output without re-reading manifest.
- **Pre/post manifest validation** — `validate_manifest()` errors surfaced on stderr before and after organize. Invalid post-organize state prevents manifest write and exits non-zero.
- **Idempotency detection** — Logs when stripping existing prefixes on re-run.
- **No secrets or sensitive data** — Only file paths and shot IDs in output.

## Verification

- `pytest tests/test_asset_manager/ -v` — all tests pass
- `pytest tests/ -v` — no regressions across all skill test suites
- `PYTHONPATH=".claude/skills/asset-manager/scripts;.claude/skills/media-acquisition/scripts" python -m asset_manager status "Duplessis Orphans"` — exits 0

## Inputs

- `.claude/skills/animation/scripts/animation/cli.py` — CLI scaffold pattern to mirror
- `.claude/skills/media-acquisition/scripts/media_acquisition/schema.py` — `validate_manifest()`, `VALID_FOLDERS`, `VALID_GAP_STATUSES` to import
- `.claude/skills/graphics-generator/scripts/graphics_generator/cli.py` — `_merge_manifest()` atomic write pattern reference
- `Architecture.md` line 213 — authoritative spec for numbering convention
- S05-RESEARCH.md — design decisions and pitfall analysis

## Expected Output

- `.claude/skills/asset-manager/scripts/asset_manager/cli.py` — Complete CLI with organize logic
- `.claude/skills/asset-manager/CONTEXT.md` — Stage contract (Inputs, Process, Checkpoints, Outputs)
- `.claude/skills/asset-manager/SKILL.md` — Usage guide
- `tests/test_asset_manager/test_organize.py` — Core organize logic tests
- `tests/test_asset_manager/test_cli.py` — CLI routing and project resolution tests
- `pytest.ini` — Updated with asset-manager scripts path
