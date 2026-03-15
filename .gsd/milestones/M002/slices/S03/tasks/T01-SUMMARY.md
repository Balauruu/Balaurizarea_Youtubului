---
id: T01
parent: S03
milestone: M002
provides:
  - Complete graphics-generator skill with CLI (load/generate/status)
  - 7 Pillow renderers producing 1920×1080 RGBA PNGs for code-gen building blocks
  - Renderer registry routing building_block → renderer function
  - Manifest merge logic (append assets, update gaps, atomic write)
  - Font fallback utility (Windows fonts → Pillow default)
key_files:
  - .claude/skills/graphics-generator/scripts/graphics_generator/cli.py
  - .claude/skills/graphics-generator/scripts/graphics_generator/renderers/__init__.py
  - .claude/skills/graphics-generator/scripts/graphics_generator/fonts.py
key_decisions:
  - "Static Noise" registered as alias for "Static Noise / Corruption" in renderer registry — both forms appear in shotlists
  - Renderers use deterministic random seeds for reproducible output (fog, streaks, noise positions)
  - Phosphor glow on code_screen samples every 3rd pixel for performance — full iteration was too slow for 1920×1080
patterns_established:
  - "Renderer signature: render(shot: dict, output_dir: Path) → Path — all 7 renderers follow this contract"
  - "Building block routing via RENDERER_REGISTRY dict lookup — unregistered blocks return None (ComfyUI skip)"
  - "Manifest merge pattern: read existing → dedupe by filename → append new → update gap statuses → atomic temp+rename write"
observability_surfaces:
  - "CLI stderr prints per-shot progress: 'Generating S042 (silhouette_figure)...'"
  - "Skip messages for ComfyUI blocks: 'Skipping S042 (Concept Diagram) — no Pillow renderer'"
  - "python -m graphics_generator status shows generated/total/skipped counts"
  - "Renderer errors include shot ID, building block type, and traceback"
duration: 30min
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: CLI scaffold + Pillow code-gen renderers + tests

**Built complete graphics-generator skill with 7 Pillow renderers (silhouette, icon, texture, glitch, noise, code_screen, profile_card), CLI with load/generate/status subcommands, manifest merge logic, and 34 passing tests.**

## What Happened

Created the full skill tree at `.claude/skills/graphics-generator/` following the visual-orchestrator pattern exactly:
- CONTEXT.md (stage contract), SKILL.md (usage guide), prompts/generation.md (shot-specific param planning prompt)
- CLI with `resolve_project_dir()` and `_ensure_utf8_stdout()` duplicated from visual-orchestrator
- `load` aggregates shotlist.json + manifest.json + channel.md into labeled stdout context
- `generate` filters animation shots, routes to renderers by building_block lookup, produces PNGs, merges manifest
- `status` shows per-building-block coverage stats

7 Pillow renderers, each producing 1920×1080 RGBA PNG with VISUAL_STYLE_GUIDE-faithful effects:
- **silhouette**: Deep red gradient, black geometric humanoid (head circle + body trapezoid), fog overlay, scanlines, optional label
- **icon**: Crimson background, scanline texture, centered diamond icon silhouette, bold label
- **texture**: Crimson background, random dark vertical streaks/drips via ImageDraw, heavy scanlines
- **glitch**: Black background, vertical red bars, horizontal scanline distortion bands, RGB channel split
- **noise**: Full-frame random noise via pixel iteration, faint dark building silhouette blended
- **code_screen**: Black CRT, monospaced BASIC code text, phosphor glow via blur+composite, scanlines
- **profile_card**: Dark background, vertical magenta accent bars, placeholder photo rectangles with teal labels

Renderer registry maps building_block names → functions. ComfyUI blocks (Concept Diagram, Ritual Illustration, etc.) are not registered — CLI skips them with a message.

Manifest merge reads existing manifest.json, appends new asset entries with proper S02-schema fields (folder: "vectors", source: "code_gen", acquired_by: "agent_graphics"), updates gap statuses from pending_generation → filled, writes atomically via temp+rename.

## Verification

- `pytest tests/test_graphics_generator/ -v` — **34/34 passed** (4.19s)
  - test_cli.py: 9 tests (resolve_project_dir, cmd_load output, missing files)
  - test_renderers.py: 18 tests (each renderer produces valid PNG, correct 1920×1080 dimensions, RGBA mode, filename includes shot ID, registry completeness)
  - test_manifest.py: 7 tests (create when absent, append without overwrite, skip duplicates, gap status update, atomic write, required fields)
- `python -m graphics_generator load "Duplessis Orphans"` — exits 0, prints labeled Shotlist/Manifest/Channel DNA sections
- `python -m graphics_generator status "Duplessis Orphans"` — exits 0, correctly reports "No animation shots in shotlist" for current 1-shot shotlist

**Slice-level verification (partial — T01 of 2):**
- ✅ `pytest tests/test_graphics_generator/ -v` — all pass
- ✅ CLI resolution, renderer output, manifest merge covered
- ⬜ ComfyUI client with mocked responses — T02
- ✅ `python -m graphics_generator status "Duplessis Orphans"` — exits 0

## Diagnostics

- Run `python -m graphics_generator status "<topic>"` to see generation coverage
- CLI stderr shows per-shot progress during generate
- Renderer errors include shot ID and building block type for debugging
- Manifest merge is atomic — interrupted writes won't corrupt manifest.json

## Deviations

- Added `fonts.py` as a shared utility module (not in original plan as a separate file, but cleaner than duplicating font logic in 7 renderers)
- "Static Noise" registered as alias alongside "Static Noise / Corruption" — the schema.py lists both forms

## Known Issues

- The phosphor glow in code_screen.py samples every 3rd pixel for performance — full pixel iteration at 1920×1080 was slow. Visual effect is acceptable.
- Noise renderer uses Python-level pixel iteration (slow for 1920×1080) — could be optimized with numpy in the future but works correctly now.

## Files Created/Modified

- `.claude/skills/graphics-generator/CONTEXT.md` — Stage contract
- `.claude/skills/graphics-generator/SKILL.md` — Usage guide with building block mapping table
- `.claude/skills/graphics-generator/prompts/generation.md` — Prompt for Claude to plan shot-specific params
- `.claude/skills/graphics-generator/scripts/graphics_generator/__init__.py` — Package init
- `.claude/skills/graphics-generator/scripts/graphics_generator/__main__.py` — Module entry point
- `.claude/skills/graphics-generator/scripts/graphics_generator/cli.py` — CLI with load/generate/status subcommands
- `.claude/skills/graphics-generator/scripts/graphics_generator/fonts.py` — Font loading utilities with Windows fallback
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/__init__.py` — Registry mapping building blocks → renderers
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/silhouette.py` — Silhouette Figure renderer
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/icon.py` — Symbolic Icon renderer
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/texture.py` — Abstract Texture renderer
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/glitch.py` — Glitch Stinger renderer
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/noise.py` — Static Noise renderer
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/code_screen.py` — Retro Code Screen renderer
- `.claude/skills/graphics-generator/scripts/graphics_generator/renderers/profile_card.py` — Character Profile Card renderer
- `tests/test_graphics_generator/__init__.py` — Test package init
- `tests/test_graphics_generator/test_cli.py` — CLI tests (9 tests)
- `tests/test_graphics_generator/test_renderers.py` — Renderer tests (18 tests)
- `tests/test_graphics_generator/test_manifest.py` — Manifest merge tests (7 tests)
