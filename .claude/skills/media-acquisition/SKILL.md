# Media Acquisition Skill — Usage Guide

## Overview

The media acquisition skill downloads assets from free sources (Wikimedia, Archive.org, Pexels, etc.) and produces `manifest.json` — the central coordination artifact consumed by graphics (S03), animation (S04), and asset manager (S05) skills.

This is a **[HEURISTIC]** skill: Claude plans search queries and shot mappings; the CLI handles downloads, validation, and manifest bookkeeping.

## Prerequisites

- `shotlist.json` in the project directory (from visual-orchestrator skill)
- `research/media_urls.md` in the project directory (from researcher skill)
- `context/channel/channel.md` in the project root

## CLI Commands

### Load Context

Aggregates shotlist.json + media_urls.md + channel.md and prints to stdout for Claude to plan search queries.

```bash
PYTHONPATH=.claude/skills/media-acquisition/scripts python -m media_acquisition load "Duplessis Orphans"
```

### Check Status

Reads manifest.json and prints gap analysis summary with coverage stats.

```bash
PYTHONPATH=.claude/skills/media-acquisition/scripts python -m media_acquisition status "Duplessis Orphans"
```

Output includes:
- Total assets and covered shots
- Gap count with status breakdown (pending_generation / filled / unfilled)
- Coverage percentage
- Per-source download summary

## Schema Validation

Validate manifest.json programmatically:

```python
from media_acquisition.schema import validate_manifest
import json

data = json.loads(Path("manifest.json").read_text())
errors = validate_manifest(data)
if errors:
    for e in errors:
        print(f"  {e}")
```

## manifest.json Contract

### Top-Level Keys (all required)
- `project` — Project name string
- `generated` — ISO 8601 timestamp of initial creation
- `updated` — ISO 8601 timestamp of last modification
- `assets` — Array of acquired asset records
- `gaps` — Array of unresolved shot needs
- `source_summary` — Per-source search/download counts

### Asset Record
```json
{
  "filename": "maurice_duplessis_1938.png",
  "folder": "archival_photos",
  "source": "wikimedia_commons",
  "source_url": "https://upload.wikimedia.org/...",
  "description": "Portrait of Maurice Duplessis, 1938",
  "license": "Public domain",
  "mapped_shots": ["S003", "S005"],
  "acquired_by": "agent_acquisition"
}
```

### Gap Record
```json
{
  "shot_id": "S012",
  "visual_need": "Interior of institution, 1950s",
  "shotlist_type": "archival_photo",
  "status": "pending_generation"
}
```

### Valid Values
- **Folders:** `archival_photos`, `archival_footage`, `documents`, `broll`, `vectors`, `animations`
- **Gap statuses:** `pending_generation`, `filled`, `unfilled`
- **Shot ID format:** `S001` through `S999`

## Stage Contract

See `CONTEXT.md` for the full stage contract (inputs, process, checkpoints, outputs).
