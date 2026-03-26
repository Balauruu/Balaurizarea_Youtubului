# Asset Pipeline Redesign

**Date:** 2026-03-26
**Status:** Implemented
**Scope:** media-scout (strip downloads), asset-downloader (new), asset-analyzer (rewrite + PySceneDetect), claude-video-analyzer (delete)

---

## Problem Statement

The current pipeline has three structural problems:

1. **Missing download step.** Media-scout discovers YouTube leads and downloads them, but shot-planner produces `broll_leads` (archive.org URLs) that nobody downloads. There is no skill that fulfills the shotlist's video needs.

2. **Expensive blind analysis.** Asset-analyzer wraps claude-video-analyzer — a general-purpose skill with prompts, modes, and reports irrelevant to documentary footage. It processes every frame at a fixed rate with no pre-filtering, making it prohibitively expensive for the typical 2+ hours of staged footage per project where only 10-20% is usable.

3. **Tangled responsibilities.** Media-scout handles both discovery (finding what exists) and acquisition (downloading it). These have different failure modes, resource costs, and tool requirements.

---

## Pipeline Architecture

**Before:**
```
media-scout (discover + download all) -> shot-planner -> asset-analyzer (wraps claude-video-analyzer)
```

**After:**
```
media-scout (discover + download images/docs only)
    | media_leads.json (web_assets + youtube_urls as URL-only leads)
shot-planner (plan visuals, match b-roll)
    | shotlist.json (with broll_leads on curate shots)
asset-downloader (download all videos)
    | download_manifest.json + staging/ videos
asset-analyzer (PySceneDetect triage -> vision analysis -> catalog -> extract)
    | video_analysis.json + extracted clips + catalog entries
```

### Handoff Contracts

| From | To | Contract File | Contents |
|------|----|--------------|----------|
| media-scout | shot-planner | `visuals/media_leads.json` | `web_assets[]` with local paths + `youtube_urls[]` with URLs only (no `local_path`) |
| shot-planner | asset-downloader | `visuals/shotlist.json` | `broll_leads[]` on `curate` shots with archive.org URLs |
| media-scout | asset-downloader | `visuals/media_leads.json` | `youtube_urls[]` with URLs, titles, scores, descriptions |
| asset-downloader | asset-analyzer | `visuals/download_manifest.json` | Per-file download state with provenance and context |
| asset-analyzer | editor (human) | `visuals/video_analysis.json` + `data/asset_catalog.db` | Timestamped segments with approval status |

---

## Skill Changes

### 1. media-scout — Remove Video Downloads

**What changes:**
- Remove Pass 2 Step 7 (download approved leads). Pass 2 ends after Step 6 (present scored leads).
- Remove the human review checkpoint ("Approve leads for download?"). Media-scout presents scored leads as information, not a gate.
- `media_leads.json` schema for `youtube_urls` entries drops `local_path` and `download_error` fields. These become asset-downloader's responsibility.
- Audit checks that reference downloads (`YouTube downloads staged`, `No orphan files` for staging/) are removed.

**What stays the same:**
- Pass 1 (web crawl, image extraction, document screenshots, image/doc downloads to archival/ and documents/)
- Pass 2 Steps 1-6 (YouTube search, crawl, pre-filter, yt-dlp validation, evaluation, presentation)
- All web_asset download logic (images and documents still downloaded by media-scout)

### 2. shot-planner — No Changes

Shot-planner already produces `broll_leads` as URL-only entries in `shotlist.json`. It reads `media_leads.json` for `known_assets` matching (images/docs), which still works since those are still downloaded by media-scout.

### 3. asset-downloader — New Skill

**Classification:** [DETERMINISTIC] — structured downloads with rate limiting. Python script.

**Purpose:** Download all video files from URLs produced by upstream skills. Single responsibility: URLs in, staged videos + manifest out.

**Inputs:**
- `projects/N. [Title]/visuals/media_leads.json` -> YouTube entries (url, title, duration, score)
- `projects/N. [Title]/visuals/shotlist.json` -> `curate` shots with `broll_leads` (archive.org URLs)

**Outputs:**
- Videos -> `projects/N. [Title]/assets/staging/`
- `projects/N. [Title]/visuals/download_manifest.json`

**Workflow:**

1. **Resolve project** — Case-insensitive substring match against `projects/`.
2. **Collect URLs** — Parse both input files. For each URL, record source skill, context, category, and URL.
3. **Deduplicate** — Same URL from both sources = keep one entry, merge provenance.
4. **Download** — To `assets/staging/`:
   - **YouTube:** `yt-dlp -f "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]" --merge-output-format mp4 --restrict-filenames`
   - **Archive.org:** Fetch item metadata via `https://archive.org/metadata/<item_id>`, select smallest MP4 with height <= 720p, fall back to smallest MPEG4/H.264 derivative. Direct HTTP download.
   - Validate: discard if under 1MB or ffprobe fails.
5. **Rate limiting** (site-specific):
   - YouTube: `--sleep-interval 3 --max-sleep-interval 8 --sleep-requests 1.5`, batches of 10 with 15s pause between batches. Stop on 429.
   - Archive.org: 2-second delay between requests.
6. **Volume cap:** 200GB total per run. Track cumulative size. When approaching cap, log remaining as `status: "skipped"`.
7. **Write download_manifest.json.**
8. **Resume logic:** If `download_manifest.json` exists, skip entries with `status: "completed"` whose files still exist on disk. Idempotent on re-run.
9. **Present results** — Summary table: total attempted, succeeded, failed with reasons.

**Download manifest schema:**

```json
{
  "project": "The Duplessis Orphans",
  "downloaded_at": "2026-03-26T14:30:00Z",
  "total_size_mb": 4230,
  "videos": [
    {
      "id": "DL-001",
      "source": "youtube",
      "source_url": "https://youtube.com/watch?v=...",
      "title": "CBC Documentary: Les Enfants de Duplessis",
      "duration_sec": 2847,
      "score": 1,
      "file_size_mb": 385,
      "local_path": "assets/staging/cbc_duplessis_documentary.mp4",
      "status": "completed",
      "shot_refs": [],
      "context": "Primary source documentary from CBC archives, interviews with survivors"
    },
    {
      "id": "DL-002",
      "source": "internet_archive",
      "source_url": "https://archive.org/details/the_cobweb_hotel",
      "title": "The Cobweb Hotel (1936)",
      "duration_sec": 420,
      "score": null,
      "file_size_mb": 95,
      "local_path": "assets/staging/cobweb_hotel_1936.mp4",
      "status": "completed",
      "shot_refs": ["S004", "S017"],
      "context": "Metaphor for institutional trap — spider-innkeeper concealing predatory intent"
    }
  ]
}
```

Key fields:
- `source`: `"youtube"` or `"internet_archive"` — determines download strategy
- `score`: from media-scout scoring (null for archive.org entries)
- `shot_refs`: which shotlist entries this video serves (empty for YouTube leads, populated for broll_leads)
- `context`: why this video matters — from media_leads description or broll_leads match_reasoning
- `status`: `"completed"`, `"failed"`, or `"skipped"`

**Audit checks:**
- Every URL from both input files has a corresponding manifest entry
- Every `status: "completed"` entry has a valid `local_path` pointing to an existing file
- Every file in `assets/staging/` has a matching manifest entry (no orphans)
- All completed files pass ffprobe validation (duration > 0, video stream present)

**Skill structure:**
```
.claude/skills/asset-downloader/
  SKILL.md
  scripts/
    download.py
```

### 4. asset-analyzer — Rewrite

**What changes:**

#### Fork claude-video-analyzer, then delete it

Asset-analyzer absorbs the scripts it needs from claude-video-analyzer, customizes them for documentary use, and becomes fully self-contained. claude-video-analyzer is deleted (its only consumer was this pipeline).

Forked scripts:
- `probe_video.py` — unchanged
- `extract_frames.py` — modified: add 512px width downscale option, remove `technical`/`detailed`/`keyframes` modes
- `estimate_cost.py` — modified: triage-aware estimation (two-pass cost)
- `export_clips.py` — unchanged
- `export_stills.py` — unchanged

New scripts:
- `scene_detect.py` — PySceneDetect wrapper: runs ContentDetector, outputs scene list with timestamps, extracts one mid-scene frame per scene

#### Two-pass analysis workflow

**Pass 1 — PySceneDetect Triage (cheap):**

1. Probe each video with ffprobe (duration, resolution, FPS)
2. Run PySceneDetect `ContentDetector` (default threshold) -> scene list with timestamps
3. Extract one frame per scene (mid-scene point, not boundary)
4. Send triage frames to vision in batches with triage prompt:

```
You are triaging footage for the documentary "[project name]".
Context for this video: [download_manifest context field]
Relevant visual needs: [shotlist entries from shot_refs, or general needs if YouTube lead]

For each frame (one per detected scene), answer:
- What does this scene show?
- Relevant (yes/no/maybe) to the project?
- If relevant, which visual need does it serve?

Be terse. This is triage, not full analysis.
```

5. Mark each scene as `relevant`, `irrelevant`, or `maybe`
6. Present triage summary per video: scene count, relevant count, total duration of relevant scenes

**Pass 2 — Full Analysis (expensive, targeted):**

For scenes marked `relevant` or `maybe`:
1. Extract frames at 1-2 fps within that scene's time range only
2. Downscale to 512px wide before sending to vision
3. Send batches with documentary-specific full analysis prompt:

```
You are analyzing footage for the documentary "[project name]".
This video: [title] — [context from download_manifest]
This scene range: [start_sec] to [end_sec]
Visual needs this video may serve: [relevant shotlist entries]

For each frame, describe:
1. Content: people, locations, objects, text on screen, era markers
2. Footage type: interview/talking head, archival film, b-roll, news broadcast, document close-up, cartoon/animation
3. Mood and atmosphere
4. Which shotlist entry this could serve (cite shot ID)
5. Scope: "project" (topic-specific) or "global" (reusable atmospheric/b-roll)

Reference timestamps. Be specific — "grey institutional building with barred windows, overcast, 1950s Quebec" not "a building".
```

4. Identify usable segments with timestamps, descriptions, mood, era, relevance, scope, category, tags
5. Steps 4-9 from current SKILL.md continue unchanged (write analysis output, catalog in SQLite, present for review, extract clips, update catalog, clean staging)

**Token cost comparison (30-minute video):**
- Current (1fps quick mode): ~1,800 frames -> ~1.98M tokens
- New triage: ~60 frames (scenes) -> ~66K tokens
- New full (relevant scenes at 1fps, 512px): ~200 frames -> ~160K tokens
- **Total new: ~226K tokens — ~85% reduction**

#### Modes reduced to two

- `triage` — PySceneDetect scene detection, 1 frame per scene
- `full` — 1-2 fps on selected time ranges, 512px downscale

The `quick`, `standard`, `detailed`, `technical`, `keyframes` modes from claude-video-analyzer are dropped.

#### Input change

- Reads `download_manifest.json` (from asset-downloader) instead of re-deriving context from media_leads + shotlist
- Still reads `shotlist.json` for visual needs matching
- Provenance from the manifest tells asset-analyzer the category and source context for each file

#### Vision prompts

Replace `references/vision_prompts.md` entirely. New file contains only:
- Triage prompt (shown above)
- Full analysis prompt — project mode (shown above)
- Full analysis prompt — standalone mode (general documentary footage description)
- Batch context template

Generic prompts (promotional, gameplay, tutorial, security, music video) are dropped.

#### Everything else stays the same

- Standalone mode and project mode
- Segment identification schema
- SQLite cataloging via `data/catalog.py`
- V1 (analysis + timestamps + cataloging) and V2 (clip extraction) workflow split
- Output schema (`video_analysis.json`)

**Updated checkpoints:**

| After | Agent Presents | Human Decides |
|-------|---------------|---------------|
| Pass 1 (triage) | Scene classification table per video, token estimate for deep pass | Override classifications, approve deep analysis |
| Pass 2 (analysis) | Segment table with timestamps | Approve/reject segments, adjust scope/category |
| V2 (cleanup) | Extraction complete | Delete staging files or keep |

**Updated skill structure:**
```
.claude/skills/asset-analyzer/
  SKILL.md
  scripts/
    probe_video.py        # forked from claude-video-analyzer (unchanged)
    scene_detect.py       # NEW: PySceneDetect wrapper
    extract_frames.py     # forked (modified: 512px downscale, reduced modes)
    estimate_cost.py      # forked (modified: triage-aware two-pass estimation)
    export_clips.py       # forked (unchanged)
    export_stills.py      # forked (unchanged)
  references/
    vision_prompts.md     # NEW: documentary-specific prompts only
```

### 5. claude-video-analyzer — Delete

This skill is removed entirely. Asset-analyzer has absorbed its useful scripts and no other pipeline skill depends on it.

---

## New Dependencies

| Dependency | Used by | Installation |
|------------|---------|-------------|
| PySceneDetect | asset-analyzer `scene_detect.py` | `pip install scenedetect[opencv]` in dedicated venv at `C:\Users\iorda\venvs\scenedetect` |
| ffmpeg | asset-downloader, asset-analyzer | Already installed |
| yt-dlp | asset-downloader | Already installed |
| opencv-python-headless | asset-analyzer | Already installed (claude-video-analyzer dependency) |

---

## Files Created / Modified / Deleted

| File | Action | Description |
|------|--------|-------------|
| `.claude/skills/asset-downloader/SKILL.md` | Create | New skill definition |
| `.claude/skills/asset-downloader/scripts/download.py` | Create | Download orchestration script |
| `.claude/skills/asset-analyzer/SKILL.md` | Rewrite | Self-contained, two-pass workflow, read download_manifest |
| `.claude/skills/asset-analyzer/scripts/probe_video.py` | Create (fork) | From claude-video-analyzer, unchanged |
| `.claude/skills/asset-analyzer/scripts/scene_detect.py` | Create | PySceneDetect wrapper |
| `.claude/skills/asset-analyzer/scripts/extract_frames.py` | Create (fork) | Modified: 512px downscale, reduced modes |
| `.claude/skills/asset-analyzer/scripts/estimate_cost.py` | Create (fork) | Modified: triage-aware two-pass estimation |
| `.claude/skills/asset-analyzer/scripts/export_clips.py` | Create (fork) | From claude-video-analyzer, unchanged |
| `.claude/skills/asset-analyzer/scripts/export_stills.py` | Create (fork) | From claude-video-analyzer, unchanged |
| `.claude/skills/asset-analyzer/references/vision_prompts.md` | Create | Documentary-specific prompts only |
| `.claude/skills/media-scout/SKILL.md` | Edit | Remove Pass 2 Step 7, remove checkpoint, update schema |
| `.claude/skills/claude-video-analyzer/` | Delete | Entire skill directory removed |
| `CLAUDE.md` | Edit | Update skill routing table, pipeline flow, folder map |
| `CONTEXT.md` | Edit | Update task routing for asset-downloader, update asset-analyzer load list |
| `.claude/Architecture.md` | Edit | Update pipeline diagram and asset pipeline section |

---

## Out of Scope

- Vector generation (ComfyUI pipeline)
- Audio analysis
- Asset Library (semantic search)
