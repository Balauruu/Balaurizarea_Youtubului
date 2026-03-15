# Animation Skill

Renders animated map clips (.mp4) from shotlist.json map entries using Remotion.

## Prerequisites

- Python 3.10+
- Node.js 18+ (for Remotion)
- Remotion project installed: `cd .claude/skills/animation/remotion && npm install`

## Usage

All commands use PYTHONPATH to locate the package:

```bash
# Set PYTHONPATH for all commands
export PYTHONPATH=.claude/skills/animation/scripts

# Load context — shows map shots, manifest state, and channel DNA
python -m animation load "Duplessis Orphans"

# Render map shots to .mp4 clips
python -m animation render "Duplessis Orphans"

# Check coverage stats
python -m animation status "Duplessis Orphans"
```

## Commands

### `load <topic>`

Aggregates context files filtered to map-type shots only. Prints three labeled sections to stdout:

- **MAP_SHOTS** — Filtered shotlist entries where `shotlist_type == "map"`
- **MANIFEST** — Current manifest.json (or placeholder if none exists)
- **CHANNEL_DNA** — Channel voice and style reference

### `render <topic>`

For each map shot in shotlist.json:

1. Maps `building_block` to Remotion variant (illustrated-map, 3d-geographic, region-highlight, connection-arc)
2. Extracts location/connection data from shot fields
3. Writes props.json and invokes `npx remotion render` via subprocess
4. Saves .mp4 to `projects/N/assets/animations/`
5. Updates manifest.json with `acquired_by: "agent_animation"` entries

### `status <topic>`

Prints coverage summary:
- Total shots vs map shots
- Breakdown by building block → variant mapping
- Rendered file count and manifest entry count
- Coverage percentage

## Shotlist Requirements

Map shots in shotlist.json must have:
- `shotlist_type: "map"` — required for filtering
- `building_block` — maps to Remotion variant
- `visual_need` — used as animation title
- `narrative_context` — used for context
- `locations` (optional) — array of `{name, x, y}` with normalized 0-1 coords

## Output Structure

```
projects/N/
  assets/
    animations/
      S001_illustrated_map.mp4
      S005_connection_arc.mp4
    manifest.json  (updated with animation entries)
```

## Diagnostics

- Render failures print shot ID and Remotion stderr to stderr
- `status` command shows gap between expected and rendered shots
- Manifest entries tagged with `acquired_by: "agent_animation"` for traceability
