# S04: Remotion Animation Skill

**Goal:** Python animation skill filters `shotlist_type == "map"` entries from shotlist.json, renders animated .mp4 clips via Remotion subprocess, and updates manifest.json with `acquired_by: "agent_animation"` entries.
**Demo:** `python -m animation render "Duplessis Orphans"` renders map shots to `assets/animations/*.mp4` and merges results into manifest.json; all tests pass with mocked subprocess.

## Must-Haves

- Remotion Node.js project under `.claude/skills/animation/remotion/` with map composition(s) accepting props JSON
- Python CLI with `load`, `render`, `status` subcommands following graphics-generator D002 pattern
- CLI filters shotlist entries where `shotlist_type == "map"` and writes per-shot props.json
- `render` subcommand invokes `npx remotion render` via `subprocess.run()` with `cwd` set to Remotion project
- Output .mp4 files land in `assets/animations/` at 1920×1080, 30fps
- Manifest merge: new assets added with `acquired_by: "agent_animation"`, gaps updated `pending_generation → filled`
- CONTEXT.md stage contract + SKILL.md usage guide
- Mocked pytest suite covering CLI, manifest merge, and error paths

## Proof Level

- This slice proves: contract (mocked subprocess — real Remotion renders deferred to S06 integration)
- Real runtime required: no (subprocess mocked in tests; T01 does one real npm install + smoke render to retire scaffold risk)
- Human/UAT required: no

## Verification

- `pytest tests/test_animation/ -v` — all tests pass
- `python -m animation load "Duplessis Orphans"` — exits 0, prints shotlist + manifest + channel context
- `python -m animation status "Duplessis Orphans"` — prints map shot coverage stats

## Observability / Diagnostics

- Inspection surfaces: `python -m animation status <topic>` — map shot counts, rendered vs pending, manifest gap summary
- Failure visibility: subprocess stderr captured and printed on non-zero exit code; manifest merge errors surface shot IDs

## Integration Closure

- Upstream surfaces consumed: `shotlist.json` (S01 schema, filter `shotlist_type == "map"`), `manifest.json` (S02/S03 gap lifecycle)
- New wiring introduced in this slice: `assets/animations/` output directory, `acquired_by: "agent_animation"` manifest entries
- What remains before the milestone is truly usable end-to-end: S05 (asset manager consumes animations/ folder), S06 (integration test with real Remotion renders)

## Tasks

- [x] **T01: Scaffold Remotion Node.js project with map compositions** `est:1h`
  - Why: The rendering engine — React compositions that accept props and produce animated map frames. Retires the "Remotion scaffold" risk by proving npm install + real render works.
  - Files: `.claude/skills/animation/remotion/package.json`, `tsconfig.json`, `src/Root.tsx`, `src/index.ts`, `src/MapComposition.tsx`
  - Do: Create self-contained Remotion project with pinned deps. Single MapComposition component handles all 4 VISUAL_STYLE_GUIDE variants (Illustrated Map, 3D Geographic, Region Highlight, Connection Arc) via `variant` prop. Props schema: `{variant, locations: [{name, x, y}], connections: [{from, to}], title, duration}`. Use Remotion's `spring()`, `interpolate()`, `useCurrentFrame()` for enter animations on markers and labels. Neon-on-black default style. Run `npm install` and verify `npx remotion render` produces a test .mp4.
  - Verify: `cd .claude/skills/animation/remotion && npx remotion render src/index.ts MapComposition out/test.mp4 --props=test-props.json` produces a valid .mp4 file
  - Done when: Remotion project renders a map .mp4 from props JSON without errors

- [x] **T02: Build Python animation CLI with manifest merge** `est:45m`
  - Why: The orchestration layer — filters map shots, writes props, calls Remotion subprocess, updates manifest. Follows the graphics-generator D002 pattern exactly.
  - Files: `.claude/skills/animation/scripts/animation/__init__.py`, `__main__.py`, `cli.py`, `.claude/skills/animation/CONTEXT.md`, `.claude/skills/animation/SKILL.md`
  - Do: Copy `_get_project_root()`, `resolve_project_dir()`, `_ensure_utf8_stdout()`, `_merge_manifest()`, `_empty_manifest()` from graphics-generator. `cmd_load` aggregates shotlist.json (map shots only) + manifest.json + channel.md. `cmd_render` iterates map shots, writes props.json per shot, calls `subprocess.run(["npx", "remotion", "render", ...], cwd=remotion_dir)`, collects results, merges manifest with `folder: "animations"` and `acquired_by: "agent_animation"`. `cmd_status` prints map shot coverage stats. Map props from shotlist fields (`narrative_context`, `visual_need`) to Remotion composition props (`locations`, `variant`, `title`, `duration`). Default duration 240 frames (8s at 30fps).
  - Verify: `python -m animation load "Duplessis Orphans"` exits 0 with labeled output sections
  - Done when: CLI has load/render/status subcommands, render calls subprocess with correct args, manifest merge updates gaps

- [x] **T03: Add pytest suite for animation CLI and manifest merge** `est:45m`
  - Why: Contract verification — proves CLI routing, manifest merge, and error paths without requiring Remotion runtime.
  - Files: `tests/test_animation/__init__.py`, `tests/test_animation/test_cli.py`, `tests/test_animation/test_manifest.py`, `pytest.ini`
  - Do: Add animation scripts to pytest.ini pythonpath. Mirror graphics-generator test patterns: `resolve_project_dir` tests (single match, multi match error, fallback to scratch), `cmd_load` stdout assertions (map shots filtered, sections labeled), `cmd_render` with `unittest.mock.patch("subprocess.run")` returning success/failure, manifest merge tests (new assets appended, gaps updated, idempotent re-merge, atomic write). Test error paths: missing shotlist, no map shots found, subprocess non-zero exit.
  - Verify: `pytest tests/test_animation/ -v` — all tests pass
  - Done when: ≥15 tests covering CLI subcommands, manifest merge, and error paths all pass

## Files Likely Touched

- `.claude/skills/animation/remotion/package.json`
- `.claude/skills/animation/remotion/tsconfig.json`
- `.claude/skills/animation/remotion/src/Root.tsx`
- `.claude/skills/animation/remotion/src/index.ts`
- `.claude/skills/animation/remotion/src/MapComposition.tsx`
- `.claude/skills/animation/scripts/animation/__init__.py`
- `.claude/skills/animation/scripts/animation/__main__.py`
- `.claude/skills/animation/scripts/animation/cli.py`
- `.claude/skills/animation/CONTEXT.md`
- `.claude/skills/animation/SKILL.md`
- `tests/test_animation/__init__.py`
- `tests/test_animation/test_cli.py`
- `tests/test_animation/test_manifest.py`
- `pytest.ini`
