# Asset Pipeline Redesign

**Date:** 2026-03-26
**Status:** Approved
**Scope:** media-scout, shot-planner, vid-downloader (new), asset-analyzer (rewrite), claude-video-analyzer (unchanged)

---

## Problem Statement

The current pipeline has an awkward handoff between media-scout (which discovers AND downloads YouTube videos) and asset-analyzer (which analyzes staged videos but has no download capability for archive.org b-roll). Additionally, asset-analyzer wraps claude-video-analyzer — a general-purpose skill whose prompts, reports, and capabilities are largely irrelevant to documentary footage processing. Finally, asset-analyzer has no pre-filtering strategy, making it prohibitively expensive for the typical 4-8 hours of footage per project where only 5-20% is usable.

## Design

### Pipeline Architecture

```
Phase 1: Narrative Engineering

  channel-assistant -> researcher -+-> writer ----------+-> shot-planner
                                   +-> media-scout -----+

Phase 2: Asset Pipeline

  media_leads.json -+-> vid-downloader -> asset-analyzer
  shotlist.json ----+
```

After Research completes, media-scout and writer run in parallel. After shot-planner produces the shotlist, vid-downloader consumes URLs from both upstream skills, downloads everything to staging, and asset-analyzer processes the staged files.

### Handoff Contracts

| From | To | Contract File | Contents |
|------|----|--------------|----------|
| media-scout | vid-downloader | `visuals/media_leads.json` | `youtube_urls[]` with URLs, titles, scores, descriptions. No `local_path`. |
| shot-planner | vid-downloader | `visuals/shotlist.json` | `broll_leads[]` on `curate` shots with archive.org URLs. |
| vid-downloader | asset-analyzer | `visuals/download_manifest.json` | Per-file download state with provenance. |
| asset-analyzer | editor (human) | `visuals/video_analysis.json` + `data/asset_catalog.db` | Timestamped segments with approval status. |

---

## Skill Changes

### 1. media-scout — Remove Video Downloads

**What changes:**
- Pass 2 workflow stops after Step 6 (present scored leads, get approval). Steps 7 (download) is removed entirely.
- `media_leads.json` schema for `youtube_urls` entries drops `local_path` and `download_error` fields. These become vid-downloader's responsibility.
- The "Approve leads for download?" checkpoint remains, but approval now means "include in download_manifest for vid-downloader" rather than "download now."
- Audit checks that reference downloads (`YouTube downloads staged`, `No orphan files` for staging/) are removed from media-scout and move to vid-downloader.

**What stays the same:**
- Pass 1 (web crawl, image extraction, document screenshots, image/doc downloads to archival/ and documents/)
- Pass 2 Steps 1-6 (YouTube search, crawl, pre-filter, yt-dlp validation, evaluation, presentation)
- All web_asset download logic (images and documents still downloaded by media-scout)

### 2. shot-planner — No Changes

The b-roll download note was already removed. Shot-planner produces `broll_leads` as URLs in `shotlist.json`. No download responsibility.

### 3. vid-downloader — New Skill

**Purpose:** Download video files from URLs produced by upstream skills. Thin, focused, deterministic.

**Inputs:**
- `visuals/media_leads.json` — `youtube_urls[]` entries
- `visuals/shotlist.json` — `broll_leads[]` from `curate` shots

**Workflow:**

1. **Resolve project** — Case-insensitive substring match against `projects/`.
2. **Collect URLs** — Parse both input files. For each URL, record:
   - `source_skill`: `"media-scout"` or `"shot-planner"`
   - `source_context`: the media_leads description/relevance OR the shotlist shot ID + narrative_context
   - `category`: inferred from source — media-scout youtube_urls -> `"archival"` (default, asset-analyzer may reclassify); shot-planner broll_leads -> read from the shot's `form` field (`broll_atmospheric` or `broll_cartoon`)
   - `url`: the download URL
3. **Deduplicate** — Same URL from both sources = keep one entry, merge provenance.
4. **Download** — To `assets/staging/`:
   - **YouTube URLs:** `yt-dlp --sleep-interval 5 -f "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]" --merge-output-format mp4`
   - **Archive.org URLs:** Direct HTTP download of the video file. Archive.org detail pages link to the actual file — resolve the download URL from the detail page if needed.
   - Filename: `{source}_{id_or_slug}.mp4` (e.g., `yt_dQw4w9WgXcQ.mp4`, `ia_cobweb-hotel-1936.mp4`)
   - Skip files that already exist at target path (idempotent)
   - Validate: discard if under 1MB (broken) or if ffprobe fails
5. **Rate limiting:**
   - YouTube: `--sleep-interval 5`, batches of 10 with 15s pause between batches. Stop on 429.
   - Archive.org: 2-second delay between requests (respectful, rarely rate-limited).
6. **Write download_manifest.json**
7. **Present results** — Summary table: total attempted, succeeded, failed with reasons. Offer to retry failures.

**Output schema — download_manifest.json:**

```json
{
  "project": "The Duplessis Orphans",
  "downloaded_at": "2026-03-26T14:30:00Z",
  "files": [
    {
      "url": "https://youtube.com/watch?v=...",
      "source_skill": "media-scout",
      "source_context": "CBC documentary about institutional abuse in Quebec",
      "category": "archival",
      "local_path": "assets/staging/yt_abc123.mp4",
      "filename": "yt_abc123.mp4",
      "status": "ok",
      "file_size_mb": 245.3,
      "duration_sec": 2847
    },
    {
      "url": "https://archive.org/details/cobweb_hotel",
      "source_skill": "shot-planner",
      "source_context": "S004 — authority concealment metaphor",
      "category": "broll_cartoon",
      "local_path": "assets/staging/ia_cobweb-hotel.mp4",
      "filename": "ia_cobweb-hotel.mp4",
      "status": "ok",
      "file_size_mb": 52.1,
      "duration_sec": 480
    },
    {
      "url": "https://youtube.com/watch?v=...",
      "source_skill": "media-scout",
      "source_context": "Survivor interview compilation",
      "category": "archival",
      "local_path": null,
      "filename": null,
      "status": "failed",
      "error": "HTTP 429 — rate limited, stopped"
    }
  ]
}
```

**Audit checks:**
- Every URL from both input files has a corresponding manifest entry
- Every `status: "ok"` entry has a valid `local_path` pointing to an existing file
- Every file in `assets/staging/` has a matching manifest entry (no orphans)
- All files pass ffprobe validation (duration > 0, video stream present)

**Checkpoints:**

| After | Agent Presents | Human Decides |
|-------|---------------|---------------|
| Step 6 | Download results table, failed downloads with reasons | Retry failures, proceed to asset-analyzer, or stop |

### 4. asset-analyzer — Rewrite (Self-Contained + Scene-Detection Pre-Filter)

**What changes:**

#### Independence from claude-video-analyzer
- Asset-analyzer gets its own `scripts/` directory with forked + modified scripts:
  - `probe_video.py` — forked from claude-video-analyzer (unchanged)
  - `estimate_cost.py` — forked, updated to estimate two-pass cost (triage + deep)
  - `extract_frames.py` — forked (unchanged)
  - `scene_detect.py` — **new**, PySceneDetect wrapper for scene boundary detection + representative frame extraction
- Asset-analyzer gets its own `prompts/vision_prompts.md` with documentary-specific prompts:
  - **Triage prompt** — quick scene relevance classification from a single representative frame
  - **Deep analysis prompt (project mode)** — era detection, mood, documentary usability, shotlist matching
  - **Deep analysis prompt (standalone mode)** — general documentary footage description
  - Replaces claude-video-analyzer's generic prompts (promotional, gameplay, security, etc.)
- No import or invocation of claude-video-analyzer skill at any point.

#### Two-pass analysis workflow

**Pass 1 — Scene-Detection Triage (cheap):**
1. Run PySceneDetect (`ContentDetector`) on each video → scene boundaries
2. Extract 1 representative frame per scene (middle frame)
3. Send representative frames to Claude vision in batches with the triage prompt
4. Claude classifies each scene: `relevant` / `irrelevant` / `maybe`
5. Present triage results — user can override classifications before deep analysis

**Pass 2 — Deep Analysis (expensive, targeted):**
1. For scenes marked `relevant` or `maybe`: extract frames at 2fps within that scene's time range
2. Run full vision analysis with documentary context prompt
3. Identify usable segments with timestamps, descriptions, mood, era, relevance
4. The rest of the workflow continues as current V1 (catalog in SQLite, present for review)

**Expected savings:** Typical video has 50-200 scenes. If 10-15% are relevant, deep analysis covers ~500 frames per 30-min video instead of ~3,600. Roughly 7x reduction in vision tokens.

#### Input change
- Reads `download_manifest.json` (from vid-downloader) instead of `media_leads.json` for video context
- Still reads `shotlist.json` for visual needs matching
- Provenance from the manifest tells asset-analyzer the category and source context for each file

#### Everything else stays the same
- Standalone mode and project mode
- Segment identification schema
- SQLite cataloging via `data/catalog.py`
- V1 (analysis + timestamps + cataloging) and V2 (clip extraction) workflow split
- Human review checkpoints
- Output schema (`video_analysis.json`)

**Updated checkpoints:**

| After | Agent Presents | Human Decides |
|-------|---------------|---------------|
| Pass 1 (triage) | Scene classification table per video, token estimate for deep pass | Override classifications, approve deep analysis |
| Pass 1 estimate | Token/cost estimate for deep pass only | Approve, adjust, or stop |
| Pass 2 (analysis) | Segment table with timestamps | Approve/reject segments, adjust scope/category |
| V2 (cleanup) | Extraction complete | Delete staging files or keep |

### 5. claude-video-analyzer — No Changes

Remains a general-purpose standalone video analysis tool. Not part of the documentary pipeline. Available for ad-hoc video analysis outside the pipeline context.

---

## New Dependencies

| Dependency | Used by | Purpose | Installation |
|------------|---------|---------|-------------|
| PySceneDetect | asset-analyzer | Scene boundary detection for triage pass | `pip install scenedetect[opencv]` in asset-analyzer venv or base conda |
| ffmpeg | vid-downloader, asset-analyzer | Video probing, frame extraction, clip cutting | Already installed |
| yt-dlp | vid-downloader | YouTube video download | Already installed |
| opencv-python-headless | asset-analyzer | Frame processing (already a dependency) | Already installed |

---

## Files Created / Modified

| File | Action | Description |
|------|--------|-------------|
| `.claude/skills/vid-downloader/SKILL.md` | Create | New skill definition |
| `.claude/skills/vid-downloader/scripts/download.py` | Create | Download orchestration script (if needed beyond yt-dlp CLI) |
| `.claude/skills/asset-analyzer/SKILL.md` | Rewrite | Remove claude-video-analyzer dependency, add two-pass workflow |
| `.claude/skills/asset-analyzer/scripts/probe_video.py` | Create (fork) | From claude-video-analyzer |
| `.claude/skills/asset-analyzer/scripts/estimate_cost.py` | Create (fork) | Modified for two-pass cost estimation |
| `.claude/skills/asset-analyzer/scripts/extract_frames.py` | Create (fork) | From claude-video-analyzer |
| `.claude/skills/asset-analyzer/scripts/scene_detect.py` | Create | PySceneDetect wrapper |
| `.claude/skills/asset-analyzer/prompts/vision_prompts.md` | Create | Documentary-specific vision prompts |
| `.claude/skills/media-scout/SKILL.md` | Edit | Remove Pass 2 Step 7, update schema, remove download audit checks |
| `.claude/Architecture.md` | Edit | Update pipeline diagram and asset pipeline section |
| `CLAUDE.md` | Edit | Update skill routing table |
| `CONTEXT.md` | Edit | Update task routing for vid-downloader, update asset-analyzer load list |

---

## Out of Scope

- Vector generation (ComfyUI pipeline) — planned separately
- Asset Library (LanceDB semantic search) — separate infrastructure, not affected by this redesign
- Audio analysis — not supported, flagged to user
- claude-video-analyzer improvements — independent of this work
