# Visual Orchestrator Skill

Transforms Script.md + VISUAL_STYLE_GUIDE.md into a structured `shotlist.json` — an ordered sequence of visual decisions with building block assignments and downstream routing types.

## Quick Start

### 1. Load context for generation

```bash
PYTHONPATH=.claude/skills/visual-orchestrator/scripts python -m visual_orchestrator load "Duplessis Orphans"
```

This prints the script, visual style guide, and channel DNA as labeled sections, plus the output path and generation prompt path.

**With a specific guide:**

```bash
PYTHONPATH=.claude/skills/visual-orchestrator/scripts python -m visual_orchestrator load "Duplessis Orphans" --guide "Mexico's Most Disturbing Cult"
```

### 2. Generate shotlist.json

After running `load`, Claude reads the generation prompt at `.claude/skills/visual-orchestrator/prompts/generation.md` and generates `shotlist.json` in the project directory.

### 3. Validate the output

```bash
PYTHONPATH=.claude/skills/visual-orchestrator/scripts python -m visual_orchestrator validate "Duplessis Orphans"
```

Exits 0 with a success message if valid. Exits 1 with a numbered error list if validation fails.

## Subcommands

### `load <topic> [--guide NAME]`

Aggregates context files and prints them to stdout for Claude to consume.

**Arguments:**
- `topic` — Topic string used to find the project directory (case-insensitive substring match)
- `--guide` — (Optional) Name of the visual reference directory to use. Defaults to the first directory found in `context/visual-references/`.

**Output sections:**
- `=== Script ===` — Full Script.md content
- `=== Visual Style Guide (Guide Name) ===` — Full VISUAL_STYLE_GUIDE.md content
- `=== Channel DNA ===` — Full channel.md content
- `Output path:` — Where shotlist.json should be written
- `Generation prompt:` — Path to the generation prompt

**Exit codes:**
- `0` — Success
- `1` — Required file missing (prints missing paths to stderr)

### `validate <topic>`

Reads shotlist.json from the project directory and validates it against the schema contract.

**Checks performed:**
- Required top-level keys (`project`, `guide_source`, `generated`, `shots`)
- Required per-shot fields (`id`, `chapter`, `chapter_title`, `narrative_context`, `visual_need`, `building_block`, `shotlist_type`)
- ID format (S001-S999, sequential)
- Valid `shotlist_type` enum values
- `text_content` populated iff `shotlist_type` is `text_overlay`
- Sequencing constraints (no back-to-back glitch, max 3 consecutive text_overlay, max 3 consecutive Silhouette Figure)

**Exit codes:**
- `0` — Valid shotlist
- `1` — Validation errors (prints numbered error list to stderr)

## Schema Contract

The `shotlist.json` schema is the stable contract for all downstream skills:
- **Media acquisition** reads shots with `shotlist_type: archival_video | archival_photo | document_scan`
- **Graphics agent** reads shots with `shotlist_type: animation | map`
- **Text overlays** (`shotlist_type: text_overlay`) generate no assets — they guide editorial placement

See `prompts/generation.md` for the full schema specification.
