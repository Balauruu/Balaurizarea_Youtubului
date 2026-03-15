---
estimated_steps: 8
estimated_files: 18
---

# T01: CLI scaffold + Pillow code-gen renderers + tests

**Slice:** S03 — Graphics Generator Skill
**Milestone:** M002

## Description

Build the complete graphics generator skill with CLI scaffold, 7 Pillow renderers for code-gen building blocks, manifest merge logic, and comprehensive tests. This delivers R005 (code-gen flat graphics) and establishes the skill structure that T02 extends with ComfyUI.

## Steps

1. Create skill structure: `CONTEXT.md` (stage contract), `SKILL.md` (usage guide), `prompts/generation.md` (prompt for Claude to plan shot-specific params like colors, text, shapes). Follow visual-orchestrator patterns exactly.
2. Create CLI (`cli.py`, `__main__.py`, `__init__.py`): `load` aggregates shotlist.json + manifest.json + channel.md into labeled context for Claude. `generate` reads shotlist, filters `shotlist_type == "animation"`, routes each shot to renderer by building_block lookup. `status` shows coverage stats. Duplicate `resolve_project_dir()` and `_ensure_utf8_stdout()` from visual-orchestrator.
3. Create renderer registry (`renderers/__init__.py`): dict mapping building_block names → renderer functions. Code-gen blocks route to Pillow renderers. ComfyUI blocks return a sentinel/skip (wired in T02). Each renderer signature: `render(shot: dict, output_dir: Path) → Path`.
4. Implement 7 Pillow renderers, each producing 1920×1080 RGBA PNG:
   - `silhouette.py`: Deep red gradient background, black geometric humanoid silhouette (head circle + body trapezoid), optional white label text, subtle fog overlay
   - `icon.py`: Crimson background with scanline texture, centered geometric icon silhouette, bold label
   - `texture.py`: Crimson background, random dark vertical streaks/drips via ImageDraw, heavy scanline overlay
   - `glitch.py`: Black background, vertical red bars, horizontal scanline distortion bands, RGB channel split effect
   - `noise.py`: Full-frame random noise via numpy or random pixel iteration, faint dark silhouette shape blended
   - `code_screen.py`: Black background, white monospaced text (Consolas/fallback), phosphor glow effect via blur+composite, scanlines
   - `profile_card.py`: Dark background, vertical magenta accent bars, placeholder photo regions as black rectangles with teal text labels
5. Font handling: try loading `arialbd.ttf`, `consola.ttf` from Windows font dir → fallback to `ImageFont.load_default()`. Wrap in utility function.
6. Implement manifest merge in CLI: read existing `assets/manifest.json` (if any), append new asset entries with fields per S02 schema (`filename`, `folder: "vectors"`, `source: "code_gen"`, `source_url: "local://graphics_generator/{block}"`, `description`, `license: "generated"`, `mapped_shots: [shot_id]`, `acquired_by: "agent_graphics"`). Update gaps matching generated shot IDs: `pending_generation → filled`. Atomic write via temp file + rename.
7. Write tests in `tests/test_graphics_generator/`:
   - `test_cli.py`: resolve_project_dir, cmd_load stdout content, missing file errors (mirror visual-orchestrator test patterns)
   - `test_renderers.py`: Each renderer produces a file, file is valid PNG, dimensions are 1920×1080 (use PIL.Image.open to verify). Use tmp_path fixture for output.
   - `test_manifest.py`: Merge appends (doesn't overwrite existing assets), gap status update, atomic write produces valid JSON
8. Ensure `python -m graphics_generator load "Duplessis Orphans"` runs without error (live smoke test).

## Must-Haves

- [ ] CLI with load/generate/status subcommands following D002 pattern
- [ ] 7 Pillow renderers each producing valid 1920×1080 PNG
- [ ] Building block effects (scanlines, noise, glow) rendered into assets per VISUAL_STYLE_GUIDE
- [ ] Manifest merge: append assets, update gaps, atomic write
- [ ] Filenames include shot ID (`S042_silhouette_figure.png`)
- [ ] Font fallback (Windows fonts → Pillow default)
- [ ] Tests cover CLI, all renderers, and manifest merge

## Verification

- `pytest tests/test_graphics_generator/test_cli.py tests/test_graphics_generator/test_renderers.py tests/test_graphics_generator/test_manifest.py -v` — all pass
- `python -m graphics_generator load "Duplessis Orphans"` — exits 0, prints labeled sections

## Observability Impact

- Signals added: CLI stderr prints per-shot progress (`Generating S042 (silhouette_figure)...`), skip messages for ComfyUI blocks
- How a future agent inspects: `python -m graphics_generator status "<topic>"` shows generated/total/skipped counts
- Failure state exposed: renderer errors include shot ID, building block type, and traceback

## Inputs

- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/cli.py` — CLI pattern to duplicate
- `.claude/skills/visual-orchestrator/scripts/visual_orchestrator/schema.py` — shotlist schema (VALID_SHOTLIST_TYPES, REQUIRED_SHOT_FIELDS)
- `.claude/skills/media-acquisition/scripts/media_acquisition/schema.py` — manifest schema (REQUIRED_ASSET_FIELDS, VALID_FOLDERS)
- `context/visual-references/Mexico's Most Disturbing Cult/VISUAL_STYLE_GUIDE.md` — Building block production specs
- S01 forward intelligence: shotlist_type filtering, building_block field usage

## Expected Output

- `.claude/skills/graphics-generator/` — Complete skill with CONTEXT.md, SKILL.md, prompts/, scripts/
- `tests/test_graphics_generator/` — test_cli.py, test_renderers.py, test_manifest.py (all green)
- Renderers produce actual PNG files with building block visual effects baked in
