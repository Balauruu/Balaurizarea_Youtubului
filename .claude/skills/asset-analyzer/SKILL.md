---
name: asset-analyzer
description: Use when analyzing video files for documentary asset extraction — identifying relevant segments, cataloging clips in SQLite, and extracting approved clips. Triggers on 'analyze assets', 'analyze staging videos', 'catalog this video', 'find usable segments', 'extract clips from [video]', or any request to process downloaded footage for the channel.
---

# Asset Analyzer

Analyze video files, identify relevant segments, catalog them in SQLite, and extract approved clips. Wraps the `claude-video-analyzer` skill as the analysis engine, adding project context awareness and asset cataloging.

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
- Load `visuals/media_leads.json` for context (why each video was downloaded, what to look for)
- Load `visuals/shotlist.json` for visual needs (what shots are still needed)
- Process all videos in `D:/Youtube/D. Mysteries Channel/3. Assets/_staging/{project_slug}/`
- Relevance scoring informed by shotlist and media_leads
- Clips route to project assets or global assets based on scope

---

## V1 Workflow — Analysis + Timestamps + Cataloging

### Step 1: Resolve context

**Standalone:** Skip to Step 2.

**Project mode:**
1. Resolve project directory from topic substring
2. Read `visuals/media_leads.json` — extract YouTube entries with `local_path` pointing to staging
3. Read `visuals/shotlist.json` — extract shot visual needs and b-roll themes
4. Build a context brief: for each staged video, pair it with its media_leads entry (source URL, title, description, relevance notes)

### Step 2: Analyze videos

For each video file, use the `claude-video-analyzer` skill:

1. **Probe** — Run the video-analyzer probe step to get duration, resolution, FPS
2. **Estimate** — Run cost estimation. Present to user. Wait for approval before proceeding.
3. **Extract frames** — Use `standard` mode (2 fps) for videos under 10 minutes. Use `quick` mode (1 fps) for longer videos.
4. **Analyze frames** — Send frame batches to Claude vision with this context prompt:

**Standalone context prompt:**
> Describe what you see in each frame. Note: era/decade, mood/atmosphere, visual content (people, places, objects, text), and potential documentary use.

**Project context prompt:**
> You are analyzing footage for the documentary "[project name]". Context for this video: [media_leads entry description and relevance]. The shotlist needs these visuals: [relevant shot visual_need descriptions]. For each frame, describe what you see and rate its relevance to the project's visual needs. Note: era, mood, specific content, and which shotlist entries it could serve.

### Step 3: Identify segments

From the frame analysis, identify **usable segments** — contiguous ranges of frames that show something useful. For each segment:

- `start_sec` / `end_sec` — timestamp boundaries
- `description` — what the segment shows
- `mood` — atmospheric quality
- `era` — time period depicted
- `relevance` — why it's useful (reference specific shotlist entries in project mode)
- `scope` — `project` (topic-specific footage) or `global` (atmospheric/b-roll reusable across projects). Claude decides based on content: interviews, specific locations, named people → project. Generic corridors, nature, industrial footage → global.
- `category` — `archival`, `broll`, or `cartoon_broll`
- `tags` — comma-separated searchable terms

### Step 4: Write analysis output

**Project mode:** Write `visuals/video_analysis.json`:

```json
{
  "project": "The Duplessis Orphans",
  "analyzed_at": "2026-03-25T14:30:00Z",
  "videos": [
    {
      "source_file": "D:/Youtube/.../3. Assets/_staging/duplessis-orphans/cbc_documentary.mp4",
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

### Step 5: Catalog in SQLite

For each identified segment, insert a row into `data/asset_catalog.db` using `data/catalog.py`:

```python
from data.catalog import get_connection, insert_clip

conn = get_connection()
insert_clip(
    conn=conn,
    path=source_file_path,       # staging path for now
    source_url=source_url,
    source_type="youtube",        # or "internet_archive", "web"
    scope="project",              # or "global"
    project="The Duplessis Orphans",  # null for global
    category="archival",
    description=segment_description,
    mood=segment_mood,
    era=segment_era,
    tags=segment_tags,
    duration_sec=end_sec - start_sec,
)
```

Status defaults to `'analyzed'` — clips are cataloged but not yet extracted.

### Step 6: Present for review

Present a summary table to the user:

| Video | Segments | Scope | Category | Key content |
|-------|----------|-------|----------|-------------|
| cbc_documentary.mp4 | 8 | 5 project, 3 global | 6 archival, 2 broll | Interviews, building exteriors, document close-ups |

Then for each video, show the segments with timestamps and descriptions. Ask the user to:
- Approve segments (mark `approved: true`)
- Reject segments (mark `approved: false`)
- Adjust timestamps if needed
- Change scope/category if misclassified

**V1 stops here.** The user now has timestamped descriptions and catalog entries. They can manually extract clips using the timestamps, or wait for V2.

---

## V2 Workflow — Clip Extraction (after human review)

### Step 7: Extract approved clips

For each segment where `approved: true`:

```bash
ffmpeg -ss {start_sec} -to {end_sec} -i "{source_file}" -c copy "{output_path}"
```

**Output path logic:**
- `scope: "project"` → `projects/N/assets/{category}/{descriptive_name}.mp4`
- `scope: "global"` → `D:/Youtube/D. Mysteries Channel/3. Assets/{category}/{descriptive_name}.mp4`

Filename: `{source_slug}_{start_sec}s_{brief_description}.mp4` (e.g., `cbc_doc_22s_institutional_exterior.mp4`)

### Step 8: Update catalog

For each extracted clip:
```python
from data.catalog import get_connection, update_clip

conn = get_connection()
update_clip(conn, clip_id, path=new_clip_path, status="extracted")
```

### Step 9: Clean staging

After all clips are extracted from a staging video, offer to delete the source file:
> "All approved clips extracted from cbc_documentary.mp4. Delete staging file? (Y/n)"

Only delete with user confirmation.

---

## Checkpoints

| After step | Agent presents | User decides |
|------------|---------------|--------------|
| Step 2 (estimate) | Token/cost estimate | Approve or adjust mode |
| Step 6 (analysis) | Segment table with timestamps | Approve/reject segments, adjust scope/category |
| Step 9 (cleanup) | Extraction complete | Delete staging files or keep |

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

## Key Locations

| What | Path |
|------|------|
| Staging area | `D:/Youtube/D. Mysteries Channel/3. Assets/_staging/{project_slug}/` |
| Global assets | `D:/Youtube/D. Mysteries Channel/3. Assets/{category}/` |
| Project assets | `projects/N/assets/{category}/` |
| Catalog DB | `data/asset_catalog.db` |
| Analysis output | `visuals/video_analysis.json` (project) or `.claude/scratch/` (standalone) |

---

## Dependencies

- `claude-video-analyzer` skill — frame extraction and vision analysis engine
- `ffmpeg` — video probing and clip extraction
- `data/catalog.py` — SQLite CRUD for asset catalog
- `opencv-python-headless`, `numpy` — frame processing (via claude-video-analyzer)
