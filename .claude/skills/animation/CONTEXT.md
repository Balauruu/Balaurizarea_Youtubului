# Animation Skill — Stage Contract

## Purpose

Renders animated map clips (.mp4) from shotlist.json entries with `shotlist_type == "map"` using Remotion (Node.js) via Python subprocess orchestration.

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| `shotlist.json` | `projects/N/shotlist.json` | Yes |
| `manifest.json` | `projects/N/assets/manifest.json` | No (created if missing) |
| `channel.md` | `context/channel/channel.md` | Yes (for `load` command) |
| Remotion project | `.claude/skills/animation/remotion/` | Yes (for `render` command) |

## Process

1. **Filter** — Extract shots where `shotlist_type == "map"` from shotlist.json
2. **Map props** — Convert each shot's `building_block` to a Remotion variant, extract locations and connections, set duration
3. **Render** — Write per-shot `props.json` to temp file, invoke `npx remotion render` via subprocess with `cwd` set to Remotion project
4. **Merge manifest** — Append rendered clips to `manifest.json` with `acquired_by: "agent_animation"` and `folder: "animations"`, transition gaps from `pending_generation → filled`

## Outputs

| Output | Location |
|--------|----------|
| Animated .mp4 clips | `projects/N/assets/animations/{shot_id}_{slug}.mp4` |
| Updated manifest | `projects/N/assets/manifest.json` |

## Variant Mapping

| Building Block | Remotion Variant |
|---------------|-----------------|
| Illustrated Map | `illustrated-map` |
| 3D Geographic Visualization | `3d-geographic` |
| Region Highlight Map | `region-highlight` |
| Connection/Arc Map | `connection-arc` |

## Checkpoints

- `load` exits 0 and prints MAP_SHOTS, MANIFEST, CHANNEL_DNA sections
- `render` produces .mp4 files and updates manifest.json
- `status` shows coverage percentage (rendered / total map shots)

## Error Handling

- Missing shotlist.json → exit 1 with path in stderr
- No map shots → exit 0 with informational message
- Remotion render failure → stderr includes shot ID and Remotion error output
- Subprocess timeout → 120s per shot, failure logged with shot ID
