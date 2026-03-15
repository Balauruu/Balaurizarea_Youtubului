---
id: S03
parent: M002
milestone: M002
provides:
  - Complete graphics-generator skill with CLI (load/generate/status)
  - 7 Pillow renderers producing 1920×1080 RGBA PNGs for code-gen building blocks
  - ComfyUI REST client with queue/poll/download and graceful connection failure handling
  - 4 ComfyUI workflow templates for creative building blocks (concept_diagram, ritual_illustration, glitch_icon, data_moshing)
  - Renderer registry routing building_block → code-gen or ComfyUI renderer
  - Manifest merge logic (append assets, update gaps, atomic write)
  - --code-gen-only CLI flag for offline/fallback operation
requires:
  - slice: S01
    provides: shotlist.json with building_block and shotlist_type per shot
  - slice: S02
    provides: manifest.json with gaps section identifying shots needing generation
affects:
  - S05
  - S06
key_files:
  - .claude/skills/graphics-generator/scripts/graphics_generator/cli.py
  - .claude/skills/graphics-generator/scripts/graphics_generator/renderers/__init__.py
  - .claude/skills/graphics-generator/scripts/graphics_generator/comfyui/client.py
  - .claude/skills/graphics-generator/scripts/graphics_generator/comfyui/workflows.py
  - .claude/skills/graphics-generator/scripts/graphics_generator/fonts.py
key_decisions:
  - "D016: Renderer signature contract — render(shot, output_dir) → Path for all renderers"
  - "D017: Building block routing via RENDERER_REGISTRY dict lookup — unregistered blocks return None"
  - "D018: HTTP polling via GET /history/{prompt_id} instead of websockets — avoids extra dependency"
  - "D019: Standard txt2img pipeline shared across all 4 ComfyUI workflow templates — differentiation in prompt text only"
  - "D020: ComfyUI import deferred inside cmd_generate body — avoids import errors in code-gen-only mode"
patterns_established:
  - "Renderer signature: render(shot: dict, output_dir: Path) → Path — all 7 Pillow renderers follow this"
  - "Building block routing via RENDERER_REGISTRY + COMFYUI_BLOCKS sets — clean code-gen vs ComfyUI separation"
  - "Manifest merge: read existing → dedupe by filename → append new → update gap statuses → atomic temp+rename write"
  - "ComfyUI dispatcher: render_comfyui(shot, output_dir, client) → build_prompt → select template → queue → poll → download"
  - "Workflow templates return plain dicts with string node IDs — no ComfyUI SDK dependency"
observability_surfaces:
  - "CLI stderr reports per-shot generation progress, ComfyUI connection status, skip reasons"
  - "python -m graphics_generator status shows generated/total/skipped counts per building block type"
  - "ComfyUIUnavailableError includes host:port and suggests --code-gen-only fallback"
  - "Renderer errors include shot ID, building block type, and traceback"
drill_down_paths:
  - .gsd/milestones/M002/slices/S03/tasks/T01-SUMMARY.md
  - .gsd/milestones/M002/slices/S03/tasks/T02-SUMMARY.md
duration: 55min
verification_result: passed
completed_at: 2026-03-15
---

# S03: Graphics Generator Skill

**Working graphics generator skill with 7 Pillow code-gen renderers, ComfyUI REST client with 4 workflow templates, manifest merge, and 69 passing tests.**

## What Happened

Built the complete graphics-generator skill in two tasks:

**T01** established the skill scaffold following the visual-orchestrator pattern — CONTEXT.md, SKILL.md, prompts/generation.md, CLI with load/generate/status subcommands. Created 7 Pillow renderers (silhouette, icon, texture, glitch, noise, code_screen, profile_card), each producing 1920×1080 RGBA PNGs with VISUAL_STYLE_GUIDE-faithful effects baked in (scanlines, noise, glow). Renderer registry maps building_block names to functions; unregistered blocks skip with a message. Manifest merge reads existing manifest.json, appends new entries with `acquired_by: "agent_graphics"`, updates gap statuses from pending_generation → filled, and writes atomically via temp+rename. Shared `fonts.py` module handles Windows font fallback (arialbd.ttf/consola.ttf → Pillow default).

**T02** added the ComfyUI integration layer — REST client (POST /prompt, GET /history/{id}, download) with all connection failures raising `ComfyUIUnavailableError` with the server address. 4 workflow templates (concept_diagram, ritual_illustration, glitch_icon, data_moshing) share a standard txt2img pipeline differentiated by prompt text and style modifiers. Prompt builder composes generation prompts from shot visual_need + narrative_context. `--code-gen-only` flag on generate command skips ComfyUI blocks with explicit messages. ComfyUI blocks wired into renderer registry alongside Pillow blocks via `COMFYUI_BLOCKS` set and `is_comfyui_block()` predicate.

## Verification

- `pytest tests/test_graphics_generator/ -v` — **69/69 passed** (4.35s)
  - test_cli.py: 9 tests (resolve_project_dir, cmd_load output, missing files)
  - test_renderers.py: 18 tests (PNG validity, 1920×1080 dimensions, RGBA mode, filename shot IDs, registry completeness)
  - test_manifest.py: 7 tests (create/append/dedupe/gap update/atomic write/required fields — actually 6 unique + 1 field check)
  - test_comfyui.py: 35 tests (client queue/poll/download, connection failures, workflow templates, prompt builder, registry, --code-gen-only)
- CLI `load "Duplessis Orphans"` — exits 0, prints labeled context sections
- CLI `status "Duplessis Orphans"` — exits 0, correctly reports "No animation shots in shotlist"

## Requirements Advanced

- R005 (Code-generated flat graphics) — 7 Pillow renderers producing 1920×1080 PNGs for all code-gen building blocks, contract-tested with 18 renderer tests
- R006 (ComfyUI creative asset generation) — REST client, 4 workflow templates, prompt builder, contract-tested with 35 mocked tests
- R010 (Gap lifecycle tracking) — Manifest merge updates gap status pending_generation → filled

## Requirements Validated

- None — R005 and R006 are contract-tested (mocked). Live validation deferred to S06 end-to-end integration.

## New Requirements Surfaced

- None

## Requirements Invalidated or Re-scoped

- None

## Deviations

- Added `fonts.py` as shared utility module — not in original plan as separate file, but cleaner than duplicating font logic across 7 renderers
- "Static Noise" registered as alias alongside "Static Noise / Corruption" — both forms appear in shotlists
- Added `graphics-generator/scripts` to `pytest.ini` pythonpath — was missing from original plan

## Known Limitations

- Current Duplessis Orphans shotlist has only 1 shot (archival_video type) — no animation shots to exercise the full generate path. Live end-to-end deferred to S06.
- Noise renderer uses Python-level pixel iteration (slow for 1920×1080) — could be optimized with numpy but works correctly
- Phosphor glow in code_screen samples every 3rd pixel for performance — visual effect is acceptable
- ComfyUI tested only with mocks — live ComfyUI server verification deferred to S06
- `python -m graphics_generator` requires PYTHONPATH set to `.claude/skills/graphics-generator/scripts` — consistent with other skills but worth noting

## Follow-ups

- S05 (Asset Manager) consumes generated assets in `assets/vectors/` and manifest.json entries with `acquired_by: "agent_graphics"`
- S06 must test with a shotlist containing animation-type shots to exercise both Pillow and ComfyUI paths end-to-end

## Files Created/Modified

- `.claude/skills/graphics-generator/CONTEXT.md` — Stage contract
- `.claude/skills/graphics-generator/SKILL.md` — Usage guide with building block mapping table
- `.claude/skills/graphics-generator/prompts/generation.md` — Prompt for Claude to plan shot-specific params
- `.claude/skills/graphics-generator/scripts/graphics_generator/__init__.py` — Package init
- `.claude/skills/graphics-generator/scripts/graphics_generator/__main__.py` — Module entry point
- `.claude/skills/graphics-generator/scripts/graphics_generator/cli.py` — CLI with load/generate/status + --code-gen-only
- `.claude/skills/graphics-generator/scripts/graphics_generator/fonts.py` — Font loading with Windows fallback
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/__init__.py` — Registry + ComfyUI routing
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/silhouette.py` — Silhouette Figure renderer
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/icon.py` — Symbolic Icon renderer
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/texture.py` — Abstract Texture renderer
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/glitch.py` — Glitch Stinger renderer
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/noise.py` — Static Noise renderer
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/code_screen.py` — Retro Code Screen renderer
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/profile_card.py` — Character Profile Card renderer
- `.claude/skills/graphics-generator/scripts/graphics_generator/comfyui/__init__.py` — ComfyUI package init
- `.claude/skills/graphics-generator/scripts/graphics_generator/comfyui/client.py` — REST client
- `.claude/skills/graphics-generator/scripts/graphics_generator/comfyui/workflows.py` — 4 workflow templates + prompt builder
- `tests/test_graphics_generator/__init__.py` — Test package init
- `tests/test_graphics_generator/test_cli.py` — 9 CLI tests
- `tests/test_graphics_generator/test_renderers.py` — 18 renderer tests
- `tests/test_graphics_generator/test_manifest.py` — 7 manifest merge tests
- `tests/test_graphics_generator/test_comfyui.py` — 35 ComfyUI tests
- `pytest.ini` — Added graphics-generator scripts to pythonpath

## Forward Intelligence

### What the next slice should know
- Graphics generator writes to `assets/vectors/` with filenames like `S042_silhouette_figure.png` — Asset Manager (S05) must look there
- Manifest entries from this skill have `acquired_by: "agent_graphics"` and `source: "code_gen"` or `source: "comfyui"`
- The renderer registry pattern (`RENDERER_REGISTRY` dict) is extensible — S04 animation skill could follow the same pattern if needed

### What's fragile
- Noise and code_screen renderers are CPU-heavy at 1920×1080 — if batch generation is slow, these are the bottleneck
- ComfyUI workflow templates assume Z-image-turbo checkpoint name — must match the actual model file on the ComfyUI server

### Authoritative diagnostics
- `pytest tests/test_graphics_generator/ -v` — 69 tests covering all code paths
- `python -c "import sys; sys.path.insert(0, '.claude/skills/graphics-generator/scripts'); from graphics_generator.cli import cmd_status; cmd_status('Duplessis Orphans')"` — live status check

### What assumptions changed
- Original plan assumed 6 manifest tests — actually 7 (added required-fields check)
- Building block name "Static Noise / Corruption" also appears as "Static Noise" in shotlists — both aliases registered
