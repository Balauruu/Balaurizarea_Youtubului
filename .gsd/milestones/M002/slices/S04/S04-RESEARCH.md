# S04: Remotion Animation Skill — Research

**Date:** 2026-03-15

## Summary

S04 delivers R007: animated location maps rendered as .mp4 clips via Remotion, orchestrated from Python via subprocess. The shotlist schema routes `shotlist_type == "map"` entries to this skill. The VISUAL_STYLE_GUIDE defines 4 map variations (Illustrated Map, 3D Geographic, Region Highlight, Connection Arc) with specific production specs — 6-13s duration, max 3 labeled points, glowing markers, bold location labels.

The approach: a self-contained Remotion Node.js project under `.claude/skills/animation/remotion/` with React compositions for each map variation, plus a Python CLI (`animation` skill) that filters map shots from shotlist.json, writes props JSON files, invokes `npx remotion render` as a subprocess, and updates manifest.json. This mirrors the graphics-generator pattern (D002 context-loader CLI, D016 renderer contract, manifest merge) but swaps Pillow for Remotion.

Key risk — Remotion project scaffold setup (npm install, TypeScript config, composition registration) — is a one-time cost retired during the first task.

## Recommendation

Follow the graphics-generator pattern closely: Python CLI with `load`/`render`/`status` subcommands, manifest merge reused from S03's pattern. The Remotion project is a standard `npx create-video` scaffold with 4 composition components (one per map variation). Each composition accepts props (locations, labels, dates, style variant) and renders a 1920×1080 animation at 30fps.

Python CLI writes a `props.json` file per shot, then calls `npx remotion render --props=props.json <composition-id> <output.mp4>` via `subprocess.run()`. This keeps the Python/Node boundary clean — Python handles orchestration and manifest, Node handles rendering.

Use the "neon on black" style as the default (simpler to implement in React/CSS than parchment textures). The parchment variant can be a stretch goal or deferred.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Video rendering from React components | Remotion (`npx remotion render`) | D006 decision — React-based, props-driven, renders to mp4 |
| Spring/easing animations | `remotion` spring() + interpolate() | Built-in, frame-rate independent, handles enter/exit |
| Map geographic outlines | SVG path data (GeoJSON → SVG) | Standard format, renderable in React, no canvas needed |
| Props passing to compositions | `--props=./props.json` CLI flag | Built into Remotion CLI, avoids shell escaping issues |
| Manifest merge | Copy pattern from graphics-generator `_merge_manifest()` | Atomic write, gap update, same contract |
| Project root + topic resolution | Copy `_get_project_root()` + `resolve_project_dir()` from graphics-generator | Same pattern, same edge cases already handled |

## Existing Code and Patterns

- `.claude/skills/graphics-generator/scripts/graphics_generator/cli.py` — Follow this CLI structure exactly: `load`/`render`/`status` subcommands, `_get_project_root()`, `resolve_project_dir()`, `_merge_manifest()`, `_empty_manifest()`, `_ensure_utf8_stdout()`
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/__init__.py` — RENDERER_REGISTRY pattern; animation skill is simpler (one "renderer" that shells out to Remotion) but can follow the same dispatch if needed
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/schema.py` — `VALID_SHOTLIST_TYPES` includes "map" — this is our filter target
- `tests/test_graphics_generator/test_cli.py` — Test patterns to mirror: resolve_project_dir tests, cmd_load stdout assertions, missing-file error paths
- `tests/test_graphics_generator/test_manifest.py` — Manifest merge tests to replicate for animation entries
- `context/visual-references/Mexico's Most Disturbing Cult/VISUAL_STYLE_GUIDE.md` lines 276-311 — Location Map building block spec with 4 variations and production constraints
- `pytest.ini` — Must add animation scripts to pythonpath

## Constraints

- **Python for orchestration, Node.js for Remotion only** — D006 allows this sole exception to the Python-only constraint
- **Node v24.13.0 + npm available** — no installation needed
- **Remotion project must be self-contained** — all node_modules, package.json, tsconfig under `.claude/skills/animation/remotion/`, not polluting project root
- **Output format: raw .mp4** — no post-processing effects (D008, R011)
- **1920×1080 resolution, 30fps** — matches other asset dimensions
- **Duration 6-13s per map shot** — from VISUAL_STYLE_GUIDE production spec; default to ~8s (240 frames at 30fps)
- **Max 3 labeled location points per frame** — VISUAL_STYLE_GUIDE rule
- **manifest.json entries use `acquired_by: "agent_animation"`** — per boundary map contract
- **Output to `assets/animations/`** — per boundary map (distinct from `assets/vectors/`)
- **Subprocess invocation** — Python calls `npx remotion render` via `subprocess.run()`, parses exit code

## Common Pitfalls

- **Remotion npm install on Windows** — `npx create-video` may prompt interactively; use `npm init video` with `--yes` or manually scaffold package.json + deps to avoid interactive prompts during automated execution
- **Shell escaping with --props** — Use `--props=./path/to/props.json` (file path) not inline JSON strings. Inline JSON on Windows cmd is a quoting nightmare
- **Remotion version pinning** — Pin exact versions in package.json. Remotion has frequent breaking changes between major versions
- **First render cold start** — Remotion's first render compiles the bundle; subsequent renders are faster. Tests should account for ~30s first-render overhead
- **subprocess.run cwd** — Must set `cwd` to the Remotion project directory so it finds package.json and node_modules
- **GeoJSON complexity** — Don't try to render detailed country borders. Simple SVG shapes (circles, lines, rough outlines) match the stylized aesthetic better than accurate cartography
- **Font loading in Remotion** — Remotion uses web fonts; load via `@import` in CSS or `loadFont()` from `@remotion/google-fonts`. Don't assume system fonts are available during headless render

## Open Risks

- **Remotion render time** — Each 8s clip at 1920×1080 30fps = 240 frames. On a typical machine, expect 1-5 minutes per clip. If a shotlist has 5+ map entries, total render time could be 10-25 minutes. Not a blocker but worth noting.
- **npm install reliability** — First-time `npm install` in the Remotion project may fail on corporate networks or due to npm registry issues. Retry logic may be needed.
- **SVG map data sourcing** — The Python CLI must provide geographic coordinates or SVG paths in props. For simple "glowing dot on dark background" maps, hardcoded region outlines work. For real geography, we'd need a lightweight GeoJSON source — but the VISUAL_STYLE_GUIDE's aesthetic is "stylized" not "accurate", so simplified shapes suffice.
- **Test isolation** — Tests must mock `subprocess.run` to avoid requiring a real Remotion project + node_modules. Real renders tested only in S06 integration.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| Remotion | `remotion-dev/skills@remotion-best-practices` (145K installs) | available — recommended, official best practices |
| Remotion | `inferen-sh/skills@remotion-render` (27.2K installs) | available — render-focused, potentially useful |

## Sources

- Remotion CLI render docs: `npx remotion render <entry-point> <composition-id> <output>` with `--props=./props.json` for data-driven rendering (source: [Remotion CLI docs](https://www.remotion.dev/docs/cli/render))
- Remotion composition registration: `registerRoot()` + `<Composition>` with id, width, height, fps, durationInFrames (source: [Remotion docs](https://www.remotion.dev/docs/register-root))
- Remotion animation primitives: `useCurrentFrame()`, `spring()`, `interpolate()` for frame-based animation (source: [Remotion interpolate docs](https://www.remotion.dev/docs/interpolate))
- VISUAL_STYLE_GUIDE Location Map: 4 variations (Illustrated Map, 3D Geographic, Region Highlight, Connection Arc), 6-13s, max 3 points, glowing markers (source: project `context/visual-references/` line 276-311)
- S03 forward intelligence: renderer registry pattern extensible, manifest merge follows atomic read-append-write (source: S03-SUMMARY.md)
- S01 forward intelligence: downstream skills filter `shotlist_type == "map"` (source: S01-SUMMARY.md)
