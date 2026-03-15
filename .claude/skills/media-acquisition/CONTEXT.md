# Media Acquisition Skill — Stage Contract

**Phase:** 15 — Media Acquisition Agent
**Skill:** media-acquisition
**Type:** [HEURISTIC] — Claude plans search queries and shot mappings; CLI handles downloads, validation, and manifest bookkeeping

---

## Inputs

| File | Source | Required |
|------|--------|----------|
| `projects/N. [Title]/shotlist.json` | visual-orchestrator skill | Yes |
| `projects/N. [Title]/research/media_urls.md` | researcher skill | Yes |
| `context/channel/channel.md` | project context | Yes |

---

## Process

1. **CLI aggregation** (`python -m media_acquisition load "[topic]"`)
   - Resolves project directory by case-insensitive substring match on `projects/`
   - Reads shotlist.json, media_urls.md, channel.md
   - Prints labeled context package to stdout
   - Prints project paths (assets directory, manifest path)

2. **Claude plans search queries** (the [HEURISTIC] part)
   - Reviews shotlist visual_need entries
   - Maps media_urls.md entries to shots
   - Generates search plan JSON with per-source queries

3. **Acquisition** (`python -m media_acquisition acquire "[topic]"`) *(future — T02+)*
   - Executes downloads from search plan
   - Per-source client modules with rate limiting
   - Writes downloaded files to `assets/` subdirectories
   - Updates manifest.json incrementally

4. **Status check** (`python -m media_acquisition status "[topic]"`)
   - Reads manifest.json and prints coverage stats
   - Shows gap count with status breakdown
   - Shows per-source download summary

---

## Checkpoints

**Automated:** Run `python -m media_acquisition status "[topic]"` after acquisition. Review gap count and coverage percentage.

**Schema validation:** Use `media_acquisition.schema.validate_manifest()` to validate manifest.json structure before downstream consumption.

**Human review:** Review manifest.json for shot mapping quality. Schema validation proves structure, not relevance.

---

## Outputs

| File | Location | Description |
|------|----------|-------------|
| `manifest.json` | `projects/N. [Title]/assets/manifest.json` | Central coordination artifact — assets, gaps, source summary |

manifest.json format:
- Top-level: `project`, `generated`, `updated`, `assets` array, `gaps` array, `source_summary` object
- Each asset: `filename`, `folder`, `source`, `source_url`, `description`, `license`, `mapped_shots`, `acquired_by`
- Each gap: `shot_id`, `visual_need`, `shotlist_type`, `status` (pending_generation|filled|unfilled)
- Valid folders: `archival_photos`, `archival_footage`, `documents`, `broll`, `vectors`, `animations`

---

## Deferred

- **MEDIA-01:** Resume/incremental acquisition (pick up where a previous run stopped)
- **MEDIA-02:** Duplicate detection across assets (same source_url downloaded twice)
- **MEDIA-03:** Asset quality scoring (resolution, relevance heuristics)
