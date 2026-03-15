# Asset Manager Skill — Stage Contract

## Purpose

Final consolidation step in the asset pipeline. Reads shotlist.json for shot ordering and manifest.json for asset-to-shot mappings, then assigns sequential numeric prefixes (`001_`, `002_`, ...) to all mapped assets, moves unmapped assets to `_pool/`, finalizes remaining gaps to terminal status, and produces a schema-valid manifest.

## Inputs

| Input | Source | Required |
|-------|--------|----------|
| `shotlist.json` | `projects/N/shotlist.json` | Yes |
| `manifest.json` | `projects/N/assets/manifest.json` | Yes |
| `channel.md` | `context/channel/channel.md` | Yes (for `load` command) |
| Type folders | `projects/N/assets/{archival_photos,archival_footage,documents,broll,vectors,animations}/` | Yes |

## Process

1. **Load** — Read shotlist.json for shot ordering and manifest.json for asset entries
2. **Validate** — Run `validate_manifest()` on current manifest (pre-check)
3. **Compute numbering** — For each asset, find earliest mapped shot in shotlist order → assign that sequence number as `NNN_` prefix
4. **Rename** — Strip any existing `\d{3}_` prefix (idempotency), then prepend new prefix. Rename in-place within type folders
5. **Pool unmapped** — Move assets with no `mapped_shots` to `_pool/` directory and remove from manifest assets array
6. **Finalize gaps** — Set remaining `pending_generation` gaps to `unfilled` terminal status
7. **Validate & write** — Run `validate_manifest()` on result, atomic write via temp+replace

## Outputs

| Output | Location |
|--------|----------|
| Numbered asset files | `projects/N/assets/{folder}/NNN_filename.ext` |
| Unmapped assets | `projects/N/assets/_pool/` |
| Updated manifest | `projects/N/assets/manifest.json` |

## Checkpoints

- `load` exits 0 and prints SHOTLIST, MANIFEST, CHANNEL_DNA sections
- `organize` renames files, moves unmapped to `_pool/`, updates manifest, exits 0
- `status` shows numbered/unnumbered/pool counts and gap breakdown
- Manifest passes `validate_manifest()` after organize

## Numbering Rules

- Sequence number = 1-based position of the shot in shotlist.json `shots` array
- Asset mapped to multiple shots → uses the **earliest** shot's sequence number
- Multiple assets on the same shot → all get the **same** prefix
- Prefix format: `NNN_` (zero-padded to 3 digits)
- Cross-folder: numbering is global across all type folders

## Error Handling

- Missing shotlist.json or manifest.json → exit 1 with path in stderr
- Pre-organize manifest validation failure → exit 1 with errors in stderr
- Post-organize manifest validation failure → manifest NOT written, exit 1
- File rename failure → logged to stderr with source/target paths
