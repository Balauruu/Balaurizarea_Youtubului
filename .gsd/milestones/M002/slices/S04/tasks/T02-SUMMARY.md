---
id: T02
parent: S04
milestone: M002
provides:
  - Python animation CLI with load/render/status subcommands for map shot orchestration
  - Manifest merge with agent_animation attribution and gap lifecycle management
key_files:
  - .claude/skills/animation/scripts/animation/cli.py
  - .claude/skills/animation/CONTEXT.md
  - .claude/skills/animation/SKILL.md
  - tests/test_animation/test_cli.py
key_decisions:
  - Mirrored graphics-generator CLI pattern exactly (_get_project_root, resolve_project_dir, _merge_manifest, _empty_manifest, _ensure_utf8_stdout) for consistency across skills
  - BUILDING_BLOCK_TO_VARIANT lookup table maps shotlist building_block strings to Remotion variant names — extensible without code changes
  - Default 8-second duration per clip (DEFAULT_DURATION_SECONDS) — agent can override via shotlist locations/props enrichment
patterns_established:
  - Animation CLI props mapping: shotlist building_block → Remotion variant, visual_need → title, optional locations[] array for explicit coordinates
  - Subprocess invocation pattern: write props.json to tempfile, call npx remotion render with cwd=remotion_dir, clean up temp on completion
  - Manifest entries use folder:"animations" and acquired_by:"agent_animation" to distinguish from graphics-generator entries
observability_surfaces:
  - "PYTHONPATH=.claude/skills/animation/scripts python -m animation status <topic>" — map shot coverage stats
  - "PYTHONPATH=.claude/skills/animation/scripts python -m animation load <topic>" — filtered context aggregation
  - cmd_render prints per-shot progress to stderr with shot ID, building block, and output filename/size
  - Failed renders include shot ID and Remotion stderr in error output
duration: 18m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T02: Build Python animation CLI with manifest merge

**Python CLI under `.claude/skills/animation/scripts/animation/` with load/render/status subcommands — filters map shots, orchestrates Remotion renders via subprocess, merges results into manifest.json with agent_animation attribution.**

## What Happened

Built the animation CLI following the graphics-generator D002 context-loader pattern. The package has three subcommands:

- **load** — Filters shotlist.json for `shotlist_type == "map"` entries, prints MAP_SHOTS, MANIFEST, and CHANNEL_DNA sections to stdout
- **render** — Maps each map shot to Remotion props (variant from building_block, title from visual_need, locations from explicit array or heuristic extraction), writes per-shot props.json to tempfile, invokes `npx remotion render` via subprocess with cwd set to the Remotion project, collects .mp4 outputs to `assets/animations/`, merges into manifest.json
- **status** — Counts total map shots vs rendered (manifest entries with `acquired_by: "agent_animation"`), prints coverage percentage

Also wrote CONTEXT.md (stage contract) and SKILL.md (usage guide), added `animation/scripts` to pytest.ini pythonpath, and created 21 tests covering all subcommands, variant mapping, manifest merge, gap lifecycle, error handling, and subprocess argument correctness.

## Verification

- `pytest tests/test_animation/ -v` — 21/21 passed
- `python -m animation load "Duplessis Orphans"` — exits 0, prints all three labeled sections (MAP_SHOTS shows "no map shots" since current shotlist has no map entries, MANIFEST and CHANNEL_DNA print correctly)
- `python -m animation status "Duplessis Orphans"` — exits 0, prints "Map shots: 0, No map shots to render"
- Code review: `cmd_render` subprocess call uses `["npx", "remotion", "render", "src/index.ts", "MapComposition", str(output_path), f"--props={props_path}"]` with `cwd=str(remotion_dir)` — correct per T01 Remotion scaffold
- test_cmd_render_calls_subprocess_correctly verifies: 2 map shots rendered (not archival_video), subprocess args match expected structure, cwd points to remotion dir, manifest updated with agent_animation entries
- test_cmd_render_gap_lifecycle verifies: pending_generation gaps transition to filled after render

### Slice-level verification status
- ✅ `pytest tests/test_animation/ -v` — 21 passed
- ✅ `python -m animation load "Duplessis Orphans"` — exits 0
- ✅ `python -m animation status "Duplessis Orphans"` — exits 0

## Diagnostics

- `PYTHONPATH=.claude/skills/animation/scripts python -m animation status <topic>` — quick coverage check
- `PYTHONPATH=.claude/skills/animation/scripts python -m animation load <topic>` — inspect what map shots the CLI sees
- cmd_render stderr shows per-shot progress: `Rendering S001 (Illustrated Map) → S001_illustrated_map.mp4...`
- Failed renders print shot ID + Remotion stderr (TypeScript errors, frame failures, timeouts)
- Manifest entries tagged `acquired_by: "agent_animation"` — grep manifest.json for attribution

## Deviations

None.

## Known Issues

- Current Duplessis Orphans shotlist has 0 map shots (only 1 archival_video entry) — real render testing requires a shotlist with map-type entries
- Location extraction from visual_need text is heuristic-based — the agent calling render should ideally enrich shotlist entries with explicit `locations[]` arrays for best results

## Files Created/Modified

- `.claude/skills/animation/scripts/animation/__init__.py` — Package init
- `.claude/skills/animation/scripts/animation/__main__.py` — Argparse entry point
- `.claude/skills/animation/scripts/animation/cli.py` — CLI with load/render/status, variant mapping, manifest merge
- `.claude/skills/animation/CONTEXT.md` — Stage contract (inputs, process, outputs, checkpoints)
- `.claude/skills/animation/SKILL.md` — Usage guide with command examples
- `tests/test_animation/__init__.py` — Test package init
- `tests/test_animation/test_cli.py` — 21 tests covering all subcommands and edge cases
- `pytest.ini` — Added `.claude/skills/animation/scripts` to pythonpath
- `.gsd/milestones/M002/slices/S04/tasks/T02-PLAN.md` — Added Observability Impact section
