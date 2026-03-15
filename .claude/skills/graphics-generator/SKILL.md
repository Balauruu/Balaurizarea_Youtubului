# Graphics Generator Skill

Produces code-gen flat graphics (Pillow) for all `shotlist_type: animation` shots, updating manifest.json with asset entries. Routes building blocks to specialized renderers that produce 1920×1080 RGBA PNGs with visual effects from the VISUAL_STYLE_GUIDE.

## Quick Start

### 1. Load context for planning

```bash
PYTHONPATH=.claude/skills/graphics-generator/scripts python -m graphics_generator load "Duplessis Orphans"
```

Prints shotlist.json, manifest.json (if exists), and channel DNA as labeled sections.

### 2. Generate assets

```bash
PYTHONPATH=.claude/skills/graphics-generator/scripts python -m graphics_generator generate "Duplessis Orphans"
```

Filters animation shots, routes each to the matching Pillow renderer, writes PNGs to `assets/vectors/`, and updates manifest.json.

### 3. Check coverage

```bash
PYTHONPATH=.claude/skills/graphics-generator/scripts python -m graphics_generator status "Duplessis Orphans"
```

Shows generated/total/skipped counts per building block type.

## Subcommands

### `load <topic>`

Aggregates shotlist.json + manifest.json + channel.md into labeled context for Claude.

**Arguments:**
- `topic` — Topic string (case-insensitive substring match on `projects/`)

**Exit codes:**
- `0` — Success, context printed to stdout
- `1` — Required file missing (error printed to stderr)

### `generate <topic>`

Routes each animation shot to its renderer and produces PNG files.

**Arguments:**
- `topic` — Topic string

**Behavior:**
- Filters shots where `shotlist_type == "animation"`
- Looks up `building_block` in renderer registry
- Produces `{shot_id}_{building_block_slug}.png` in `assets/vectors/`
- Updates manifest.json: appends asset entries, marks matching gaps as `filled`
- Skips unregistered building blocks (ComfyUI blocks) with a stderr message

**Exit codes:**
- `0` — All routable shots generated
- `1` — Shotlist missing or generation errors

### `status <topic>`

Prints coverage summary from manifest.json and shotlist.json.

**Arguments:**
- `topic` — Topic string

**Exit codes:**
- `0` — Status printed
- `1` — Required files missing

## Building Block → Renderer Mapping

| Building Block | Renderer | Type |
|----------------|----------|------|
| Silhouette Figure | `silhouette.py` | Pillow |
| Symbolic Icon | `icon.py` | Pillow |
| Abstract Texture | `texture.py` | Pillow |
| Glitch Stinger | `glitch.py` | Pillow |
| Static Noise / Corruption | `noise.py` | Pillow |
| Retro Code Screen | `code_screen.py` | Pillow |
| Character Profile Card | `profile_card.py` | Pillow |
| Concept Diagram | *(ComfyUI — T02)* | Skip |
| Ritual Illustration | *(ComfyUI — T02)* | Skip |
| Glitch Icon | *(ComfyUI — T02)* | Skip |
| Data Moshing Montage | *(ComfyUI — T02)* | Skip |
| Location Map | *(ComfyUI — T02)* | Skip |

## File Naming

Output files follow: `{shot_id}_{building_block_slug}.png`
Example: `S042_silhouette_figure.png`

The slug is the building block name lowercased with spaces replaced by underscores.
