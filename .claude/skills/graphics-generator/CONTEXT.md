# Graphics Generator Skill — Stage Contract

**Phase:** 16 — Graphics Generator Agent
**Skill:** graphics-generator
**Type:** [HYBRID] — CLI routes shots to code-gen (Pillow) or ComfyUI renderers; Claude plans shot-specific params via generation prompt

---

## Inputs

| File | Source | Required |
|------|--------|----------|
| `projects/N. [Title]/shotlist.json` | visual-orchestrator skill | Yes |
| `projects/N. [Title]/assets/manifest.json` | media-acquisition skill | No (created if absent) |
| `context/channel/channel.md` | project context | Yes |

---

## Process

1. **CLI aggregation** (`python -m graphics_generator load "[topic]"`)
   - Resolves project directory by case-insensitive substring match on `projects/`
   - Reads shotlist.json, manifest.json (if exists), channel.md
   - Prints labeled context package to stdout
   - Prints generation prompt path

2. **Claude reads generation prompt** (`.claude/skills/graphics-generator/prompts/generation.md`)
   - Reviews animation shots and their building blocks
   - Plans shot-specific visual params (colors, text, shapes) for each renderer

3. **Generation** (`python -m graphics_generator generate "[topic]"`)
   - Reads shotlist.json, filters `shotlist_type == "animation"` shots
   - Routes each shot to the appropriate renderer by `building_block` lookup
   - Produces 1920×1080 RGBA PNGs in `assets/vectors/`
   - Updates manifest.json with new asset entries and gap status changes
   - Skips ComfyUI blocks with a message (until T02 wires them)

4. **Status check** (`python -m graphics_generator status "[topic]"`)
   - Reads manifest.json and shotlist.json
   - Prints generation coverage stats (generated/total/skipped per building block type)

---

## Checkpoints

**Automated:** Run `python -m graphics_generator status "[topic]"` after generation. Check coverage percentage.

**Human review:** Review generated PNGs for visual quality. Code-gen produces building-block-faithful assets, not creative masterpieces.

---

## Outputs

| File | Location | Description |
|------|----------|-------------|
| `*.png` | `projects/N. [Title]/assets/vectors/` | Generated 1920×1080 RGBA PNGs per animation shot |
| `manifest.json` | `projects/N. [Title]/assets/manifest.json` | Updated with new asset entries, gaps marked filled |

---

## Deferred

- **GFX-01:** ComfyUI integration for creative building blocks (T02)
- **GFX-02:** Shot-specific param planning via Claude heuristic pass
- **GFX-03:** Batch rendering with progress bar for large shotlists
