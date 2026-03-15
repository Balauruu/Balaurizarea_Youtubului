# Asset Manager Skill

## What It Does

Organizes project assets by assigning sequential numeric prefixes based on shotlist order. This is the final consolidation step before editor handoff — assets get numbered for timeline assembly order.

## Commands

### Load Context
```bash
PYTHONPATH=".claude/skills/asset-manager/scripts;.claude/skills/media-acquisition/scripts" python -m asset_manager load "Topic Name"
```
Prints SHOTLIST, MANIFEST, and CHANNEL_DNA sections to stdout for Claude to consume.

### Organize Assets
```bash
PYTHONPATH=".claude/skills/asset-manager/scripts;.claude/skills/media-acquisition/scripts" python -m asset_manager organize "Topic Name"
```
- Reads shotlist.json for shot ordering
- Assigns `001_`, `002_`, ... prefixes based on first appearance in shotlist
- Renames files in-place within their type folders
- Moves unmapped assets to `_pool/`
- Sets remaining `pending_generation` gaps to `unfilled`
- Writes updated manifest.json (atomic)

### Check Status
```bash
PYTHONPATH=".claude/skills/asset-manager/scripts;.claude/skills/media-acquisition/scripts" python -m asset_manager status "Topic Name"
```
Reports: total assets, numbered count, unnumbered count, pool count, gap summary.

## Numbering Rules

- Number = shot's position in shotlist.json (1-based)
- Asset mapped to multiple shots → gets earliest shot's number
- Multiple assets on same shot → all share the prefix
- Format: `NNN_originalname.ext` (3-digit zero-padded)
- Idempotent: re-running strips existing `NNN_` prefix first

## Dependencies

- Imports `validate_manifest` from `media_acquisition.schema` — requires media-acquisition scripts on PYTHONPATH
