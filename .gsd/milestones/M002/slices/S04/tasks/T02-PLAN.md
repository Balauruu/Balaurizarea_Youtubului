---
estimated_steps: 5
estimated_files: 6
---

# T02: Build Python animation CLI with manifest merge

**Slice:** S04 — Remotion Animation Skill
**Milestone:** M002

## Description

Python CLI under `.claude/skills/animation/scripts/animation/` that orchestrates Remotion renders from shotlist.json. Follows the graphics-generator D002 context-loader pattern exactly: `load` aggregates context, `render` iterates map shots and invokes Remotion via subprocess, `status` prints coverage stats. Reuses `_get_project_root()`, `resolve_project_dir()`, `_merge_manifest()`, `_empty_manifest()`, `_ensure_utf8_stdout()` patterns from graphics-generator. Also writes CONTEXT.md (stage contract) and SKILL.md (usage guide).

## Steps

1. Create package files: `__init__.py`, `__main__.py` (argparse dispatch to load/render/status).
2. Implement `cli.py` with `cmd_load(topic)` — filters shotlist.json for `shotlist_type == "map"` entries, prints labeled sections (MAP_SHOTS, MANIFEST, CHANNEL_DNA) to stdout.
3. Implement `cmd_render(topic)` — iterates map shots, maps shotlist fields to Remotion props (variant selection from `building_block`, locations from `visual_need`/`narrative_context`, default 240 frames), writes per-shot `props.json` to temp dir, calls `subprocess.run(["npx", "remotion", "render", entry_point, "MapComposition", output_path, f"--props={props_path}"], cwd=remotion_dir)`, captures stderr on failure, collects results, calls `_merge_manifest()` with `folder: "animations"` and `acquired_by: "agent_animation"`.
4. Implement `cmd_status(topic)` — counts total map shots vs rendered (present in manifest with `acquired_by: "agent_animation"`), prints summary.
5. Write CONTEXT.md (Inputs: shotlist.json map entries; Process: props mapping → Remotion render → manifest merge; Outputs: .mp4 clips in assets/animations/, updated manifest.json) and SKILL.md (usage examples for load/render/status).

## Must-Haves

- [ ] CLI filters only `shotlist_type == "map"` shots from shotlist.json
- [ ] `cmd_render` writes props.json per shot and calls `npx remotion render` via subprocess
- [ ] subprocess.run called with `cwd` set to Remotion project directory
- [ ] Output .mp4 files written to `assets/animations/` directory
- [ ] Manifest merge adds entries with `acquired_by: "agent_animation"` and `folder: "animations"`
- [ ] Gap lifecycle: `pending_generation → filled` for rendered map shots
- [ ] CONTEXT.md stage contract and SKILL.md usage guide

## Verification

- `python -m animation load "Duplessis Orphans"` exits 0 and prints labeled sections with map-only shots
- `python -m animation status "Duplessis Orphans"` exits 0 and prints coverage stats
- Code review: `cmd_render` subprocess call uses correct args and cwd

## Inputs

- `.claude/skills/graphics-generator/scripts/graphics_generator/cli.py` — Pattern source for `_get_project_root()`, `resolve_project_dir()`, `_merge_manifest()`, `_empty_manifest()`, `_ensure_utf8_stdout()`
- T01 output — Remotion project path and composition ID for subprocess invocation
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/schema.py` — `VALID_SHOTLIST_TYPES` confirms "map" is valid

## Observability Impact

- `python -m animation status <topic>` — new surface: prints map shot counts (total, rendered, pending), manifest gap summary with per-shot status
- `cmd_render` captures subprocess stderr on non-zero exit and prints shot ID + error context — failures are attributable to specific shots
- Manifest merge writes `acquired_by: "agent_animation"` on each entry — future agents can query manifest.json to see which shots were rendered by this skill
- Gap lifecycle transitions (`pending_generation → filled`) are visible in manifest.json gaps array — `cmd_status` reads these to compute coverage

## Expected Output

- `.claude/skills/animation/scripts/animation/__init__.py` — Package init
- `.claude/skills/animation/scripts/animation/__main__.py` — Argparse entry point
- `.claude/skills/animation/scripts/animation/cli.py` — CLI with load/render/status subcommands
- `.claude/skills/animation/CONTEXT.md` — Stage contract
- `.claude/skills/animation/SKILL.md` — Usage guide
