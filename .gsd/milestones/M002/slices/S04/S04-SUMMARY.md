---
id: S04
parent: M002
milestone: M002
provides:
  - Remotion Node.js project rendering animated map .mp4 clips from props JSON (4 VISUAL_STYLE_GUIDE variants)
  - Python animation CLI with load/render/status subcommands orchestrating Remotion via subprocess
  - Manifest merge with acquired_by agent_animation attribution and gap lifecycle management
  - 22 mocked pytest tests covering CLI routing, manifest merge, and error paths
requires:
  - slice: S01
    provides: shotlist.json schema with shotlist_type field for filtering map entries
affects:
  - S05
  - S06
key_files:
  - .claude/skills/animation/remotion/src/MapComposition.tsx
  - .claude/skills/animation/remotion/src/Root.tsx
  - .claude/skills/animation/scripts/animation/cli.py
  - .claude/skills/animation/CONTEXT.md
  - .claude/skills/animation/SKILL.md
  - tests/test_animation/test_cli.py
  - tests/test_animation/test_manifest.py
key_decisions:
  - D021: Remotion props contract uses normalized 0-1 coordinates with durationSeconds — Python CLI controls clip length without knowing pixel dimensions or frame math
  - D022: Single MapComposition component with variant prop + PALETTES lookup instead of 4 separate components — all variants share animation logic, only colors differ
  - SVG-based rendering in Remotion (not canvas) — composable, debuggable, reliable in headless Chrome
  - Mirrored graphics-generator D002 CLI pattern exactly for cross-skill consistency
patterns_established:
  - Remotion props contract: {variant, title, locations[{name,x,y}], connections[{from,to}], durationSeconds}
  - Subprocess invocation: write props.json to tempfile → npx remotion render with cwd=remotion_dir → collect .mp4
  - Manifest entries use folder:"animations" and acquired_by:"agent_animation"
  - BUILDING_BLOCK_TO_VARIANT lookup maps shotlist building_block → Remotion variant name
observability_surfaces:
  - "PYTHONPATH=.claude/skills/animation/scripts python -m animation status <topic>" — map shot coverage stats
  - "PYTHONPATH=.claude/skills/animation/scripts python -m animation load <topic>" — filtered context aggregation
  - cmd_render stderr shows per-shot progress with shot ID, building block, output filename
  - "cd .claude/skills/animation/remotion && npx remotion render src/index.ts MapComposition out/test.mp4 --props=test-props.json" — Remotion smoke test
drill_down_paths:
  - .gsd/milestones/M002/slices/S04/tasks/T01-SUMMARY.md
  - .gsd/milestones/M002/slices/S04/tasks/T02-SUMMARY.md
  - .gsd/milestones/M002/slices/S04/tasks/T03-SUMMARY.md
duration: 53m
verification_result: passed
completed_at: 2026-03-15
---

# S04: Remotion Animation Skill

**Python animation skill filters map shots from shotlist.json, renders animated .mp4 clips via Remotion subprocess, and updates manifest.json — proven with 22 mocked tests and live CLI smoke tests.**

## What Happened

Built in three tasks:

**T01 — Remotion scaffold.** Created a self-contained Node.js project under `.claude/skills/animation/remotion/` with Remotion v4.0.435. Single `MapComposition` component handles all 4 VISUAL_STYLE_GUIDE map variants (Illustrated Map, 3D Geographic, Region Highlight, Connection Arc) via a `variant` prop with per-variant neon color palettes. SVG-based rendering with spring() markers, interpolate() label fades, progressive stroke-dashoffset for connection arcs, and pulsing glow effects. `calculateMetadata` derives frame count from `props.durationSeconds`. Smoke render produced valid 1920×1080 h264 .mp4 at 30fps (6s, 180 frames).

**T02 — Python CLI.** Built animation CLI mirroring the graphics-generator D002 pattern. `load` filters shotlist for `shotlist_type == "map"` and prints MAP_SHOTS, MANIFEST, CHANNEL_DNA sections. `render` maps each map shot to Remotion props (building_block → variant, visual_need → title), writes per-shot props.json, calls `npx remotion render` via subprocess, collects .mp4 outputs to `assets/animations/`, and merges into manifest.json with `acquired_by: "agent_animation"`. `status` prints coverage stats. Also wrote CONTEXT.md stage contract and SKILL.md usage guide.

**T03 — Test suite.** 22 mocked tests: 15 in test_cli.py (resolve_project_dir, cmd_load filtering, cmd_render subprocess orchestration and error paths) and 7 in test_manifest.py (create/append/dedup/gap-update/atomic-write/required-fields/empty-skeleton).

## Verification

- `pytest tests/test_animation/ -v` — 22/22 passed (0.13s)
- `python -m animation load "Duplessis Orphans"` — exits 0, prints all three labeled sections
- `python -m animation status "Duplessis Orphans"` — exits 0, prints "Map shots: 0, No map shots to render"
- Remotion smoke render: `npx remotion render` produced valid .mp4 confirmed by ffprobe (1920×1080, h264, 30fps)
- No regressions: `pytest tests/test_graphics_generator/ tests/test_animation/ -v` — 91 passed

## Requirements Advanced

- R007 (Remotion animated maps) — Contract-tested: CLI filters map shots, subprocess invocation verified with mocks, manifest merge proven. Real Remotion renders confirmed in T01 smoke test.
- R010 (Gap lifecycle tracking) — Animation skill transitions gaps from pending_generation → filled on successful render

## Requirements Validated

- R007 — Moved to contract-tested. Full validation deferred to S06 integration with real shotlist containing map entries.

## New Requirements Surfaced

- None

## Requirements Invalidated or Re-scoped

- None

## Deviations

None.

## Known Limitations

- Current Duplessis Orphans shotlist has 0 map shots — real render testing requires a shotlist with map-type entries (deferred to S06)
- Location extraction from visual_need text is heuristic-based — agent should ideally enrich shotlist entries with explicit `locations[]` arrays
- Font rendering uses Arial/Helvetica system fallback — custom brand fonts would need @remotion/google-fonts
- Region outline is a static simplified polygon, not geographic — matches "stylized not accurate" aesthetic

## Follow-ups

- S05 needs to consume `assets/animations/` folder and `acquired_by: "agent_animation"` manifest entries
- S06 integration test should include a shotlist with map-type entries to prove real end-to-end Remotion rendering

## Files Created/Modified

- `.claude/skills/animation/remotion/package.json` — Remotion project manifest with pinned v4.0.435 deps
- `.claude/skills/animation/remotion/tsconfig.json` — TypeScript config
- `.claude/skills/animation/remotion/src/index.ts` — Entry point
- `.claude/skills/animation/remotion/src/Root.tsx` — Composition registration with calculateMetadata
- `.claude/skills/animation/remotion/src/MapComposition.tsx` — Map animation component (4 variants, SVG, spring/interpolate)
- `.claude/skills/animation/remotion/test-props.json` — Smoke render test props
- `.claude/skills/animation/remotion/.gitignore` — Ignores node_modules, out, dist
- `.claude/skills/animation/scripts/animation/__init__.py` — Package init
- `.claude/skills/animation/scripts/animation/__main__.py` — Argparse entry point
- `.claude/skills/animation/scripts/animation/cli.py` — CLI with load/render/status, variant mapping, manifest merge
- `.claude/skills/animation/CONTEXT.md` — Stage contract
- `.claude/skills/animation/SKILL.md` — Usage guide
- `tests/test_animation/__init__.py` — Test package init
- `tests/test_animation/test_cli.py` — 15 CLI tests
- `tests/test_animation/test_manifest.py` — 7 manifest merge tests
- `pytest.ini` — Added animation scripts to pythonpath

## Forward Intelligence

### What the next slice should know
- Animation outputs land in `assets/animations/` with filenames like `S001_illustrated_map.mp4` — S05 asset manager must scan this folder
- Manifest entries from animation have `acquired_by: "agent_animation"` and `folder: "animations"` — use these to distinguish from graphics-generator entries (`agent_graphics`)
- The Remotion project is fully self-contained at `.claude/skills/animation/remotion/` — first render downloads Chrome Headless Shell (~108MB) and caches it

### What's fragile
- The current Duplessis Orphans shotlist has 0 map shots — S06 must either modify the shotlist or use a different project to prove real animation rendering
- BUILDING_BLOCK_TO_VARIANT lookup maps specific building_block strings — if VISUAL_STYLE_GUIDE adds new map types, the lookup needs updating

### Authoritative diagnostics
- `pytest tests/test_animation/ -v` — contract regression check (22 tests, <0.2s)
- `npx remotion render src/index.ts MapComposition out/test.mp4 --props=test-props.json` in the remotion dir — proves the rendering engine works
- `python -m animation status <topic>` — quick coverage check showing map shots found vs rendered

### What assumptions changed
- No assumptions changed — slice executed cleanly per plan
