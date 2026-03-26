---
name: asset-analyzer
description: Use when analyzing video files for documentary asset extraction — identifying relevant segments, cataloging clips in SQLite, and extracting approved clips. Triggers on 'analyze assets', 'analyze staging videos', 'catalog this video', 'find usable segments', 'extract clips from [video]', or any request to process downloaded footage for the channel.
---

# Asset Analyzer

Two-pass video analysis pipeline: PySceneDetect triage filters irrelevant footage cheaply, then full vision analysis runs only on relevant scenes. Approved segments are extracted as clips and cataloged in SQLite.

## Modes

**Project mode** (default) — User references a project: "Analyze staging videos for Duplessis Orphans"
- Resolve project dir (case-insensitive substring match against `projects/`)
- Load `visuals/download_manifest.json` for video context + `visuals/shotlist.json` for visual needs
- Process all videos in `assets/staging/`
- Clips route to project or global assets based on scope

**Standalone mode** — User provides a video path: "Analyze this video D:/path/to/video.mp4"
- No project context — Claude describes what it sees
- User specifies clip destination
- Skip manifest/shotlist loading, use standalone vision prompts

---

## Workflow

### Step 1: Resolve context

**Project mode:**
1. Resolve project directory
2. Read `visuals/download_manifest.json` — extract entries with `local_path`, `source_url`, `title`, `context`, `shot_refs`
3. Read `visuals/shotlist.json` — extract visual needs from shots referenced by `shot_refs`
4. Build context brief: pair each staged video with its manifest entry

**Standalone:** Skip to Step 2.

### Step 2: Probe and detect scenes

For each video:

```bash
python .claude/skills/asset-analyzer/scripts/probe_video.py <video_path>
python .claude/skills/asset-analyzer/scripts/scene_detect.py --input <video> --output <temp_dir>
```

Probe returns duration, resolution, FPS. Scene detection outputs `scenes.json` (boundaries) and `triage_manifest.json` (one mid-scene frame per scene at 512px).

Show the user a two-pass token estimate:
```bash
python .claude/skills/asset-analyzer/scripts/estimate_cost.py --video-name <name> --duration <sec> --scenes <count>
```
**Wait for approval before proceeding.**

### Step 3: Triage vision analysis (Pass 1)

Send triage frames in batches of 15 to Claude vision using the **triage prompt** from `references/vision_prompts.md`. Prepend the **batch context template** to each batch.

Template variables:
- `[PROJECT_NAME]` — project name or "Standalone Analysis"
- `[CONTEXT]` — manifest `context` field or user-provided description
- `[SHOT_REFS_OR_GENERAL_NEEDS]` — shotlist entries from `shot_refs` or "Describe what you see"

Claude classifies each scene: **relevant** / **irrelevant** / **maybe**.

Present triage summary:

| Video | Total Scenes | Relevant | Maybe | Irrelevant | Relevant Duration |
|-------|-------------|----------|-------|------------|-------------------|

Show per-scene detail. User can override classifications. Show token estimate for Pass 2 based on relevant+maybe scene duration.

### Step 4: Full analysis (Pass 2)

For each relevant/maybe scene:

```bash
python .claude/skills/asset-analyzer/scripts/extract_frames.py \
  --input <video> --output <temp_dir> --mode full \
  --start <scene_start> --end <scene_end> --max-width 512
```

Send frame batches to Claude vision using the **full analysis prompt** (project or standalone) from `references/vision_prompts.md`.

From the analysis, identify **usable segments** — contiguous frame ranges showing useful content. For each segment:

| Field | Description |
|-------|------------|
| `id` | `SEG-001` sequential |
| `start_sec` / `end_sec` | Timestamp boundaries |
| `description` | What the segment shows |
| `mood` | Atmospheric quality |
| `era` | Time period depicted |
| `relevance` | Why useful — cite shot IDs in project mode |
| `scope` | `project` (interviews, named people, specific locations) or `global` (generic corridors, nature, industrial) |
| `category` | `archival`, `broll`, or `cartoon_broll` |
| `tags` | Comma-separated searchable terms |

**Scope assignment rules:**

Assign `scope: "project"` (default) unless ALL of these are true:
- Content is generic — no named people, specific locations, or topic-specific events from this documentary
- Clearly reusable across multiple unrelated projects
- Falls into a recognizable global category: atmospheric footage (corridors, weather, textures, urban/rural environments), cartoon clips with broad metaphorical use, generic institutional or industrial footage

When in doubt, assign `project`. Global scope is strict — the clip must be useful to a documentary about a completely different topic.

### Step 5: Write analysis + catalog + present for review

1. **Write `video_analysis.json`** — project mode: `visuals/video_analysis.json`; standalone: `.claude/scratch/video_analysis_{filename}.json`

```json
{
  "project": "The Duplessis Orphans",
  "analyzed_at": "2026-03-25T14:30:00Z",
  "videos": [
    {
      "source_file": "assets/staging/cbc_documentary.mp4",
      "source_url": "https://youtube.com/...",
      "duration_sec": 2847,
      "segments": [
        {
          "id": "SEG-001",
          "start_sec": 22.0, "end_sec": 35.5,
          "description": "Exterior shot of grey institutional building, overcast sky",
          "mood": "oppressive, cold", "era": "1950s",
          "relevance": "Matches shotlist S003 — institutional establishing shot",
          "scope": "project", "category": "archival",
          "tags": "institution, exterior, 1950s, quebec",
          "approved": null
        }
      ]
    }
  ]
}
```

2. **Catalog in SQLite** — insert each segment into `data/asset_catalog.db`:

```python
from data.catalog import get_connection, insert_clip

conn = get_connection()
insert_clip(conn, path=source_file_path, source_type="youtube",
            scope="project", source_url=source_url,
            project="The Duplessis Orphans", category="archival",
            description=segment_description, mood=segment_mood,
            era=segment_era, tags=segment_tags,
            duration_sec=end_sec - start_sec)
```

3. **Present for review** in two tiers:

**Tier 1 — Shot-matched segments** (segments whose `relevance` cites a specific shot ID):

| Video | Segment | Shot | Timestamps | Description | Scope |
|-------|---------|------|------------|-------------|-------|

**Tier 2 — Unmatched global candidates** (segments with `scope: "global"` that don't cite any shot ID):

| Video | Segment | Timestamps | Description | Category | Tags |
|-------|---------|------------|-------------|----------|------|

Present Tier 1 first — these are the clips the shotlist needs. Tier 2 follows — these are potential additions to the global asset library. User approves/rejects from both tiers, adjusts timestamps or scope/category.

### Step 6: Extract approved clips

For each segment where user approved:

Build a clips JSON and run extraction:
```bash
python .claude/skills/asset-analyzer/scripts/export_clips.py \
  --input "<source_file>" \
  --output "<output_dir>" \
  --clips '[{"start": "<start_sec>", "end": "<end_sec>", "label": "<descriptive_name>"}]'
```

**Output path:**
- `scope: "project"` → `projects/N/assets/{category}/`
- `scope: "global"` → `D:/Youtube/D. Mysteries Channel/3. Assets/{subject_category}/{subcategory}/`

For global clips, determine the subject category from the segment's description and tags:
- Locations (urban, rural, interiors, aerial)
- Nature (weather, water, forests, landscapes)
- People (crowds, silhouettes, hands_details)
- Objects (documents, artifacts, symbols)
- Textures (film_grain, light, particles, surfaces)
- Cartoons (PD animation clips)
- Transitions (establishing, time_passage, movement)

**Filename:** `{source_slug}_{start_sec}s_{brief_description}.mp4`

After extraction, update catalog status:
```python
from data.catalog import get_connection, update_clip
conn = get_connection()
update_clip(conn, clip_id, path=new_clip_path, status="extracted")
```

### Step 7: Clean staging

After all clips extracted from a staging video, offer to delete the source:
> "All approved clips extracted from cbc_documentary.mp4. Delete staging file? (Y/n)"

Only delete with user confirmation.

---

## Checkpoints

| After | Agent Presents | Human Decides |
|-------|---------------|---------------|
| Step 2 (estimate) | Two-pass token/cost estimate | Approve or stop |
| Step 3 (triage) | Scene classification table, Pass 2 token estimate | Override classifications, approve deep analysis |
| Step 5 (analysis) | Segment table with timestamps | Approve/reject segments, adjust scope/category |
| Step 7 (cleanup) | Extraction complete | Delete staging files or keep |

---

## Catalog Query

Search the catalog at any time:

```python
from data.catalog import get_connection, search_clips, list_clips
conn = get_connection()
search_clips(conn, "institutional corridor")           # text search
list_clips(conn, scope="global", category="broll")     # filter by scope+category
list_clips(conn, project="The Duplessis Orphans")      # all clips for project
```

---

## Dependencies

- `scenedetect` (venv: `C:\Users\iorda\venvs\scenedetect`) — scene boundary detection
- `ffmpeg` — probing, frame extraction, clip cutting
- `data/catalog.py` — SQLite CRUD for asset catalog
