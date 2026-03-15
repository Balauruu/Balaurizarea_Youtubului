# S03: Graphics Generator Skill

**Goal:** A working graphics generator skill that produces code-gen flat graphics (Pillow) and ComfyUI creative assets for all `shotlist_type: animation` shots, updating manifest.json with new asset entries.
**Demo:** Run `python -m graphics_generator generate "Duplessis Orphans"` → PNG files appear in `assets/vectors/`, manifest.json updated with asset entries and gaps marked filled.

## Must-Haves

- CLI with `load`, `generate`, `status` subcommands following context-loader pattern (D002)
- 7 Pillow renderers producing 1920×1080 PNGs for code-gen building blocks (silhouette, icon, texture, glitch, noise, code_screen, profile_card)
- ComfyUI REST client with connection failure handling and `--code-gen-only` fallback
- 4 ComfyUI workflow templates for creative building blocks (concept_diagram, ritual_illustration, glitch_icon, data_moshing)
- Manifest.json merge: read existing → append new asset entries → atomic write
- Each asset filename includes shot ID to avoid collisions (`S042_silhouette_figure.png`)
- Building block effects (scanlines, noise, glow) rendered INTO assets per VISUAL_STYLE_GUIDE specs — not post-production (clarification of D008)

## Proof Level

- This slice proves: contract + integration (Pillow rendering verified by tests, ComfyUI verified by mocked tests + live in S06)
- Real runtime required: yes for Pillow renderers, mocked for ComfyUI
- Human/UAT required: no (visual quality assessed in S06 integration)

## Verification

- `pytest tests/test_graphics_generator/ -v` — all tests pass
- Tests cover: CLI resolution, renderer output (valid PNG, correct dimensions), manifest merge logic, ComfyUI client with mocked responses, building block → renderer routing
- `python -m graphics_generator status "Duplessis Orphans"` — exits 0 showing generation coverage

## Observability / Diagnostics

- Runtime signals: CLI stderr reports per-shot generation progress, ComfyUI connection status, skip reasons
- Inspection surfaces: `python -m graphics_generator status "<topic>"` shows coverage (generated/total/skipped per building block type)
- Failure visibility: ComfyUI connection failures report server address and which blocks require it; Pillow errors include shot ID and building block type

## Integration Closure

- Upstream surfaces consumed: `shotlist.json` (S01 schema), `manifest.json` (S02 schema), `channel.md`
- New wiring introduced: graphics_generator reads shotlist → filters animation type → routes to renderer/ComfyUI → writes assets + updates manifest
- What remains: S04 (animation), S05 (asset manager), S06 (end-to-end integration)

## Tasks

- [x] **T01: CLI scaffold + Pillow code-gen renderers + tests** `est:2h`
  - Why: Delivers R005 (code-gen flat graphics) — the lower-risk half of the skill. Establishes CLI pattern, all 7 Pillow renderers, manifest merge, and comprehensive tests.
  - Files: `.claude/skills/graphics-generator/` (full skill tree), `tests/test_graphics_generator/`
  - Do: Create skill with CONTEXT.md, SKILL.md, CLI (load/generate/status), 7 renderer modules (silhouette, icon, texture, glitch, noise, code_screen, profile_card), renderer registry routing building_block → function, manifest merge logic. Each renderer: `(shot_dict, output_dir) → Path`, produces 1920×1080 PNG with building block effects baked in. CLI reads shotlist.json, filters `shotlist_type == "animation"`, routes each shot to code-gen or marks as ComfyUI-pending. Manifest merge: read existing manifest.json, append new entries with `acquired_by: "agent_graphics"`, atomic temp+rename write. Use `_ensure_utf8_stdout()`, duplicate `resolve_project_dir()` from visual-orchestrator. Font fallback: try arialbd.ttf/consola.ttf → Pillow default. Generate prompt in `prompts/generation.md` for Claude to plan shot-specific generation params (colors, text content, shape descriptions). Tests: CLI tests (resolve, load output, missing files), renderer tests (output exists, is PNG, 1920×1080), manifest merge tests (append-not-overwrite, atomic write), registry routing tests.
  - Verify: `pytest tests/test_graphics_generator/ -v` — all pass; `python -m graphics_generator load "Duplessis Orphans"` exits 0
  - Done when: 7 renderers produce valid PNGs, CLI load/generate/status work, manifest merge tested, all tests green

- [x] **T02: ComfyUI client + workflow templates + tests** `est:1.5h`
  - Why: Delivers R006 (ComfyUI creative assets) — the high-risk half. Retires the primary S03 risk (ComfyUI style adherence) at mock level.
  - Files: `.claude/skills/graphics-generator/scripts/graphics_generator/comfyui/` (client.py, workflows.py), `tests/test_graphics_generator/test_comfyui.py`
  - Do: REST client (POST /prompt, GET /history/{id}, polling for completion — use requests, no websocket dep). 4 workflow templates as Python dicts (concept_diagram, ritual_illustration, glitch_icon, data_moshing) with Z-image-turbo model params. Prompt builder: shot context (narrative_context, visual_need, building_block variant) → workflow JSON with 1920×1080 resolution enforcement. `--code-gen-only` flag on generate command skips ComfyUI blocks with clear message. Wire ComfyUI blocks into renderer registry alongside Pillow blocks. Download generated image from ComfyUI output → save to assets/vectors/. Tests: mocked ComfyUI responses (queue, poll, download), workflow template validation, connection failure handling, `--code-gen-only` behavior.
  - Verify: `pytest tests/test_graphics_generator/ -v` — all tests pass including ComfyUI mocks
  - Done when: ComfyUI client queues prompts and downloads results (mocked), connection failures handled gracefully, `--code-gen-only` works, all tests green

## Files Likely Touched

- `.claude/skills/graphics-generator/CONTEXT.md`
- `.claude/skills/graphics-generator/SKILL.md`
- `.claude/skills/graphics-generator/prompts/generation.md`
- `.claude/skills/graphics-generator/scripts/graphics_generator/__init__.py`
- `.claude/skills/graphics-generator/scripts/graphics_generator/__main__.py`
- `.claude/skills/graphics-generator/scripts/graphics_generator/cli.py`
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/__init__.py`
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/silhouette.py`
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/icon.py`
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/texture.py`
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/glitch.py`
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/noise.py`
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/code_screen.py`
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/profile_card.py`
- `.claude/skills/graphics-generator/scripts/graphics_generator/comfyui/__init__.py`
- `.claude/skills/graphics-generator/scripts/graphics_generator/comfyui/client.py`
- `.claude/skills/graphics-generator/scripts/graphics_generator/comfyui/workflows.py`
- `tests/test_graphics_generator/__init__.py`
- `tests/test_graphics_generator/test_cli.py`
- `tests/test_graphics_generator/test_renderers.py`
- `tests/test_graphics_generator/test_manifest.py`
- `tests/test_graphics_generator/test_comfyui.py`
