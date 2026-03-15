# S05: Asset Manager Skill

**Goal:** A working asset-manager skill that reads shotlist.json + manifest.json, numbers all mapped assets by shotlist order, moves unmapped assets to `_pool/`, finalizes gap statuses, and produces a schema-valid manifest.
**Demo:** Run `organize "Duplessis Orphans"` → files in type folders get `001_` prefixes in shotlist order, unmapped files land in `_pool/`, manifest.json gaps show `unfilled` terminal status, `status` command reports organized counts.

## Must-Haves

- Sequential numeric prefixes (001_, 002_, ...) assigned by order of first appearance in shotlist.json
- Assets mapped to multiple shots get the number of their earliest shot
- Multiple assets on the same shot all get the same prefix
- Unmapped assets moved to `_pool/` directory and removed from manifest assets array
- Remaining `pending_generation` gaps set to `unfilled` terminal status
- Manifest remains schema-valid after organize (passes `validate_manifest()`)
- Idempotent — running organize twice produces the same result
- CLI with `load`, `organize`, and `status` subcommands following D002 pattern
- CONTEXT.md and SKILL.md docs
- No content modification of any asset file (R011)

## Verification

- `pytest tests/test_asset_manager/ -v` — all tests pass covering:
  - Numbering assignment from shotlist order
  - Multi-shot asset gets first-appearance number
  - Same-shot assets share prefix
  - Unmapped assets moved to `_pool/` and removed from manifest
  - Gap finalization (`pending_generation` → `unfilled`)
  - Already-numbered files handled on re-run (idempotency)
  - Manifest validity after organize via `validate_manifest()`
  - CLI subcommand routing
- `PYTHONPATH=.claude/skills/asset-manager/scripts python -m asset_manager status "Duplessis Orphans"` — exits 0
- No regressions: `pytest tests/ -v` — all existing tests still pass

## Observability / Diagnostics

- **`status` command** — Primary inspection surface. Reports numbered/unnumbered/pool counts, gap summary (filled/unfilled/pending). A future agent runs `status "Topic"` to see if organize succeeded.
- **stderr logging during `organize`** — Prints each rename, each pool move, gap finalization count, and manifest validation result to stderr. Enables post-mortem from CLI output.
- **Manifest validity** — Pre/post `validate_manifest()` calls. If post-validation fails, organize exits non-zero with validation errors on stderr. Manifest is NOT written if invalid.
- **Idempotency signal** — On re-run, logs `(already organized, re-numbering)` to stderr so the agent knows it's a re-run.
- **Failure visibility** — File rename errors include source and target paths. Pool directory creation logged. Non-zero exit on any validation or I/O failure.
- **No secrets** — This skill handles only local file paths and shot metadata. No redaction needed.

## Integration Closure

- Upstream surfaces consumed: `shotlist.json` (S01), `manifest.json` + type folders (S02/S03/S04), `schema.validate_manifest()` (S02)
- New wiring: asset-manager CLI reads manifest schema from media-acquisition package (cross-skill import via PYTHONPATH)
- What remains: S06 end-to-end integration proving all 5 skills chain on a real project

## Tasks

- [x] **T01: Implement asset-manager skill with CLI, organize logic, and tests** `est:45m`
  - Why: Entire slice — deterministic file ops with no external deps, no natural split point
  - Files: `.claude/skills/asset-manager/scripts/asset_manager/cli.py`, `tests/test_asset_manager/test_cli.py`, `tests/test_asset_manager/test_organize.py`, `.claude/skills/asset-manager/CONTEXT.md`, `.claude/skills/asset-manager/SKILL.md`, `pytest.ini`
  - Do: (1) Create skill scaffold: `__init__.py`, `__main__.py`, CONTEXT.md, SKILL.md. (2) Implement `cli.py` with `load` (prints shotlist + manifest + channel context), `organize` (compute numbering from shotlist order → rename files in-place → move unmapped to `_pool/` → finalize gaps → atomic manifest write), and `status` (numbered/unnumbered/pool counts). (3) Handle idempotency: strip existing `\d{3}_` prefix before re-numbering. (4) Import `validate_manifest` from `media_acquisition.schema` for pre/post validation. (5) Remove `_pool/` assets from manifest assets array (not tracked by pipeline). (6) Write test suite: `test_organize.py` for core logic (numbering, multi-shot, same-shot, pool, gaps, idempotency, manifest validity), `test_cli.py` for subcommand routing and project resolution. (7) Add asset-manager scripts to pytest.ini pythonpath.
  - Verify: `pytest tests/test_asset_manager/ -v` passes, `pytest tests/ -v` shows no regressions
  - Done when: All tests pass, CLI smoke test exits 0, manifest passes `validate_manifest()` after organize

## Files Likely Touched

- `.claude/skills/asset-manager/scripts/asset_manager/__init__.py`
- `.claude/skills/asset-manager/scripts/asset_manager/__main__.py`
- `.claude/skills/asset-manager/scripts/asset_manager/cli.py`
- `.claude/skills/asset-manager/CONTEXT.md`
- `.claude/skills/asset-manager/SKILL.md`
- `tests/test_asset_manager/__init__.py`
- `tests/test_asset_manager/test_cli.py`
- `tests/test_asset_manager/test_organize.py`
- `pytest.ini`
