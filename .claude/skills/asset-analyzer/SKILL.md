---
name: asset-analyzer
description: Use when analyzing video files for documentary asset extraction — identifying relevant segments, cataloging clips in SQLite, and extracting approved clips. Triggers on 'analyze assets', 'analyze staging videos', 'catalog this video', 'find usable segments', 'extract clips from [video]', or any request to process downloaded footage for the channel.
---

# Asset Analyzer

Analyze video files, identify relevant segments, catalog them in SQLite, and extract approved clips. Self-contained two-pass workflow: PySceneDetect triage filters irrelevant footage cheaply, then full vision analysis runs only on relevant scenes.

## Two Modes

### Standalone Mode
**Trigger:** User provides a video path directly (e.g., "Analyze this video D:/path/to/video.mp4")

- Analyze any video file regardless of source
- No project context — Claude describes what it sees
- User specifies destination for extracted clips
- Clips cataloged in `data/asset_catalog.db`

### Project Mode
**Trigger:** User references a project (e.g., "Analyze staging videos for Duplessis Orphans")

- Resolve project directory (case-insensitive substring match against `projects/`)
- Load `visuals/download_manifest.json` for video context (source URLs, titles, contexts, shot_refs)
- Load `visuals/shotlist.json` for visual needs (what shots are still needed)
- Process all videos in `projects/N. [Title]/assets/staging/`
- Relevance scoring informed by shotlist and download manifest
- Clips route to project assets or global assets based on scope

---

## V1 Workflow — Two-Pass Analysis + Timestamps + Cataloging

### Step 1: Resolve context

**Standalone:** Skip to Step 2.

**Project mode:**
1. Resolve project directory from topic substring
2. Read `visuals/download_manifest.json` — extract video entries with `local_path`, `source_url`, `title`, `context`, `shot_refs`
3. Read `visuals/shotlist.json` — extract shot visual needs and b-roll themes
4. Build a context brief: for each staged video, pair it with its manifest entry (source URL, title, context, shot_refs pointing to shotlist entries)

### Step 2: Probe videos

For each video file:

```bash
python .claude/skills/asset-analyzer/scripts/probe_video.py <video_path>
```

Get duration, resolution, FPS.

### Step 3: Scene detection (triage)

For each video:

```bash
python .claude/skills/asset-analyzer/scripts/scene_detect.py --input <video> --output <temp_dir>
```

Outputs:
- `scenes.json` — scene boundaries (start/end timestamps)
- `triage_manifest.json` — one mid-scene frame per scene at 512px width

### Step 4: Estimate cost

```bash
python .claude/skills/asset-analyzer/scripts/estimate_cost.py --video-name <name> --duration <sec> --scenes <count>
```

Shows two-pass token/cost estimate (triage frames + projected full-analysis frames). **Wait for user approval before proceeding.**

### Step 5: Triage vision analysis (Pass 1)

Send triage frames to Claude vision in batches of 15 frames per batch.

Use the **triage prompt** from `references/vision_prompts.md`:
- `[PROJECT_NAME]` — project name (project mode) or "Standalone Analysis" (standalone)
- `[CONTEXT]` — download_manifest `context` field (project mode) or user-provided description (standalone)
- `[SHOT_REFS_OR_GENERAL_NEEDS]` — shotlist entries referenced by the manifest's `shot_refs` (project mode) or "Describe what you see" (standalone)

Prepend the **batch context template** from `references/vision_prompts.md` to each batch.

Claude classifies each scene: **relevant** / **irrelevant** / **maybe**.

### Step 6: Present triage results

Show scene classification table per video:

| Video | Total Scenes | Relevant | Maybe | Irrelevant | Relevant Duration |
|-------|-------------|----------|-------|------------|-------------------|

Then show per-scene detail: scene number, timestamp range, classification, brief description.

User can:
- Override classifications before deep analysis
- Approve proceeding to Pass 2

**Show token estimate for the deep analysis pass** based on the number and duration of relevant+maybe scenes.

### Step 7: Full analysis (Pass 2) on relevant scenes

For each scene marked **relevant** or **maybe**, extract frames:

```bash
python .claude/skills/asset-analyzer/scripts/extract_frames.py --input <video> --output <temp_dir> --mode full --start <scene_start> --end <scene_end> --max-width 512
```

Send frame batches to Claude vision with:
- **Project mode:** Full analysis prompt (project) from `references/vision_prompts.md`
- **Standalone mode:** Full analysis prompt (standalone) from `references/vision_prompts.md`

Prepend the **batch context template** to each batch.

Identify usable segments with precise timestamps.

### Step 8: Identify segments

From the full analysis, identify **usable segments** — contiguous ranges of frames that show something useful. For each segment:

- `start_sec` / `end_sec` — timestamp boundaries
- `description` — what the segment shows
- `mood` — atmospheric quality
- `era` — time period depicted
- `relevance` — why it's useful (reference specific shotlist entries in project mode)
- `scope` — `project` (topic-specific footage) or `global` (atmospheric/b-roll reusable across projects). Claude decides based on content: interviews, specific locations, named people -> project. Generic corridors, nature, industrial footage -> global.
- `category` — `archival`, `broll`, or `cartoon_broll`
- `tags` — comma-separated searchable terms
- `approved` — null (pending human review)

### Step 9: Write video_analysis.json

**Project mode:** Write `visuals/video_analysis.json`:

```json
{
  "project": "The Duplessis Orphans",
  "analyzed_at": "2026-03-25T14:30:00Z",
  "videos": [
    {
      "source_file": "projects/1. The Duplessis Orphans/assets/staging/cbc_documentary.mp4",
      "source_url": "https://youtube.com/...",
      "duration_sec": 2847,
      "segments": [
        {
          "id": "SEG-001",
          "start_sec": 22.0,
          "end_sec": 35.5,
          "description": "Exterior shot of grey institutional building, overcast sky",
          "mood": "oppressive, cold",
          "era": "1950s",
          "relevance": "Matches shotlist S003 — institutional establishing shot",
          "scope": "project",
          "category": "archival",
          "tags": "institution, exterior, 1950s, quebec",
          "approved": null
        }
      ]
    }
  ]
}
```

**Standalone:** Write to `.claude/scratch/video_analysis_{filename}.json` with the same schema (minus `project` field).

### Step 10: Catalog in SQLite

For each identified segment, insert a row into `data/asset_catalog.db` using `data/catalog.py`:

```python
from data.catalog import get_connection, insert_clip

conn = get_connection()
insert_clip(
    conn=conn,
    path=source_file_path,       # staging path for now
    source_type="youtube",        # or "internet_archive", "web"
    scope="project",              # or "global"
    source_url=source_url,
    project="The Duplessis Orphans",  # None for global
    category="archival",
    description=segment_description,
    mood=segment_mood,
    era=segment_era,
    tags=segment_tags,
    duration_sec=end_sec - start_sec,
)
```

Status defaults to `'analyzed'` — clips are cataloged but not yet extracted.

### Step 11: Present for review

Present a summary table to the user:

| Video | Segments | Scope | Category | Key content |
|-------|----------|-------|----------|-------------|
| cbc_documentary.mp4 | 8 | 5 project, 3 global | 6 archival, 2 broll | Interviews, building exteriors, document close-ups |

Then for each video, show the segments with timestamps and descriptions. Ask the user to:
- Approve segments (mark `approved: true`)
- Reject segments (mark `approved: false`)
- Adjust timestamps if needed
- Change scope/category if misclassified

**V1 stops here.** The user now has timestamped descriptions and catalog entries. They can manually extract clips using the timestamps, or proceed to V2.

---

## V2 Workflow — Clip Extraction (after human review)

### Step 1: Extract approved clips

For each segment where `approved: true`:

```bash
python .claude/skills/asset-analyzer/scripts/export_clips.py --input "{source_file}" --start {start_sec} --end {end_sec} --output "{output_path}"
```

**Output path logic:**
- `scope: "project"` -> `projects/N/assets/{category}/{descriptive_name}.mp4`
- `scope: "global"` -> `D:/Youtube/D. Mysteries Channel/3. Assets/{category}/{descriptive_name}.mp4`

Filename: `{source_slug}_{start_sec}s_{brief_description}.mp4` (e.g., `cbc_doc_22s_institutional_exterior.mp4`)

### Step 2: Update catalog

For each extracted clip:
```python
from data.catalog import get_connection, update_clip

conn = get_connection()
update_clip(conn, clip_id, path=new_clip_path, status="extracted")
```

### Step 3: Clean staging

After all clips are extracted from a staging video, offer to delete the source file:
> "All approved clips extracted from cbc_documentary.mp4. Delete staging file? (Y/n)"

Only delete with user confirmation.

---

## Checkpoints

| After | Agent Presents | Human Decides |
|-------|---------------|---------------|
| Step 4 (estimate) | Two-pass token/cost estimate | Approve or stop |
| Step 6 (triage) | Scene classification table per video, token estimate for deep pass | Override classifications, approve deep analysis |
| Step 11 (analysis) | Segment table with timestamps | Approve/reject segments, adjust scope/category |
| V2 Step 3 (cleanup) | Extraction complete | Delete staging files or keep |

---

## Catalog Query

The catalog can be searched at any time, independent of analysis:

```python
from data.catalog import get_connection, search_clips, list_clips

conn = get_connection()

# Search by description
results = search_clips(conn, "institutional corridor")

# List all global b-roll
results = list_clips(conn, scope="global", category="broll")

# List all clips for a project
results = list_clips(conn, project="The Duplessis Orphans")
```

When the user asks "what clips do I have for X" or "search the catalog for Y", use these functions.

---

## Frame Extraction Modes

Only two modes exist:

| Mode | Use | FPS | Resolution | When |
|------|-----|-----|------------|------|
| `triage` | 1 frame per scene via PySceneDetect | N/A (scene-based) | 512px wide | Pass 1 — scene classification |
| `full` | 2fps on selected time ranges | 2 | 512px wide | Pass 2 — detailed analysis of relevant scenes |

---

## Key Locations

| What | Path |
|------|------|
| Staging area | `projects/N. [Title]/assets/staging/` |
| Global assets | `D:/Youtube/D. Mysteries Channel/3. Assets/{category}/` |
| Project assets | `projects/N/assets/{category}/` |
| Catalog DB | `data/asset_catalog.db` |
| Catalog CRUD | `data/catalog.py` |
| Analysis output | `visuals/video_analysis.json` (project) or `.claude/scratch/` (standalone) |
| Probe script | `.claude/skills/asset-analyzer/scripts/probe_video.py` |
| Scene detect script | `.claude/skills/asset-analyzer/scripts/scene_detect.py` |
| Frame extraction script | `.claude/skills/asset-analyzer/scripts/extract_frames.py` |
| Cost estimation script | `.claude/skills/asset-analyzer/scripts/estimate_cost.py` |
| Clip export script | `.claude/skills/asset-analyzer/scripts/export_clips.py` |
| Still export script | `.claude/skills/asset-analyzer/scripts/export_stills.py` |
| Vision prompts | `.claude/skills/asset-analyzer/references/vision_prompts.md` |

---

## Dependencies

- `scenedetect` (venv at `C:\Users\iorda\venvs\scenedetect`) — scene boundary detection
- `ffmpeg` — video probing, frame extraction, clip cutting
- `data/catalog.py` — SQLite CRUD for asset catalog
- `opencv-python-headless`, `numpy` — frame processing
